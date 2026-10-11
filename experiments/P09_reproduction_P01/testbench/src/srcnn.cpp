#include "srcnn.h"

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
    // 保存前两层的中间特征图，避免大数组占用函数调用栈。
    static ftmap_t conv1_ftmap[N1][H][W];
    static ftmap_t conv2_ftmap[N2][H][W];

    conv1(input_ftmap, conv1_weights, conv1_biases, conv1_ftmap);

    // 第二层为逐像素的 1×1 卷积，并应用 ReLU。
    for (int oc = 0; oc < N2; ++oc) {
        for (int y = 0; y < H; ++y) {
            for (int x = 0; x < W; ++x) {
                ftmap_t sum = conv2_biases[oc];
                for (int ic = 0; ic < N1; ++ic) {
                    for (int ky = 0; ky < F2; ++ky) {
                        for (int kx = 0; kx < F2; ++kx) {
                            const int iy = y + ky - F2 / 2;
                            const int ix = x + kx - F2 / 2;
                            if (iy >= 0 && iy < H && ix >= 0 && ix < W) {
                                sum += conv1_ftmap[ic][iy][ix] *
                                       conv2_weights[oc][ic][ky][kx];
                            }
                        }
                    }
                }
                conv2_ftmap[oc][y][x] = sum > 0 ? sum : 0;
            }
        }
    }

    // 第三层使用边缘像素填充以保持图像尺寸，输出重建值不再激活。
    for (int oc = 0; oc < N3; ++oc) {
        for (int y = 0; y < H; ++y) {
            for (int x = 0; x < W; ++x) {
                ftmap_t sum = conv3_biases[oc];
                for (int ic = 0; ic < N2; ++ic) {
                    for (int ky = 0; ky < F3; ++ky) {
                        for (int kx = 0; kx < F3; ++kx) {
                            const int iy = y + ky - F3 / 2;
                            const int ix = x + kx - F3 / 2;
                            const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                            const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                            sum += conv2_ftmap[ic][py][px] *
                                   conv3_weights[oc][ic][ky][kx];
                        }
                    }
                }
                output_ftmap[oc][y][x] = sum;
            }
        }
    }
}
