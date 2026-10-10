#ifndef DATAFLOW_TYPES_H
#define DATAFLOW_TYPES_H
#include <ap_fixed.h>
#include <hls_stream.h>
#ifndef EXP_FIXED
#define EXP_FIXED 0
#endif
#ifndef EXP_W_BITS
#define EXP_W_BITS 10
#endif
#ifndef EXP_A_BITS
#define EXP_A_BITS 10
#endif
#ifndef EXP_T
#define EXP_T 32
#endif
#ifndef EXP_C1_SPLIT
#define EXP_C1_SPLIT 0
#endif
#ifndef EXP_C2_SPLIT
#define EXP_C2_SPLIT 0
#endif
#ifndef EXP_C3_SPLIT
#define EXP_C3_SPLIT 0
#endif
#ifndef EXP_STORAGE
#define EXP_STORAGE 0
#endif
namespace numeric {
constexpr int T = EXP_T;
static_assert(T == 32 || T == 16 || T == 8 || T == 4, "Supported fold schedules");
constexpr int C1_OC = EXP_C1_SPLIT ? 64 : 64 / T;
constexpr int C1_TAP = EXP_C1_SPLIT ? (81 + T - 1) / T : 81;
constexpr int C2_OC = EXP_C2_SPLIT ? 32 : 32 / T;
constexpr int C2_IC = EXP_C2_SPLIT ? 64 / T : 64;
constexpr int C3_IC = EXP_C3_SPLIT ? 32 : 32 / T;
constexpr int C3_TAP = EXP_C3_SPLIT ? (25 + T - 1) / T : 25;
#if EXP_FIXED
using weight = ap_fixed<EXP_W_BITS, 1, AP_RND_CONV, AP_SAT>;
using bias = weight;
using input = ap_fixed<EXP_A_BITS, 2, AP_RND_CONV, AP_SAT>;
using act1 = input;
using act2 = ap_fixed<EXP_A_BITS, 3, AP_RND_CONV, AP_SAT>;
using output = input;
using acc1 = ap_fixed<EXP_W_BITS + EXP_A_BITS + 3, 6, AP_RND_CONV, AP_SAT>;
using acc2 = acc1;
using acc3 = ap_fixed<EXP_W_BITS + EXP_A_BITS + 3, 7, AP_RND_CONV, AP_SAT>;
#else
using weight = float;
using bias = float;
using input = float;
using act1 = float;
using act2 = float;
using output = float;
using acc1 = float;
using acc2 = float;
using acc3 = float;
#endif
struct pixel1 { act1 v[64]; };
struct pixel2 { act2 v[32]; };
}
#endif
