#include "srcnn.h"
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef EXP_COLD_START
#define EXP_COLD_START 0
#endif
static_assert(EXP_RELOAD_SWITCH && EXP_FIXED && EXP_W_BITS == 10 && EXP_A_BITS == 10,
              "Reload switch verification requires the independent mixed T4 design");
static_assert(EXP_FRAMES == (EXP_COLD_START ? 1 : 4), "Wrong reload transaction count");

static ftmap_t image[N0][H][W], output[N3][H][W], reference[N3][H][W];
static param_t w1[N1][N0][F1][F1], b1[N1];
static param_t w2[N2][N1][F2][F2], b2[N2];
static param_t w3[N3][N2][F3][F3], b3[N3];

template<class T> static void read_exact(const std::string &path, T *data, size_t count) {
    std::ifstream in(path.c_str(), std::ios::binary | std::ios::ate);
    if (!in || in.tellg() != std::streamoff(count * sizeof(T)))
        throw std::runtime_error("Missing/wrong-size input: " + path);
    in.seekg(0);
    if (!in.read(reinterpret_cast<char *>(data), count * sizeof(T)))
        throw std::runtime_error("Short read: " + path);
}

static void read_image(const std::string &path) {
    std::vector<unsigned char> bytes(H * W);
    read_exact(path, bytes.data(), bytes.size());
    for (int i = 0; i < H * W; ++i) image[0][i / W][i % W] = float(bytes[i]) / 255;
}

static double mse(bool border) {
    double total = 0;
    size_t count = 0;
    for (int i = 0; i < H * W; ++i) {
        const int y = i / W, x = i % W;
        if (border && y >= 6 && y < H - 6 && x >= 6 && x < W - 6) continue;
        if (!std::isfinite(output[0][y][x]) || !std::isfinite(reference[0][y][x]))
            throw std::runtime_error("Nonfinite model output");
        const double delta = double(output[0][y][x]) - reference[0][y][x];
        total += delta * delta;
        ++count;
    }
    return total / count;
}

static void require_exact(const std::string &name) {
    if (std::memcmp(output, reference, sizeof(output)))
        throw std::runtime_error(name + " differs from exact reference");
}

static void invoke(int transaction, bool load) {
    srcnn_reload(image, w1, b1, w2, b2, w3, b3, output, load);
    std::cout << "EXP_RELOAD_TX transaction=" << transaction << " load=" << int(load) << std::endl;
}

static void clear_params() {
    std::memset(w1, 0, sizeof(w1));
    std::memset(w2, 0, sizeof(w2));
    std::memset(w3, 0, sizeof(w3));
    std::memset(b1, 0, sizeof(b1));
    std::memset(b2, 0, sizeof(b2));
    std::memset(b3, 0, sizeof(b3));
}

static void constructed_params() {
    clear_params();
    for (int c = 0; c < N1; ++c) b1[c] = 0.5f;
    for (int c = 0; c < N2; ++c) b2[c] = 0.25f;
    b3[0] = 0.125f;
    w1[0][0][F1 / 2][F1 / 2] = 0.25f;
    w2[0][0][0][0] = 0.5f;
    w3[0][0][F3 / 2][F3 / 2] = 0.5f;
}

int main() {
    try {
        read_exact("weights/conv1_weights_3x_flp.bin", &w1[0][0][0][0], N1 * F1 * F1);
        read_exact("weights/conv1_biases_3x_flp.bin", b1, N1);
        read_exact("weights/conv2_weights_3x_flp.bin", &w2[0][0][0][0], N2 * N1);
        read_exact("weights/conv2_biases_3x_flp.bin", b2, N2);
        read_exact("weights/conv3_weights_3x_flp.bin", &w3[0][0][0][0], N2 * F3 * F3);
        read_exact("weights/conv3_biases_3x_flp.bin", b3, N3);
        read_image("set5/butterfly_3x_LR_u8.bin");
        invoke(0, !EXP_COLD_START);
        read_exact("fixed_reference.bin", &reference[0][0][0], H * W);
        require_exact("First butterfly transaction");
        {
            std::ofstream out("butterfly_output.bin", std::ios::binary);
            if (!out.write(reinterpret_cast<const char *>(output), sizeof(output)))
                throw std::runtime_error("Butterfly output write failed");
        }
        read_exact("set5/butterfly_3x_GR_flp.bin", &reference[0][0][0], H * W);
        const double butterfly_mse = mse(false), border_mse = mse(true);
        const float expected = 104.0f / 256.0f;
        if (!EXP_COLD_START) {
            constructed_params();
            read_image("set14/lenna_3x_LR_u8.bin");
            invoke(1, false);
            read_exact("numpy_reference/lenna_output.bin", &reference[0][0][0], H * W);
            require_exact("Skipped-load lenna with ignored constructed parameters");
            for (int i = 0; i < H * W; ++i) image[0][i / W][i % W] = 0.5f;
            invoke(2, true);
            for (int i = 0; i < H * W; ++i) reference[0][i / W][i % W] = expected;
            require_exact("Reloaded constructed parameters");
            clear_params();
            invoke(3, false);
            require_exact("Skipped-load retention of most recent constructed parameters");
        }
        std::cout << std::setprecision(17)
                  << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"reload_switch_pass\":true,"
                  << "\"frame_count\":" << EXP_FRAMES << ",\"cold_start_pass\":"
                  << (EXP_COLD_START ? "true" : "false") << ",\"reuse_pass\":"
                  << (EXP_COLD_START ? "false" : "true") << ",\"reload_pass\":"
                  << (EXP_COLD_START ? "false" : "true") << ",\"retained_latest_pass\":"
                  << (EXP_COLD_START ? "false" : "true") << ",\"reload_expected\":" << expected
                  << ",\"load_flags\":" << (EXP_COLD_START ? "[0]" : "[1,0,1,0]")
                  << ",\"butterfly_mse\":" << butterfly_mse << ",\"border_mse\":" << border_mse
                  << ",\"image_count\":0,\"set14_psnr\":null,\"delta_psnr\":null}" << std::endl;
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "EXP_ERROR " << e.what() << std::endl;
        return 1;
    }
}
