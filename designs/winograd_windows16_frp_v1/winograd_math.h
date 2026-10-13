#ifndef WINOGRAD_INTEGER_MATH_H
#define WINOGRAD_INTEGER_MATH_H
#include <ap_int.h>
#include <cstdint>
namespace wino {
#ifdef __SYNTHESIS__
template<int Bits> using Word = ap_int<Bits>;
#else
template<int Bits> using Word = int64_t;
#endif

template<int Bits> static Word<Bits> add(Word<Bits> a, Word<Bits> b) {
#pragma HLS INLINE
    Word<Bits> result = a + b;
#pragma HLS BIND_OP variable=result op=add impl=fabric
    return result;
}
template<int Bits> static Word<Bits> sub(Word<Bits> a, Word<Bits> b) {
#pragma HLS INLINE
    Word<Bits> result = a - b;
#pragma HLS BIND_OP variable=result op=sub impl=fabric
    return result;
}

template<int Bits> static void input_transform(const Word<Bits> data[16], Word<Bits+2> value[16]) {
#pragma HLS INLINE
    using V = Word<Bits+2>;
    V temp[16];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
        temp[c] = sub<Bits+2>(V(data[c]), V(data[8+c]));
        temp[4+c] = add<Bits+2>(V(data[4+c]), V(data[8+c]));
        temp[8+c] = sub<Bits+2>(V(data[8+c]), V(data[4+c]));
        temp[12+c] = sub<Bits+2>(V(data[4+c]), V(data[12+c]));
    }
    for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
        value[4*r] = sub<Bits+2>(temp[4*r], temp[4*r+2]);
        value[4*r+1] = add<Bits+2>(temp[4*r+1], temp[4*r+2]);
        value[4*r+2] = sub<Bits+2>(temp[4*r+2], temp[4*r+1]);
        value[4*r+3] = sub<Bits+2>(temp[4*r+1], temp[4*r+3]);
    }
}

template<int Bits> static void weight_transform(const Word<Bits> kernel[9], Word<Bits+4> value[16]) {
#pragma HLS INLINE
    using U = Word<Bits+4>;
    U temp[12];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 3; ++c) {
#pragma HLS UNROLL
        temp[c] = U(kernel[c]) * 2;
        temp[3+c] = add<Bits+4>(add<Bits+4>(U(kernel[c]), U(kernel[3+c])), U(kernel[6+c]));
        temp[6+c] = add<Bits+4>(sub<Bits+4>(U(kernel[c]), U(kernel[3+c])), U(kernel[6+c]));
        temp[9+c] = U(kernel[6+c]) * 2;
    }
    for (int r = 0; r < 4; ++r) {
#pragma HLS UNROLL
        value[4*r] = temp[3*r] * 2;
        value[4*r+1] = add<Bits+4>(add<Bits+4>(temp[3*r], temp[3*r+1]), temp[3*r+2]);
        value[4*r+2] = add<Bits+4>(sub<Bits+4>(temp[3*r], temp[3*r+1]), temp[3*r+2]);
        value[4*r+3] = temp[3*r+2] * 2;
    }
}

template<int Bits> static void output_transform(const Word<Bits> value[16], Word<Bits> output[4]) {
#pragma HLS INLINE
    Word<Bits> temp[8];
#pragma HLS ARRAY_PARTITION variable=temp complete
    for (int c = 0; c < 4; ++c) {
#pragma HLS UNROLL
        temp[c] = add<Bits>(add<Bits>(value[c], value[4+c]), value[8+c]);
        temp[4+c] = sub<Bits>(sub<Bits>(value[4+c], value[8+c]), value[12+c]);
    }
    for (int r = 0; r < 2; ++r) {
#pragma HLS UNROLL
        output[2*r] = add<Bits>(add<Bits>(temp[4*r], temp[4*r+1]), temp[4*r+2]);
        output[2*r+1] = sub<Bits>(sub<Bits>(temp[4*r+1], temp[4*r+2]), temp[4*r+3]);
    }
}
}
#endif
