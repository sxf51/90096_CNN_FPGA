#include "srcnn.h"
#include "tile.h"

void srcnn(ftmap_t input_ftmap[N0][H][W],
           param_t conv1_weights[N1][N0][F1][F1],
           param_t conv1_biases[N1],
           param_t conv2_weights[N2][N1][F2][F2],
           param_t conv2_biases[N2],
           param_t conv3_weights[N3][N2][F3][F3],
           param_t conv3_biases[N3],
           ftmap_t output_ftmap[N3][H][W])
{
    // Implement end-to-end SRCNN here
    using namespace srcnn_tile;
#pragma HLS INTERFACE m_axi port=input_ftmap offset=slave bundle=image_in depth=65025 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=output_ftmap offset=slave bundle=image_out depth=65025 max_write_burst_length=64
#pragma HLS INTERFACE m_axi port=conv1_weights offset=slave bundle=params depth=5184
#pragma HLS INTERFACE m_axi port=conv1_biases offset=slave bundle=params depth=64
#pragma HLS INTERFACE m_axi port=conv2_weights offset=slave bundle=params depth=2048
#pragma HLS INTERFACE m_axi port=conv2_biases offset=slave bundle=params depth=32
#pragma HLS INTERFACE m_axi port=conv3_weights offset=slave bundle=params depth=800
#pragma HLS INTERFACE m_axi port=conv3_biases offset=slave bundle=params depth=1
#pragma HLS INTERFACE s_axilite port=input_ftmap bundle=control
#pragma HLS INTERFACE s_axilite port=output_ftmap bundle=control
#pragma HLS INTERFACE s_axilite port=conv1_weights bundle=control
#pragma HLS INTERFACE s_axilite port=conv1_biases bundle=control
#pragma HLS INTERFACE s_axilite port=conv2_weights bundle=control
#pragma HLS INTERFACE s_axilite port=conv2_biases bundle=control
#pragma HLS INTERFACE s_axilite port=conv3_weights bundle=control
#pragma HLS INTERFACE s_axilite port=conv3_biases bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    static weight_t w1[N1][N0][F1][F1];
    static weight_t w2[N2][N1];
    static weight_t w3[N2][F3*F3];
    accumulator_t b1[N1], b2[N2];
    static activation_t c1[N1][S*S];
    static activation_t c2[N2][V][S*S/V];
    accumulator_t sums[B*B];
    accumulator_t partial[P][S*S];
#pragma HLS ARRAY_PARTITION variable=partial complete dim=1
#pragma HLS BIND_STORAGE variable=partial type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=w1 cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS ARRAY_PARTITION variable=w2 cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS ARRAY_PARTITION variable=c1 cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS ARRAY_PARTITION variable=c2 cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS BIND_STORAGE variable=c1 type=ram_2p impl=bram
#if SRCNN_INT8
// Four adjacent Conv3 pixels read four banks; use small distributed RAM
// banks to avoid spending a whole BRAM18K on each shallow 8-bit bank.
#pragma HLS ARRAY_PARTITION variable=c2 complete dim=2
#pragma HLS ARRAY_PARTITION variable=sums cyclic factor=4 dim=1
#pragma HLS BIND_STORAGE variable=c2 type=ram_2p impl=lutram
#else
#pragma HLS BIND_STORAGE variable=c2 type=ram_2p impl=bram
#endif
#pragma HLS BIND_STORAGE variable=w1 type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=w2 type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=w3 type=ram_1p impl=bram
#pragma HLS BIND_STORAGE variable=sums type=ram_2p impl=bram
    // Runtime weights are refreshed on EVERY call, then reused across tiles.
    load_w1: for (int oc = 0; oc < N1; ++oc) {
        b1[oc] = bias(conv1_biases[oc], 48960);
        for (int ky = 0; ky < F1; ++ky)
            for (int kx = 0; kx < F1; ++kx) {
#pragma HLS PIPELINE II=1
                w1[oc][0][ky][kx] = weight(conv1_weights[oc][0][ky][kx], 192);
            }
    }
    load_w2: for (int oc = 0; oc < N2; ++oc) {
        b2[oc] = bias(conv2_biases[oc], 12288);
        for (int ic = 0; ic < N1; ++ic) {
#pragma HLS PIPELINE II=1
            w2[oc][ic] = weight(conv2_weights[oc][ic][0][0], 128);
        }
    }
    load_w3: for (int ic = 0; ic < N2; ++ic)
        for (int k = 0; k < F3*F3; ++k) {
#pragma HLS PIPELINE II=1
            w3[ic][k] = weight(conv3_weights[0][ic][k/F3][k%F3], 640);
        }
    const accumulator_t b3 = bias(conv3_biases[0], 30720);
    tile_rows: for (int y0 = 0; y0 < H; y0 += B) {
        tile_columns: for (int x0 = 0; x0 < W; x0 += B) {
            first(input_ftmap, w1, b1, y0-F3/2, x0-F3/2, c1);
            c2_channels: for (int oc = 0; oc < N2; oc += P) {
                c2_init: for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < P; ++lane) {
#pragma HLS UNROLL
                        partial[lane][p] = b2[oc+lane];
                    }
                }
                c2_inputs: for (int ic = 0; ic < N1; ++ic) {
                    c2_pixels: for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
                        const activation_t v = c1[ic][p];
                        for (int lane = 0; lane < P; ++lane) {
#pragma HLS UNROLL
                            partial[lane][p] += v * w2[oc+lane][ic];
                        }
                    }
                }
                c2_relu: for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
                    for (int lane = 0; lane < P; ++lane) {
#pragma HLS UNROLL
                        c2[oc+lane][p%V][p/V] = relu(partial[lane][p], 2);
                    }
                }
            }
            c3_init: for (int p = 0; p < B*B; ++p) {
#pragma HLS PIPELINE II=1
                sums[p] = b3;
            }
            c3_inputs: for (int ic = 0; ic < N2; ++ic) {
                c3_taps: for (int k = 0; k < F3*F3; ++k) {
                    c3_pixels: for (int p = 0; p < B*B; p += V) {
#pragma HLS PIPELINE II=1
                        activation_t samples[V];
#pragma HLS ARRAY_PARTITION variable=samples complete
                        // Read each physical bank exactly once. The tap's
                        // column offset only rotates the register values.
                        for (int bank = 0; bank < V; ++bank) {
#pragma HLS UNROLL
                            const int lane = (bank-(k%F3)%V+V)%V;
                            const int address = (p/B+k/F3)*S+p%B+lane+k%F3;
                            samples[bank] = c2[ic][bank][address/V];
                        }
                        for (int lane = 0; lane < V; ++lane) {
#pragma HLS UNROLL
                            sums[p+lane] += samples[(lane+k%F3)%V] * w3[ic][k];
                        }
                    }
                }
            }
            store_rows: for (int y = 0; y < B; ++y)
                store_columns: for (int x = 0; x < B; ++x) {
#pragma HLS PIPELINE II=1
                    if (y0+y < H && x0+x < W)
                        output_ftmap[0][y0+y][x0+x] = output_value(sums[y*B+x]);
                }
        }
    }
}
