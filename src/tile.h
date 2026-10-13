#ifndef SRCNN_TILE_H
#define SRCNN_TILE_H
#include "srcnn.h"
#include <cstdint>
#ifndef SRCNN_INT8
#define SRCNN_INT8 0
#endif
#if SRCNN_INT8
#define SRCNN_CHANNEL_LANES 16
#define SRCNN_SPATIAL_LANES 4
#else
#define SRCNN_CHANNEL_LANES 8
#define SRCNN_SPATIAL_LANES 1
#endif

// 16x16 final outputs, 20x20 Conv2 features, 28x28 input footprint.
// Keep float accumulation order; parallelism is across output channels.
namespace srcnn_tile {
constexpr int B = 16;
constexpr int S = B + F3 - 1;
constexpr int I = S + F1 - 1;
constexpr int P = SRCNN_CHANNEL_LANES;
constexpr int V = SRCNN_SPATIAL_LANES;
inline int clamp(int v, int limit) {
    return v < 0 ? 0 : (v >= limit ? limit - 1 : v);
}
#if SRCNN_INT8
// Calibrated for the supplied weights and normalized [0,1] images.
// Signed INT8 weights, unsigned INT8 ReLU activations, INT32 MAC sums.
// Scales: input=255, W1=192, A1=96, W2=128, A2=48, W3=640.
// Values outside the calibrated ranges saturate; public tensors stay float.
using weight_t = int8_t;
using activation_t = uint8_t;
using accumulator_t = int32_t;
using input_t = uint8_t;
inline int32_t rounded(float v) { return static_cast<int32_t>(v >= 0 ? v+0.5f : v-0.5f); }
inline weight_t weight(float v, int scale) {
    int32_t q = rounded(v*scale);
    return static_cast<weight_t>(q < -127 ? -127 : q > 127 ? 127 : q);
}
inline accumulator_t bias(float v, int scale) { return rounded(v*scale); }
inline input_t input_value(float v) {
    int32_t q = rounded(v*255);
    return static_cast<input_t>(q < 0 ? 0 : q > 255 ? 255 : q);
}
inline activation_t relu(accumulator_t v, int layer) {
    // Input scale 255; W1=192, W2=128; A1=96, A2=48.
    int32_t q = v <= 0 ? 0 : layer == 1 ? (v+255)/510 : (v+128)/256;
    return static_cast<activation_t>(q > 255 ? 255 : q);
}
inline float output_value(accumulator_t v) { return static_cast<float>(v)/30720; }
#else
using weight_t = param_t;
using activation_t = ftmap_t;
using accumulator_t = ftmap_t;
using input_t = ftmap_t;
inline weight_t weight(float v, int) { return v; }
inline accumulator_t bias(float v, int) { return v; }
inline input_t input_value(float v) { return v; }
inline activation_t relu(accumulator_t v, int) { return v > 0 ? v : 0; }
inline float output_value(accumulator_t v) { return v; }
#endif
void first(ftmap_t input[N0][H][W], weight_t weights[N1][N0][F1][F1],
           accumulator_t biases[N1], int y0, int x0, activation_t features[N1][S*S]);
}
#endif
