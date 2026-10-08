#ifndef MFI_EDGE_STAGE15A_WIN_COMPAT_H
#define MFI_EDGE_STAGE15A_WIN_COMPAT_H

#include <stdint.h>
#include <float.h>

typedef uint16_t u_int16_t;
typedef uint32_t u_int32_t;
typedef uint64_t u_int64_t;

static inline double erand48(unsigned short state[3])
{
    uint64_t value =
        (static_cast<uint64_t>(state[2]) << 32) |
        (static_cast<uint64_t>(state[1]) << 16) |
        static_cast<uint64_t>(state[0]);
    value = (value * 0x5DEECE66DULL + 0xBULL) & ((1ULL << 48) - 1ULL);
    state[0] = static_cast<unsigned short>(value & 0xffffULL);
    state[1] = static_cast<unsigned short>((value >> 16) & 0xffffULL);
    state[2] = static_cast<unsigned short>((value >> 32) & 0xffffULL);
    return static_cast<double>(value) / static_cast<double>(1ULL << 48);
}

#define mxCreateScalarDouble mxCreateDoubleScalar
#define finite _finite
#define __STRING(value) #value

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#endif
