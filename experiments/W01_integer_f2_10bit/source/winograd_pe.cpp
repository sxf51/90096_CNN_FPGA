#include "winograd_pe.h"
#include "winograd_math.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif
using Acc = wino::Word<2*EXP_BITS+14>;
void winograd_pe(TileInput input[WPE_TILES][16], TransformedWeight weights[16],
                 TileResult output[WPE_TILES][4]) {
#pragma HLS ARRAY_PARTITION variable=input complete dim=2
#pragma HLS ARRAY_PARTITION variable=weights complete
#pragma HLS ARRAY_PARTITION variable=output complete dim=2
    wino_tiles: for (int tile = 0; tile < WPE_TILES; ++tile) {
#pragma HLS PIPELINE II=1
#if EXP_DIRECT
        for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
#pragma HLS UNROLL
            Acc sum = 0;
            for (int ky = 0; ky < 3; ++ky) for (int kx = 0; kx < 3; ++kx) {
#pragma HLS UNROLL
#ifdef __SYNTHESIS__
                ap_int<EXP_BITS> coefficient = weights[ky*3+kx];
                auto product = input[tile][(y+ky)*4+x+kx] * coefficient;
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
                const int64_t product = int64_t(input[tile][(y+ky)*4+x+kx].to_int()) * weights[ky*3+kx].to_int();
#endif
                sum = wino::add<2*EXP_BITS+14>(sum, Acc(product));
            }
            output[tile][2*y+x] = sum;
        }
#else
        wino::Word<EXP_BITS> data[16];
        wino::Word<EXP_BITS+2> transformed[16];
        Acc products[16], result[4];
#pragma HLS ARRAY_PARTITION variable=data complete
#pragma HLS ARRAY_PARTITION variable=transformed complete
#pragma HLS ARRAY_PARTITION variable=products complete
#pragma HLS ARRAY_PARTITION variable=result complete
        for (int i = 0; i < 16; ++i) {
#pragma HLS UNROLL
            data[i] = wino::Word<EXP_BITS>(input[tile][i]);
        }
        wino::input_transform<EXP_BITS>(data, transformed);
        for (int i = 0; i < 16; ++i) {
#pragma HLS UNROLL
#ifdef __SYNTHESIS__
            auto product = transformed[i] * weights[i];
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#else
            const int64_t product = int64_t(transformed[i]) * weights[i].to_int64();
#endif
            products[i] = Acc(product);
        }
        wino::output_transform<2*EXP_BITS+14>(products, result);
        for (int i = 0; i < 4; ++i) {
#pragma HLS UNROLL
#ifndef __SYNTHESIS__
            assert(result[i] % 4 == 0);
#endif
            output[tile][i] = result[i] >> 2;
        }
#endif
    }
}
