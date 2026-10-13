#include "ieee_decode.h"
#ifndef EXP_LEGACY_DECODE
#define EXP_LEGACY_DECODE 0
#endif

void ieee_decode_pe(const ap_int<10> input[IEEE_WORDS], float output[IEEE_WORDS]) {
    decode_words: for (int i = 0; i < IEEE_WORDS; ++i) {
#pragma HLS PIPELINE II=1
#if EXP_LEGACY_DECODE
        output[i] = float(input[i])/256.0f;
#else
        output[i] = exact_ieee_decode<10,8>(input[i]);
#endif
    }
}
