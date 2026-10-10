#ifndef EXP_FIXED_TYPES_H
#define EXP_FIXED_TYPES_H
#include <ap_fixed.h>
#ifndef EXP_W_BITS
#define EXP_W_BITS 16
#endif
#ifndef EXP_A_BITS
#define EXP_A_BITS 16
#endif
namespace numeric {
constexpr int WB = EXP_W_BITS, AB = EXP_A_BITS;
using weight = ap_fixed<WB, 1, AP_RND_CONV, AP_SAT>;
using bias = ap_fixed<WB, 1, AP_RND_CONV, AP_SAT>;
using input = ap_fixed<AB, 2, AP_RND_CONV, AP_SAT>;
using weight2 = ap_fixed<8, 1, AP_RND_CONV, AP_SAT>;
using acc2mixed = ap_fixed<EXP_A_BITS + 11, 6, AP_RND_CONV, AP_SAT>;
using act1 = ap_fixed<AB, 2, AP_RND_CONV, AP_SAT>;
using act2 = ap_fixed<AB, 3, AP_RND_CONV, AP_SAT>;
using output = ap_fixed<AB, 2, AP_RND_CONV, AP_SAT>;
// Analytical range: exact product fractions plus worst-case absolute sums.
using acc1 = ap_fixed<WB + AB + 3, 6, AP_RND_CONV, AP_SAT>;
using acc2 = ap_fixed<WB + AB + 3, 6, AP_RND_CONV, AP_SAT>;
using acc3 = ap_fixed<WB + AB + 3, 7, AP_RND_CONV, AP_SAT>;
}
#endif
