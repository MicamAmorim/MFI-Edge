#ifndef MFI_EDGE_STAGE15A_SYS_TIMES_H
#define MFI_EDGE_STAGE15A_SYS_TIMES_H

#include <time.h>

struct tms {
    clock_t tms_utime;
    clock_t tms_stime;
    clock_t tms_cutime;
    clock_t tms_cstime;
};

static inline clock_t times(struct tms* value)
{
    const clock_t now = clock();
    if (value != 0) {
        value->tms_utime = now;
        value->tms_stime = 0;
        value->tms_cutime = 0;
        value->tms_cstime = 0;
    }
    return now;
}

#endif
