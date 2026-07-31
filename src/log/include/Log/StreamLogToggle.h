#pragma once

#include <iostream>

#if defined(UT_DISABLE_STREAM_LOG)
    #define UT_COUT if (true) {} else std::cout
    #define UT_CERR if (true) {} else std::cerr
    #define UT_CLOG if (true) {} else std::clog
#else
    #define UT_COUT std::cout
    #define UT_CERR std::cerr
    #define UT_CLOG std::clog
#endif

#if defined(UT_DISABLE_STREAM_LOG_2)
    #define UT2_COUT if (true) {} else std::cout
    #define UT2_CERR if (true) {} else std::cerr
    #define UT2_CLOG if (true) {} else std::clog
#else
    #define UT2_COUT std::cout
    #define UT2_CERR std::cerr
    #define UT2_CLOG std::clog
#endif
