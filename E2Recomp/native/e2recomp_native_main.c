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
    unsigned inject_delay_seconds;
    unsigned inject_key;
    unsigned inject_keys[16];
    unsigned inject_key_count;
    unsigned inject_interval_ms;
    int dump_all_surfaces;
} E2R_FrameDumpRequest;

static E2R_FrameDumpRequest e2r_frame_dump_request;
extern uintptr_t E2R_input_probe_keydown_count;
extern uintptr_t E2R_input_probe_last_key;
extern uintptr_t E2R_input_probe_last_char_queue;
extern uintptr_t E2R_input_probe_last_scan_queue;
extern uintptr_t E2R_requester_probe_ce58_count;
extern uintptr_t E2R_requester_probe_last_id;
extern uintptr_t E2R_requester_probe_last_mode;
extern uintptr_t E2R_requester_probe_b384_count;
extern uintptr_t E2R_requester_probe_b384_bad_ptr_count;
extern uintptr_t E2R_requester_probe_b384_last_ptr;
extern uintptr_t E2R_requester_probe_b9bc_count;
extern uintptr_t E2R_requester_probe_b9bc_last_item;
extern uintptr_t E2R_requester_probe_bd4c_count;
extern uintptr_t E2R_requester_probe_bd4c_last_key;

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

static unsigned e2r_frame_hash(uintptr_t framebuffer, size_t bytes)
{
    const unsigned char *pixels = (const unsigned char *)framebuffer;
    unsigned hash = 2166136261u;
    size_t i;

    for (i = 0; i < bytes; i++) {
        hash ^= pixels[i];
        hash *= 16777619u;
    }
    return hash;
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

static int e2r_write_surface_pgm(const char *path, unsigned surface, unsigned *hash_out, int *nonblank_out)
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
    framebuffer = e2r_surface_framebuffer(surface);
    if (framebuffer == 0 || IsBadReadPtr((const void *)framebuffer, bytes)) {
        return 0;
    }

    *hash_out = e2r_frame_hash(framebuffer, bytes);
    *nonblank_out = e2r_frame_has_pixels(framebuffer, bytes);

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

static int e2r_write_surface_set(const char *prefix)
{
    unsigned surface;
    int wrote = 0;

    for (surface = 0; surface < 4; surface++) {
        char path[512];
        unsigned hash = 0;
        int nonblank = 0;

        snprintf(path, sizeof(path), "%s-s%u.pgm", prefix, surface);
        if (e2r_write_surface_pgm(path, surface, &hash, &nonblank)) {
            fprintf(stderr, "wrote surface dump: %s (surface %u nonblank=%d hash=%08x)\n",
                    path, surface, nonblank, hash);
            wrote++;
        }
        else {
            fprintf(stderr, "failed to write surface dump: %s (surface %u)\n", path, surface);
        }
    }
    return wrote;
}

static void *e2r_frame_dump_thread(void *arg)
{
    E2R_FrameDumpRequest *request = (E2R_FrameDumpRequest *)arg;
    unsigned surface = 0;
    unsigned remaining_delay = request->delay_seconds;

    if (request->inject_key_count != 0 && request->inject_delay_seconds < remaining_delay) {
        unsigned key_index;

        sleep(request->inject_delay_seconds);
        remaining_delay -= request->inject_delay_seconds;

        for (key_index = 0; key_index < request->inject_key_count; key_index++) {
            uintptr_t keydown_count_before = E2R_input_probe_keydown_count;
            unsigned inject_key = request->inject_keys[key_index];
            MSG msg;

            if (key_index != 0) {
                usleep(request->inject_interval_ms * 1000u);
            }
            if (PostMessageA((HWND)_DAT_00ac4dac, WM_KEYDOWN, inject_key, 0)) {
                fprintf(stderr, "posted key 0x%02x through the Win32 message queue\n", inject_key);
            }
            else {
                fprintf(stderr, "failed to post key 0x%02x through the Win32 message queue\n",
                        inject_key);
            }
            if (PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE) && msg.message != WM_QUIT) {
                TranslateMessage(&msg);
                DispatchMessageA(&msg);
                fprintf(stderr, "dispatched one queued probe message\n");
            }
            else {
                fprintf(stderr, "no queued probe message available for dispatch\n");
            }
            usleep(100000);
            fprintf(stderr,
                    "input state after dispatch wait: keydowns %lu->%lu last_key=0x%02lx "
                    "last_char_queue=0x%02lx last_scan_queue=0x%02lx "
                    "DAT_00636844=%lu DAT_00636853=%lu DAT_00479de8=%lu "
                    "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu] "
                    "DAT_0047a76c=%lu DAT_0047a43c=%lu _DAT_0073cc3c=0x%lx\n",
                    (unsigned long)keydown_count_before,
                    (unsigned long)E2R_input_probe_keydown_count,
                    (unsigned long)E2R_input_probe_last_key,
                    (unsigned long)E2R_input_probe_last_char_queue,
                    (unsigned long)E2R_input_probe_last_scan_queue,
                    (unsigned long)DAT_00636844, (unsigned long)DAT_00636853,
                    (unsigned long)DAT_00479de8, (unsigned long)DAT_00636859,
                    (unsigned long)DAT_00636858, (unsigned long)DAT_0063685b,
                    (unsigned long)DAT_00636854, (unsigned long)DAT_00636856,
                    (unsigned long)DAT_00636857, (unsigned long)DAT_0063685c,
                    (unsigned long)DAT_0063685a, (unsigned long)DAT_00636855,
                    (unsigned long)DAT_0047a76c, (unsigned long)DAT_0047a43c,
                    (unsigned long)_DAT_0073cc3c);
            fflush(stderr);
        }
    }
    sleep(remaining_delay);
    if (request->dump_all_surfaces) {
        int wrote = e2r_write_surface_set(request->path);
        if (wrote > 0) {
            fprintf(stderr, "wrote %d surface dump(s) with prefix: %s\n", wrote, request->path);
            fprintf(stderr,
                    "input state: DAT_00636844=%lu DAT_00636853=%lu _DAT_00643650=%lu "
                    "DAT_00479de8=%lu DAT_0047a76c=%lu DAT_0047a43c=%lu "
                    "DAT_0047a730=%lu DAT_00479de4=%lu DAT_0047a788=%lu "
                    "_DAT_00636690=%lu _DAT_0073cc3c=0x%lx "
                    "requester=[ce58=%lu id=0x%lx mode=%lu b384=%lu bad=%lu ptr=0x%lx "
                    "b9bc=%lu item=0x%lx bd4c=%lu key=0x%lx] "
                    "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu]\n",
                    (unsigned long)DAT_00636844, (unsigned long)DAT_00636853,
                    (unsigned long)_DAT_00643650, (unsigned long)DAT_00479de8,
                    (unsigned long)DAT_0047a76c, (unsigned long)DAT_0047a43c,
                    (unsigned long)DAT_0047a730, (unsigned long)DAT_00479de4,
                    (unsigned long)DAT_0047a788, (unsigned long)_DAT_00636690,
                    (unsigned long)_DAT_0073cc3c,
                    (unsigned long)E2R_requester_probe_ce58_count,
                    (unsigned long)E2R_requester_probe_last_id,
                    (unsigned long)E2R_requester_probe_last_mode,
                    (unsigned long)E2R_requester_probe_b384_count,
                    (unsigned long)E2R_requester_probe_b384_bad_ptr_count,
                    (unsigned long)E2R_requester_probe_b384_last_ptr,
                    (unsigned long)E2R_requester_probe_b9bc_count,
                    (unsigned long)E2R_requester_probe_b9bc_last_item,
                    (unsigned long)E2R_requester_probe_bd4c_count,
                    (unsigned long)E2R_requester_probe_bd4c_last_key,
                    (unsigned long)DAT_00636859,
                    (unsigned long)DAT_00636858, (unsigned long)DAT_0063685b,
                    (unsigned long)DAT_00636854, (unsigned long)DAT_00636856,
                    (unsigned long)DAT_00636857, (unsigned long)DAT_0063685c,
                    (unsigned long)DAT_0063685a, (unsigned long)DAT_00636855);
            fflush(stderr);
            _exit(0);
        }
        fprintf(stderr, "failed to write surface dumps with prefix: %s\n", request->path);
        fflush(stderr);
        _exit(3);
    }

    if (e2r_write_frame_pgm(request->path, &surface)) {
        fprintf(stderr, "wrote frame dump: %s (surface %u)\n", request->path, surface);
        fprintf(stderr,
                "input state: DAT_00636844=%lu DAT_00636853=%lu _DAT_00643650=%lu "
                "DAT_00479de8=%lu DAT_0047a76c=%lu DAT_0047a43c=%lu "
                "DAT_0047a730=%lu DAT_00479de4=%lu DAT_0047a788=%lu "
                "_DAT_00636690=%lu _DAT_0073cc3c=0x%lx "
                "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu]\n",
                (unsigned long)DAT_00636844, (unsigned long)DAT_00636853,
                (unsigned long)_DAT_00643650, (unsigned long)DAT_00479de8,
                (unsigned long)DAT_0047a76c, (unsigned long)DAT_0047a43c,
                (unsigned long)DAT_0047a730, (unsigned long)DAT_00479de4,
                (unsigned long)DAT_0047a788, (unsigned long)_DAT_00636690,
                (unsigned long)_DAT_0073cc3c, (unsigned long)DAT_00636859,
                (unsigned long)DAT_00636858, (unsigned long)DAT_0063685b,
                (unsigned long)DAT_00636854, (unsigned long)DAT_00636856,
                (unsigned long)DAT_00636857, (unsigned long)DAT_0063685c,
                (unsigned long)DAT_0063685a, (unsigned long)DAT_00636855);
        fflush(stderr);
        _exit(0);
    }
    fprintf(stderr, "failed to write frame dump: %s\n", request->path);
    fflush(stderr);
    _exit(3);
    return NULL;
}

static int e2r_start_frame_dump(const char *path, unsigned delay_seconds,
                                unsigned inject_delay_seconds, unsigned inject_key,
                                int dump_all_surfaces)
{
    pthread_t thread;

    e2r_frame_dump_request.path = path;
    e2r_frame_dump_request.delay_seconds = delay_seconds == 0 ? 5 : delay_seconds;
    e2r_frame_dump_request.inject_delay_seconds = inject_delay_seconds;
    e2r_frame_dump_request.inject_key = inject_key;
    e2r_frame_dump_request.inject_keys[0] = inject_key;
    e2r_frame_dump_request.inject_key_count = inject_key != 0 ? 1 : 0;
    e2r_frame_dump_request.inject_interval_ms = 250;
    e2r_frame_dump_request.dump_all_surfaces = dump_all_surfaces;
    if (pthread_create(&thread, NULL, e2r_frame_dump_thread, &e2r_frame_dump_request) != 0) {
        fprintf(stderr, "failed to start frame dump thread\n");
        return 0;
    }
    pthread_detach(thread);
    return 1;
}

static unsigned e2r_parse_virtual_key(const char *name)
{
    if (strcmp(name, "enter") == 0 || strcmp(name, "return") == 0) {
        return VK_RETURN;
    }
    if (strcmp(name, "space") == 0) {
        return VK_SPACE;
    }
    if (strcmp(name, "escape") == 0 || strcmp(name, "esc") == 0) {
        return VK_ESCAPE;
    }
    if (strcmp(name, "q") == 0) {
        return VK_Q;
    }
    if (strcmp(name, "ctrl") == 0 || strcmp(name, "control") == 0) {
        return 0x11;
    }
    if (strcmp(name, "a") == 0) {
        return 0x41;
    }
    if (strcmp(name, "c") == 0) {
        return 0x43;
    }
    if (strcmp(name, "d") == 0) {
        return 0x44;
    }
    if (strcmp(name, "m") == 0) {
        return 0x4d;
    }
    if (strcmp(name, "p") == 0) {
        return 0x50;
    }
    if (strcmp(name, "w") == 0) {
        return 0x57;
    }
    if (strcmp(name, "x") == 0) {
        return 0x58;
    }
    if (strcmp(name, "z") == 0) {
        return 0x5a;
    }
    if (strncmp(name, "num", 3) == 0 && name[3] >= '1' && name[3] <= '9' && name[4] == '\0') {
        return 0x60u + (unsigned)(name[3] - '0');
    }
    if (strncmp(name, "f", 1) == 0 && name[1] >= '1' && name[1] <= '9' && name[2] == '\0') {
        return 0x6fu + (unsigned)(name[1] - '0');
    }
    if (strcmp(name, "f10") == 0) {
        return 0x79;
    }
    if (strcmp(name, "f11") == 0) {
        return 0x7a;
    }
    if (strcmp(name, "f12") == 0) {
        return 0x7b;
    }
    return (unsigned)strtoul(name, NULL, 0);
}

static unsigned e2r_parse_virtual_key_sequence(const char *value, unsigned *keys, unsigned max_keys)
{
    char buffer[256];
    char *token;
    unsigned count = 0;

    snprintf(buffer, sizeof(buffer), "%s", value);
    token = strtok(buffer, ",+");
    while (token != NULL && count < max_keys) {
        unsigned key = e2r_parse_virtual_key(token);
        if (key == 0) {
            return 0;
        }
        keys[count++] = key;
        token = strtok(NULL, ",+");
    }
    return count;
}

static int e2r_start_key_sequence_dump(const char *path, unsigned delay_seconds,
                                       unsigned inject_delay_seconds, const unsigned *keys,
                                       unsigned key_count, unsigned interval_ms,
                                       int dump_all_surfaces)
{
    pthread_t thread;
    unsigned i;

    e2r_frame_dump_request.path = path;
    e2r_frame_dump_request.delay_seconds = delay_seconds == 0 ? 5 : delay_seconds;
    e2r_frame_dump_request.inject_delay_seconds = inject_delay_seconds;
    e2r_frame_dump_request.inject_key = key_count != 0 ? keys[0] : 0;
    e2r_frame_dump_request.inject_key_count = key_count;
    e2r_frame_dump_request.inject_interval_ms = interval_ms == 0 ? 250 : interval_ms;
    e2r_frame_dump_request.dump_all_surfaces = dump_all_surfaces;
    for (i = 0; i < key_count && i < 16; i++) {
        e2r_frame_dump_request.inject_keys[i] = keys[i];
    }
    if (pthread_create(&thread, NULL, e2r_frame_dump_thread, &e2r_frame_dump_request) != 0) {
        fprintf(stderr, "failed to start key sequence dump thread\n");
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
        if (!e2r_start_frame_dump(argv[2], delay_seconds, 0, 0, 0)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 2 && strcmp(argv[1], "--dump-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--dump-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned delay_seconds = argc > 3 ? (unsigned)strtoul(argv[3], NULL, 10) : 5;
        if (!e2r_start_frame_dump(argv[2], delay_seconds, 0, 0, 1)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 3 && strcmp(argv[1], "--inject-key-dump") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-key-dump needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned inject_key = e2r_parse_virtual_key(argv[3]);
        unsigned inject_delay_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 2;
        unsigned delay_seconds = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 6;
        if (inject_key == 0) {
            fprintf(stderr, "unknown key for --inject-key-dump: %s\n", argv[3]);
            return 3;
        }
        if (!e2r_start_frame_dump(argv[2], delay_seconds, inject_delay_seconds, inject_key, 0)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 3 && strcmp(argv[1], "--inject-key-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-key-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned inject_key = e2r_parse_virtual_key(argv[3]);
        unsigned inject_delay_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 2;
        unsigned delay_seconds = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 6;
        if (inject_key == 0) {
            fprintf(stderr, "unknown key for --inject-key-surfaces: %s\n", argv[3]);
            return 3;
        }
        if (!e2r_start_frame_dump(argv[2], delay_seconds, inject_delay_seconds, inject_key, 1)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 3 && strcmp(argv[1], "--inject-key-sequence-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-key-sequence-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned keys[16];
        unsigned key_count = e2r_parse_virtual_key_sequence(argv[3], keys, 16);
        unsigned inject_delay_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 2;
        unsigned interval_ms = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 250;
        unsigned delay_seconds = argc > 6 ? (unsigned)strtoul(argv[6], NULL, 10) : 6;
        if (key_count == 0) {
            fprintf(stderr, "unknown key sequence for --inject-key-sequence-surfaces: %s\n", argv[3]);
            return 3;
        }
        if (!e2r_start_key_sequence_dump(argv[2], delay_seconds, inject_delay_seconds, keys,
                                         key_count, interval_ms, 1)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    puts("Linux scaffold initialized. Pass --run-recon to enter the reconstructed game startup thunk.");
    puts("Pass --dump-frame <path.pgm> [seconds] to write a bounded framebuffer inspection dump.");
    puts("Pass --dump-surfaces <prefix> [seconds] to write all four bounded framebuffer dumps.");
    puts("Pass --inject-key-dump <path.pgm> <key|vk> [inject_seconds] [dump_seconds] to probe input.");
    puts("Pass --inject-key-surfaces <prefix> <key|vk> [inject_seconds] [dump_seconds] to probe input surfaces.");
    puts("Pass --inject-key-sequence-surfaces <prefix> <key[,key...]> [inject_seconds] [interval_ms] [dump_seconds] to probe input sequences.");
    return 0;
}
