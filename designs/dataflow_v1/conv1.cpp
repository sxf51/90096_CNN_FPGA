#include "types.h"
#include "srcnn.h"
using namespace numeric;

void conv1(ftmap_t in[N0][H][W], param_t weights[N1][N0][F1][F1],
           param_t biases[N1], ftmap_t out[N1][H][W]) {
    for (int oc = 0; oc < N1; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
                acc1 sum = bias(biases[oc]);
                for (int ky = 0; ky < F1; ++ky)
                    for (int kx = 0; kx < F1; ++kx) {
                        const int iy = y + ky - 4, ix = x + kx - 4;
                        const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                        const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                        sum += input(in[0][py][px]) * weight(weights[oc][0][ky][kx]);
                    }
                out[oc][y][x] = static_cast<float>(sum > 0 ? act1(sum) : act1(0));
            }
}
