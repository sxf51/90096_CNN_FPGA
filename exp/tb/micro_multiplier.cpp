#include "benchmark.h"
#include <cstdint>
#include <iostream>
static const int coefficient[16] = {143, -271, 937, -1567, 329, -127, 641, -883,
                                    1973, -457, 769, -1223, 53, -991, 1499, -613};
int main() {
    Operand a[SAMPLE_COUNT], b[SAMPLE_COUNT];
    Result output[SAMPLE_COUNT];
    uint32_t state = 0x48620261;
    int count = 0;
    for (int batch = 0; batch < 1024; ++batch) {
        for (int i = 0; i < SAMPLE_COUNT; ++i) {
            const int n = batch * SAMPLE_COUNT + i;
            if (EXP_MUL_WIDTH == 8) {
                a[i] = n / 256 - 128;
                b[i] = n % 256 - 128;
            } else {
                state = 1664525 * state + 1013904223;
                a[i] = int16_t(state >> 16);
                state = 1664525 * state + 1013904223;
                b[i] = int16_t(state >> 16);
            }
        }
        benchmark(a, b, output);
        for (int i = 0; i < SAMPLE_COUNT; ++i) {
            const int left = a[i].to_int();
            const int right = EXP_CONSTANT ? coefficient[i % 16] : b[i].to_int();
            const int expected = EXP_ADD_ONLY ? left + right : left * right;
            if (output[i].to_int() != expected) {
                std::cerr << "Multiplier mismatch at " << count << std::endl;
                return 1;
            }
            ++count;
        }
    }
    std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"tested_pairs\":" << count << "}" << std::endl;
    return 0;
}
