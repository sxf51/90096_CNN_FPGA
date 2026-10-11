#include "packing16_pe.h"
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>

static Operand16 a[PACK16_TERMS], b[PACK16_TERMS], c[PACK16_TERMS];
static Product32 first[PACK16_TERMS], second[PACK16_TERMS];
static int used = 0;
static uint64_t terms = 0;

static void check_batch() {
    packing16_pe(a, b, c, first, second);
    for (int i = 0; i < PACK16_TERMS; ++i) {
        const int64_t expected_first = int64_t(a[i].to_int()) * c[i].to_int();
        const int64_t expected_second = int64_t(b[i].to_int()) * c[i].to_int();
        if (first[i].to_int64() != expected_first || second[i].to_int64() != expected_second)
            throw std::runtime_error("Complete INT16 product mismatch at term " +
                                     std::to_string(terms + i) + ", a=" +
                                     std::to_string(a[i].to_int()) + ", b=" +
                                     std::to_string(b[i].to_int()) + ", c=" +
                                     std::to_string(c[i].to_int()));
    }
    terms += PACK16_TERMS;
    used = 0;
}

static void add(int left, int right, int shared) {
    a[used] = left;
    b[used] = right;
    c[used] = shared;
    if (++used == PACK16_TERMS) check_batch();
}

static int random16(uint32_t &state) {
    state = state * 1664525u + 1013904223u;
    return int((state >> 8) & 65535u) - 32768;
}

int main() {
    try {
        const int edges[] = {-32768, -32767, -32640, -32513, -32512, -257, -256,
                             -255, -129, -128, -127, -1, 0, 1, 127, 128, 129,
                             255, 256, 257, 32511, 32639, 32640, 32766, 32767};
        uint64_t boundary_count = 0;
        for (int left : edges) for (int right : edges) for (int shared : edges) {
            add(left, right, shared);
            ++boundary_count;
        }
        const int companions[][2] = {{-32768, -32768}, {-1, 32767}, {0, -1}, {32767, 1}};
        uint64_t sweep_count = 0;
        for (int value = -32768; value <= 32767; ++value) {
            for (const auto &pair : companions) {
                add(value, pair[0], pair[1]);
                add(pair[0], value, pair[1]);
                add(pair[0], pair[1], value);
                sweep_count += 3;
            }
        }
        for (int lo = 0; lo < 256; ++lo) for (int shared = 0; shared < 256; ++shared)
            add(lo - 32768, 32767 - lo, shared - 32768);
        uint32_t state = 0x1600486u;
        constexpr uint64_t random_count = 1ULL << 20;
        for (uint64_t i = 0; i < random_count; ++i) {
            const int left = random16(state), right = random16(state), shared = random16(state);
            add(left, right, shared);
        }
        while (used) add(-32768, 32767, -1);
        std::cout << "EXP_METRICS {\"csim_pass\":true,\"bit_exact\":true,\"tested_terms\":"
                  << terms << ",\"checked_products\":" << 2 * terms
                  << ",\"boundary_triples\":" << boundary_count
                  << ",\"role_sweep_triples\":" << sweep_count
                  << ",\"random_triples\":" << random_count
                  << ",\"signed16_value_coverage_per_role\":65536,\"exhaustive_triples\":false}"
                  << std::endl;
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "EXP_ERROR " << error.what() << std::endl;
        return 1;
    }
}
