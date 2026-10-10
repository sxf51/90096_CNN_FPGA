#include "srcnn.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

#ifndef EXP_FIXED
#define EXP_FIXED 0
#endif
#ifndef EXP_SET14
#define EXP_SET14 0
#endif
#ifndef EXP_REFERENCE
#define EXP_REFERENCE 0
#endif
#ifndef EXP_NUMPY_REFERENCE
#define EXP_NUMPY_REFERENCE 0
#endif
#ifndef EXP_QUICK
#define EXP_QUICK 0
#endif

int tb_conv1();
int tb_srcnn();
void golden_srcnn(ftmap_t [N0][H][W], param_t [N1][N0][F1][F1],
                  param_t [N1], param_t [N2][N1][F2][F2], param_t [N2],
                  param_t [N3][N2][F3][F3], param_t [N3], ftmap_t [N3][H][W]);
void golden_conv1(ftmap_t [N0][H][W], param_t [N1][N0][F1][F1],
                  param_t [N1], ftmap_t [N1][H][W]);

static ftmap_t image[N0][H][W], output[N3][H][W], reference[N3][H][W];
static ftmap_t first[N1][H][W], first_ref[N1][H][W];
static param_t w1[N1][N0][F1][F1], b1[N1];
static param_t w2[N2][N1][F2][F2], b2[N2];
static param_t w3[N3][N2][F3][F3], b3[N3];

template<class T> void read_exact(const std::string &path, T *data, size_t n) {
    std::ifstream in(path.c_str(), std::ios::binary | std::ios::ate);
    if (!in || in.tellg() != std::streamoff(n * sizeof(T)))
        throw std::runtime_error("Missing/wrong-size input: " + path);
    in.seekg(0);
    if (!in.read(reinterpret_cast<char *>(data), n * sizeof(T)))
        throw std::runtime_error("Short read: " + path);
}

void read_image(const std::string &path) {
    std::vector<unsigned char> bytes(H * W);
    read_exact(path, bytes.data(), bytes.size());
    for (int i = 0; i < H * W; ++i) image[0][i / W][i % W] = float(bytes[i]) / 255;
}

double mse(const float *a, const float *b, size_t n, bool border = false) {
    double total = 0;
    size_t count = 0;
    for (size_t i = 0; i < n; ++i) {
        const int y = (i / W) % H, x = i % W;
        if (border && y >= 6 && y < H - 6 && x >= 6 && x < W - 6) continue;
        if (!std::isfinite(a[i]) || !std::isfinite(b[i]))
            throw std::runtime_error("Nonfinite model output");
        const double d = double(a[i]) - double(b[i]);
        total += d * d;
        ++count;
    }
    return total / count;
}

void infer(bool golden) {
    if (golden) golden_srcnn(image, w1, b1, w2, b2, w3, b3, reference);
    else srcnn(image, w1, b1, w2, b2, w3, b3, output);
}

void save(const std::string &path, const float *data, size_t n) {
    std::ofstream out(path.c_str(), std::ios::binary);
    if (!out.write(reinterpret_cast<const char *>(data), n * sizeof(float)))
        throw std::runtime_error("Output write failed: " + path);
}

int main() {
    try {
        read_exact("weights/conv1_weights_3x_flp.bin", &w1[0][0][0][0], N1 * F1 * F1);
        read_exact("weights/conv1_biases_3x_flp.bin", b1, N1);
        read_exact("weights/conv2_weights_3x_flp.bin", &w2[0][0][0][0], N2 * N1);
        read_exact("weights/conv2_biases_3x_flp.bin", b2, N2);
        read_exact("weights/conv3_weights_3x_flp.bin", &w3[0][0][0][0], N2 * F3 * F3);
        read_exact("weights/conv3_biases_3x_flp.bin", b3, N3);
        // Preserve both original testbench outputs; their zero return is not the gate.
        if (!EXP_QUICK || !EXP_FIXED) {
            tb_conv1();
            tb_srcnn();
        }
        read_image("set5/butterfly_3x_LR_u8.bin");
        bool conv1_exact = false;
        double conv1_mse = 0;
        if (!EXP_QUICK || !EXP_FIXED) {
            conv1(image, w1, b1, first);
            golden_conv1(image, w1, b1, first_ref);
            conv1_exact = std::memcmp(first, first_ref, sizeof(first)) == 0;
            read_exact("set5/butterfly_3x_CONV1_flp.bin", &first_ref[0][0][0], N1 * H * W);
            conv1_mse = mse(&first[0][0][0], &first_ref[0][0][0], N1 * H * W);
        }
        infer(false);
        save("butterfly_output.bin", &output[0][0][0], H * W);
        infer(true);
        const bool float_exact = std::memcmp(output, reference, sizeof(output)) == 0;
        bool bit_exact = float_exact;
        if (EXP_REFERENCE) {
            read_exact("fixed_reference.bin", &reference[0][0][0], H * W);
            bit_exact = std::memcmp(output, reference, sizeof(output)) == 0;
        }
        if (EXP_NUMPY_REFERENCE) {
            read_exact("numpy_reference/butterfly_output.bin", &reference[0][0][0], H * W);
            bit_exact = std::memcmp(output, reference, sizeof(output)) == 0;
        }
        read_exact("set5/butterfly_3x_GR_flp.bin", &reference[0][0][0], H * W);
        const double butterfly_mse = mse(&output[0][0][0], &reference[0][0][0], H * W);
        const double border_mse = mse(&output[0][0][0], &reference[0][0][0], H * W, true);
        const char *names[] = {"baboon", "barbara", "bridge", "coastguard", "face",
                              "flowers", "foreman", "lenna", "man", "monarch",
                              "pepper", "ppt3", "zebra"};
        double model_psnr = 0, golden_psnr = 0;
        int count = 0;
        if (EXP_SET14) {
            std::ofstream detail("quality.csv");
            detail << "image,psnr,golden_psnr,delta_psnr,mse,border_mse\n";
            for (const char *name : names) {
                const std::string prefix = std::string("set14/") + name + "_3x_";
                read_image(prefix + "LR_u8.bin");
                infer(false);
                infer(true);
                if (EXP_NUMPY_REFERENCE) {
                    std::vector<float> numpy_output(H * W);
                    read_exact(std::string("numpy_reference/") + name + "_output.bin", numpy_output.data(), H * W);
                    if (std::memcmp(output, numpy_output.data(), sizeof(output)))
                        throw std::runtime_error(std::string("ap_fixed vs numpy mismatch: ") + name);
                }
                if (!EXP_FIXED && std::memcmp(output, reference, sizeof(output)))
                    throw std::runtime_error(std::string("Float mismatch on ") + name);
                std::vector<unsigned char> gt(H * W);
                std::vector<float> gt_f(H * W);
                read_exact(prefix + "GT_u8.bin", gt.data(), gt.size());
                for (int i = 0; i < H * W; ++i) gt_f[i] = float(gt[i]) / 255;
                const double err = mse(&output[0][0][0], gt_f.data(), H * W);
                const double gold_err = mse(&reference[0][0][0], gt_f.data(), H * W);
                const double p = -10 * std::log10(err), g = -10 * std::log10(gold_err);
                model_psnr += p;
                golden_psnr += g;
                ++count;
                detail << std::setprecision(17) << name << ',' << p << ',' << g << ','
                       << p - g << ',' << err << ','
                       << mse(&output[0][0][0], &reference[0][0][0], H * W, true) << '\n';
                save(std::string(name) + "_output.bin", &output[0][0][0], H * W);
                save(std::string(name) + "_golden.bin", &reference[0][0][0], H * W);
                std::cout << "EXP_IMAGE " << name << " psnr=" << p << " delta=" << p - g << std::endl;
            }
            model_psnr /= count;
            golden_psnr /= count;
        }
        const bool pass = EXP_FIXED ? ((!(EXP_REFERENCE || EXP_NUMPY_REFERENCE) || bit_exact) &&
                            (!EXP_SET14 || model_psnr - golden_psnr >= -0.1))
                                    : (float_exact && conv1_exact);
        std::cout << std::setprecision(17) << "EXP_METRICS {\"csim_pass\":" << (pass ? "true" : "false")
                  << ",\"conv1_mse\":";
        if (EXP_QUICK && EXP_FIXED) std::cout << "null"; else std::cout << conv1_mse;
        std::cout << ",\"conv1_exact\":" << (conv1_exact ? "true" : "false")
                  << ",\"butterfly_mse\":" << butterfly_mse << ",\"border_mse\":" << border_mse
                  << ",\"float_exact\":" << (float_exact ? "true" : "false")
                  << ",\"bit_exact\":" << (bit_exact ? "true" : "false")
                  << ",\"image_count\":" << count << ",\"set14_psnr\":";
        if (count) std::cout << model_psnr; else std::cout << "null";
        std::cout << ",\"golden_psnr\":";
        if (count) std::cout << golden_psnr; else std::cout << "null";
        std::cout << ",\"delta_psnr\":";
        if (count) std::cout << model_psnr - golden_psnr; else std::cout << "null";
        std::cout << "}" << std::endl;
        return pass ? 0 : 1;
    } catch (const std::exception &e) {
        std::cerr << "EXP_ERROR " << e.what() << std::endl;
        return 1;
    }
}
