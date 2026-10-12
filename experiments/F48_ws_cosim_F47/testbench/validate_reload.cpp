#include "srcnn.h"
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef EXP_FRAMES
#define EXP_FRAMES 2
#endif
#ifndef EXP_FIXED
#define EXP_FIXED 0
#endif
#ifndef EXP_W_BITS
#define EXP_W_BITS 0
#endif
#ifndef EXP_A_BITS
#define EXP_A_BITS 0
#endif
static_assert(EXP_FRAMES == 2, "Reload verification requires exactly two calls");
static_assert(EXP_FIXED && EXP_W_BITS == 10 && EXP_A_BITS == 10,
              "Reload expectation is for the frozen w10a10 quantization boundaries");

static ftmap_t image[N0][H][W], output[N3][H][W], saved_image[N0][H][W];
static ftmap_t reference[N3][H][W], saved_output[N3][H][W];
static param_t w1[N1][N0][F1][F1], b1[N1], saved_w1[N1][N0][F1][F1], saved_b1[N1];
static param_t w2[N2][N1][F2][F2], b2[N2], saved_w2[N2][N1][F2][F2], saved_b2[N2];
static param_t w3[N3][N2][F3][F3], b3[N3], saved_w3[N3][N2][F3][F3], saved_b3[N3];

template<class T> static void read_exact(const std::string &path, T *data, size_t count) {
    std::ifstream in(path.c_str(), std::ios::binary | std::ios::ate);
    if (!in || in.tellg() != std::streamoff(count * sizeof(T)))
        throw std::runtime_error("Missing/wrong-size input: " + path);
    in.seekg(0);
    if (!in.read(reinterpret_cast<char *>(data), count * sizeof(T)))
        throw std::runtime_error("Short read: " + path);
}

static double mse(const float *a, const float *b, bool border) {
    double total = 0;
    size_t count = 0;
    for (int i = 0; i < H * W; ++i) {
        const int y = i / W, x = i % W;
        if (border && y >= 6 && y < H - 6 && x >= 6 && x < W - 6) continue;
        if (!std::isfinite(a[i]) || !std::isfinite(b[i]))
            throw std::runtime_error("Nonfinite model output");
        const double delta = double(a[i]) - double(b[i]);
        total += delta * delta;
        ++count;
    }
    return total / count;
}

int main() {
    try {
        read_exact("weights/conv1_weights_3x_flp.bin", &w1[0][0][0][0], N1 * F1 * F1);
        read_exact("weights/conv1_biases_3x_flp.bin", b1, N1);
        read_exact("weights/conv2_weights_3x_flp.bin", &w2[0][0][0][0], N2 * N1);
        read_exact("weights/conv2_biases_3x_flp.bin", b2, N2);
        read_exact("weights/conv3_weights_3x_flp.bin", &w3[0][0][0][0], N2 * F3 * F3);
        read_exact("weights/conv3_biases_3x_flp.bin", b3, N3);
        std::vector<unsigned char> bytes(H * W);
        read_exact("set5/butterfly_3x_LR_u8.bin", bytes.data(), bytes.size());
        for (int i = 0; i < H * W; ++i) image[0][i / W][i % W] = float(bytes[i]) / 255;
        std::memcpy(saved_image, image, sizeof(image));
        std::memcpy(saved_w1, w1, sizeof(w1));
        std::memcpy(saved_b1, b1, sizeof(b1));
        std::memcpy(saved_w2, w2, sizeof(w2));
        std::memcpy(saved_b2, b2, sizeof(b2));
        std::memcpy(saved_w3, w3, sizeof(w3));
        std::memcpy(saved_b3, b3, sizeof(b3));

        srcnn(image, w1, b1, w2, b2, w3, b3, output);
        read_exact("fixed_reference.bin", &reference[0][0][0], H * W);
        if (std::memcmp(output, reference, sizeof(output)))
            throw std::runtime_error("First butterfly frame differs from E017 reference");
        std::memcpy(saved_output, output, sizeof(output));
        {
            std::ofstream out("butterfly_output.bin", std::ios::binary);
            if (!out.write(reinterpret_cast<const char *>(output), sizeof(output)))
                throw std::runtime_error("Butterfly output write failed");
        }
        read_exact("set5/butterfly_3x_GR_flp.bin", &reference[0][0][0], H * W);
        const double butterfly_mse = mse(&output[0][0][0], &reference[0][0][0], false);
        const double border_mse = mse(&output[0][0][0], &reference[0][0][0], true);

        std::memset(w1, 0, sizeof(w1));
        std::memset(w2, 0, sizeof(w2));
        std::memset(w3, 0, sizeof(w3));
        for (int c = 0; c < N1; ++c) b1[c] = 0.5f;
        for (int c = 0; c < N2; ++c) b2[c] = 0.25f;
        for (int c = 0; c < N3; ++c) b3[c] = 0.125f;
        w1[0][0][F1 / 2][F1 / 2] = 0.25f;
        w2[0][0][0][0] = 0.5f;
        w3[0][0][F3 / 2][F3 / 2] = 0.5f;
        for (int i = 0; i < H * W; ++i) image[0][i / W][i % W] = 0.5f;
        srcnn(image, w1, b1, w2, b2, w3, b3, output);
        // The layer2 carrier has seven fractional bits; final output has eight.
        const float expected = 104.0f / 256.0f;
        for (int i = 0; i < H * W; ++i) {
            if (std::memcmp(&output[0][i / W][i % W], &expected, sizeof(expected)))
                throw std::runtime_error("Changed-parameter second frame mismatch at pixel " + std::to_string(i));
        }

        std::memcpy(image, saved_image, sizeof(image));
        std::memcpy(w1, saved_w1, sizeof(w1));
        std::memcpy(b1, saved_b1, sizeof(b1));
        std::memcpy(w2, saved_w2, sizeof(w2));
        std::memcpy(b2, saved_b2, sizeof(b2));
        std::memcpy(w3, saved_w3, sizeof(w3));
        std::memcpy(b3, saved_b3, sizeof(b3));
        std::memcpy(output, saved_output, sizeof(output));
        std::cout << std::setprecision(17)
                  << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"frame_count\":2,"
                  << "\"reload_pass\":true,\"reload_expected\":" << expected
                  << ",\"butterfly_mse\":" << butterfly_mse << ",\"border_mse\":" << border_mse
                  << ",\"image_count\":0,\"set14_psnr\":null,\"delta_psnr\":null}" << std::endl;
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "EXP_ERROR " << e.what() << std::endl;
        return 1;
    }
}
