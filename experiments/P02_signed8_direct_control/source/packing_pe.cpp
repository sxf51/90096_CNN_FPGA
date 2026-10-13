#include "packing_pe.h"
#include <cstdint>
#if EXP_PACK_MODE == 3
#include <hls_dsp_builtins.h>
#endif

#ifdef __SYNTHESIS__
using Wide = ap_int<48>;
using Packed = ap_int<27>;
using Low = ap_int<8>;
using Residual = ap_int<3>;
#else
using Wide = int64_t;
using Packed = int32_t;
using Low = int32_t;
using Residual = int32_t;
#endif

static Wide residual_product(Residual residual, Shared value) {
#pragma HLS INLINE
    Wide result = 0;
    if (residual == 1) result = value;
    else if (residual == -1) result = -Wide(value);
    else if (residual == 2) result = Wide(value) * 2;
    else if (residual == -2) result = -Wide(value) * 2;
    return result * 256;
}

void packing_pe(Coefficient a[PE_TERMS], Coefficient b[PE_TERMS], Shared c[PE_TERMS],
                ProductSum first[PE_GROUPS], ProductSum second[PE_GROUPS]) {
    static_assert(PE_TERMS % EXP_GROUP == 0, "Whole groups only");
    static_assert(EXP_OPERAND_BITS <= 8 || EXP_GROUP == 1, "Generic signed10 coefficients unpack every term");
    static_assert(EXP_C_BITS <= 8 || EXP_GROUP == 1 || (EXP_NONNEG && EXP_GROUP <= 2), "Signed18 low-field bound");
    Wide packed_sum = 0, extra_first = 0, extra_second = 0;
    pack_terms: for (int i = 0; i < PE_TERMS; ++i) {
#pragma HLS PIPELINE II=1
        if (i % EXP_GROUP == 0) {
            packed_sum = 0;
            extra_first = 0;
            extra_second = 0;
        }
#if EXP_PACK_MODE == 0
#ifdef __SYNTHESIS__
        auto direct_first = a[i] * c[i];
        auto direct_second = b[i] * c[i];
#pragma HLS BIND_OP variable=direct_first op=mul impl=dsp
#pragma HLS BIND_OP variable=direct_second op=mul impl=dsp
#else
        const Wide direct_first = Wide(a[i].to_int()) * c[i].to_int();
        const Wide direct_second = Wide(b[i].to_int()) * c[i].to_int();
#endif
        extra_first += direct_first;
        extra_second += direct_second;
#else
#ifdef __SYNTHESIS__
        const Low lo_a = a[i], lo_b = b[i];
        const Residual res_a = (ap_int<11>(a[i]) - ap_int<11>(lo_a)) >> 8;
        const Residual res_b = (ap_int<11>(b[i]) - ap_int<11>(lo_b)) >> 8;
#else
        const Low lo_a = (a[i].to_int() + 640) % 256 - 128;
        const Low lo_b = (b[i].to_int() + 640) % 256 - 128;
        const Residual res_a = (a[i].to_int() - lo_a) / 256;
        const Residual res_b = (b[i].to_int() - lo_b) / 256;
#endif
        const Packed upper = Packed(lo_a) * 262144;
        const Packed packed = upper + Packed(lo_b);
#if EXP_PACK_MODE == 3
        const Wide product = Wide(hls::dsp48e2::add_mul_add<
            hls::dspInternal::FULL_PIPELINE | hls::dspInternal::REG_M | hls::dspInternal::REG_P>(
                hls::dsp48e2::D_t(lo_b), hls::dsp48e2::A_t(upper),
                hls::dsp48e2::B_t(c[i]), hls::dsp48e2::C_t(0)));
#elif defined(__SYNTHESIS__)
        auto product = packed * c[i];
#if EXP_PACK_MODE == 1
#pragma HLS BIND_OP variable=product op=mul impl=dsp
#endif
#else
        const Wide product = Wide(packed) * c[i].to_int();
#endif
        packed_sum += product;
#pragma HLS BIND_OP variable=packed_sum op=add impl=fabric latency=1
        extra_first += residual_product(res_a, c[i]);
        extra_second += residual_product(res_b, c[i]);
#endif
        if (i % EXP_GROUP == EXP_GROUP - 1) {
#if EXP_PACK_MODE == 0
            first[i / EXP_GROUP] = extra_first;
            second[i / EXP_GROUP] = extra_second;
#else
            const int low_bits = int(packed_sum & 262143);
            const int low = low_bits >= 131072 ? low_bits - 262144 : low_bits;
            const Wide high = (packed_sum >> 18) + (low < 0 ? 1 : 0);
            first[i / EXP_GROUP] = high + extra_first;
            second[i / EXP_GROUP] = Wide(low) + extra_second;
#endif
        }
    }
}
