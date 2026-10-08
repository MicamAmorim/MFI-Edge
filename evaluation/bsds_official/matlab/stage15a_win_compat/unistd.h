#ifndef MFI_EDGE_STAGE15A_UNISTD_H
#define MFI_EDGE_STAGE15A_UNISTD_H

#include <time.h>

#ifndef _SC_CLK_TCK
#define _SC_CLK_TCK 2
#endif

static inline long sysconf(int name)
{
    return name == _SC_CLK_TCK ? static_cast<long>(CLOCKS_PER_SEC) : -1L;
}

#endif
