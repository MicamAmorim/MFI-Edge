#ifndef MFI_EDGE_STAGE15A_IEEE754_H
#define MFI_EDGE_STAGE15A_IEEE754_H

#include <stdint.h>

#define IEEE754_DOUBLE_BIAS 0x3ff

union ieee754_double {
    double d;
    struct {
        uint32_t mantissa1;
        uint32_t mantissa0 : 20;
        uint32_t exponent : 11;
        uint32_t negative : 1;
    } ieee;
};

#endif
