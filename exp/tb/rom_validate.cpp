#include "srcnn.h"

void srcnn(ftmap_t in[N0][H][W], param_t [N1][N0][F1][F1], param_t [N1],
           param_t [N2][N1][F2][F2], param_t [N2],
           param_t [N3][N2][F3][F3], param_t [N3], ftmap_t out[N3][H][W]) {
    srcnn_rom(in, out);
}

#include "validate.cpp"
