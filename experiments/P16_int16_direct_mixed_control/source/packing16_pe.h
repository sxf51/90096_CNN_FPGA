#ifndef PACKING16_PE_H
#define PACKING16_PE_H
#include <ap_int.h>

#ifndef EXP_PACK16_MODE
#define EXP_PACK16_MODE 0
#endif

constexpr int PACK16_TERMS = 64;
using Operand16 = ap_int<16>;
using Product32 = ap_int<32>;

void packing16_pe(Operand16 a[PACK16_TERMS], Operand16 b[PACK16_TERMS],
                  Operand16 c[PACK16_TERMS], Product32 first[PACK16_TERMS],
                  Product32 second[PACK16_TERMS]);
#endif
