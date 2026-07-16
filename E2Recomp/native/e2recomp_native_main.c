#include "E2Recomp_recon.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#if UINTPTR_MAX <= UINT32_MAX
#include <pthread.h>
#include <unistd.h>
#endif

#if UINTPTR_MAX <= UINT32_MAX
typedef struct E2R_FrameDumpRequest {
    const char *path;
    unsigned delay_seconds;
} E2R_FrameDumpRequest;

static E2R_FrameDumpRequest e2r_frame_dump_request;

static uintptr_t e2r_surface_framebuffer(unsigned surface)
{
    switch (surface & 3u) {
    case 0: return _DAT_00636150;
    case 1: return _DAT_00636154;
    case 2: return _DAT_00636158;
    case 3: return _DAT_0063615c;
    default: return 0;
    }
}

static int e2r_frame_has_pixels(uintptr_t framebuffer, size_t bytes)
{
    const unsigned char *pixels = (const unsigned char *)framebuffer;
    size_t i;

    for (i = 0; i < bytes; i++) {
        if (pixels[i] != 0) {
            return 1;
        }
    }
    return 0;
}

static int e2r_select_framebuffer(uintptr_t *framebuffer_out, unsigned *surface_out, size_t bytes)
{
    unsigned visible = (unsigned)(DAT_0047a279 >> 24) & 3u;
    unsigned attempt;

    for (attempt = 0; attempt < 4; attempt++) {
        unsigned surface = (visible + attempt) & 3u;
        uintptr_t framebuffer = e2r_surface_framebuffer(surface);
        if (framebuffer != 0 && !IsBadReadPtr((const void *)framebuffer, bytes) &&
            e2r_frame_has_pixels(framebuffer, bytes)) {
            *framebuffer_out = framebuffer;
            *surface_out = surface;
            return 1;
        }
    }

    *framebuffer_out = e2r_surface_framebuffer(visible);
    *surface_out = visible;
    return *framebuffer_out != 0 && !IsBadReadPtr((const void *)*framebuffer_out, bytes);
}

static int e2r_write_frame_pgm(const char *path, unsigned *surface_out)
{
    uintptr_t framebuffer;
    unsigned width = (unsigned)_DAT_006401ec;
    unsigned height = (unsigned)_DAT_006401d4;
    size_t bytes;
    FILE *out;

    if (width == 0 || height == 0 || width > 4096 || height > 4096) {
        return 0;
    }
    bytes = (size_t)width * (size_t)height;
    if (!e2r_select_framebuffer(&framebuffer, surface_out, bytes)) {
        return 0;
    }

    out = fopen(path, "wb");
    if (out == NULL) {
        return 0;
    }
    fprintf(out, "P5\n%u %u\n255\n", width, height);
    if (fwrite((const void *)framebuffer, 1, bytes, out) != bytes) {
        fclose(out);
        return 0;
    }
    fclose(out);
    return 1;
}

static void *e2r_frame_dump_thread(void *arg)
{
    E2R_FrameDumpRequest *request = (E2R_FrameDumpRequest *)arg;
    unsigned surface = 0;

    sleep(request->delay_seconds);
    if (e2r_write_frame_pgm(request->path, &surface)) {
        fprintf(stderr, "wrote frame dump: %s (surface %u)\n", request->path, surface);
        fflush(stderr);
        _exit(0);
    }
    fprintf(stderr, "failed to write frame dump: %s\n", request->path);
    fflush(stderr);
    _exit(3);
    return NULL;
}

static int e2r_start_frame_dump(const char *path, unsigned delay_seconds)
{
    pthread_t thread;

    e2r_frame_dump_request.path = path;
    e2r_frame_dump_request.delay_seconds = delay_seconds == 0 ? 5 : delay_seconds;
    if (pthread_create(&thread, NULL, e2r_frame_dump_thread, &e2r_frame_dump_request) != 0) {
        fprintf(stderr, "failed to start frame dump thread\n");
        return 0;
    }
    pthread_detach(thread);
    return 1;
}
#endif

int main(int argc, char **argv)
{
    printf("Ecstatica II data: %s\n", E2RECOMP_DATA_DIR);
    if (!SetCurrentDirectoryA(E2RECOMP_DATA_DIR)) {
        fprintf(stderr, "failed to enter Ecstatica II data directory\n");
        return 1;
    }
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

    if (argc > 2 && strcmp(argv[1], "--dump-frame") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--dump-frame needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned delay_seconds = argc > 3 ? (unsigned)strtoul(argv[3], NULL, 10) : 5;
        if (!e2r_start_frame_dump(argv[2], delay_seconds)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    puts("Linux scaffold initialized. Pass --run-recon to enter the reconstructed game startup thunk.");
    puts("Pass --dump-frame <path.pgm> [seconds] to write a bounded framebuffer inspection dump.");
    return 0;
}
