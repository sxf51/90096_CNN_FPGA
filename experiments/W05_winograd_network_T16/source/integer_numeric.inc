static_assert(EXP_FIXED, "Integer carrier requires the fixed precision contract");
#ifdef __SYNTHESIS__
template<int Bits> using word = ap_int<Bits>;
#else
template<int Bits> using word = typename std::conditional<(Bits <= 16), int16_t,
    typename std::conditional<(Bits <= 32), int32_t, int64_t>::type>::type;
#endif
using weight = word<EXP_W_BITS>;
using bias = weight;
using input = word<EXP_A_BITS>;
using act1 = input;
using act2 = input;
using output = input;
using acc1 = word<EXP_W_BITS + EXP_A_BITS + 3>;
using acc2 = acc1;
using acc3 = acc1;

template<class Q, int Bits> static word<Bits> raw_value(Q value) {
#pragma HLS INLINE
    ap_int<Bits> bits = value.range();
#ifdef __SYNTHESIS__
    return bits;
#else
    return bits.to_int();
#endif
}
static input encode_input(float value) {
#pragma HLS INLINE
    using Q = ap_fixed<EXP_A_BITS, 2, AP_RND_CONV, AP_SAT>;
    return raw_value<Q, EXP_A_BITS>(Q(value));
}
static weight encode_weight(float value) {
#pragma HLS INLINE
    using Q = ap_fixed<EXP_W_BITS, 1, AP_RND_CONV, AP_SAT>;
    return raw_value<Q, EXP_W_BITS>(Q(value));
}
static acc1 bias1(bias value) {
#pragma HLS INLINE
    return acc1(value) * (1 << (EXP_A_BITS - 2));
}
static acc3 bias3(bias value) {
#pragma HLS INLINE
    return acc3(value) * (1 << (EXP_A_BITS - 3));
}
template<int Shift, class Acc> static output quantize(Acc sum) {
#pragma HLS INLINE
    static_assert(Shift > 0, "The boundary removes fractional bits");
    Acc base = sum >> Shift;
    const Acc remainder = sum & ((1 << Shift) - 1);
    const int half = 1 << (Shift - 1);
    if (remainder > half || (remainder == half && (base & 1) != 0)) ++base;
    const int low = -(1 << (EXP_A_BITS - 1));
    const int high = (1 << (EXP_A_BITS - 1)) - 1;
    if (base < low) return output(low);
    if (base > high) return output(high);
    return output(base);
}
static act1 relu1(acc1 sum) {
#pragma HLS INLINE
    return sum > 0 ? quantize<EXP_W_BITS - 1>(sum) : act1(0);
}
static act2 relu2(acc2 sum) {
#pragma HLS INLINE
    return sum > 0 ? quantize<EXP_W_BITS>(sum) : act2(0);
}
static float decode(output value) {
#pragma HLS INLINE
    return float(value) / float(1 << (EXP_A_BITS - 2));
}
