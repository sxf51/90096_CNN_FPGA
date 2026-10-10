#include "types.h"
#include "srcnn.h"
using namespace numeric;

static void first_layer(input in[N0][H][W], weight weights[N1][N0][F1][F1],
                        bias biases[N1], act1 out[N1][H][W]) {
    c1_oc: for (int oc = 0; oc < N1; ++oc)
        c1_y: for (int y = 0; y < H; ++y)
            c1_x: for (int x = 0; x < W; ++x) {
                acc1 sum = biases[oc];
                c1_ic: for (int ic = 0; ic < N0; ++ic)
                    c1_ky: for (int ky = 0; ky < F1; ++ky)
                        c1_kx: for (int kx = 0; kx < F1; ++kx) {
                            const int iy = y + ky - F1 / 2, ix = x + kx - F1 / 2;
                            const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                            const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                            sum += in[ic][py][px] * weights[oc][ic][ky][kx];
                        }
                out[oc][y][x] = sum > 0 ? act1(sum) : act1(0);
            }
}

void conv1(ftmap_t in[N0][H][W], param_t weights[N1][N0][F1][F1],
           param_t biases[N1], ftmap_t out[N1][H][W]) {
    static input qin[N0][H][W];
    static act1 qout[N1][H][W];
    weight qw[N1][N0][F1][F1];
    bias qb[N1];
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) qin[0][y][x] = in[0][y][x];
    for (int oc = 0; oc < N1; ++oc) {
        qb[oc] = biases[oc];
        for (int ky = 0; ky < F1; ++ky)
            for (int kx = 0; kx < F1; ++kx) qw[oc][0][ky][kx] = weights[oc][0][ky][kx];
    }
    first_layer(qin, qw, qb, qout);
    for (int oc = 0; oc < N1; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) out[oc][y][x] = qout[oc][y][x].to_float();
}

void srcnn(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
           param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
           param_t weights3[N3][N2][F3][F3], param_t biases3[N3], ftmap_t out[N3][H][W]) {
    static input qin[N0][H][W];
    static act1 a1[N1][H][W];
    static act2 a2[N2][H][W];
    weight w1[N1][N0][F1][F1], w2[N2][N1][F2][F2], w3[N3][N2][F3][F3];
    bias b1[N1], b2[N2], b3[N3];
    for (int oc = 0; oc < N1; ++oc) {
        b1[oc] = biases1[oc];
        for (int ky = 0; ky < F1; ++ky)
            for (int kx = 0; kx < F1; ++kx) w1[oc][0][ky][kx] = weights1[oc][0][ky][kx];
    }
    for (int oc = 0; oc < N2; ++oc) {
        b2[oc] = biases2[oc];
        for (int ic = 0; ic < N1; ++ic) w2[oc][ic][0][0] = weights2[oc][ic][0][0];
    }
    b3[0] = biases3[0];
    for (int ic = 0; ic < N2; ++ic)
        for (int ky = 0; ky < F3; ++ky)
            for (int kx = 0; kx < F3; ++kx) w3[0][ic][ky][kx] = weights3[0][ic][ky][kx];
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) qin[0][y][x] = in[0][y][x];
    first_layer(qin, w1, b1, a1);
    c2_oc: for (int oc = 0; oc < N2; ++oc)
        c2_y: for (int y = 0; y < H; ++y)
            c2_x: for (int x = 0; x < W; ++x) {
                acc2 sum = b2[oc];
                c2_ic: for (int ic = 0; ic < N1; ++ic) sum += a1[ic][y][x] * w2[oc][ic][0][0];
                a2[oc][y][x] = sum > 0 ? act2(sum) : act2(0);
            }
    c3_y: for (int y = 0; y < H; ++y)
        c3_x: for (int x = 0; x < W; ++x) {
            acc3 sum = b3[0];
            c3_ic: for (int ic = 0; ic < N2; ++ic)
                c3_ky: for (int ky = 0; ky < F3; ++ky)
                    c3_kx: for (int kx = 0; kx < F3; ++kx) {
                        const int iy = y + ky - 2, ix = x + kx - 2;
                        const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                        const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                        sum += a2[ic][py][px] * w3[0][ic][ky][kx];
                    }
            out[0][y][x] = output(sum).to_float();
        }
}
