#ifndef MICRO_MULTIPLIER_H
#define MICRO_MULTIPLIER_H
#include <ap_int.h>
#ifndef EXP_MUL_WIDTH
#define EXP_MUL_WIDTH 16
#endif
#ifndef EXP_CONSTANT
#define EXP_CONSTANT 0
#endif
#ifndef EXP_FABRIC
#define EXP_FABRIC 0
#endif
#ifndef EXP_ADD_ONLY
#define EXP_ADD_ONLY 0
#endif
constexpr int SAMPLE_COUNT = 64;
using Operand = ap_int<EXP_MUL_WIDTH>;
using Result = ap_int<2 * EXP_MUL_WIDTH>;
void benchmark(Operand a[SAMPLE_COUNT], Operand b[SAMPLE_COUNT], Result out[SAMPLE_COUNT]);
#endif
