#include "types.h"
#include <iostream>
#include <cstdint>
using namespace numeric;

template<int Integer, int Shift> static bool check(int32_t sum) {
    using Acc = ap_fixed<23, Integer, AP_TRN, AP_WRAP>;
    using Out = ap_fixed<10, (23 - Integer - Shift == 8 ? 2 : 3), AP_RND_CONV, AP_SAT>;
    Acc a;
    a.range() = ap_int<23>(sum);
    const int expected = raw_value<Out, 10>(Out(a));
    const int actual = quantize<Shift>(sum);
    if (actual != expected) {
        std::cerr << "round mismatch " << sum << ' ' << Shift << ' '
                  << actual << ' ' << expected << '\n';
        return false;
    }
    return true;
}
int main() {
    uint64_t count = 0;
    for (int32_t sum = -(1 << 22); sum < (1 << 22); ++sum) {
        if (!check<6, 9>(sum) || !check<6, 10>(sum) || !check<7, 8>(sum)) return 1;
        count += 3;
    }
    std::cout << "EXP_BOUNDARY_CASES " << count << '\n';
    std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true}" << std::endl;
    return 0;
}
