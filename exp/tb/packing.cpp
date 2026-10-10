#include "packing_pe.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>

static Coefficient a[PE_TERMS], b[PE_TERMS];
static Shared c[PE_TERMS];
static ProductSum first[PE_GROUPS], second[PE_GROUPS];
static uint64_t terms = 0, groups = 0;

static void check() {
    packing_pe(a, b, c, first, second);
    for (int group = 0; group < PE_GROUPS; ++group) {
        int64_t expected_first = 0, expected_second = 0;
        for (int lane = 0; lane < EXP_GROUP; ++lane) {
            const int index = group * EXP_GROUP + lane;
            expected_first += int64_t(a[index].to_int()) * c[index].to_int();
            expected_second += int64_t(b[index].to_int()) * c[index].to_int();
        }
        if (first[group].to_int64() != expected_first || second[group].to_int64() != expected_second)
            throw std::runtime_error("Packed pair mismatch at group " + std::to_string(groups));
        ++groups;
    }
    terms += PE_TERMS;
}

int main() {
    try {
        constexpr int coeff_min = -(1 << (EXP_OPERAND_BITS - 1));
        constexpr int coeff_max = (1 << (EXP_OPERAND_BITS - 1)) - 1;
        constexpr int shared_min = EXP_NONNEG ? 0 : -(1 << (EXP_C_BITS - 1));
        constexpr int shared_max = (1 << (EXP_C_BITS - 1)) - 1;
        const int edges_a[] = {coeff_min, coeff_min + 1, -1, 0, 1, coeff_max - 1, coeff_max};
        const int edges_c[] = {shared_min, shared_min + 1, 0, 1, shared_max - 1, shared_max};
        for (int left : edges_a) for (int right : edges_a) for (int shared : edges_c) {
            for (int i = 0; i < PE_TERMS; ++i) { a[i] = left; b[i] = right; c[i] = shared; }
            check();
        }
        uint32_t state = 0x4861011;
        const uint64_t count = EXP_OPERAND_BITS == 8 && EXP_C_BITS == 8 ? (1ULL << 24) : (1ULL << 20);
        for (uint64_t offset = 0; offset < count; offset += PE_TERMS) {
            for (int i = 0; i < PE_TERMS; ++i) {
                const uint64_t index = (offset + i) % count;
                if (EXP_OPERAND_BITS == 8 && EXP_C_BITS == 8) {
                    a[i] = int(index >> 16) - 128;
                    b[i] = int((index >> 8) & 255) - 128;
                    c[i] = int(index & 255) - 128;
                } else {
                    state = 1664525 * state + 1013904223;
                    a[i] = int((state >> 9) & ((1 << EXP_OPERAND_BITS) - 1)) + coeff_min;
                    state = 1664525 * state + 1013904223;
                    b[i] = int((state >> 9) & ((1 << EXP_OPERAND_BITS) - 1)) + coeff_min;
                    state = 1664525 * state + 1013904223;
                    c[i] = int((state >> 9) & ((1 << (EXP_C_BITS - EXP_NONNEG)) - 1)) + shared_min;
                }
            }
            check();
        }
        std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"tested_terms\":" << terms
                  << ",\"tested_groups\":" << groups << ",\"exhaustive_signed8_triples\":"
                  << (EXP_OPERAND_BITS == 8 && EXP_C_BITS == 8 ? "true" : "false") << "}" << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "EXP_ERROR " << error.what() << std::endl;
        return 1;
    }
}
