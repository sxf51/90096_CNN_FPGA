#define srcnn golden_srcnn
#define conv1 golden_conv1
#include "../../src/conv1.cpp"
#include "../../src/srcnn.cpp"
#include <algorithm>
#include <cmath>

extern "C" void forward(const float *input, const float *w1, const float *b1,
                        const float *w2, const float *b2, const float *w3,
                        const float *b3, float *output, double *ranges) {
    static float a1[N1][H][W], a2[N2][H][W];
    double acc_max[3] = {}, act_max[3] = {};
    for (int oc = 0; oc < N1; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
                float sum = b1[oc];
                acc_max[0] = std::max(acc_max[0], double(std::fabs(sum)));
                for (int ky = 0; ky < F1; ++ky)
                    for (int kx = 0; kx < F1; ++kx) {
                        const int py = std::max(0, std::min(H - 1, y + ky - 4));
                        const int px = std::max(0, std::min(W - 1, x + kx - 4));
                        sum += input[py * W + px] * w1[oc * 81 + ky * 9 + kx];
                        acc_max[0] = std::max(acc_max[0], double(std::fabs(sum)));
                    }
                a1[oc][y][x] = std::max(sum, 0.0f);
                act_max[0] = std::max(act_max[0], double(a1[oc][y][x]));
            }
    for (int oc = 0; oc < N2; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
                float sum = b2[oc];
                acc_max[1] = std::max(acc_max[1], double(std::fabs(sum)));
                for (int ic = 0; ic < N1; ++ic) {
                    sum += a1[ic][y][x] * w2[oc * N1 + ic];
                    acc_max[1] = std::max(acc_max[1], double(std::fabs(sum)));
                }
                a2[oc][y][x] = std::max(sum, 0.0f);
                act_max[1] = std::max(act_max[1], double(a2[oc][y][x]));
            }
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) {
            float sum = b3[0];
            acc_max[2] = std::max(acc_max[2], double(std::fabs(sum)));
            for (int ic = 0; ic < N2; ++ic)
                for (int ky = 0; ky < F3; ++ky)
                    for (int kx = 0; kx < F3; ++kx) {
                        const int py = std::max(0, std::min(H - 1, y + ky - 2));
                        const int px = std::max(0, std::min(W - 1, x + kx - 2));
                        sum += a2[ic][py][px] * w3[ic * 25 + ky * 5 + kx];
                        acc_max[2] = std::max(acc_max[2], double(std::fabs(sum)));
                    }
            output[y * W + x] = sum;
            act_max[2] = std::max(act_max[2], double(std::fabs(sum)));
        }
    for (int i = 0; i < 3; ++i) {
        ranges[2 * i] = acc_max[i];
        ranges[2 * i + 1] = act_max[i];
    }
}

extern "C" void original_forward(const float *input, const float *w1, const float *b1,
                                 const float *w2, const float *b2, const float *w3,
                                 const float *b3, float *output) {
    golden_srcnn((float (*)[H][W])input, (float (*)[N0][F1][F1])w1, (float *)b1,
                 (float (*)[N1][F2][F2])w2, (float *)b2,
                 (float (*)[N2][F3][F3])w3, (float *)b3, (float (*)[H][W])output);
}
