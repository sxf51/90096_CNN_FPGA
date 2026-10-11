#include "srcnn.h"
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <vector>
using namespace numeric;

static ftmap_t image[N0][H][W];
static param_t weights[N1][N0][F1][F1], biases[N1];
static input raw[H][W];
static weight coefficients[N1][81], bias_values[N1];

template<class Value>
static void read_exact(const char *path, Value *values, size_t count) {
    std::ifstream source(path,std::ios::binary|std::ios::ate);
    if (!source || source.tellg() != std::streamoff(count*sizeof(Value)))
        throw std::runtime_error(std::string("Missing/wrong-size file: ")+path);
    source.seekg(0);
    if (!source.read(reinterpret_cast<char *>(values),count*sizeof(Value)))
        throw std::runtime_error("Short read");
}

int main() {
    try {
        std::vector<unsigned char> bytes(H*W);
        std::vector<float> golden(N1*H*W);
        read_exact("set5/butterfly_3x_LR_u8.bin",bytes.data(),bytes.size());
        read_exact("weights/conv1_weights_3x_flp.bin",&weights[0][0][0][0],N1*81);
        read_exact("weights/conv1_biases_3x_flp.bin",biases,N1);
        read_exact("set5/butterfly_3x_CONV1_flp.bin",golden.data(),golden.size());
        for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) {
            image[0][y][x] = float(bytes[y*W+x])/255;
            raw[y][x] = encode_input(image[0][y][x]);
        }
        for (int oc = 0; oc < N1; ++oc) {
            bias_values[oc] = encode_weight(biases[oc]);
            for (int t = 0; t < 81; ++t)
                coefficients[oc][t] = encode_weight(weights[oc][0][t/9][t%9]);
        }
        uint64_t checked = 0, borders = 0;
        double mse = 0, border = 0;
        for (int frame = 0; frame < 2; ++frame) {
            hls::stream<pixel1> result;
            wino_conv1(image,weights,biases,result);
            for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) {
                if (result.empty()) throw std::runtime_error("Short output stream");
                const pixel1 actual = result.read();
                for (int oc = 0; oc < N1; ++oc) {
                    int64_t sum = int64_t(bias_values[oc])*256;
                    for (int ky = 0; ky < 9; ++ky) for (int kx = 0; kx < 9; ++kx) {
                        const int sy = std::max(0,std::min(H-1,y+ky-4));
                        const int sx = std::max(0,std::min(W-1,x+kx-4));
                        sum += int64_t(raw[sy][sx])*coefficients[oc][ky*9+kx];
                    }
                    const act1 expected = relu1(acc1(sum));
                    if (actual.v[oc] != expected)
                        throw std::runtime_error("Layer bit mismatch at "+std::to_string(y)+","+std::to_string(x)+","+std::to_string(oc));
                    const double error = double(actual.v[oc])/256-golden[(oc*H+y)*W+x];
                    mse += error*error;
                    if (y < 6 || y >= H-6 || x < 6 || x >= W-6) {
                        border += error*error;
                        ++borders;
                    }
                    ++checked;
                }
            }
            if (!result.empty()) throw std::runtime_error("Extra output stream values");
        }
        std::cout.precision(17);
        std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"checked_outputs\":" << checked
                  << ",\"butterfly_mse\":" << mse/checked << ",\"border_mse\":" << border/borders << "}" << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "EXP_ERROR " << error.what() << std::endl;
        return 1;
    }
}
