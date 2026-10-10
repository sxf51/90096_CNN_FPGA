#include "ieee_decode.h"
#include <cstring>
#include <iostream>

int main() {
    ap_int<10> input[IEEE_WORDS];
    float output[IEEE_WORDS];
    for (int order = 0; order < 3; ++order) {
        for (int i = 0; i < IEEE_WORDS; ++i)
            input[i] = ((i*(order == 2 ? 511 : 1)+(order == 1 ? 511 : 0))&1023)-512;
        ieee_decode_pe(input,output);
        for (int i = 0; i < IEEE_WORDS; ++i) {
            const float expected = float(input[i].to_int())/256.0f;
            if (std::memcmp(&output[i],&expected,sizeof(float))) {
                std::cerr << "EXP_ERROR IEEE mismatch at raw=" << input[i] << '\n';
                return 1;
            }
        }
    }
    std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"decode_values_checked\":3072}" << std::endl;
    return 0;
}
