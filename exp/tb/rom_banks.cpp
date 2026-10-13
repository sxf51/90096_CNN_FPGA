#define main arithmetic_validation_main
#include "validate.cpp"
#undef main
#include "rom_constants.h"

template<size_t Count>
static void compare_bank(const char *name, const int16_t (&expected)[Count], std::ofstream &detail) {
    int16_t actual[Count];
    read_exact(std::string("runtime_bank_") + name + ".bin", actual, Count);
    const bool exact = std::memcmp(actual, expected, sizeof(actual)) == 0;
    detail << name << "," << Count << "," << (exact ? "true" : "false") << "\n";
    if (!exact) throw std::runtime_error(std::string("Runtime vs constant ROM bank mismatch: ") + name);
}

int main() {
    if (arithmetic_validation_main()) return 1;
    try {
        const int16_t expected1[9216] = EXP_ROM_W1;
        const int16_t expectedb1[64] = EXP_ROM_B1;
        const int16_t expected2[2048] = EXP_ROM_W2;
        const int16_t expectedb2[32] = EXP_ROM_B2;
        const int16_t expected3[800] = EXP_ROM_W3;
        const int16_t expectedb3[1] = EXP_ROM_B3;
        std::ofstream detail("rom_banks.csv");
        detail << "bank,values,bit_exact\n";
        compare_bank("W1", expected1, detail);
        compare_bank("B1", expectedb1, detail);
        compare_bank("W2", expected2, detail);
        compare_bank("B2", expectedb2, detail);
        compare_bank("W3", expected3, detail);
        compare_bank("B3", expectedb3, detail);
        read_exact("butterfly_output.bin", &output[0][0][0], H*W);
        read_exact("set5/butterfly_3x_GR_flp.bin", &reference[0][0][0], H*W);
        std::cout << std::setprecision(17)
                  << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"rom_bank_exact\":true,"
                  << "\"rom_values_checked\":" << EXP_ROM_BANK_VALUE_COUNT
                  << ",\"butterfly_mse\":" << mse(&output[0][0][0], &reference[0][0][0], H*W)
                  << ",\"border_mse\":" << mse(&output[0][0][0], &reference[0][0][0], H*W, true)
                  << "}\n";
    } catch (const std::exception &error) {
        std::cerr << "ROM_BANK_FAIL " << error.what() << "\n";
        return 1;
    }
    return 0;
}
