static void conv3_stream(hls::stream<pixel2> &in, hls::stream<output> &out,
                         weight weights[N2][25], bias biases[N3]) {
#if EXP_FIXED
    static_assert(EXP_W_BITS + EXP_A_BITS + 3 <= 32, "32-bit scatter cache must preserve reference accumulator precision");
    using partial = ap_fixed<32, 32 - (EXP_W_BITS + EXP_A_BITS - 4), AP_TRN, AP_WRAP>;
#else
    using partial = float;
#endif
    static partial buffer[5][W];
    partial window[5][5];
#pragma HLS ARRAY_PARTITION variable=buffer complete dim=1
#pragma HLS BIND_STORAGE variable=buffer type=ram_2p impl=bram
#pragma HLS ARRAY_PARTITION variable=window complete dim=0
    constexpr int LANES = N2 / T;
    scatter_rows: for (int y = 0; y < H + 4; ++y) {
        const int base = (y + 1) % 5;
        for (int r = 0; r < 5; ++r)
            for (int c = 0; c < 5; ++c) {
#pragma HLS UNROLL
                window[r][c] = 0;
            }
        scatter_columns: for (int x = 0; x < W + 4; ++x) {
            const pixel2 value = in.read();
            // Fixed physical banks each get at most one read and one write.
            if (x >= 5 && x - 5 < W)
                for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
                    buffer[bank][x - 5] = window[(bank + 5 - base) % 5][0];
                }
            partial column[5];
#pragma HLS ARRAY_PARTITION variable=column complete
            for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
                column[bank] = x < W ? buffer[bank][x] : partial(0);
            }
            for (int r = 0; r < 5; ++r) {
#pragma HLS UNROLL
                for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
                    window[r][c] = window[r][c + 1];
                }
                const int output_y = y - 4 + r;
                window[r][4] = (r == 4 || output_y < 0 || output_y >= H) ? partial(0) : column[(base + r) % 5];
            }
            partial contribution[25];
#pragma HLS ARRAY_PARTITION variable=contribution complete
            for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                contribution[tap] = 0;
            }
            c3_fold: for (int step = 0; step < T; ++step) {
#pragma HLS PIPELINE II=1
                for (int lane = 0; lane < LANES; ++lane) {
#pragma HLS UNROLL
                    const int ic = step * LANES + lane;
                    for (int tap = 0; tap < 25; ++tap) {
#pragma HLS UNROLL
                        contribution[tap] += value.v[ic] * weights[ic][tap];
                    }
                }
            }
            for (int ky = 0; ky < 5; ++ky) {
#pragma HLS UNROLL
                for (int kx = 0; kx < 5; ++kx) {
#pragma HLS UNROLL
                    if (y >= ky && y - ky < H && x >= kx && x - kx < W)
                        window[4 - ky][4 - kx] += contribution[ky * 5 + kx];
                }
            }
            if (y >= 4 && x >= 4) out.write(output(window[0][0] + biases[0]));
        }
        // Last valid column remains in registers at the end of the padded row.
        for (int bank = 0; bank < 5; ++bank) {
#pragma HLS UNROLL
            buffer[bank][W - 1] = window[(bank + 5 - base) % 5][0];
        }
    }
}
