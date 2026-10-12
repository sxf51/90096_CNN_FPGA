#include "srcnn.h"
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <vector>

static ftmap_t image[N0][H][W], output[N3][H][W], expected[N3][H][W], golden[N3][H][W];

template<class Value>
static void read_exact(const char *filename, Value *data, size_t count) {
    std::ifstream stream(filename, std::ios::binary | std::ios::ate);
    if (!stream || stream.tellg() != std::streamoff(count*sizeof(Value)))
        throw std::runtime_error("Missing or wrong-size ROM verification input");
    stream.seekg(0);
    if (!stream.read(reinterpret_cast<char *>(data), count*sizeof(Value)))
        throw std::runtime_error("Short ROM verification read");
}

static void read_image(const char *filename) {
    std::vector<unsigned char> bytes(H*W);
    read_exact(filename, bytes.data(), bytes.size());
    for (int index = 0; index < H*W; ++index)
        image[0][index/W][index%W] = float(bytes[index])/255;
}

static double error_mse(bool border) {
    double sum = 0;
    int count = 0;
    for (int y = 0; y < H; ++y) {
        for (int x = 0; x < W; ++x) {
            if (border && y >= 6 && y < H-6 && x >= 6 && x < W-6) continue;
            const double difference = double(output[0][y][x])-golden[0][y][x];
            if (!std::isfinite(difference)) throw std::runtime_error("Nonfinite ROM output");
            sum += difference*difference;
            ++count;
        }
    }
    return sum/count;
}

int main() {
    try {
        read_image("set5/butterfly_3x_LR_u8.bin");
        read_exact("fixed_reference.bin", &expected[0][0][0], H*W);
        read_exact("set5/butterfly_3x_GR_flp.bin", &golden[0][0][0], H*W);
        srcnn_rom(image, output);
        if (std::memcmp(output, expected, sizeof(output)))
            throw std::runtime_error("ROM butterfly does not match E017 bitwise");
        const double butterfly = error_mse(false), border = error_mse(true);
        read_image("set14/lenna_3x_LR_u8.bin");
        read_exact("numpy_reference/lenna_output.bin", &expected[0][0][0], H*W);
        srcnn_rom(image, output);
        if (std::memcmp(output, expected, sizeof(output)))
            throw std::runtime_error("ROM second changed-input frame is not bit exact");
        std::cout << std::setprecision(17)
                  << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"frame_count\":2,"
                  << "\"same_weights_changed_input\":true,\"changed_input_pass\":true,"
                  << "\"butterfly_mse\":" << butterfly << ",\"border_mse\":" << border << "}\n";
    } catch (const std::exception &error) {
        std::cerr << "ROM_RTL_FAIL " << error.what() << "\n";
        return 1;
    }
    return 0;
}
