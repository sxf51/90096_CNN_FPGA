#include "winograd_pe.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>

static const int g2[4][3] = {{2,0,0}, {1,1,1}, {1,-1,1}, {0,0,2}};
static TileInput input[WPE_TILES][16];
static TransformedWeight weights[16];
static TileResult output[WPE_TILES][4];

int main() {
    try {
        uint32_t state = 0x1011f223;
        uint64_t checked = 0;
        const int limit = 1 << (EXP_BITS - 1);
        for (int batch = 0; batch < 4096; ++batch) {
            int64_t raw[9];
            for (int i = 0; i < 9; ++i) {
                state = 1664525 * state + 1013904223;
                raw[i] = int((state >> 9) & (2*limit - 1)) - limit;
                if (batch < 2) raw[i] = batch ? limit-1 : -limit;
            }
            for (int r = 0; r < 4; ++r) for (int c = 0; c < 4; ++c) {
                int64_t transformed = 0;
                for (int y = 0; y < 3; ++y) for (int x = 0; x < 3; ++x)
                    transformed += g2[r][y] * raw[y*3+x] * g2[c][x];
                weights[r*4+c] = EXP_DIRECT ? (r*4+c < 9 ? raw[r*4+c] : 0) : transformed;
            }
            for (int tile = 0; tile < WPE_TILES; ++tile) for (int i = 0; i < 16; ++i) {
                state = 1664525 * state + 1013904223;
                input[tile][i] = int((state >> 9) & (2*limit - 1)) - limit;
                if (batch < 2) input[tile][i] = batch ? limit-1 : -limit;
            }
            winograd_pe(input, weights, output);
            for (int tile = 0; tile < WPE_TILES; ++tile) for (int y = 0; y < 2; ++y) for (int x = 0; x < 2; ++x) {
                int64_t expected = 0;
                for (int ky = 0; ky < 3; ++ky) for (int kx = 0; kx < 3; ++kx)
                    expected += int64_t(input[tile][(y+ky)*4+x+kx].to_int()) * raw[ky*3+kx];
                if (output[tile][2*y+x].to_int64() != expected)
                    throw std::runtime_error("Winograd mismatch at output " + std::to_string(checked));
                ++checked;
            }
        }
        std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"checked_outputs\":" << checked
                  << ",\"inverse_divisible_by4\":" << (EXP_DIRECT ? "null" : "true") << "}" << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "EXP_ERROR " << error.what() << std::endl;
        return 1;
    }
}
