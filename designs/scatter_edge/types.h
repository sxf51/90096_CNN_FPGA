#ifndef DATAFLOW_TYPES_H
#define DATAFLOW_TYPES_H
#include <ap_fixed.h>
#include <cstdint>
#include <type_traits>
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
#include "integer_numeric.inc"
using edge_weight = word<15>;
struct pixel1 { act1 v[64]; };
struct pixel2 { act2 v[32]; };
}
#endif
