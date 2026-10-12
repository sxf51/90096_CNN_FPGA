#include "packing16_pe.h"
#ifndef __SYNTHESIS__
#include <cassert>
#endif

#if EXP_PACK16_MODE == 1
static void byte_pair(ap_int<9> a, ap_int<9> b, ap_int<9> c,
                      Product32 &first, Product32 &second) {
#pragma HLS INLINE
    const ap_int<27> packed = (ap_int<27>(a) << 18) + ap_int<27>(b);
    auto product = packed * c;
#pragma HLS BIND_OP variable=product op=mul impl=dsp
    const ap_int<18> low = product.range(17, 0);
    const ap_int<19> high = (product >> 18) + (low < 0 ? 1 : 0);
    first = high;
    second = low;
}

static void limb_pair(Operand16 a, Operand16 b, Operand16 c,
                      Product32 &first, Product32 &second) {
#pragma HLS INLINE
    const ap_uint<8> al = a.range(7, 0), bl = b.range(7, 0), cl = c.range(7, 0);
    const ap_int<8> ah = a.range(15, 8), bh = b.range(15, 8), ch = c.range(15, 8);
    Product32 ll0, ll1, hl0, hl1, lh0, lh1, hh0, hh1;
    byte_pair(ap_int<9>(al), ap_int<9>(bl), ap_int<9>(cl), ll0, ll1);
    byte_pair(ap_int<9>(ah), ap_int<9>(bh), ap_int<9>(cl), hl0, hl1);
    byte_pair(ap_int<9>(al), ap_int<9>(bl), ap_int<9>(ch), lh0, lh1);
    byte_pair(ap_int<9>(ah), ap_int<9>(bh), ap_int<9>(ch), hh0, hh1);
    first = ap_int<34>(ll0) + ((ap_int<34>(hl0) + ap_int<34>(lh0)) << 8)
            + (ap_int<34>(hh0) << 16);
    second = ap_int<34>(ll1) + ((ap_int<34>(hl1) + ap_int<34>(lh1)) << 8)
             + (ap_int<34>(hh1) << 16);
}
#elif EXP_PACK16_MODE == 2
static void overlap_pair(Operand16 a, Operand16 b, Operand16 c,
                         Product32 &first, Product32 &second) {
#pragma HLS INLINE
    const ap_int<8> low = b;
    const ap_int<17> difference = ap_int<17>(b) - ap_int<17>(low);
    const ap_int<9> residual = difference >> 8;
    const ap_int<27> packed = (ap_int<27>(a) << 10) + ap_int<27>(low);
    auto packed_product = packed * c;
#pragma HLS BIND_OP variable=packed_product op=mul impl=dsp
    auto low_product = low * c;
#pragma HLS BIND_OP variable=low_product op=mul impl=fabric
    auto residual_product = residual * c;
#pragma HLS BIND_OP variable=residual_product op=mul impl=fabric
    // Cancel the entire overlapping product before shifting, not just its low bits.
    const ap_int<44> recovered = ap_int<44>(packed_product) - ap_int<44>(low_product);
#ifndef __SYNTHESIS__
    assert((recovered & 1023) == 0);
#endif
    first = recovered >> 10;
    second = ap_int<34>(low_product) + (ap_int<34>(residual_product) << 8);
}
#endif

void packing16_pe(Operand16 a[PACK16_TERMS], Operand16 b[PACK16_TERMS],
                  Operand16 c[PACK16_TERMS], Product32 first[PACK16_TERMS],
                  Product32 second[PACK16_TERMS]) {
    static_assert(EXP_PACK16_MODE >= 0 && EXP_PACK16_MODE <= 3, "Supported INT16 controls");
    pack16_terms: for (int i = 0; i < PACK16_TERMS; ++i) {
#pragma HLS PIPELINE II=1
#if EXP_PACK16_MODE == 0 || EXP_PACK16_MODE == 3
        auto first_product = a[i] * c[i];
#pragma HLS BIND_OP variable=first_product op=mul impl=dsp
        auto second_product = b[i] * c[i];
#if EXP_PACK16_MODE == 0
#pragma HLS BIND_OP variable=second_product op=mul impl=dsp
#else
#pragma HLS BIND_OP variable=second_product op=mul impl=fabric
#endif
        first[i] = first_product;
        second[i] = second_product;
#elif EXP_PACK16_MODE == 1
        limb_pair(a[i], b[i], c[i], first[i], second[i]);
#else
        overlap_pair(a[i], b[i], c[i], first[i], second[i]);
#endif
    }
}
