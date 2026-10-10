#ifndef _SRCNN_H_
#define _SRCNN_H_
#define H 255
#define W 255
#define N0 1
#define N1 64
#define F1 9
#define N2 32
#define F2 1
#define N3 1
#define F3 5
typedef float ftmap_t;
typedef float param_t;
void srcnn(ftmap_t [N0][H][W], param_t [N1][N0][F1][F1], param_t [N1],
           param_t [N2][N1][F2][F2], param_t [N2],
           param_t [N3][N2][F3][F3], param_t [N3], ftmap_t [N3][H][W]);
void conv1(ftmap_t [N0][H][W], param_t [N1][N0][F1][F1], param_t [N1], ftmap_t [N1][H][W]);
#endif
