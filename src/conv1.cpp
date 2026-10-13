#include "srcnn.h"
#include "tile.h"

// Shared bounded-memory Conv1 engine. A tap is applied to the whole tile
// before the next tap: 400 independent sums hide float adder latency.
void srcnn_tile::first(ftmap_t input[N0][H][W],
                      weight_t weights[N1][N0][F1][F1], accumulator_t biases[N1],
                      int y0, int x0, activation_t features[N1][S*S])
{
#pragma HLS INLINE off
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS ARRAY_PARTITION variable=features cyclic factor=SRCNN_CHANNEL_LANES dim=1
    input_t image[I][I];
    accumulator_t partial[P][S*S];
#pragma HLS ARRAY_PARTITION variable=partial complete dim=1
#pragma HLS BIND_STORAGE variable=partial type=ram_2p impl=bram
#pragma HLS BIND_STORAGE variable=image type=ram_2p impl=bram
    load_rows: for (int y = 0; y < I; ++y) {
        load_columns: for (int x = 0; x < I; ++x) {
#pragma HLS PIPELINE II=1
            // Clamp the feature coordinate FIRST, then the input tap.
            // This duplicates actual edge features for Conv3 padding.
            image[y][x] = input_value(input[0][clamp(y0+y-F1/2, H)][clamp(x0+x-F1/2, W)]);
        }
    }
    channel_blocks: for (int oc = 0; oc < N1; oc += P) {
        init_pixels: for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
            for (int lane = 0; lane < P; ++lane) {
#pragma HLS UNROLL
                partial[lane][p] = biases[oc+lane];
            }
        }
        kernel_rows: for (int ky = 0; ky < F1; ++ky) {
            kernel_columns: for (int kx = 0; kx < F1; ++kx) {
                pixels: for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
                    const int py = clamp(y0+p/S, H)-y0;
                    const int px = clamp(x0+p%S, W)-x0;
                    const input_t v = image[py+ky][px+kx];
                    for (int lane = 0; lane < P; ++lane) {
#pragma HLS UNROLL
                        partial[lane][p] += v * weights[oc+lane][0][ky][kx];
                    }
                }
            }
        }
        relu_pixels: for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
            for (int lane = 0; lane < P; ++lane) {
#pragma HLS UNROLL
                features[oc+lane][p] = relu(partial[lane][p], 1);
            }
        }
    }
}

// implements conv1 layer of SRCNN
void conv1(ftmap_t input_ftmap[N0][H][W],
           param_t conv1_weights[N1][N0][F1][F1],
           param_t conv1_biases[N1],
           ftmap_t output_ftmap[N1][H][W])
{
    // implement conv1 layer of SRCNN here
#pragma HLS INTERFACE m_axi port=input_ftmap offset=slave bundle=image_in depth=65025 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=output_ftmap offset=slave bundle=image_out depth=4161600 max_write_burst_length=64
#pragma HLS INTERFACE m_axi port=conv1_weights offset=slave bundle=params depth=5184
#pragma HLS INTERFACE m_axi port=conv1_biases offset=slave bundle=params depth=64
#pragma HLS INTERFACE s_axilite port=input_ftmap bundle=control
#pragma HLS INTERFACE s_axilite port=output_ftmap bundle=control
#pragma HLS INTERFACE s_axilite port=conv1_weights bundle=control
#pragma HLS INTERFACE s_axilite port=conv1_biases bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
    using namespace srcnn_tile;
    static weight_t weights[N1][N0][F1][F1];
    accumulator_t biases[N1];
    static activation_t features[N1][S*S];
#pragma HLS ARRAY_PARTITION variable=weights cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS ARRAY_PARTITION variable=features cyclic factor=SRCNN_CHANNEL_LANES dim=1
#pragma HLS BIND_STORAGE variable=features type=ram_2p impl=bram
    for (int oc = 0; oc < N1; ++oc) {
        biases[oc] = bias(conv1_biases[oc], 48960);
        for (int ky = 0; ky < F1; ++ky)
            for (int kx = 0; kx < F1; ++kx) {
#pragma HLS PIPELINE II=1
                weights[oc][0][ky][kx] = weight(conv1_weights[oc][0][ky][kx], 192);
            }
    }
    for (int y = 0; y < H; y += S)
        for (int x = 0; x < W; x += S) {
            first(input_ftmap, weights, biases, y, x, features);
            for (int oc = 0; oc < N1; ++oc)
                for (int p = 0; p < S*S; ++p) {
#pragma HLS PIPELINE II=1
                    if (y+p/S < H && x+p%S < W)
                        output_ftmap[oc][y+p/S][x+p%S] = features[oc][p]
#if SRCNN_INT8
                            /96.0f
#endif
                            ;
                }
        }
}
