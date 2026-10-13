#ifndef EXACT_IEEE_DECODE_H
#define EXACT_IEEE_DECODE_H
#include <ap_int.h>
#include <utils/x_hls_utils.h>

template<int Bits, int Fraction, class Raw>
static float exact_ieee_decode(Raw value) {
#pragma HLS INLINE
    static_assert(Bits <= 16 && Fraction >= 0 && Fraction <= 23, "Exact binary32 carrier range");
    const bool negative = value < 0;
    // Widen before negating the minimum signed carrier value.
    const ap_int<Bits+1> signed_value = value;
    ap_uint<Bits> magnitude;
    if (negative) magnitude = -signed_value;
    else magnitude = signed_value;
    ap_uint<5> high = 0;
    ieee_high_bit: for (int bit = 0; bit < Bits; ++bit) {
#pragma HLS UNROLL
        if (magnitude[bit]) high = bit;
    }
    fp_struct<float> result;
    result.sign = negative;
    result.exp = 0;
    if (magnitude != 0) result.exp = 127-Fraction+high;
    result.sig = ap_uint<32>(magnitude) << (23-high);
    return result.to_ieee();
}

constexpr int IEEE_WORDS = 1024;
void ieee_decode_pe(const ap_int<10> input[IEEE_WORDS], float output[IEEE_WORDS]);
#endif
