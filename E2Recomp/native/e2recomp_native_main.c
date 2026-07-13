#include "E2Recomp_recon.h"

#include <stdint.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv)
{
    printf("Ecstatica II data: %s\n", E2RECOMP_DATA_DIR);
    E2R_MapLegacyAddressSpace();
    E2R_InitData();

    if (argc > 1 && strcmp(argv[1], "--run-recon") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--run-recon needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    puts("Linux scaffold initialized. Pass --run-recon to enter the reconstructed game startup thunk.");
    return 0;
}
