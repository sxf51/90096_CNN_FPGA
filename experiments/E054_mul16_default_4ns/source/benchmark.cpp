#include "benchmark.h"
// Representative non-power-of-two signed constants; source provenance in config.
static const int coefficient[16] = {143, -271, 937, -1567, 329, -127, 641, -883,
                                    1973, -457, 769, -1223, 53, -991, 1499, -613};
void benchmark(Operand a[SAMPLE_COUNT], Operand b[SAMPLE_COUNT], Result out[SAMPLE_COUNT]) {
#if EXP_CONSTANT
#pragma HLS ARRAY_PARTITION variable=a complete
#pragma HLS ARRAY_PARTITION variable=out complete
#endif
    samples: for (int i = 0; i < SAMPLE_COUNT; ++i) {
#if EXP_CONSTANT
#pragma HLS UNROLL
        Result product = a[i] * Operand(coefficient[i % 16]);
#elif EXP_ADD_ONLY
#pragma HLS PIPELINE II=1
        Result product = Result(a[i]) + Result(b[i]);
#else
#pragma HLS PIPELINE II=1
        Result product = a[i] * b[i];
#if EXP_FABRIC
#pragma HLS BIND_OP variable=product op=mul impl=fabric
#endif
#endif
        out[i] = product;
    }
}
