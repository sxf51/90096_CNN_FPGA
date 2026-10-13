#include "srcnn.h"

// implements conv1 layer of SRCNN
void conv1(ftmap_t input_ftmap[N0][H][W],
           param_t conv1_weights[N1][N0][F1][F1],
           param_t conv1_biases[N1],
           ftmap_t output_ftmap[N1][H][W])
{
    // implement conv1 layer of SRCNN here
    // 对输入做同尺寸卷积；边界外使用最近的边缘像素。
    for (int oc = 0; oc < N1; ++oc) {
        for (int y = 0; y < H; ++y) {
            for (int x = 0; x < W; ++x) {
                ftmap_t sum = conv1_biases[oc];
                for (int ic = 0; ic < N0; ++ic) {
                    for (int ky = 0; ky < F1; ++ky) {
                        for (int kx = 0; kx < F1; ++kx) {
                            const int iy = y + ky - F1 / 2;
                            const int ix = x + kx - F1 / 2;
                            const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                            const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                            sum += input_ftmap[ic][py][px] *
                                   conv1_weights[oc][ic][ky][kx];
                        }
                    }
                }
                // 第一层卷积之后应用 ReLU 激活。
                output_ftmap[oc][y][x] = sum > 0 ? sum : 0;
            }
        }
    }
}
