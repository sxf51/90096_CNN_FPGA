#include <ap_fixed.h>
#include <cstdint>
#include "srcnn.h"
#ifndef EXP_W_BITS
#define EXP_W_BITS 10
#endif
#ifndef EXP_A_BITS
#define EXP_A_BITS 10
#endif
constexpr int WB = EXP_W_BITS, AB = EXP_A_BITS;
using Weight = ap_fixed<WB, 1, AP_RND_CONV, AP_SAT>;
using Weight2 = ap_fixed<8, 1, AP_RND_CONV, AP_SAT>;
using Acc2 = ap_fixed<AB + 11, 6, AP_RND_CONV, AP_SAT>;
using A1 = ap_fixed<AB, 2, AP_RND_CONV, AP_SAT>;
using A2 = ap_fixed<AB, 3, AP_RND_CONV, AP_SAT>;
using Acc1 = ap_fixed<WB + AB + 3, 6, AP_RND_CONV, AP_SAT>;
using Acc3 = ap_fixed<WB + AB + 3, 7, AP_RND_CONV, AP_SAT>;

template<class Q> static int16_t raw(Q value) {
    ap_int<Q::width> bits = value.range();
    return int16_t(bits.to_int());
}
template<class Acc, class Activation> static int16_t cast_raw(int64_t sum) {
    Acc value;
    value.range() = ap_int<Acc::width>(sum);
    return raw(Activation(value));
}
static float decode(int16_t value, int integer) {
    return float(value) / float(1 << (AB - integer));
}
static void layer1(const int16_t in[H][W], const int16_t weights[N1][81],
                   const int16_t biases[N1], int16_t out[N1][H][W]) {
    for (int oc = 0; oc < N1; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
                int64_t sum = int64_t(biases[oc]) * (int64_t(1) << (AB - 2));
                for (int tap = 0; tap < 81; ++tap) {
                    const int iy = y + tap / 9 - 4, ix = x + tap % 9 - 4;
                    const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                    const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                    sum += int64_t(in[py][px]) * weights[oc][tap];
                }
                out[oc][y][x] = cast_raw<Acc1, A1>(sum > 0 ? sum : 0);
            }
}

void conv1(ftmap_t in[N0][H][W], param_t weights[N1][N0][F1][F1],
           param_t biases[N1], ftmap_t out[N1][H][W]) {
    static int16_t qin[H][W], qout[N1][H][W];
    int16_t qw[N1][81], qb[N1];
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) qin[y][x] = raw(A1(in[0][y][x]));
    for (int oc = 0; oc < N1; ++oc) {
        qb[oc] = raw(Weight(biases[oc]));
        for (int tap = 0; tap < 81; ++tap) qw[oc][tap] = raw(Weight(weights[oc][0][tap / 9][tap % 9]));
    }
    layer1(qin, qw, qb, qout);
    for (int oc = 0; oc < N1; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) out[oc][y][x] = decode(qout[oc][y][x], 2);
}

void srcnn(ftmap_t in[N0][H][W], param_t weights1[N1][N0][F1][F1], param_t biases1[N1],
           param_t weights2[N2][N1][F2][F2], param_t biases2[N2],
           param_t weights3[N3][N2][F3][F3], param_t biases3[N3], ftmap_t out[N3][H][W]) {
    static int16_t qin[H][W], a1[N1][H][W], a2[N2][H][W];
    int16_t w1[N1][81], w2[N2][N1], w3[N2][25], b1[N1], b2[N2], b3;
    for (int oc = 0; oc < N1; ++oc) {
        b1[oc] = raw(Weight(biases1[oc]));
        for (int tap = 0; tap < 81; ++tap) w1[oc][tap] = raw(Weight(weights1[oc][0][tap / 9][tap % 9]));
    }
    for (int oc = 0; oc < N2; ++oc) {
        b2[oc] = raw(Weight2(biases2[oc]));
        for (int ic = 0; ic < N1; ++ic) w2[oc][ic] = raw(Weight2(weights2[oc][ic][0][0]));
    }
    b3 = raw(Weight(biases3[0]));
    for (int ic = 0; ic < N2; ++ic)
        for (int tap = 0; tap < 25; ++tap) w3[ic][tap] = raw(Weight(weights3[0][ic][tap / 5][tap % 5]));
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) qin[y][x] = raw(A1(in[0][y][x]));
    layer1(qin, w1, b1, a1);
    for (int oc = 0; oc < N2; ++oc)
        for (int y = 0; y < H; ++y)
            for (int x = 0; x < W; ++x) {
                int64_t sum = int64_t(b2[oc]) * (int64_t(1) << (AB - 2));
                for (int ic = 0; ic < N1; ++ic) sum += int64_t(a1[ic][y][x]) * w2[oc][ic];
                a2[oc][y][x] = cast_raw<Acc2, A2>(sum > 0 ? sum : 0);
            }
    for (int y = 0; y < H; ++y)
        for (int x = 0; x < W; ++x) {
            int64_t sum = int64_t(b3) * (int64_t(1) << (AB - 3));
            for (int ic = 0; ic < N2; ++ic)
                for (int tap = 0; tap < 25; ++tap) {
                    const int iy = y + tap / 5 - 2, ix = x + tap % 5 - 2;
                    const int py = iy < 0 ? 0 : (iy >= H ? H - 1 : iy);
                    const int px = ix < 0 ? 0 : (ix >= W ? W - 1 : ix);
                    sum += int64_t(a2[ic][py][px]) * w3[ic][tap];
                }
            out[0][y][x] = decode(cast_raw<Acc3, A1>(sum), 2);
        }
}
