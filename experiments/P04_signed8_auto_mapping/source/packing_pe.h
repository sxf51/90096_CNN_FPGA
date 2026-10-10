#ifndef PACKING_PE_H
#define PACKING_PE_H
#include <ap_int.h>
#ifndef EXP_PACK_MODE
#define EXP_PACK_MODE 1
#endif
#ifndef EXP_GROUP
#define EXP_GROUP 1
#endif
#ifndef EXP_OPERAND_BITS
#define EXP_OPERAND_BITS 8
#endif
#ifndef EXP_C_BITS
#define EXP_C_BITS 8
#endif
#ifndef EXP_NONNEG
#define EXP_NONNEG 0
#endif
constexpr int PE_TERMS = 56;
constexpr int PE_GROUPS = PE_TERMS / EXP_GROUP;
using Coefficient = ap_int<EXP_OPERAND_BITS>;
using Shared = ap_int<EXP_C_BITS>;
using ProductSum = ap_int<32>;
void packing_pe(Coefficient a[PE_TERMS], Coefficient b[PE_TERMS], Shared c[PE_TERMS],
                ProductSum first[PE_GROUPS], ProductSum second[PE_GROUPS]);
#endif
