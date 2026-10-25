// C17 (designs/winograd_t4_windows32_v1) 的平铺版本，只用于阅读和分析。
//
// 与原版的关系：
//   - 计算、数据流结构、所有 HLS pragma、FIFO 深度都和原版一样。
//   - 编译宏已经代入：T=4, EXP_ALL_CONTINUOUS=1, EXP_ONLINE_PAD=1,
//     EXP_W_BITS=10, EXP_A_BITS=10, EXP_C*_SPLIT=0, 没有定义 EXP_ROW_LUTRAM。
//   - 位宽按综合 (__SYNTHESIS__) 时的 ap_int 写出；原版 C 仿真时用 int16/int32/int64 代替。
//   - 函数名、循环标签、变量名尽量保持原样，方便和 HLS 报告对照。
//
// 原版名字 → 这里的写法：
//   weight, bias, input, act1, act2, output   → ap_int<10>
//   weight2                                   → ap_int<8>
//   acc1, acc2, acc3                          → ap_int<23>
//   mixed_acc                                 → ap_int<21>
//   transformed_input / transformed_weight    → ap_int<12> / ap_int<14>
//   inverse                                   → ap_int<34>
//   word<27>                                  → ap_int<27>
//   Reduction<64>::sum, Reduction<256>::sum   → add_tree_64, add_tree_256
//   online_pad<input,4>, online_pad<pixel2,2> → online_pad1, online_pad3
//   quantize<9>, quantize<8>(21 位), quantize<8>(23 位) → quantize_conv1/2/3
//   load_local(...)                           → 直接写进 engine3
//   T=4, WOC=4, PAIRS=4, C3_IC=8, COUNT=256, TILE_H=TILE_W=128
//
// 定点格式（存的整数 = 实数 × 2^小数位数）：
//   输入像素、conv1 输出、最终输出  ap_int<10>，8 位小数 (ap_fixed<10,2>)
//   conv2 输出                    ap_int<10>，7 位小数
//   conv1、conv3 的权重和偏置      ap_int<10>，9 位小数 (ap_fixed<10,1>)
//   conv2 的权重和偏置             ap_int<8>， 7 位小数 (ap_fixed<8,1>)
//   累加器                         ap_int<23>
//
// 数据流 (dataflow_region 里的进程，箭头是 hls::stream)：
//   read_input → online_pad1 → conv1 → conv2 → online_pad3 → conv3 → write_output
//   conv1 = wino_windows → wino_engine → distribute_tiles → reorder_rows
//   conv3 = windows3 → engine3
//   read_params = read_raw_params → transform_params1，分别把权重送给三层

#include <ap_int.h>
#include <ap_fixed.h>
#include <hls_stream.h>
#include <utils/x_hls_utils.h>   // fp_struct<float>：直接拼出 float 的符号、指数、尾数

struct pixel1 { ap_int<10> v[64]; };               // conv1 输出的一个像素，64 通道
struct pixel2 { ap_int<10> v[32]; };               // conv2 输出的一个像素，32 通道
struct window3 { ap_int<10> v[400]; };             // conv3 的 5x5 窗口，只放一半通道：25 × 16 = 400
struct transformed_params1 { ap_int<14> v[16]; };  // 一个 3x3 子核做 Winograd 变换后的 4x4 = 16 个数
struct transformed_window { ap_int<12> v[9][16]; };// 一个 10x10 输入块：9 个 4x4 子块，各自变换后 16 个数
struct tile_block { pixel1 pixel[4]; };            // conv1 一次算出的 2x2 = 4 个输出像素

// ---------------------------------------------------------------------------
// 浮点 ↔ 定点
// ---------------------------------------------------------------------------

static ap_int<10> encode_input(float value) {      // 输入像素 → 8 位小数
#pragma HLS INLINE
    ap_fixed<10, 2, AP_RND_CONV, AP_SAT> q = value;
    ap_int<10> bits = q.range();                    // 取出原始位，当整数用
    return bits;
}

static ap_int<10> encode_weight(float value) {     // conv1、conv3 参数 → 9 位小数
#pragma HLS INLINE
    ap_fixed<10, 1, AP_RND_CONV, AP_SAT> q = value;
    ap_int<10> bits = q.range();
    return bits;
}

static ap_int<8> encode_weight2(float value) {     // conv2 参数 → 8 位宽、7 位小数
#pragma HLS INLINE
    ap_fixed<8, 1, AP_RND_CONV, AP_SAT> q = value;
    ap_int<8> bits = q.range();
    return bits;
}

// 输出 value / 256 对应的 float。
// 不用整数转浮点的 IP，而是找最高位的 1，直接拼出 float 的位，结果是精确的。
static float decode(ap_int<10> value) {
#pragma HLS INLINE
    const bool negative = value < 0;
    const ap_int<11> signed_value = value;          // 多 1 位，-512 取反时不会溢出
    ap_uint<10> magnitude;
    if (negative) magnitude = -signed_value;
    else magnitude = signed_value;
    ap_uint<5> high = 0;                            // 最高位 1 的位置
    ieee_high_bit: for (int bit = 0; bit < 10; ++bit) {
#pragma HLS UNROLL
        if (magnitude[bit]) high = bit;
    }
    fp_struct<float> result;
    result.sign = negative;
    result.exp = 0;
    if (magnitude != 0) result.exp = 127 - 8 + high;   // 8 = 小数位数
    result.sig = ap_uint<32>(magnitude) << (23 - high);
    return result.to_ieee();
}

// 去掉多余的小数位：四舍五入到偶数 (round half to even)，再饱和到 10 位 [-512, 511]。
// conv1：17 位小数 (8+9) → 8 位小数，去掉 9 位
static ap_int<10> quantize_conv1(ap_int<23> sum) {
#pragma HLS INLINE
    ap_int<23> base = sum >> 9;
    const ap_int<23> remainder = sum & 511;          // 被去掉的低 9 位
    const int half = 256;
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    if (base < -512) return ap_int<10>(-512);
    if (base > 511) return ap_int<10>(511);
    return ap_int<10>(base);
}

// conv2：15 位小数 (8+7) → 7 位小数，去掉 8 位；输入已经截成 21 位
static ap_int<10> quantize_conv2(ap_int<21> sum) {
#pragma HLS INLINE
    ap_int<21> base = sum >> 8;
    const ap_int<21> remainder = sum & 255;
    const int half = 128;
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    if (base < -512) return ap_int<10>(-512);
    if (base > 511) return ap_int<10>(511);
    return ap_int<10>(base);
}

// conv3：16 位小数 (7+9) → 8 位小数，去掉 8 位
static ap_int<10> quantize_conv3(ap_int<23> sum) {
#pragma HLS INLINE
    ap_int<23> base = sum >> 8;
    const ap_int<23> remainder = sum & 255;
    const int half = 128;
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    if (base < -512) return ap_int<10>(-512);
    if (base > 511) return ap_int<10>(511);
    return ap_int<10>(base);
}

static ap_int<10> relu1(ap_int<23> sum) {
#pragma HLS INLINE
    return sum > 0 ? quantize_conv1(sum) : ap_int<10>(0);
}

// 偏置（9 位小数）左移，对齐到累加器的小数位
static ap_int<23> bias1(ap_int<10> value) {         // → 17 位小数，conv1 用
#pragma HLS INLINE
    return ap_int<23>(value) * 256;
}
static ap_int<23> bias3(ap_int<10> value) {         // → 16 位小数，conv3 用
#pragma HLS INLINE
    return ap_int<23>(value) * 128;
}

// ---------------------------------------------------------------------------
// 加法树：每一级把相邻两个数相加，数量减半；每级加法用 LUT 实现并打一拍 (latency=1)
// ---------------------------------------------------------------------------

static ap_int<23> add_tree_64(ap_int<23> x[64]) {   // 64→32→16→8→4→2→1，6 级
#pragma HLS INLINE
    for (int level = 0; level < 6; ++level) {
#pragma HLS UNROLL
        const int n = 32 >> level;                   // 这一级的加法个数
        for (int i = 0; i < 32; ++i) {
#pragma HLS UNROLL
            if (i < n) {
                ap_int<23> value = x[2*i] + x[2*i+1];
#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1
                x[i] = value;
            }
        }
    }
    return x[0];
}

static ap_int<23> add_tree_256(ap_int<23> x[256]) { // 256→128→…→1，8 级
#pragma HLS INLINE
    for (int level = 0; level < 8; ++level) {
#pragma HLS UNROLL
        const int n = 128 >> level;
        for (int i = 0; i < 128; ++i) {
#pragma HLS UNROLL
            if (i < n) {
                ap_int<23> value = x[2*i] + x[2*i+1];
#pragma HLS BIND_OP variable=value op=add impl=fabric latency=1
                x[i] = value;
            }
        }
    }
    return x[0];
}

// ---------------------------------------------------------------------------
// Winograd F(2x2, 3x3)：4x4 输入块 × 3x3 核 → 2x2 输出，16 次乘法代替 36 次。
// 变换里的加减法全部强制用 LUT (fabric)，不让 HLS 把它们放进 DSP。
// ---------------------------------------------------------------------------

static ap_int<12> add12(ap_int<12> a, ap_int<12> b) {
#pragma HLS INLINE
    ap_int<12> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
static ap_int<12> sub12(ap_int<12> a, ap_int<12> b) {
#pragma HLS INLINE
    ap_int<12> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}
static ap_int<14> add14(ap_int<14> a, ap_int<14> b) {
#pragma HLS INLINE
    ap_int<14> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
static ap_int<14> sub14(ap_int<14> a, ap_int<14> b) {
#pragma HLS INLINE
    ap_int<14> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}
static ap_int<34> add34(ap_int<34> a, ap_int<34> b) {
#pragma HLS INLINE
    ap_int<34> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
static ap_int<34> sub34(ap_int<34> a, ap_int<34> b) {
#pragma HLS INLINE
    ap_int<34> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}

// 输入变换 B^T d B：4x4 输入 (10 位) → 4x4 (12 位)
static void input_transform(const ap_int<10> data[16], ap_int<12> value[16]) {
#pragma HLS INLINE
    ap_int<12> temp[16];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
        temp[c]    = sub12(data[c],   data[8+c]);
        temp[4+c]  = add12(data[4+c], data[8+c]);
        temp[8+c]  = sub12(data[8+c], data[4+c]);
        temp[12+c] = sub12(data[4+c], data[12+c]);
    }
    for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
        value[4*r]   = sub12(temp[4*r],   temp[4*r+2]);
        value[4*r+1] = add12(temp[4*r+1], temp[4*r+2]);
        value[4*r+2] = sub12(temp[4*r+2], temp[4*r+1]);
        value[4*r+3] = sub12(temp[4*r+1], temp[4*r+3]);
    }
}

// 权重变换 G g G^T：3x3 核 (10 位) → 4x4 (14 位)。
// 标准 G 里有 1/2，这里把 G 乘 2 变成整数，两边各乘 2，结果放大 4 倍，wino_engine 最后右移 2 位还原。
static void weight_transform(const ap_int<10> kernel[9], ap_int<14> value[16]) {
#pragma HLS INLINE
    ap_int<14> temp[12];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 3; ++c) {
#pragma HLS UNROLL
        temp[c]   = ap_int<14>(kernel[c]) * 2;
        temp[3+c] = add14(add14(kernel[c], kernel[3+c]), kernel[6+c]);
        temp[6+c] = add14(sub14(kernel[c], kernel[3+c]), kernel[6+c]);
        temp[9+c] = ap_int<14>(kernel[6+c]) * 2;
    }
    for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
        value[4*r]   = temp[3*r] * 2;
        value[4*r+1] = add14(add14(temp[3*r], temp[3*r+1]), temp[3*r+2]);
        value[4*r+2] = add14(sub14(temp[3*r], temp[3*r+1]), temp[3*r+2]);
        value[4*r+3] = temp[3*r+2] * 2;
    }
}

// 输出变换 A^T m A：4x4 (34 位) → 2x2 输出
static void output_transform(const ap_int<34> value[16], ap_int<34> output[4]) {
#pragma HLS INLINE
    ap_int<34> temp[8];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
        temp[c]   = add34(add34(value[c], value[4+c]), value[8+c]);
        temp[4+c] = sub34(sub34(value[4+c], value[8+c]), value[12+c]);
    }
    for (int r = 0; r < 2; ++r) {
#pragma HLS UNROLL
        output[2*r]   = add34(add34(temp[4*r], temp[4*r+1]), temp[4*r+2]);
        output[2*r+1] = sub34(sub34(temp[4*r+1], temp[4*r+2]), temp[4*r+3]);
    }
}

// ---------------------------------------------------------------------------
// 输入图像：255 x 255 float → 定点像素流
// ---------------------------------------------------------------------------

static void read_input(float in[1][255][255], hls::stream<ap_int<10> > &stream) {
    read_pixels: for (int i = 0; i < 255 * 255; ++i) {
#pragma HLS PIPELINE II=1
        stream.write(encode_input(in[0][i / 255][i % 255]));
    }
}

// ---------------------------------------------------------------------------
// 边缘复制填充（边读边写，只缓存一行）
// ---------------------------------------------------------------------------

// conv1 前：四周各补 4 圈，右边和下边再多补 1 → 264 x 264。
// 多补的那一行一列让 2x2 输出块刚好铺满：(264 - 10) / 2 + 1 = 128 块。
static void online_pad1(hls::stream<ap_int<10> > &in, hls::stream<ap_int<10> > &out) {
    ap_int<10> row[255];                             // 最近一行，最后用来补下边
#pragma HLS AGGREGATE variable=row compact=bit
#pragma HLS BIND_STORAGE variable=row type=ram_2p impl=bram
    online_first_read: for (int x = 0; x < 255; ++x) {
#pragma HLS PIPELINE II=1
        row[x] = in.read();
    }
    online_first_repeats: for (int y = 0; y <= 4; ++y)   // 上边 4 行 + 第 0 行
        online_first_write: for (int x = 0; x < 264; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 4 ? 0 : x >= 259 ? 254 : x - 4;
            out.write(row[sx]);
        }
    online_rows: for (int y = 1; y < 255; ++y) {         // 第 1..254 行
        ap_int<10> value;
        online_columns: for (int x = 0; x < 264; ++x) {
#pragma HLS PIPELINE II=1
            // x=0 读第 0 列；x=1..4 重复它（左边）；x=5..258 读第 1..254 列；x>=259 重复最后一列（右边）
            if (x == 0 || (x > 4 && x < 259)) {
                value = in.read();
                row[x == 0 ? 0 : x - 4] = value;
            }
            out.write(value);
        }
    }
    online_bottom_repeats: for (int y = 0; y < 5; ++y)   // 下边 4 行 + 多补的 1 行
        online_bottom_write: for (int x = 0; x < 264; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 4 ? 0 : x >= 259 ? 254 : x - 4;
            out.write(row[sx]);
        }
}

// conv3 前：四周各补 2 圈 → 259 x 259，每个像素 32 通道
static void online_pad3(hls::stream<pixel2> &in, hls::stream<pixel2> &out) {
    pixel2 row[255];
#pragma HLS AGGREGATE variable=row compact=bit
#pragma HLS BIND_STORAGE variable=row type=ram_2p impl=bram
    online_first_read: for (int x = 0; x < 255; ++x) {
#pragma HLS PIPELINE II=1
        row[x] = in.read();
    }
    online_first_repeats: for (int y = 0; y <= 2; ++y)   // 上边 2 行 + 第 0 行
        online_first_write: for (int x = 0; x < 259; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 2 ? 0 : x >= 257 ? 254 : x - 2;
            out.write(row[sx]);
        }
    online_rows: for (int y = 1; y < 255; ++y) {
        pixel2 value;
        online_columns: for (int x = 0; x < 259; ++x) {
#pragma HLS PIPELINE II=1
            if (x == 0 || (x > 2 && x < 257)) {
                value = in.read();
                row[x == 0 ? 0 : x - 2] = value;
            }
            out.write(value);
        }
    }
    online_bottom_repeats: for (int y = 0; y < 2; ++y)   // 下边 2 行
        online_bottom_write: for (int x = 0; x < 259; ++x) {
#pragma HLS PIPELINE II=1
            const int sx = x < 2 ? 0 : x >= 257 ? 254 : x - 2;
            out.write(row[sx]);
        }
}

// ---------------------------------------------------------------------------
// 参数：从 DDR 读 float，转定点，按层分到三个流
// ---------------------------------------------------------------------------

// 一共 8129 个参数，按下面的顺序读：
//   [0, 5184)     conv1 权重 64 × 81
//   [5184, 5248)  conv1 偏置 64
//   [5248, 7296)  conv2 权重 32 × 64（编码成 8 位）
//   [7296, 7328)  conv2 偏置 32（编码成 8 位）
//   [7328, 8128)  conv3 权重 32 × 25
//   [8128, 8129)  conv3 偏置 1
static void read_raw_params(float weights1[64][1][9][9], float biases1[64],
                            float weights2[32][64][1][1], float biases2[32],
                            float weights3[1][32][5][5], float biases3[1],
                            hls::stream<ap_int<10> > &raw1, hls::stream<ap_int<10> > &params2,
                            hls::stream<ap_int<10> > &params3) {
    int oc1 = 0, ky1 = 0, kx1 = 0;                   // 用计数器代替除法算下标
    int ic3 = 0, ky3 = 0, kx3 = 0;
    read_all_params: for (int i = 0; i < 8129; ++i) {
#pragma HLS PIPELINE II=1
        float value;
        if (i < 5184) {
            value = weights1[oc1][0][ky1][kx1];
            if (kx1 == 8) {
                kx1 = 0;
                if (ky1 == 8) { ky1 = 0; ++oc1; }
                else ++ky1;
            } else ++kx1;
        } else if (i < 5248) value = biases1[i - 5184];
        else if (i < 7296) value = weights2[(i - 5248) / 64][(i - 5248) % 64][0][0];
        else if (i < 7328) value = biases2[i - 7296];
        else if (i < 8128) {
            value = weights3[0][ic3][ky3][kx3];
            if (kx3 == 4) {
                kx3 = 0;
                if (ky3 == 4) { ky3 = 0; ++ic3; }
                else ++ky3;
            } else ++kx3;
        } else value = biases3[0];
        // conv2 参数是 8 位，先符号扩展到 10 位放进同一种流，conv2 里再截回 8 位
        const ap_int<10> encoded = i >= 5248 && i < 7328 ? ap_int<10>(encode_weight2(value))
                                                         : encode_weight(value);
        if (i < 5248) raw1.write(encoded);
        else if (i < 7328) params2.write(encoded);
        else params3.write(encoded);
    }
}

// conv1 的 9x9 核拆成 3x3 个 3x3 子核（group），每个子核做 Winograd 权重变换。
// 输出：64 个通道 × 9 个子核的变换结果，然后 64 个偏置（放在 packet.v[0]）。
static void transform_params1(hls::stream<ap_int<10> > &raw1, hls::stream<transformed_params1> &params1) {
    ap_int<10> raw[9][9];                            // [子核编号][子核内位置]
#pragma HLS ARRAY_PARTITION variable=raw complete dim=0
    transform_channels: for (int oc = 0; oc < 64; ++oc) {
        transform_read_rows: for (int row = 0; row < 9; ++row)
            transform_read_columns: for (int column = 0; column < 9; ++column) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
                const int group = (row / 3) * 3 + column / 3;
                const int tap = (row % 3) * 3 + column % 3;
                raw[group][tap] = raw1.read();
            }
        transform_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS PIPELINE II=1
            ap_int<10> kernel[9];
            transformed_params1 packet;
#pragma HLS ARRAY_PARTITION variable=kernel complete
#pragma HLS ARRAY_PARTITION variable=packet.v complete
            for (int tap = 0; tap < 9; ++tap) {
#pragma HLS UNROLL
                kernel[tap] = raw[group][tap];
            }
            weight_transform(kernel, packet.v);
            params1.write(packet);
        }
    }
    transform_bias: for (int oc = 0; oc < 64; ++oc) {
#pragma HLS PIPELINE II=1
        transformed_params1 packet;
        for (int field = 0; field < 16; ++field) {
#pragma HLS UNROLL
            packet.v[field] = 0;
        }
        packet.v[0] = raw1.read();
        params1.write(packet);
    }
}

static void read_params(float weights1[64][1][9][9], float biases1[64],
                        float weights2[32][64][1][1], float biases2[32],
                        float weights3[1][32][5][5], float biases3[1],
                        hls::stream<transformed_params1> &params1,
                        hls::stream<ap_int<10> > &params2, hls::stream<ap_int<10> > &params3) {
#pragma HLS DATAFLOW
    hls::stream<ap_int<10> > raw1("raw_conv1_params");
#pragma HLS STREAM variable=raw1 depth=16
#pragma HLS BIND_STORAGE variable=raw1 type=fifo impl=lutram
    read_raw_params(weights1, biases1, weights2, biases2, weights3, biases3, raw1, params2, params3);
    transform_params1(raw1, params1);
}

// ---------------------------------------------------------------------------
// conv1：9x9 卷积，1 → 64 通道，Winograd
// ---------------------------------------------------------------------------

// 用 9 行行缓存在 264 x 264 的填充图上滑一个 10x10 窗口，横竖每次走 2 步。
// 每个 10x10 窗口对应 2x2 个输出像素；把它拆成 3x3 个互相重叠的 4x4 子块（起点间隔 3），
// 每个子块做输入变换。一共 128 x 128 个窗口。
static void wino_windows(hls::stream<ap_int<10> > &in, hls::stream<transformed_window> &out) {
    static ap_int<10> line[9][264], window[10][10];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    wino_make_windows: for (int p = 0; p < 264 * 264; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p / 264, x = p % 264;
        ap_int<10> column[10];                       // 当前列从上到下 10 个像素
#pragma HLS ARRAY_PARTITION variable=column complete
        for (int r = 0; r < 9; ++r) {
#pragma HLS UNROLL
            column[r] = line[r][x];
        }
        column[9] = in.read();
        for (int r = 0; r < 9; ++r) {                // 行缓存整体上移一行
#pragma HLS UNROLL
            line[r][x] = column[r+1];
        }
        for (int r = 0; r < 10; ++r) {               // 窗口左移一列，新列放最右边
#pragma HLS UNROLL
            for (int c = 0; c < 9; ++c) {
#pragma HLS UNROLL
                window[r][c] = window[r][c+1];
            }
            window[r][9] = column[r];
        }
        if (y >= 9 && x >= 9 && (y - 9) % 2 == 0 && (x - 9) % 2 == 0) {
            transformed_window result;
#pragma HLS ARRAY_PARTITION variable=result.v complete dim=0
            for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
                ap_int<10> data[16];
#pragma HLS ARRAY_PARTITION variable=data complete
                for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                    data[j] = window[group / 3 * 3 + j / 4][group % 3 * 3 + j % 4];
                }
                input_transform(data, result.v[group]);
            }
            out.write(result);
        }
    }
}

// 每个窗口花 16 拍：每拍算 4 个输出通道（4 条 lane），16 拍算完 64 个通道。
// 每条 lane 每拍做 9 个子块 × 16 = 144 次乘法，4 条 lane 共 576 个 DSP 乘法。
static void wino_engine(hls::stream<transformed_window> &in, hls::stream<tile_block> &out,
                        hls::stream<transformed_params1> &params) {
    static ap_int<14> weights[64][9][16];            // [输出通道][子核][变换后位置]
    static ap_int<10> biases[64];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=weights complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete dim=3
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=biases complete
    wino_local_load_channels: for (int oc = 0; oc < 64; ++oc)
        wino_local_load_groups: for (int group = 0; group < 9; ++group) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const transformed_params1 packet = params.read();
            for (int tap = 0; tap < 16; ++tap) {
#pragma HLS UNROLL
                weights[oc][group][tap] = packet.v[tap];
            }
        }
    wino_local_load_bias: for (int oc = 0; oc < 64; ++oc) {   // 移位寄存器方式装偏置
#pragma HLS PIPELINE II=1
        const transformed_params1 packet = params.read();
        for (int c = 0; c < 63; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[63] = ap_int<10>(packet.v[0]);
    }
    transformed_window value;
    tile_block tile;
#pragma HLS ARRAY_PARTITION variable=value.v complete dim=0
#pragma HLS ARRAY_PARTITION variable=tile.pixel complete dim=0
    continuous_wino_fold: for (int iteration = 0; iteration < 128 * 128 * 16; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration % 16;
        if (step == 0) value = in.read();            // 每 16 拍读一个新窗口
        ap_int<10> next[4][4];                        // [2x2 中的哪个像素][lane]
#pragma HLS ARRAY_PARTITION variable=next complete dim=0
        for (int lane = 0; lane < 4; ++lane) {
#pragma HLS UNROLL
            const int oc = step * 4 + lane;
            ap_int<34> m[16], result[4];
#pragma HLS ARRAY_PARTITION variable=m complete
#pragma HLS ARRAY_PARTITION variable=result complete
            for (int j = 0; j < 16; ++j) {
#pragma HLS UNROLL
                ap_int<34> sum = 0;                  // 9 个子块在变换域里直接相加
                for (int group = 0; group < 9; ++group) {
#pragma HLS UNROLL
                    ap_int<26> product = value.v[group][j] * weights[oc][group][j];   // 12 位 × 14 位
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                    sum = add34(sum, product);
                }
                m[j] = sum;
            }
            output_transform(m, result);
            for (int j = 0; j < 4; ++j) {
#pragma HLS UNROLL
                // 权重变换放大了 4 倍，result 一定是 4 的倍数，右移 2 位还原
                next[j][lane] = relu1(ap_int<23>(result[j] >> 2) + bias1(biases[oc]));
            }
        }
        // tile 里 64 个通道当移位寄存器：每拍整体左移 4 个，新算的 4 个通道放最后，16 拍后正好按 0..63 排好
        for (int j = 0; j < 4; ++j) {
#pragma HLS UNROLL
            for (int c = 0; c < 60; ++c) {
#pragma HLS UNROLL
                tile.pixel[j].v[c] = tile.pixel[j].v[c+4];
            }
            for (int lane = 0; lane < 4; ++lane) {
#pragma HLS UNROLL
                tile.pixel[j].v[60 + lane] = next[j][lane];
            }
        }
        if (step == 15) out.write(tile);
    }
}

// 2x2 输出块 → 上下两行分开：上面两个像素进 top，下面两个进 bottom。
// 第 255 行和第 255 列是多补出来的，丢掉。
static void distribute_tiles(hls::stream<tile_block> &in, hls::stream<pixel1> &top,
                             hls::stream<pixel1> &bottom) {
    tile_block value;
#pragma HLS ARRAY_PARTITION variable=value.pixel complete dim=0
    distribute_tile_pixels: for (int p = 0; p < 128 * 128 * 4; ++p) {
#pragma HLS PIPELINE II=1
        const int j = p % 4, tile = p / 4;
        if (j == 0) value = in.read();
        const int y = 2 * (tile / 128) + j / 2;
        const int x = 2 * (tile % 128) + j % 2;
        if (y < 255 && x < 255) {
            if (j < 2) top.write(value.pixel[j]);
            else bottom.write(value.pixel[j]);
        }
    }
}

// 恢复成逐行扫描顺序：偶数行从 top 取，奇数行从 bottom 取
static void reorder_rows(hls::stream<pixel1> &top, hls::stream<pixel1> &bottom,
                         hls::stream<pixel1> &out) {
    raster_rows: for (int y = 0; y < 255; ++y)
        raster_columns: for (int x = 0; x < 255; ++x) {
#pragma HLS PIPELINE II=1
            out.write(y % 2 ? bottom.read() : top.read());
        }
}

static void conv1_stream(hls::stream<ap_int<10> > &in, hls::stream<pixel1> &out,
                         hls::stream<transformed_params1> &params) {
#pragma HLS DATAFLOW
    hls::stream<transformed_window> windows("wino_windows");
    hls::stream<tile_block> tiles("wino_tile_blocks");
    hls::stream<pixel1> top("wino_top_rows"), bottom("wino_bottom_rows");
#pragma HLS STREAM variable=windows depth=32
#pragma HLS STREAM variable=tiles depth=2
#pragma HLS BIND_STORAGE variable=windows type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=tiles type=fifo impl=lutram
#pragma HLS STREAM variable=top depth=512
#pragma HLS STREAM variable=bottom depth=512
    wino_windows(in, windows);
    wino_engine(windows, tiles, params);
    distribute_tiles(tiles, top, bottom);
    reorder_rows(top, bottom, out);
}

// ---------------------------------------------------------------------------
// conv2：1x1 卷积，64 → 32 通道
// ---------------------------------------------------------------------------

// 一个 DSP 乘法同时算两个输出通道：把两个 8 位权重拼进一个 27 位数
//   packed = first * 2^18 + second
//   packed * x = first*x * 2^18 + second*x
// second*x 在 18 位有符号范围内，所以低 18 位就是 second*x，高位就是 first*x
// （低 18 位是负数时高位被借了 1，要加回来）。
// 每像素 4 拍：每拍 4 条 lane，每条 lane 算 2 个通道，4 拍算完 32 个通道。
// 每拍 4 × 64 = 256 个 DSP 乘法。
static void conv2_stream(hls::stream<pixel1> &in, hls::stream<pixel2> &out,
                         hls::stream<ap_int<10> > &params) {
    static ap_int<27> packed_weights[16][64];        // [通道对][输入通道]
    static ap_int<8> biases[32];
    ap_int<8> first_row[64];
#pragma HLS ARRAY_PARTITION variable=packed_weights cyclic factor=4 dim=1
#pragma HLS ARRAY_PARTITION variable=packed_weights complete dim=2
#pragma HLS BIND_STORAGE variable=packed_weights type=ram_s2p impl=lutram
#pragma HLS ARRAY_PARTITION variable=first_row complete
#pragma HLS ARRAY_PARTITION variable=biases complete
    packed_load_pairs: for (int pair = 0; pair < 16; ++pair) {
        packed_load_first: for (int ic = 0; ic < 64; ++ic) {     // 通道 2*pair 的权重
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            first_row[ic] = ap_int<8>(params.read());
        }
        packed_load_second: for (int ic = 0; ic < 64; ++ic) {    // 通道 2*pair+1 的权重
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            const ap_int<8> second = ap_int<8>(params.read());
            packed_weights[pair][ic] = ap_int<27>(first_row[ic]) * 262144 + ap_int<27>(second);   // 262144 = 2^18
        }
    }
    packed_load_bias: for (int i = 0; i < 32; ++i) {
#pragma HLS PIPELINE II=1
        for (int c = 0; c < 31; ++c) {
#pragma HLS UNROLL
            biases[c] = biases[c+1];
        }
        biases[31] = ap_int<8>(params.read());
    }
    pixel1 value;
    pixel2 result;
#pragma HLS ARRAY_PARTITION variable=value.v complete
#pragma HLS ARRAY_PARTITION variable=result.v complete
    continuous_c2_fold: for (int iteration = 0; iteration < 255 * 255 * 4; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration % 4;
        if (step == 0) value = in.read();            // 每 4 拍读一个新像素
        ap_int<10> next[8];
#pragma HLS ARRAY_PARTITION variable=next complete
        for (int lane = 0; lane < 4; ++lane) {
#pragma HLS UNROLL
            const int pair = step * 4 + lane, oc = 2 * pair;
            ap_int<23> first[64], second[64];
#pragma HLS ARRAY_PARTITION variable=first complete
#pragma HLS ARRAY_PARTITION variable=second complete
            for (int ic = 0; ic < 64; ++ic) {
#pragma HLS UNROLL
                ap_int<37> product = packed_weights[pair][ic] * value.v[ic];     // 27 位 × 10 位
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                const int bits = int(product & 262143);                 // 低 18 位
                const int low = bits >= 131072 ? bits - 262144 : bits;  // 当成 18 位有符号数
                first[ic] = ap_int<23>(product >> 18) + (low < 0 ? 1 : 0);
                second[ic] = low;
            }
            // 偏置 7 位小数，乘 256 对齐到乘积的 15 位小数
            const ap_int<23> sum0 = add_tree_64(first) + ap_int<23>(biases[oc]) * 256;
            const ap_int<23> sum1 = add_tree_64(second) + ap_int<23>(biases[oc+1]) * 256;
            // 截成 21 位：原版 C 仿真用 assert 检查过测试数据不会超出 21 位有符号范围（取决于权重）
            const ap_int<21> s0 = sum0, s1 = sum1;
            next[2*lane]   = s0 > 0 ? quantize_conv2(s0) : ap_int<10>(0);   // ReLU
            next[2*lane+1] = s1 > 0 ? quantize_conv2(s1) : ap_int<10>(0);
        }
        // 32 个通道当移位寄存器，每拍左移 8 个，4 拍后按 0..31 排好
        for (int c = 0; c < 24; ++c) {
#pragma HLS UNROLL
            result.v[c] = result.v[c+8];
        }
        for (int c = 0; c < 8; ++c) {
#pragma HLS UNROLL
            result.v[24 + c] = next[c];
        }
        if (step == 3) out.write(result);
    }
}

static void conv12(hls::stream<ap_int<10> > &in, hls::stream<pixel2> &out,
                   hls::stream<transformed_params1> &params1, hls::stream<ap_int<10> > &params2) {
#pragma HLS DATAFLOW
    hls::stream<pixel1> features("conv1_features");
#pragma HLS STREAM variable=features depth=4
#pragma HLS BIND_STORAGE variable=features type=fifo impl=lutram
    conv1_stream(in, features, params1);
    conv2_stream(features, out, params2);
}

// ---------------------------------------------------------------------------
// conv3：5x5 卷积，32 → 1 通道
// ---------------------------------------------------------------------------

// 4 行行缓存在 259 x 259 的填充图上滑 5x5 窗口，每个位置输出一个窗口。
// 窗口太宽，按通道拆成两半：0..15 进 out0，16..31 进 out1。
static void windows3(hls::stream<pixel2> &in, hls::stream<window3> &out0, hls::stream<window3> &out1) {
    static ap_int<10> line[4][259][32], window[5][5][32];
#pragma HLS ARRAY_PARTITION variable=line complete dim=1
#pragma HLS ARRAY_RESHAPE variable=line complete dim=3
#pragma HLS BIND_STORAGE variable=line type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    make_windows3: for (int p = 0; p < 259 * 259; ++p) {
#pragma HLS PIPELINE II=1
        const int y = p / 259, x = p % 259;
        const pixel2 value = in.read();
        window3 result0, result1;
#pragma HLS ARRAY_PARTITION variable=result0.v complete
#pragma HLS ARRAY_PARTITION variable=result1.v complete
        for (int ic = 0; ic < 32; ++ic) {
#pragma HLS UNROLL
            ap_int<10> column[5];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
                column[r] = line[r][x][ic];
            }
            column[4] = value.v[ic];
            for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
                line[r][x][ic] = column[r+1];
            }
            for (int r = 0; r < 5; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                    window[r][c][ic] = window[r][c+1][ic];
                }
                window[r][4][ic] = column[r];
                for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                    if (ic < 16) result0.v[(r * 5 + c) * 16 + ic] = window[r][c][ic];
                    else result1.v[(r * 5 + c) * 16 + ic - 16] = window[r][c][ic];
                }
            }
        }
        if (y >= 4 && x >= 4) {
            out0.write(result0);
            out1.write(result1);
        }
    }
}

// 每个输出像素 4 拍：每拍算 8 个输入通道 × 25 = 200 次乘法（200 个 DSP），
// 补 0 到 256 个后过加法树，再累加到 sum。
static void engine3(hls::stream<window3> &in0, hls::stream<window3> &in1, hls::stream<ap_int<10> > &out,
                    hls::stream<ap_int<10> > &params) {
    static ap_int<10> weights[32][25];               // [输入通道][5x5 位置]
    static ap_int<10> biases[1];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=8 dim=1
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=25 dim=2
#pragma HLS BIND_STORAGE variable=weights type=ram_s2p impl=lutram
    local_load_channels: for (int oc = 0; oc < 32; ++oc)
        local_load_taps: for (int tap = 0; tap < 25; ++tap) {
#pragma HLS LOOP_FLATTEN off
#pragma HLS PIPELINE II=1
            weights[oc][tap] = params.read();
        }
    local_load_bias: for (int i = 0; i < 1; ++i) {   // 只有 1 个偏置；保留循环和原版 load_local 一致
#pragma HLS PIPELINE II=1
        biases[0] = params.read();
    }
    window3 value0, value1;
    ap_int<23> sum = 0;
#pragma HLS ARRAY_PARTITION variable=value0.v complete
#pragma HLS ARRAY_PARTITION variable=value1.v complete
    continuous_c3_fold: for (int iteration = 0; iteration < 255 * 255 * 4; ++iteration) {
#pragma HLS PIPELINE II=1
        const int step = iteration % 4;
        if (step == 0) { value0 = in0.read(); value1 = in1.read(); }
        ap_int<23> products[256];
#pragma HLS ARRAY_PARTITION variable=products complete
        for (int index = 0; index < 256; ++index) {
#pragma HLS UNROLL
            if (index < 200) {
                const int ic = step * 8 + index / 25, tap = index % 25;
                ap_int<20> product = (ic < 16 ? value0.v[tap * 16 + ic] : value1.v[tap * 16 + ic - 16]) * weights[ic][tap];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
                products[index] = product;
            } else products[index] = 0;
        }
        const ap_int<23> partial = add_tree_256(products);
        // 第 0 拍从偏置开始，之后累加上一拍的 sum
        ap_int<23> next = (step == 0 ? bias3(biases[0]) : sum) + partial;
#pragma HLS BIND_OP variable=next op=add impl=fabric latency=1
        sum = next;
        if (step == 3) out.write(quantize_conv3(next));   // 没有 ReLU
    }
}

static void conv3_stream(hls::stream<pixel2> &in, hls::stream<ap_int<10> > &out,
                         hls::stream<ap_int<10> > &params) {
#pragma HLS DATAFLOW
    hls::stream<window3> windows0("windows3_low_channels"), windows1("windows3_high_channels");
#pragma HLS STREAM variable=windows0 depth=2
#pragma HLS STREAM variable=windows1 depth=2
#pragma HLS BIND_STORAGE variable=windows0 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=windows1 type=fifo impl=lutram
    windows3(in, windows0, windows1);
    engine3(windows0, windows1, out, params);
}

// ---------------------------------------------------------------------------
// 输出、顶层
// ---------------------------------------------------------------------------

static void write_output(hls::stream<ap_int<10> > &stream, float out[1][255][255]) {
    write_pixels: for (int i = 0; i < 255 * 255; ++i) {
#pragma HLS PIPELINE II=1
        out[0][i / 255][i % 255] = decode(stream.read());
    }
}

static void dataflow_region(float in[1][255][255], float out[1][255][255],
                            float weights1[64][1][9][9], float biases1[64],
                            float weights2[32][64][1][1], float biases2[32],
                            float weights3[1][32][5][5], float biases3[1]) {
#pragma HLS DATAFLOW
    hls::stream<ap_int<10> > raw("raw"), padded1("padded1");
    hls::stream<pixel2> features2("features2"), padded3("padded3");
    hls::stream<ap_int<10> > result("result");
    hls::stream<transformed_params1> params1("params1");
    hls::stream<ap_int<10> > params2("params2"), params3("params3");
#pragma HLS AGGREGATE variable=params1 compact=bit
#pragma HLS STREAM variable=params1 depth=4
#pragma HLS STREAM variable=params2 depth=16
#pragma HLS STREAM variable=params3 depth=16
#pragma HLS BIND_STORAGE variable=params1 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=params2 type=fifo impl=lutram
#pragma HLS BIND_STORAGE variable=params3 type=fifo impl=lutram
#pragma HLS STREAM variable=raw depth=512
#pragma HLS STREAM variable=padded1 depth=16
#pragma HLS STREAM variable=features2 depth=4
#pragma HLS BIND_STORAGE variable=features2 type=fifo impl=lutram
#pragma HLS STREAM variable=padded3 depth=16
#pragma HLS BIND_STORAGE variable=padded3 type=fifo impl=lutram
#pragma HLS STREAM variable=result depth=16
    read_input(in, raw);
    read_params(weights1, biases1, weights2, biases2, weights3, biases3, params1, params2, params3);
    online_pad1(raw, padded1);
    conv12(padded1, features2, params1, params2);
    online_pad3(features2, padded3);
    conv3_stream(padded3, result, params3);
    write_output(result, out);
}

void srcnn(float in[1][255][255], float weights1[64][1][9][9], float biases1[64],
           float weights2[32][64][1][1], float biases2[32],
           float weights3[1][32][5][5], float biases3[1], float out[1][255][255]) {
#pragma HLS INTERFACE mode=m_axi port=in offset=slave bundle=image_in depth=65025 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=out offset=slave bundle=image_out depth=65025 max_write_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=weights1 offset=slave bundle=parameters depth=5184 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases1 offset=slave bundle=parameters depth=64
#pragma HLS INTERFACE mode=m_axi port=weights2 offset=slave bundle=parameters depth=2048 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases2 offset=slave bundle=parameters depth=32
#pragma HLS INTERFACE mode=m_axi port=weights3 offset=slave bundle=parameters depth=800 max_read_burst_length=256
#pragma HLS INTERFACE mode=m_axi port=biases3 offset=slave bundle=parameters depth=1
#pragma HLS INTERFACE mode=s_axilite port=in bundle=control
#pragma HLS INTERFACE mode=s_axilite port=out bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights1 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases1 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights2 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases2 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=weights3 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=biases3 bundle=control
#pragma HLS INTERFACE mode=s_axilite port=return bundle=control
    dataflow_region(in, out, weights1, biases1, weights2, biases2, weights3, biases3);
}
