#ifndef WINOGRAD_PE_H
#define WINOGRAD_PE_H
#include <ap_int.h>
#ifndef EXP_BITS
#define EXP_BITS 10
#endif
#ifndef EXP_DIRECT
#define EXP_DIRECT 0
#endif
constexpr int WPE_TILES = 32;
using TileInput = ap_int<EXP_BITS>;
using TransformedWeight = ap_int<EXP_BITS+4>;
using TileResult = ap_int<2*EXP_BITS+14>;
void winograd_pe(TileInput input[WPE_TILES][16], TransformedWeight weights[16],
                 TileResult output[WPE_TILES][4]);
#endif
