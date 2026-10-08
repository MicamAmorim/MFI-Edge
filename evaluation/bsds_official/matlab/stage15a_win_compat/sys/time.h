#ifndef MFI_EDGE_STAGE15A_SYS_TIME_H
#define MFI_EDGE_STAGE15A_SYS_TIME_H

#include <chrono>

struct timeval {
    long tv_sec;
    long tv_usec;
};

static inline int gettimeofday(struct timeval* value, void*)
{
    const std::chrono::microseconds elapsed =
        std::chrono::duration_cast<std::chrono::microseconds>(
            std::chrono::system_clock::now().time_since_epoch());
    value->tv_sec = static_cast<long>(elapsed.count() / 1000000);
    value->tv_usec = static_cast<long>(elapsed.count() % 1000000);
    return 0;
}

#endif
