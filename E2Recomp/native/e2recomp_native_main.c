#include "E2Recomp_recon.h"
#include "e2recomp_host_backend.h"

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "e2recomp_log.h"
#if UINTPTR_MAX <= UINT32_MAX
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#endif

static volatile unsigned e2r_visibility_dump_requests;

void E2R_RequestVisibilityDump(void)
{
    e2r_visibility_dump_requests++;
    fprintf(stderr, "visibility dump requested via host hotkey\n");
}

#if UINTPTR_MAX <= UINT32_MAX
#define E2R_MAX_MOUSE_CLICKS 8

typedef struct E2R_FrameDumpRequest {
    const char *path;
    unsigned delay_seconds;
    unsigned inject_delay_seconds;
    unsigned inject_key;
    unsigned inject_keys[16];
    unsigned inject_key_groups[16];
    unsigned inject_key_count;
    unsigned inject_interval_ms;
    unsigned gameplay_key_split;
    unsigned post_action_delay_seconds;
    unsigned mouse_click_x[E2R_MAX_MOUSE_CLICKS];
    unsigned mouse_click_y[E2R_MAX_MOUSE_CLICKS];
    unsigned mouse_click_count;
    unsigned mouse_click_interval_ms;
    int inject_mouse_click;
    int wait_for_requester_ready;
    int wait_for_gameplay_frame;
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
extern uintptr_t E2R_requester_probe_bd4c_seen_key_count;
extern uintptr_t E2R_requester_probe_bd4c_no_key_count;
extern uintptr_t E2R_requester_probe_bd4c_last_cursor;
extern uintptr_t E2R_requester_probe_bd4c_param_item;
extern uintptr_t E2R_requester_probe_selected_item;
extern uintptr_t E2R_requester_probe_selected_next;
extern uintptr_t E2R_requester_probe_selected_action;
extern uintptr_t E2R_requester_probe_move_count;
extern uintptr_t E2R_requester_probe_move_key;
extern uintptr_t E2R_requester_probe_move_from;
extern uintptr_t E2R_requester_probe_move_to;
extern uintptr_t E2R_requester_probe_pending_key_count;
extern uintptr_t E2R_requester_probe_pending_key_read;
extern uintptr_t E2R_requester_probe_fed_key_count;
extern uintptr_t E2R_requester_probe_last_fed_key;
extern uintptr_t E2R_requester_probe_last_fed_char;
extern uintptr_t E2R_requester_probe_last_fed_scan;
extern uintptr_t E2R_requester_probe_action_count;
extern uintptr_t E2R_requester_probe_last_action;
extern uintptr_t E2R_start_game_probe_count;
extern uintptr_t E2R_start_game_probe_last_player;
extern uintptr_t E2R_start_game_probe_last_mode;
extern uintptr_t E2R_start_code_probe_startup_scans;
extern uintptr_t E2R_start_code_probe_startup_matches;
extern uintptr_t E2R_start_code_probe_action_scans;
extern uintptr_t E2R_start_code_probe_action_matches;
extern uintptr_t E2R_start_code_probe_dispatches;
extern uintptr_t E2R_start_code_probe_last_node;
extern uintptr_t E2R_start_code_probe_last_name_index;
extern uintptr_t E2R_start_code_probe_last_bytecode_offset;
extern uintptr_t E2R_action_opcode_count;
extern uintptr_t E2R_action_last_opcode;
extern uintptr_t E2R_action_last_cursor;
extern uintptr_t E2R_action_hit_75_count;
extern uint32_t E2R_active_palette[256];

static void e2r_read_current_action_state(
    uintptr_t *actor_out,
    uintptr_t *slot_out,
    uintptr_t *action_out,
    unsigned *duration_out,
    unsigned *progress_out,
    unsigned *slot_flags_out,
    unsigned *actor_flags_out)
{
    uintptr_t actor = DAT_0047a470;
    uintptr_t slot = 0;
    uintptr_t action = 0;
    unsigned duration = 0;
    unsigned progress = 0;
    unsigned slot_flags = 0;
    unsigned actor_flags = 0;

    if (actor != 0 && !IsBadReadPtr((const void *)actor, 0xb8)) {
        slot = actor + 0xa6;
        actor_flags = *(const unsigned char *)(actor + 3);
        if (!IsBadReadPtr((const void *)slot, 0x12)) {
            action = *(const uint32_t *)slot;
            duration = *(const uint16_t *)(slot + 4);
            progress = *(const uint16_t *)(slot + 6);
            slot_flags = *(const uint16_t *)(slot + 0xc);
        }
    }

    *actor_out = actor;
    *slot_out = slot;
    *action_out = action;
    *duration_out = duration;
    *progress_out = progress;
    *slot_flags_out = slot_flags;
    *actor_flags_out = actor_flags;
}
extern uintptr_t E2R_active_palette_valid;
extern uintptr_t E2R_active_palette_update_count;

static int e2r_write_surface_set(const char *prefix);
static int e2r_write_visibility_packet(HWND hwnd, const char *prefix);

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

static unsigned e2r_palette_hash(void)
{
    unsigned hash = 2166136261u;
    unsigned i;

    for (i = 0; i < 256u; i++) {
        uint32_t color = E2R_active_palette[i];
        hash ^= color & 0xffu;
        hash *= 16777619u;
        hash ^= (color >> 8) & 0xffu;
        hash *= 16777619u;
        hash ^= (color >> 16) & 0xffu;
        hash *= 16777619u;
    }
    return hash;
}

static unsigned e2r_palette_nonzero_count(void)
{
    unsigned count = 0;
    unsigned i;

    for (i = 0; i < 256u; i++) {
        if (E2R_active_palette[i] != 0) {
            count++;
        }
    }
    return count;
}

static unsigned e2r_recovered_front_surface(void)
{
    unsigned visible = (unsigned)(DAT_0047a279 >> 24) & 3u;

    if (DAT_0047a43c != 0) {
        return (visible & 1u) + 2u;
    }
    return visible;
}

static int e2r_select_framebuffer(uintptr_t *framebuffer_out, unsigned *surface_out, size_t bytes)
{
    unsigned front = e2r_recovered_front_surface();
    unsigned visible = (unsigned)(DAT_0047a279 >> 24) & 3u;
    unsigned visible_pair = visible ^ 1u;
    unsigned low_visible = visible & 1u;
    unsigned low_pair = low_visible ^ 1u;
    unsigned candidates[4];
    unsigned attempt;
    uintptr_t front_framebuffer = e2r_surface_framebuffer(front);

    if (front_framebuffer != 0 && !IsBadReadPtr((const void *)front_framebuffer, bytes) &&
        e2r_frame_has_pixels(front_framebuffer, bytes)) {
        *framebuffer_out = front_framebuffer;
        *surface_out = front;
        return 1;
    }

    if (DAT_0047a43c != 0) {
        candidates[0] = low_visible + 2u;
        candidates[1] = low_pair + 2u;
        candidates[2] = low_visible;
        candidates[3] = low_pair;
    }
    else {
        candidates[0] = visible;
        candidates[1] = visible_pair;
        candidates[2] = (visible + 2u) & 3u;
        candidates[3] = (visible + 3u) & 3u;
    }

    for (attempt = 0; attempt < 4; attempt++) {
        unsigned surface = candidates[attempt];
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

static void e2r_trace_present_surfaces(unsigned selected_surface, size_t bytes)
{
    unsigned surface;

    fprintf(stderr,
            "host backend live presentation: selected=%u front=%u visible=%u hires=%lu "
            "width=%lu height=%lu palette=%lu updates=%lu\n",
            selected_surface, e2r_recovered_front_surface(),
            (unsigned)(DAT_0047a279 >> 24) & 3u,
            (unsigned long)DAT_0047a43c,
            (unsigned long)_DAT_006401ec, (unsigned long)_DAT_006401d4,
            (unsigned long)E2R_active_palette_valid,
            (unsigned long)E2R_active_palette_update_count);
    for (surface = 0; surface < 4u; surface++) {
        uintptr_t framebuffer = e2r_surface_framebuffer(surface);
        int readable = framebuffer != 0 && !IsBadReadPtr((const void *)framebuffer, bytes);
        fprintf(stderr,
                "  surface %u fb=0x%lx readable=%d nonblank=%d hash=%08x\n",
                surface, (unsigned long)framebuffer, readable,
                readable ? e2r_frame_has_pixels(framebuffer, bytes) : 0,
                readable ? e2r_frame_hash(framebuffer, bytes) : 0u);
    }
}

static uint64_t e2r_monotonic_milliseconds(void)
{
    struct timespec ts;

    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return ((uint64_t)ts.tv_sec * 1000u) + ((uint64_t)ts.tv_nsec / 1000000u);
}

static int e2r_present_current_frame(HWND hwnd, int force_present)
{
    static uint64_t last_present_ms;
    static int diag_initialized;
    static int diag_enabled;
    static unsigned diag_count;
    static unsigned diag_last_surface = ~0u;
    static unsigned long diag_last_hires = ~0ul;
    uintptr_t framebuffer;
    unsigned surface;
    unsigned width = (unsigned)_DAT_006401ec;
    unsigned height = (unsigned)_DAT_006401d4;
    uint64_t now_ms;
    size_t bytes;
    int presented;

    if (hwnd == NULL || hwnd->ptr == NULL ||
        width == 0 || height == 0 || width > 4096u || height > 4096u) {
        return 0;
    }
    E2R_PumpHostEvents();
    if (hwnd->ptr == NULL) {
        return 0;
    }
    now_ms = e2r_monotonic_milliseconds();
    if (!force_present && last_present_ms != 0 && now_ms != 0 &&
        now_ms - last_present_ms < 33u) {
        return 0;
    }
    last_present_ms = now_ms;
    bytes = (size_t)width * (size_t)height;
    if (!e2r_select_framebuffer(&framebuffer, &surface, bytes)) {
        return 0;
    }
    presented = E2R_HostPresentIndexed8((E2R_HostWindow *)hwnd->ptr,
                                        (const unsigned char *)framebuffer,
                                        width, height, width,
                                        E2R_active_palette_valid ? E2R_active_palette : NULL);
    if (!diag_initialized) {
        const char *diag = getenv("E2R_PRESENT_DIAG");
        diag_enabled = diag != NULL && diag[0] != '\0' && diag[0] != '0';
        diag_initialized = 1;
    }
    if (presented && diag_enabled) {
        unsigned long hires = (unsigned long)DAT_0047a43c;
        int changed = surface != diag_last_surface || hires != diag_last_hires;

        if (diag_count < 8u || changed) {
            e2r_trace_present_surfaces(surface, bytes);
            if (diag_count < 64u) {
                diag_count++;
            }
            diag_last_surface = surface;
            diag_last_hires = hires;
        }
    }
    if (presented) {
        static int auto_initialized;
        static int auto_done;
        static int auto_enabled;
        static uint64_t auto_start_ms;
        static uint64_t auto_delay_ms;
        static int auto_scene_slot = -1;
        static char auto_prefix[512];
        unsigned request_count = e2r_visibility_dump_requests;
        int should_dump = 0;
        char prefix[512];

        if (!auto_initialized) {
            const char *value = getenv("E2R_VISIBILITY_DUMP_PREFIX");
            const char *delay = getenv("E2R_VISIBILITY_DUMP_AFTER_MS");
            const char *scene_slot = getenv("E2R_VISIBILITY_DUMP_SCENE_SLOT");

            if (value != NULL && value[0] != '\0') {
                snprintf(auto_prefix, sizeof(auto_prefix), "%s", value);
                auto_enabled = 1;
            }
            if (delay != NULL && delay[0] != '\0') {
                auto_delay_ms = (uint64_t)strtoull(delay, NULL, 10);
            }
            if (scene_slot != NULL && scene_slot[0] != '\0') {
                auto_scene_slot = (int)strtol(scene_slot, NULL, 0);
            }
            auto_start_ms = now_ms;
            auto_initialized = 1;
        }
        if (request_count != 0) {
            static unsigned manual_dump_count;
            const char *manual_prefix = getenv("E2R_VISIBILITY_DUMP_PREFIX");

            e2r_visibility_dump_requests = request_count - 1;
            if (manual_prefix != NULL && manual_prefix[0] != '\0') {
                snprintf(prefix, sizeof(prefix), "%s", manual_prefix);
            }
            else {
                snprintf(prefix, sizeof(prefix), "/tmp/e2-visibility-%03u",
                         manual_dump_count++);
            }
            should_dump = 1;
        }
        else if (auto_enabled && !auto_done) {
            uint64_t elapsed_ms = 0;
            uintptr_t scene = _DAT_0073cc3c;
            int slot_match = 1;
            int startsc_done_match = 1;

            if (now_ms != 0 && auto_start_ms != 0 && now_ms >= auto_start_ms) {
                elapsed_ms = now_ms - auto_start_ms;
            }
            if (auto_scene_slot >= 0) {
                uintptr_t base = 0x0067c728u;
                uintptr_t end = base + (uintptr_t)0x4b0u * (uintptr_t)0x1cu;

                slot_match = scene >= base && scene < end &&
                    ((scene - base) % 0x1cu) == 0 &&
                    (int)((scene - base) / 0x1cu) == auto_scene_slot;
            }
            if (auto_scene_slot == 175) {
                uintptr_t action_actor;
                uintptr_t action_slot;
                uintptr_t action;
                unsigned action_duration;
                unsigned action_progress;
                unsigned action_slot_flags;
                unsigned action_actor_flags;

                e2r_read_current_action_state(&action_actor, &action_slot, &action,
                                              &action_duration, &action_progress,
                                              &action_slot_flags, &action_actor_flags);
                (void)action_actor;
                (void)action_slot;
                (void)action_duration;
                (void)action_progress;
                (void)action_slot_flags;
                (void)action_actor_flags;
                startsc_done_match = action != 0x9377e3u;
            }
            if (scene != 0 && elapsed_ms >= auto_delay_ms && slot_match &&
                startsc_done_match) {
                snprintf(prefix, sizeof(prefix), "%s", auto_prefix);
                should_dump = 1;
                auto_done = 1;
            }
        }
        if (should_dump) {
            e2r_write_visibility_packet(hwnd, prefix);
        }
    }
    return presented;
}

int E2R_TryPresentCurrentFrame(HWND hwnd)
{
    return e2r_present_current_frame(hwnd, 0);
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

    errno = 0;
    out = fopen(path, "wb");
    if (out == NULL) {
        fprintf(stderr, "surface dump fopen failed: %s errno=%d %s\n",
                path, errno, strerror(errno));
        return 0;
    }
    fprintf(out, "P5\n%u %u\n255\n", width, height);
    if (fwrite((const void *)framebuffer, 1, bytes, out) != bytes) {
        fprintf(stderr, "surface dump fwrite failed: %s errno=%d %s\n",
                path, errno, strerror(errno));
        fclose(out);
        return 0;
    }
    fclose(out);
    return 1;
}

static int e2r_write_surface_ppm(const char *path, unsigned surface)
{
    uintptr_t framebuffer;
    unsigned width = (unsigned)_DAT_006401ec;
    unsigned height = (unsigned)_DAT_006401d4;
    size_t bytes;
    FILE *out;
    unsigned y;

    if (!E2R_active_palette_valid ||
        width == 0 || height == 0 || width > 4096 || height > 4096) {
        return 0;
    }
    bytes = (size_t)width * (size_t)height;
    framebuffer = e2r_surface_framebuffer(surface);
    if (framebuffer == 0 || IsBadReadPtr((const void *)framebuffer, bytes)) {
        return 0;
    }

    out = fopen(path, "wb");
    if (out == NULL) {
        return 0;
    }
    fprintf(out, "P6\n%u %u\n255\n", width, height);
    for (y = 0; y < height; y++) {
        const unsigned char *src = (const unsigned char *)framebuffer + ((size_t)y * width);
        unsigned x;
        for (x = 0; x < width; x++) {
            uint32_t color = E2R_active_palette[src[x]];
            unsigned char rgb[3];
            rgb[0] = (unsigned char)((color >> 16) & 0xffu);
            rgb[1] = (unsigned char)((color >> 8) & 0xffu);
            rgb[2] = (unsigned char)(color & 0xffu);
            if (fwrite(rgb, 1, sizeof(rgb), out) != sizeof(rgb)) {
                fclose(out);
                return 0;
            }
        }
    }
    fclose(out);
    return 1;
}

static int e2r_write_surface_set(const char *prefix)
{
    unsigned surface;
    int wrote = 0;
    unsigned width = (unsigned)_DAT_006401ec;
    unsigned height = (unsigned)_DAT_006401d4;
    size_t bytes = 0;
    uintptr_t selected_framebuffer = 0;
    unsigned selected_surface = 0;
    int selected_valid = 0;

    if (width != 0 && height != 0 && width <= 4096 && height <= 4096) {
        bytes = (size_t)width * (size_t)height;
        selected_valid = e2r_select_framebuffer(&selected_framebuffer,
                                                &selected_surface, bytes);
    }

    fprintf(stderr,
            "surface dump state: width=%u height=%u front=%u selected=%u selected_fb=0x%lx "
            "selected_valid=%d visible=%u "
            "fb=[0x%lx,0x%lx,0x%lx,0x%lx] bad=[%d,%d,%d,%d] "
            "palette=%lu updates=%lu palette_nonzero=%u palette_hash=%08x\n",
            width, height, e2r_recovered_front_surface(),
            selected_surface, (unsigned long)selected_framebuffer, selected_valid,
            (unsigned)(DAT_0047a279 >> 24) & 3u,
            (unsigned long)_DAT_00636150, (unsigned long)_DAT_00636154,
            (unsigned long)_DAT_00636158, (unsigned long)_DAT_0063615c,
            bytes == 0 ? 1 : IsBadReadPtr((const void *)_DAT_00636150, bytes),
            bytes == 0 ? 1 : IsBadReadPtr((const void *)_DAT_00636154, bytes),
            bytes == 0 ? 1 : IsBadReadPtr((const void *)_DAT_00636158, bytes),
            bytes == 0 ? 1 : IsBadReadPtr((const void *)_DAT_0063615c, bytes),
            (unsigned long)E2R_active_palette_valid,
            (unsigned long)E2R_active_palette_update_count,
            e2r_palette_nonzero_count(), e2r_palette_hash());

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
            uintptr_t framebuffer = e2r_surface_framebuffer(surface);
            if (bytes != 0 && framebuffer != 0 &&
                !IsBadReadPtr((const void *)framebuffer, bytes)) {
                hash = e2r_frame_hash(framebuffer, bytes);
                nonblank = e2r_frame_has_pixels(framebuffer, bytes);
                fprintf(stderr,
                        "surface dump candidate: %s (surface %u nonblank=%d hash=%08x)\n",
                        path, surface, nonblank, hash);
            }
            fprintf(stderr, "failed to write surface dump: %s (surface %u)\n", path, surface);
        }
        snprintf(path, sizeof(path), "%s-s%u.ppm", prefix, surface);
        if (e2r_write_surface_ppm(path, surface)) {
            fprintf(stderr, "wrote color surface dump: %s (surface %u)\n", path, surface);
        }
    }
    return wrote;
}

static int e2r_current_scene_table_slot(uintptr_t scene)
{
    uintptr_t base = 0x0067c728u;
    uintptr_t end = base + (uintptr_t)0x4b0u * (uintptr_t)0x1cu;

    if (scene < base || scene >= end || ((scene - base) % 0x1cu) != 0) {
        return -1;
    }
    return (int)((scene - base) / 0x1cu);
}

static int e2r_read_short_field(uintptr_t ptr, short *value_out)
{
    if (ptr == 0 || IsBadReadPtr((const void *)ptr, sizeof(short))) {
        return 0;
    }
    *value_out = *(const short *)ptr;
    return 1;
}

static int e2r_read_u8_field(uintptr_t ptr, unsigned *value_out)
{
    if (ptr == 0 || IsBadReadPtr((const void *)ptr, sizeof(unsigned char))) {
        return 0;
    }
    *value_out = *(const unsigned char *)ptr;
    return 1;
}

static int e2r_read_u16_field(uintptr_t ptr, unsigned *value_out)
{
    if (ptr == 0 || IsBadReadPtr((const void *)ptr, sizeof(uint16_t))) {
        return 0;
    }
    *value_out = *(const uint16_t *)ptr;
    return 1;
}

static int e2r_read_u32_field(uintptr_t ptr, uintptr_t *value_out)
{
    if (ptr == 0 || IsBadReadPtr((const void *)ptr, sizeof(uint32_t))) {
        return 0;
    }
    *value_out = *(const uint32_t *)ptr;
    return 1;
}

static uintptr_t e2r_actor_table_entry(short actor_id)
{
    uintptr_t table_entry = 0x00630b60u + (uintptr_t)(uint16_t)actor_id * 4u;
    uintptr_t actor = 0;

    if (actor_id < 0 || actor_id >= 5000 ||
        IsBadReadPtr((const void *)table_entry, sizeof(uint32_t))) {
        return 0;
    }
    e2r_read_u32_field(table_entry, &actor);
    return actor;
}

static unsigned e2r_actor_table_flags(short actor_id)
{
    uintptr_t flags = 0x0064a178u + (uintptr_t)(uint16_t)actor_id * 2u;
    unsigned value = 0;

    if (actor_id < 0 || actor_id >= 5000) {
        return 0;
    }
    e2r_read_u16_field(flags, &value);
    return value;
}

static uintptr_t e2r_actor_asset_offset(short actor_id)
{
    uintptr_t offset_ptr = 0x00653840u + (uintptr_t)(uint16_t)actor_id * 4u;
    uintptr_t value = 0;

    if (actor_id < 0 || actor_id >= 5000) {
        return 0;
    }
    e2r_read_u32_field(offset_ptr, &value);
    return value;
}

static uintptr_t e2r_scene_asset_offset(short scene_id)
{
    uintptr_t offset_ptr = 0x00650fa0u + (uintptr_t)(uint16_t)scene_id * 4u;
    uintptr_t value = 0;

    if (scene_id < 0 || scene_id >= 0x9c4) {
        return 0;
    }
    e2r_read_u32_field(offset_ptr, &value);
    return value;
}

static uintptr_t e2r_rep_asset_offset(short rep_id)
{
    uintptr_t offset_ptr = 0x00663a10u + (uintptr_t)(uint16_t)rep_id * 4u;
    uintptr_t value = 0;

    if (rep_id < 0 || rep_id >= 500) {
        return 0;
    }
    e2r_read_u32_field(offset_ptr, &value);
    return value;
}

static uintptr_t e2r_scene_record_table_entry(int scene_slot)
{
    uintptr_t table_entry;
    uintptr_t scene_record = 0;

    if (scene_slot < 0 || scene_slot >= 0x4b0) {
        return 0;
    }
    table_entry = 0x0062e450u + (uintptr_t)scene_slot * 4u;
    e2r_read_u32_field(table_entry, &scene_record);
    return scene_record;
}

static int e2r_actor_on_global_list(uintptr_t actor)
{
    uintptr_t cursor = _DAT_0063726c;
    unsigned guard;

    if (actor == 0) {
        return 0;
    }
    for (guard = 0; cursor != 0 && guard < 256u; guard++) {
        uintptr_t next = 0;

        if (cursor == actor) {
            return 1;
        }
        if (IsBadReadPtr((const void *)cursor, 0x50)) {
            return 0;
        }
        e2r_read_u32_field(cursor + 0x4c, &next);
        if (next == cursor) {
            return 0;
        }
        cursor = next;
    }
    return 0;
}

static void e2r_write_actor_summary(FILE *out, const char *label, unsigned index, uintptr_t actor)
{
    short id = -1;
    unsigned flags2 = 0;
    unsigned flags3 = 0;
    unsigned state82 = 0;
    unsigned state91 = 0;
    unsigned action_duration = 0;
    unsigned action_progress = 0;
    unsigned action_flags = 0;
    short live_x = 0;
    short live_y = 0;
    short live_z = 0;
    short home_x = 0;
    short home_y = 0;
    short home_z = 0;
    short prev_x = 0;
    short prev_y = 0;
    short prev_z = 0;
    short attached_rep_id = -1;
    short render_rep_id = -1;
    short model_id = -1;
    uintptr_t table_actor = 0;
    uintptr_t next = 0;
    uintptr_t action_field = 0;
    uintptr_t scene_owner = 0;
    uintptr_t attached_rep = 0;
    uintptr_t render_rep = 0;
    uintptr_t model = 0;
    int readable;

    if (actor == 0) {
        fprintf(out, "%s[%u] actor=0x0 readable=0\n", label, index);
        return;
    }
    readable = !IsBadReadPtr((const void *)actor, 0x136);
    if (!readable) {
        fprintf(out, "%s[%u] actor=0x%lx readable=0\n",
                label, index, (unsigned long)actor);
        return;
    }

    e2r_read_short_field(actor, &id);
    table_actor = e2r_actor_table_entry(id);
    e2r_read_u8_field(actor + 2, &flags2);
    e2r_read_u8_field(actor + 3, &flags3);
    e2r_read_u16_field(actor + 0x82, &state82);
    e2r_read_u16_field(actor + 0x122, &state91);
    e2r_read_u32_field(actor + 0x4c, &next);
    e2r_read_u32_field(actor + 0xa6, &action_field);
    e2r_read_u16_field(actor + 0xaa, &action_duration);
    e2r_read_u16_field(actor + 0xac, &action_progress);
    e2r_read_u16_field(actor + 0xb2, &action_flags);
    e2r_read_u32_field(actor + 0x132, &scene_owner);
    e2r_read_short_field(actor + 0x84, &live_x);
    e2r_read_short_field(actor + 0x86, &live_y);
    e2r_read_short_field(actor + 0x88, &live_z);
    e2r_read_short_field(actor + 0x9c, &home_x);
    e2r_read_short_field(actor + 0x9e, &home_y);
    e2r_read_short_field(actor + 0xa0, &home_z);
    e2r_read_short_field(actor + 0xfc, &prev_x);
    e2r_read_short_field(actor + 0xfe, &prev_y);
    e2r_read_short_field(actor + 0x100, &prev_z);
    e2r_read_u32_field(actor + 0xf2, &attached_rep);
    if (attached_rep != 0 && !IsBadReadPtr((const void *)attached_rep, 0x26)) {
        e2r_read_short_field(attached_rep, &attached_rep_id);
    }
    e2r_read_u32_field(actor + 0x11e, &render_rep);
    if (render_rep != 0 && !IsBadReadPtr((const void *)render_rep, 0x26)) {
        e2r_read_short_field(render_rep, &render_rep_id);
        e2r_read_u32_field(render_rep + 0x22, &model);
        if (model != 0 && !IsBadReadPtr((const void *)model, sizeof(short))) {
            e2r_read_short_field(model, &model_id);
        }
    }

    fprintf(out,
            "%s[%u] actor=0x%lx readable=1 id=%d current=%d table=0x%lx "
            "table_match=%d table_flags=0x%04x asset_offset=0x%lx on_global=%d "
            "next=0x%lx flags2=0x%02x flags3=0x%02x visible_bit=%d state82=0x%04x "
            "state91=0x%04x scene_owner=0x%lx scene_match=%d action_field=0x%lx "
            "action_duration=%u action_progress=%u action_flags=0x%04x "
            "attached_rep=0x%lx attached_rep_id=%d render_rep=0x%lx "
            "render_rep_id=%d model=0x%lx model_id=%d live=%d,%d,%d "
            "home=%d,%d,%d prev=%d,%d,%d\n",
            label, index, (unsigned long)actor, (int)id,
            actor == DAT_0047a470, (unsigned long)table_actor,
            table_actor == actor, e2r_actor_table_flags(id),
            (unsigned long)e2r_actor_asset_offset(id),
            e2r_actor_on_global_list(actor), (unsigned long)next,
            flags2, flags3, (flags2 & 8u) != 0u, state82, state91,
            (unsigned long)scene_owner, scene_owner == _DAT_0073cc3c,
            (unsigned long)action_field, action_duration, action_progress,
            action_flags, (unsigned long)attached_rep, (int)attached_rep_id,
            (unsigned long)render_rep, (int)render_rep_id, (unsigned long)model,
            (int)model_id,
            (int)live_x, (int)live_y, (int)live_z,
            (int)home_x, (int)home_y, (int)home_z,
            (int)prev_x, (int)prev_y, (int)prev_z);
}

static void e2r_write_actor_list_state(FILE *out)
{
    uintptr_t actor = _DAT_0063726c;
    unsigned guard;

    fprintf(out,
            "actor_heads global=0x%lx head_7248=0x%lx head_7254=0x%lx head_7270=0x%lx\n",
            (unsigned long)_DAT_0063726c, (unsigned long)_DAT_00637248,
            (unsigned long)_DAT_00637254, (unsigned long)_DAT_00637270);
    for (guard = 0; actor != 0 && guard < 128u; guard++) {
        uintptr_t next = 0;

        e2r_write_actor_summary(out, "actor_list", guard, actor);
        if (IsBadReadPtr((const void *)actor, 0x50) ||
            !e2r_read_u32_field(actor + 0x4c, &next) || next == actor) {
            if (next == actor) {
                fprintf(out, "actor_list_cycle actor=0x%lx\n", (unsigned long)actor);
            }
            return;
        }
        actor = next;
    }
    if (actor != 0) {
        fprintf(out, "actor_list_truncated next=0x%lx limit=128\n", (unsigned long)actor);
    }
}

static void e2r_write_scene_child_state(FILE *out, uintptr_t scene)
{
    uintptr_t child = 0;
    uintptr_t active_next = 0;
    unsigned guard;

    if (scene == 0 || IsBadReadPtr((const void *)scene, 0xa0)) {
        fprintf(out, "scene_children scene=0x%lx readable=0\n", (unsigned long)scene);
        return;
    }
    e2r_read_u32_field(scene + 4, &child);
    e2r_read_u32_field(scene + 0x9c, &active_next);
    fprintf(out, "scene_children scene=0x%lx head=0x%lx active_next=0x%lx\n",
            (unsigned long)scene, (unsigned long)child, (unsigned long)active_next);

    for (guard = 0; child != 0 && guard < 128u; guard++) {
        short child_id = -1;
        short word2_id = -1;
        unsigned child_flags = 0;
        uintptr_t child_action = 0;
        uintptr_t next = 0;
        uintptr_t actor = 0;
        uintptr_t word2_actor = 0;

        if (IsBadReadPtr((const void *)child, 0x1c)) {
            fprintf(out, "scene_child[%u] child=0x%lx readable=0\n",
                    guard, (unsigned long)child);
            return;
        }
        e2r_read_short_field(child, &child_id);
        e2r_read_short_field(child + 4, &word2_id);
        e2r_read_u8_field(child + 0xe, &child_flags);
        e2r_read_u32_field(child + 6, &child_action);
        e2r_read_u32_field(child + 0x18, &next);
        actor = e2r_actor_table_entry(child_id);
        word2_actor = e2r_actor_table_entry(word2_id);

        fprintf(out,
                "scene_child[%u] child=0x%lx id=%d word2=%d flags=0x%02x hidden=%d "
                "action=0x%lx next=0x%lx actor=0x%lx actor_on_global=%d "
                "word2_actor=0x%lx table_flags=0x%04x actor_offset=0x%lx "
                "scene_offset=0x%lx rep_offset=0x%lx word2_actor_offset=0x%lx "
                "word2_scene_offset=0x%lx word2_rep_offset=0x%lx\n",
                guard, (unsigned long)child, (int)child_id, (int)word2_id,
                child_flags, (child_flags & 0x20u) != 0u,
                (unsigned long)child_action, (unsigned long)next,
                (unsigned long)actor, e2r_actor_on_global_list(actor),
                (unsigned long)word2_actor, e2r_actor_table_flags(child_id),
                (unsigned long)e2r_actor_asset_offset(child_id),
                (unsigned long)e2r_scene_asset_offset(child_id),
                (unsigned long)e2r_rep_asset_offset(child_id),
                (unsigned long)e2r_actor_asset_offset(word2_id),
                (unsigned long)e2r_scene_asset_offset(word2_id),
                (unsigned long)e2r_rep_asset_offset(word2_id));
        e2r_write_actor_summary(out, "scene_child_actor", guard, actor);
        if (next == child) {
            fprintf(out, "scene_child_cycle child=0x%lx\n", (unsigned long)child);
            return;
        }
        child = next;
    }
    if (child != 0) {
        fprintf(out, "scene_children_truncated next=0x%lx limit=128\n",
                (unsigned long)child);
    }
}

static void e2r_write_visibility_state(FILE *out, unsigned front_surface,
                                       unsigned selected_surface,
                                       uintptr_t selected_framebuffer,
                                       int selected_valid, int host_wrote)
{
    uintptr_t action_actor;
    uintptr_t action_slot;
    uintptr_t action;
    unsigned action_duration;
    unsigned action_progress;
    unsigned action_slot_flags;
    unsigned action_actor_flags;
    uintptr_t scene = _DAT_0073cc3c;
    int scene_slot = e2r_current_scene_table_slot(scene);
    short scene_id = -1;
    short actor_id = -1;
    unsigned width = (unsigned)_DAT_006401ec;
    unsigned height = (unsigned)_DAT_006401d4;
    size_t bytes = width != 0 && height != 0 ? (size_t)width * (size_t)height : 0;
    unsigned surface;

    e2r_read_current_action_state(&action_actor, &action_slot, &action,
                                  &action_duration, &action_progress,
                                  &action_slot_flags, &action_actor_flags);
    e2r_read_short_field(scene, &scene_id);
    e2r_read_short_field(DAT_0047a470, &actor_id);

    fprintf(out,
            "visibility_packet\n"
            "scene_ptr=0x%lx scene_slot=%d scene_id=%d view_selector=0x%lx\n"
            "current_actor=0x%lx current_actor_id=%d action_actor=0x%lx "
            "action_slot=0x%lx action_ptr=0x%lx action_duration=%u "
            "action_progress=%u action_slot_flags=0x%x action_actor_flags=0x%x\n"
            "width=%u height=%u front_surface=%u selected_surface=%u "
            "selected_framebuffer=0x%lx selected_valid=%d visible=%u hires=%lu "
            "palette_valid=%lu palette_updates=%lu palette_nonzero=%u "
            "palette_hash=%08x host_dumps=%d\n"
            "flags shift=%lu ctrl=%lu alt=%lu space=%lu q=%lu f1_4=%lu "
            "f5_8=%lu f9_12=%lu\n"
            "move=%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu\n",
            (unsigned long)scene, scene_slot, (int)scene_id,
            (unsigned long)_DAT_0073ccb8,
            (unsigned long)DAT_0047a470, (int)actor_id,
            (unsigned long)action_actor, (unsigned long)action_slot,
            (unsigned long)action, action_duration, action_progress,
            action_slot_flags, action_actor_flags,
            width, height, front_surface, selected_surface,
            (unsigned long)selected_framebuffer, selected_valid,
            (unsigned)(DAT_0047a279 >> 24) & 3u,
            (unsigned long)DAT_0047a43c,
            (unsigned long)E2R_active_palette_valid,
            (unsigned long)E2R_active_palette_update_count,
            e2r_palette_nonzero_count(), e2r_palette_hash(), host_wrote,
            (unsigned long)DAT_00636846,
            (unsigned long)DAT_00636852,
            (unsigned long)DAT_0063684a,
            (unsigned long)DAT_00636850,
            (unsigned long)DAT_00636853,
            (unsigned long)DAT_0063684d,
            (unsigned long)DAT_00636848,
            (unsigned long)DAT_0063684c,
            (unsigned long)DAT_00636859,
            (unsigned long)DAT_00636858, (unsigned long)DAT_0063685b,
            (unsigned long)DAT_00636854, (unsigned long)DAT_00636856,
            (unsigned long)DAT_00636857, (unsigned long)DAT_0063685c,
            (unsigned long)DAT_0063685a, (unsigned long)DAT_00636855);

    for (surface = 0; surface < 4u; surface++) {
        uintptr_t framebuffer = e2r_surface_framebuffer(surface);
        int readable = bytes != 0 && framebuffer != 0 &&
            !IsBadReadPtr((const void *)framebuffer, bytes);

        fprintf(out, "surface%u framebuffer=0x%lx readable=%d nonblank=%d hash=%08x\n",
                surface, (unsigned long)framebuffer, readable,
                readable ? e2r_frame_has_pixels(framebuffer, bytes) : 0,
                readable ? e2r_frame_hash(framebuffer, bytes) : 0u);
    }
    e2r_write_actor_list_state(out);
    fprintf(out, "scene_record_table slot=%d record=0x%lx\n",
            scene_slot, (unsigned long)e2r_scene_record_table_entry(scene_slot));
    e2r_write_scene_child_state(out, scene);
    e2r_write_scene_child_state(out, e2r_scene_record_table_entry(scene_slot));
}

static int e2r_write_visibility_packet(HWND hwnd, const char *prefix)
{
    char path[512];
    FILE *state;
    uintptr_t selected_framebuffer = 0;
    unsigned selected_surface = 0;
    unsigned width = (unsigned)_DAT_006401ec;
    unsigned height = (unsigned)_DAT_006401d4;
    size_t bytes = width != 0 && height != 0 ? (size_t)width * (size_t)height : 0;
    int selected_valid = 0;
    unsigned front_surface = e2r_recovered_front_surface();
    int surface_wrote;
    int host_wrote = 0;

    if (prefix == NULL || prefix[0] == '\0') {
        return 0;
    }
    if (bytes != 0 && width <= 4096u && height <= 4096u) {
        selected_valid = e2r_select_framebuffer(&selected_framebuffer,
                                                &selected_surface, bytes);
    }

    fprintf(stderr, "visibility packet begin: prefix=%s\n", prefix);
    surface_wrote = e2r_write_surface_set(prefix);
    if (hwnd != NULL && hwnd->ptr != NULL) {
        host_wrote = E2R_HostDumpPresentation((E2R_HostWindow *)hwnd->ptr, prefix);
    }
    else {
        fprintf(stderr, "visibility packet host dump skipped: no hwnd\n");
    }

    snprintf(path, sizeof(path), "%s-state.txt", prefix);
    state = fopen(path, "wb");
    if (state != NULL) {
        e2r_write_visibility_state(state, front_surface, selected_surface,
                                   selected_framebuffer, selected_valid, host_wrote);
        fclose(state);
        fprintf(stderr, "wrote visibility state: %s\n", path);
    }
    else {
        fprintf(stderr, "failed to write visibility state: %s errno=%d %s\n",
                path, errno, strerror(errno));
    }
    fprintf(stderr,
            "visibility packet end: prefix=%s game_surfaces=%d host_surfaces=%d "
            "front=%u selected=%u selected_valid=%d scene=0x%lx actor=0x%lx\n",
            prefix, surface_wrote, host_wrote, front_surface, selected_surface,
            selected_valid, (unsigned long)_DAT_0073cc3c,
            (unsigned long)DAT_0047a470);
    return surface_wrote > 0 || host_wrote > 0;
}

static unsigned e2r_wait_for_requester_ready(unsigned timeout_seconds)
{
    unsigned waited_ms = 0;
    unsigned timeout_ms = timeout_seconds * 1000u;

    while (waited_ms < timeout_ms) {
        if (DAT_0047a76c != 0 || DAT_00479de8 != 0 || _DAT_00643650 == 5) {
            fprintf(stderr,
                    "requester-ready wait satisfied after %u ms: DAT_0047a76c=%lu "
                    "DAT_00479de8=%lu _DAT_00643650=%lu\n",
                    waited_ms, (unsigned long)DAT_0047a76c,
                    (unsigned long)DAT_00479de8, (unsigned long)_DAT_00643650);
            return waited_ms;
        }
        usleep(10000);
        waited_ms += 10;
    }
    fprintf(stderr,
            "requester-ready wait timed out after %u ms: DAT_0047a76c=%lu "
            "DAT_00479de8=%lu _DAT_00643650=%lu\n",
            waited_ms, (unsigned long)DAT_0047a76c,
            (unsigned long)DAT_00479de8, (unsigned long)_DAT_00643650);
    return waited_ms;
}

static unsigned e2r_wait_for_requester_dialog(unsigned timeout_seconds)
{
    unsigned waited_ms = 0;
    unsigned timeout_ms = timeout_seconds * 1000u;
    uintptr_t initial_b9bc_count = E2R_requester_probe_b9bc_count;

    while (waited_ms < timeout_ms) {
        if (_DAT_00643650 == 5 && E2R_requester_probe_b9bc_count != initial_b9bc_count) {
            fprintf(stderr,
                    "requester-dialog wait satisfied after %u ms: _DAT_00643650=%lu "
                    "b9bc %lu->%lu bd4c=%lu\n",
                    waited_ms, (unsigned long)_DAT_00643650,
                    (unsigned long)initial_b9bc_count,
                    (unsigned long)E2R_requester_probe_b9bc_count,
                    (unsigned long)E2R_requester_probe_bd4c_count);
            return waited_ms;
        }
        usleep(10000);
        waited_ms += 10;
    }
    fprintf(stderr,
            "requester-dialog wait timed out after %u ms: _DAT_00643650=%lu "
            "b9bc %lu->%lu bd4c=%lu\n",
            waited_ms, (unsigned long)_DAT_00643650,
            (unsigned long)initial_b9bc_count,
            (unsigned long)E2R_requester_probe_b9bc_count,
            (unsigned long)E2R_requester_probe_bd4c_count);
    return waited_ms;
}

static unsigned e2r_wait_for_gameplay_frame(unsigned timeout_seconds, int require_control_ready)
{
    unsigned waited_ms = 0;
    unsigned timeout_ms = timeout_seconds * 1000u;
    unsigned next_report_ms = 5000u;
    const char *label = require_control_ready ? "gameplay-control" : "gameplay-frame";

    while (waited_ms < timeout_ms) {
        if (E2R_start_game_probe_count != 0 && DAT_00479de8 != 0 && _DAT_0073cc3c != 0 &&
            (!require_control_ready || _DAT_00643650 == 0)) {
            fprintf(stderr,
                    "%s wait satisfied after %u ms: start_game=%lu "
                    "DAT_00479de8=%lu DAT_0047a76c=%lu _DAT_00643650=%lu "
                    "_DAT_0073cc3c=0x%lx\n",
                    label, waited_ms, (unsigned long)E2R_start_game_probe_count,
                    (unsigned long)DAT_00479de8, (unsigned long)DAT_0047a76c,
                    (unsigned long)_DAT_00643650, (unsigned long)_DAT_0073cc3c);
            return waited_ms;
        }
        usleep(10000);
        waited_ms += 10;
        if (waited_ms >= next_report_ms) {
            fprintf(stderr,
                    "%s wait progress after %u ms: start_game=%lu "
                    "DAT_00479de8=%lu DAT_0047a76c=%lu _DAT_00643650=%lu "
                    "_DAT_0073cc3c=0x%lx actions=%lu dispatch=%lu "
                    "opcodes=%lu last_opcode=0x%lx hit75=%lu "
                    "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu]\n",
                    label, waited_ms, (unsigned long)E2R_start_game_probe_count,
                    (unsigned long)DAT_00479de8, (unsigned long)DAT_0047a76c,
                    (unsigned long)_DAT_00643650, (unsigned long)_DAT_0073cc3c,
                    (unsigned long)E2R_requester_probe_action_count,
                    (unsigned long)E2R_start_code_probe_dispatches,
                    (unsigned long)E2R_action_opcode_count,
                    (unsigned long)E2R_action_last_opcode,
                    (unsigned long)E2R_action_hit_75_count,
                    (unsigned long)DAT_00636859, (unsigned long)DAT_00636858,
                    (unsigned long)DAT_0063685b, (unsigned long)DAT_00636854,
                    (unsigned long)DAT_00636856, (unsigned long)DAT_00636857,
                    (unsigned long)DAT_0063685c, (unsigned long)DAT_0063685a,
                    (unsigned long)DAT_00636855);
            fflush(stderr);
            next_report_ms += 5000u;
        }
    }
    fprintf(stderr,
            "%s wait timed out after %u ms: start_game=%lu "
            "DAT_00479de8=%lu DAT_0047a76c=%lu _DAT_00643650=%lu "
            "_DAT_0073cc3c=0x%lx\n",
            label, waited_ms, (unsigned long)E2R_start_game_probe_count,
            (unsigned long)DAT_00479de8, (unsigned long)DAT_0047a76c,
            (unsigned long)_DAT_00643650, (unsigned long)_DAT_0073cc3c);
    return waited_ms;
}

static void e2r_inject_sequence_key(E2R_FrameDumpRequest *request, unsigned key_index,
                                    unsigned phase_first_key_index,
                                    unsigned *remaining_delay)
{
    uintptr_t action_count_before_key = E2R_requester_probe_action_count;
    uintptr_t start_game_count_before_key = E2R_start_game_probe_count;
    uintptr_t keydown_count_before = E2R_input_probe_keydown_count;
    unsigned group = request->inject_key_groups[key_index];
    unsigned group_end = key_index + 1;
    unsigned key_cursor;
    MSG msg;
    unsigned dispatch_count = 0;
    unsigned dispatched_target_keys = 0;

    while (group_end < request->inject_key_count &&
           request->inject_key_groups[group_end] == group) {
        group_end++;
    }
    if (key_index != phase_first_key_index) {
        usleep(request->inject_interval_ms * 1000u);
    }
    if (request->wait_for_requester_ready && key_index > 0) {
        for (key_cursor = key_index; key_cursor < group_end; key_cursor++) {
            unsigned inject_key = request->inject_keys[key_cursor];
            E2R_RequesterProbeQueueKey(inject_key);
            fprintf(stderr,
                    "queued requester probe key 0x%02x for bd4c dispatch (%lu/%lu fed=%lu)\n",
                    inject_key,
                    (unsigned long)E2R_requester_probe_pending_key_read,
                    (unsigned long)E2R_requester_probe_pending_key_count,
                    (unsigned long)E2R_requester_probe_fed_key_count);
        }
    }
    else {
        for (key_cursor = key_index; key_cursor < group_end; key_cursor++) {
            unsigned inject_key = request->inject_keys[key_cursor];
            if (PostMessageA((HWND)_DAT_00ac4dac, WM_KEYDOWN, inject_key, 0)) {
                fprintf(stderr,
                        "posted key 0x%02x through the Win32 message queue group=%u\n",
                        inject_key, group);
            }
            else {
                fprintf(stderr,
                        "failed to post key 0x%02x through the Win32 message queue group=%u\n",
                        inject_key, group);
            }
        }
    }
    if (!request->wait_for_requester_ready || key_index == 0) {
        while (dispatch_count < 16 && PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE)) {
            if (msg.message == WM_QUIT) {
                break;
            }
            TranslateMessage(&msg);
            DispatchMessageA(&msg);
            dispatch_count++;
            if (msg.message == WM_KEYDOWN) {
                for (key_cursor = key_index; key_cursor < group_end; key_cursor++) {
                    if ((unsigned)msg.wParam == request->inject_keys[key_cursor]) {
                        dispatched_target_keys++;
                        break;
                    }
                }
                if (dispatched_target_keys == group_end - key_index) {
                    break;
                }
            }
        }
        if (dispatch_count != 0) {
            fprintf(stderr,
                    "dispatched %u queued probe message(s), target_keys_seen=%u/%u\n",
                    dispatch_count, dispatched_target_keys, group_end - key_index);
        }
        else {
            fprintf(stderr, "no queued probe message available for dispatch\n");
        }
    }
    usleep(100000);
    fprintf(stderr,
            "input state after dispatch wait: keydowns %lu->%lu last_key=0x%02lx "
            "last_char_queue=0x%02lx last_scan_queue=0x%02lx "
            "DAT_00636844=%lu DAT_00636853=%lu DAT_00479de8=%lu "
            "flags=[shift=%lu ctrl=%lu alt=%lu space=%lu q=%lu f1_4=%lu f5_8=%lu] "
            "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu] "
            "DAT_0047a76c=%lu DAT_0047a43c=%lu _DAT_0073cc3c=0x%lx\n",
            (unsigned long)keydown_count_before,
            (unsigned long)E2R_input_probe_keydown_count,
            (unsigned long)E2R_input_probe_last_key,
            (unsigned long)E2R_input_probe_last_char_queue,
            (unsigned long)E2R_input_probe_last_scan_queue,
            (unsigned long)DAT_00636844, (unsigned long)DAT_00636853,
            (unsigned long)DAT_00479de8,
            (unsigned long)DAT_00636846, (unsigned long)DAT_00636852,
            (unsigned long)DAT_0063684a, (unsigned long)DAT_00636850,
            (unsigned long)DAT_00636853, (unsigned long)DAT_0063684d,
            (unsigned long)DAT_00636848,
            (unsigned long)DAT_00636859,
            (unsigned long)DAT_00636858, (unsigned long)DAT_0063685b,
            (unsigned long)DAT_00636854, (unsigned long)DAT_00636856,
            (unsigned long)DAT_00636857, (unsigned long)DAT_0063685c,
            (unsigned long)DAT_0063685a, (unsigned long)DAT_00636855,
            (unsigned long)DAT_0047a76c, (unsigned long)DAT_0047a43c,
            (unsigned long)_DAT_0073cc3c);
    fflush(stderr);
    if (request->wait_for_requester_ready && key_index == 0 &&
        request->inject_key_count > 1) {
        e2r_wait_for_requester_dialog(request->inject_delay_seconds);
    }
    if (request->wait_for_requester_ready) {
        unsigned waited_ms = 0;
        while (waited_ms < 1000 &&
               E2R_requester_probe_action_count == action_count_before_key &&
               E2R_requester_probe_pending_key_read != E2R_requester_probe_pending_key_count) {
            usleep(10000);
            waited_ms += 10;
        }
        if (E2R_requester_probe_action_count != action_count_before_key ||
            E2R_requester_probe_pending_key_read == E2R_requester_probe_pending_key_count) {
            fprintf(stderr,
                    "requester probe completed after %u ms: pending=%lu/%lu actions=%lu\n",
                    waited_ms,
                    (unsigned long)E2R_requester_probe_pending_key_read,
                    (unsigned long)E2R_requester_probe_pending_key_count,
                    (unsigned long)E2R_requester_probe_action_count);
        }
        if ((E2R_requester_probe_last_action == (uintptr_t)&LAB_0043d458 ||
             E2R_requester_probe_last_action == (uintptr_t)&LAB_0043d464) &&
            E2R_start_game_probe_count == start_game_count_before_key) {
            waited_ms = 0;
            while (waited_ms < 2000 &&
                   E2R_start_game_probe_count == start_game_count_before_key) {
                usleep(10000);
                waited_ms += 10;
            }
            fprintf(stderr,
                    "start-game probe wait finished after %u ms: entries %lu->%lu "
                    "player=%lu mode=%lu\n",
                    waited_ms, (unsigned long)start_game_count_before_key,
                    (unsigned long)E2R_start_game_probe_count,
                    (unsigned long)E2R_start_game_probe_last_player,
                    (unsigned long)E2R_start_game_probe_last_mode);
        }
        if ((E2R_requester_probe_last_action == (uintptr_t)&LAB_0043d458 ||
             E2R_requester_probe_last_action == (uintptr_t)&LAB_0043d464) &&
            E2R_start_game_probe_count != start_game_count_before_key) {
            fprintf(stderr,
                    "start-game entry observed: entries %lu->%lu player=%lu mode=%lu; "
                    "waiting %u second(s) before dump\n",
                    (unsigned long)start_game_count_before_key,
                    (unsigned long)E2R_start_game_probe_count,
                    (unsigned long)E2R_start_game_probe_last_player,
                    (unsigned long)E2R_start_game_probe_last_mode,
                    request->post_action_delay_seconds);
            *remaining_delay = request->post_action_delay_seconds;
        }
        else {
            *remaining_delay = 0;
        }
    }
}

static LPARAM e2r_pack_mouse_point(unsigned x, unsigned y)
{
    return (LPARAM)((x & 0xffffu) | ((y & 0xffffu) << 16));
}

static void e2r_inject_mouse_click(E2R_FrameDumpRequest *request, unsigned click_index)
{
    unsigned mouse_x = request->mouse_click_x[click_index];
    unsigned mouse_y = request->mouse_click_y[click_index];
    LPARAM point = e2r_pack_mouse_point(mouse_x, mouse_y);
    uintptr_t action_count_before = E2R_requester_probe_action_count;
    unsigned waited_ms;

    PostMessageA((HWND)_DAT_00ac4dac, WM_MOUSEMOVE, 0, point);
    PostMessageA((HWND)_DAT_00ac4dac, WM_LBUTTONDOWN, 0, point);
    PostMessageA((HWND)_DAT_00ac4dac, WM_LBUTTONUP, 0, point);
    fprintf(stderr, "posted mouse click %u/%u through Win32 queue at %u,%u\n",
            click_index + 1, request->mouse_click_count, mouse_x, mouse_y);

    waited_ms = 0;
    while (waited_ms < 2000 &&
           E2R_requester_probe_action_count == action_count_before) {
        usleep(10000);
        waited_ms += 10;
    }
    fprintf(stderr,
            "mouse click probe wait finished after %u ms: actions %lu->%lu "
            "last_action=0x%lx selected=0x%lx state=%lu requester=0x%lx\n",
            waited_ms, (unsigned long)action_count_before,
            (unsigned long)E2R_requester_probe_action_count,
            (unsigned long)E2R_requester_probe_last_action,
            (unsigned long)E2R_requester_probe_selected_item,
            (unsigned long)_DAT_00643650,
            (unsigned long)E2R_requester_probe_last_id);
}

static void e2r_inject_mouse_click_sequence(E2R_FrameDumpRequest *request,
                                            unsigned *remaining_delay)
{
    unsigned i;

    for (i = 0; i < request->mouse_click_count; i++) {
        e2r_inject_mouse_click(request, i);
        if (i + 1 < request->mouse_click_count) {
            usleep(request->mouse_click_interval_ms * 1000u);
        }
    }
    *remaining_delay = request->post_action_delay_seconds;
}

static void *e2r_frame_dump_thread(void *arg)
{
    E2R_FrameDumpRequest *request = (E2R_FrameDumpRequest *)arg;
    unsigned surface = 0;
    unsigned remaining_delay = request->delay_seconds;

    if (request->inject_key_count != 0 && request->inject_delay_seconds < remaining_delay) {
        unsigned key_index;
        unsigned pre_gameplay_key_count = request->inject_key_count;
        if (request->wait_for_requester_ready) {
            unsigned waited_ms = e2r_wait_for_requester_ready(request->inject_delay_seconds);
            unsigned waited_seconds = (waited_ms + 999u) / 1000u;
            if (waited_seconds < remaining_delay) {
                remaining_delay -= waited_seconds;
            }
            else {
                remaining_delay = 1;
            }
        }
        else {
            sleep(request->inject_delay_seconds);
            remaining_delay -= request->inject_delay_seconds;
        }

        if (request->wait_for_gameplay_frame &&
            request->gameplay_key_split < pre_gameplay_key_count) {
            pre_gameplay_key_count = request->gameplay_key_split;
        }
        for (key_index = 0; key_index < pre_gameplay_key_count; key_index++) {
            e2r_inject_sequence_key(request, key_index, 0, &remaining_delay);
            while (key_index + 1 < pre_gameplay_key_count &&
                   request->inject_key_groups[key_index + 1] ==
                       request->inject_key_groups[key_index]) {
                key_index++;
            }
        }
        if (request->wait_for_gameplay_frame && pre_gameplay_key_count < request->inject_key_count) {
            if (remaining_delay != 0) {
                unsigned waited_ms = e2r_wait_for_gameplay_frame(remaining_delay, 1);
                unsigned waited_seconds = (waited_ms + 999u) / 1000u;
                if (waited_seconds < remaining_delay) {
                    remaining_delay -= waited_seconds;
                }
                else {
                    remaining_delay = 1;
                }
            }
            for (key_index = pre_gameplay_key_count;
                 key_index < request->inject_key_count;
                 key_index++) {
                e2r_inject_sequence_key(request, key_index, pre_gameplay_key_count,
                                        &remaining_delay);
                while (key_index + 1 < request->inject_key_count &&
                       request->inject_key_groups[key_index + 1] ==
                           request->inject_key_groups[key_index]) {
                    key_index++;
                }
            }
        }
    }
    if (request->inject_mouse_click) {
        e2r_wait_for_requester_dialog(request->inject_delay_seconds);
        e2r_inject_mouse_click_sequence(request, &remaining_delay);
    }
    if (request->wait_for_gameplay_frame && remaining_delay != 0) {
        e2r_wait_for_gameplay_frame(remaining_delay, 0);
    }
    else if (remaining_delay != 0) {
        sleep(remaining_delay);
    }
    if (request->dump_all_surfaces) {
        int wrote = e2r_write_surface_set(request->path);
        if (wrote > 0) {
            uintptr_t action_actor;
            uintptr_t action_slot;
            uintptr_t action;
            unsigned action_duration;
            unsigned action_progress;
            unsigned action_slot_flags;
            unsigned action_actor_flags;

            e2r_read_current_action_state(&action_actor, &action_slot, &action,
                                          &action_duration, &action_progress,
                                          &action_slot_flags, &action_actor_flags);
            fprintf(stderr, "wrote %d surface dump(s) with prefix: %s\n", wrote, request->path);
            fprintf(stderr,
                    "input state: DAT_00636844=%lu DAT_00636850=%lu DAT_00636853=%lu "
                    "_DAT_00479e78=%lu _DAT_00479e7a=%lu DAT_00479dfc=%lu "
                    "DAT_00479e00=%lu _DAT_00643650=%lu "
                    "DAT_00479de8=%lu DAT_0047a76c=%lu DAT_0047a43c=%lu "
                    "DAT_0047a730=%lu DAT_00479de4=%lu DAT_0047a788=%lu "
                    "_DAT_00636690=%lu _DAT_00637378=%lu _DAT_0063737c=%lu "
                    "_DAT_0073cc3c=0x%lx "
                    "requester=[ce58=%lu id=0x%lx mode=%lu b384=%lu bad=%lu ptr=0x%lx "
                    "b9bc=%lu item=0x%lx bd4c=%lu key=0x%lx seen=%lu none=%lu cursor=%lu "
                    "param=0x%lx selected=0x%lx next=0x%lx selected_action=0x%lx "
                    "moves=%lu move_key=0x%lx move_from=0x%lx move_to=0x%lx "
                    "pending=%lu/%lu fed=%lu fed_key=0x%lx fed_char=0x%lx fed_scan=0x%lx "
                    "actions=%lu last_action=0x%lx] "
                    "start_game=[entries=%lu player=%lu mode=%lu "
                    "startup_scan=%lu startup_match=%lu action_scan=%lu action_match=%lu "
                    "dispatch=%lu node=0x%lx name=%lu code=0x%lx "
                    "opcodes=%lu last_opcode=0x%lx last_cursor=0x%lx hit75=%lu] "
                    "action=[actor=0x%lx slot=0x%lx ptr=0x%lx duration=%u progress=%u "
                    "slot_flags=0x%x actor_flags=0x%x] "
                    "settings=[music=%lu sfx=%lu difficulty=%lu resolution=%lu "
                    "requested_resolution=%lu install=%lu] "
                    "flags=[shift=%lu ctrl=%lu alt=%lu space=%lu q=%lu f1_4=%lu f5_8=%lu f9_12=%lu] "
                    "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu]\n",
                    (unsigned long)DAT_00636844, (unsigned long)DAT_00636850,
                    (unsigned long)DAT_00636853,
                    (unsigned long)_DAT_00479e78, (unsigned long)_DAT_00479e7a,
                    (unsigned long)DAT_00479dfc, (unsigned long)DAT_00479e00,
                    (unsigned long)_DAT_00643650, (unsigned long)DAT_00479de8,
                    (unsigned long)DAT_0047a76c, (unsigned long)DAT_0047a43c,
                    (unsigned long)DAT_0047a730, (unsigned long)DAT_00479de4,
                    (unsigned long)DAT_0047a788, (unsigned long)_DAT_00636690,
                    (unsigned long)_DAT_00637378, (unsigned long)_DAT_0063737c,
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
                    (unsigned long)E2R_requester_probe_bd4c_seen_key_count,
                    (unsigned long)E2R_requester_probe_bd4c_no_key_count,
                    (unsigned long)E2R_requester_probe_bd4c_last_cursor,
                    (unsigned long)E2R_requester_probe_bd4c_param_item,
                    (unsigned long)E2R_requester_probe_selected_item,
                    (unsigned long)E2R_requester_probe_selected_next,
                    (unsigned long)E2R_requester_probe_selected_action,
                    (unsigned long)E2R_requester_probe_move_count,
                    (unsigned long)E2R_requester_probe_move_key,
                    (unsigned long)E2R_requester_probe_move_from,
                    (unsigned long)E2R_requester_probe_move_to,
                    (unsigned long)E2R_requester_probe_pending_key_read,
                    (unsigned long)E2R_requester_probe_pending_key_count,
                    (unsigned long)E2R_requester_probe_fed_key_count,
                    (unsigned long)E2R_requester_probe_last_fed_key,
                    (unsigned long)E2R_requester_probe_last_fed_char,
                    (unsigned long)E2R_requester_probe_last_fed_scan,
                    (unsigned long)E2R_requester_probe_action_count,
                    (unsigned long)E2R_requester_probe_last_action,
                    (unsigned long)E2R_start_game_probe_count,
                    (unsigned long)E2R_start_game_probe_last_player,
                    (unsigned long)E2R_start_game_probe_last_mode,
                    (unsigned long)E2R_start_code_probe_startup_scans,
                    (unsigned long)E2R_start_code_probe_startup_matches,
                    (unsigned long)E2R_start_code_probe_action_scans,
                    (unsigned long)E2R_start_code_probe_action_matches,
                    (unsigned long)E2R_start_code_probe_dispatches,
                    (unsigned long)E2R_start_code_probe_last_node,
                    (unsigned long)E2R_start_code_probe_last_name_index,
                    (unsigned long)E2R_start_code_probe_last_bytecode_offset,
                    (unsigned long)E2R_action_opcode_count,
                    (unsigned long)E2R_action_last_opcode,
                    (unsigned long)E2R_action_last_cursor,
                    (unsigned long)E2R_action_hit_75_count,
                    (unsigned long)action_actor,
                    (unsigned long)action_slot,
                    (unsigned long)action,
                    action_duration,
                    action_progress,
                    action_slot_flags,
                    action_actor_flags,
                    (unsigned long)DAT_0047a49c,
                    (unsigned long)DAT_0047a4a0,
                    (unsigned long)DAT_0047a4a4,
                    (unsigned long)DAT_0047a43c,
                    (unsigned long)DAT_0047a440,
                    (unsigned long)DAT_00479dbc,
                    (unsigned long)DAT_00636846,
                    (unsigned long)DAT_00636852,
                    (unsigned long)DAT_0063684a,
                    (unsigned long)DAT_00636850,
                    (unsigned long)DAT_00636853,
                    (unsigned long)DAT_0063684d,
                    (unsigned long)DAT_00636848,
                    (unsigned long)DAT_0063684c,
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
                "_DAT_00636690=%lu _DAT_00637378=%lu _DAT_0063737c=%lu "
                "_DAT_0073cc3c=0x%lx "
                "move=[%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu]\n",
                (unsigned long)DAT_00636844, (unsigned long)DAT_00636853,
                (unsigned long)_DAT_00643650, (unsigned long)DAT_00479de8,
                (unsigned long)DAT_0047a76c, (unsigned long)DAT_0047a43c,
                (unsigned long)DAT_0047a730, (unsigned long)DAT_00479de4,
                (unsigned long)DAT_0047a788, (unsigned long)_DAT_00636690,
                (unsigned long)_DAT_00637378, (unsigned long)_DAT_0063737c,
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
    e2r_frame_dump_request.inject_key_groups[0] = 0;
    e2r_frame_dump_request.inject_key_count = inject_key != 0 ? 1 : 0;
    e2r_frame_dump_request.inject_interval_ms = 250;
    e2r_frame_dump_request.gameplay_key_split = e2r_frame_dump_request.inject_key_count;
    e2r_frame_dump_request.post_action_delay_seconds = 0;
    e2r_frame_dump_request.mouse_click_x[0] = 0;
    e2r_frame_dump_request.mouse_click_y[0] = 0;
    e2r_frame_dump_request.mouse_click_count = 0;
    e2r_frame_dump_request.mouse_click_interval_ms = 250;
    e2r_frame_dump_request.inject_mouse_click = 0;
    e2r_frame_dump_request.wait_for_requester_ready = 0;
    e2r_frame_dump_request.wait_for_gameplay_frame = 0;
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
    if (strcmp(name, "up") == 0 || strcmp(name, "arrowup") == 0) {
        return VK_UP;
    }
    if (strcmp(name, "down") == 0 || strcmp(name, "arrowdown") == 0) {
        return VK_DOWN;
    }
    if (strcmp(name, "left") == 0 || strcmp(name, "arrowleft") == 0) {
        return VK_LEFT;
    }
    if (strcmp(name, "right") == 0 || strcmp(name, "arrowright") == 0) {
        return VK_RIGHT;
    }
    if (strcmp(name, "shift") == 0 || strcmp(name, "lshift") == 0 ||
        strcmp(name, "rshift") == 0) {
        return VK_SHIFT;
    }
    if (strcmp(name, "alt") == 0 || strcmp(name, "lalt") == 0 ||
        strcmp(name, "leftalt") == 0 || strcmp(name, "menu") == 0) {
        return VK_MENU;
    }
    if (strcmp(name, "ralt") == 0 || strcmp(name, "rightalt") == 0) {
        return VK_RMENU;
    }
    if (strcmp(name, "q") == 0) {
        return VK_Q;
    }
    if (strcmp(name, "ctrl") == 0 || strcmp(name, "control") == 0) {
        return VK_CONTROL;
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
    if (strcmp(name, "i") == 0) {
        return VK_I;
    }
    if (strcmp(name, "m") == 0) {
        return 0x4d;
    }
    if (strcmp(name, "p") == 0) {
        return 0x50;
    }
    if (strcmp(name, "l") == 0) {
        return VK_L;
    }
    if (strcmp(name, "s") == 0) {
        return VK_S;
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

static unsigned e2r_parse_virtual_key_sequence(const char *value, unsigned *keys,
                                               unsigned *groups, unsigned max_keys)
{
    char buffer[256];
    char *token_start;
    char *cursor;
    unsigned group = 0;
    unsigned count = 0;

    snprintf(buffer, sizeof(buffer), "%s", value);
    token_start = buffer;
    cursor = buffer;
    while (1) {
        char delimiter = *cursor;
        if (delimiter != ',' && delimiter != '+' && delimiter != '\0') {
            cursor++;
            continue;
        }
        *cursor = '\0';
        if (*token_start != '\0') {
            unsigned key;
            if (count >= max_keys) {
                break;
            }
            key = e2r_parse_virtual_key(token_start);
            if (key == 0) {
                return 0;
            }
            keys[count] = key;
            groups[count] = group;
            count++;
        }
        if (delimiter == '\0') {
            break;
        }
        if (delimiter == ',') {
            group++;
        }
        token_start = cursor + 1;
        cursor++;
    }
    if (count != 0) {
        return count;
    }
    return 0;
}

static unsigned e2r_parse_virtual_key_sequence_legacy(const char *value, unsigned *keys,
                                                      unsigned max_keys)
{
    unsigned groups[16];
    return e2r_parse_virtual_key_sequence(value, keys, groups, max_keys);
}

static int e2r_start_key_sequence_dump(const char *path, unsigned delay_seconds,
                                       unsigned inject_delay_seconds, const unsigned *keys,
                                       const unsigned *groups, unsigned key_count,
                                       unsigned interval_ms,
                                       int dump_all_surfaces, int wait_for_requester_ready,
                                       unsigned post_action_delay_seconds,
                                       int wait_for_gameplay_frame, unsigned gameplay_key_split)
{
    pthread_t thread;
    unsigned i;

    e2r_frame_dump_request.path = path;
    e2r_frame_dump_request.delay_seconds = delay_seconds == 0 ? 5 : delay_seconds;
    e2r_frame_dump_request.inject_delay_seconds = inject_delay_seconds;
    e2r_frame_dump_request.inject_key = key_count != 0 ? keys[0] : 0;
    e2r_frame_dump_request.inject_key_count = key_count;
    e2r_frame_dump_request.inject_interval_ms = interval_ms == 0 ? 250 : interval_ms;
    e2r_frame_dump_request.gameplay_key_split =
        gameplay_key_split <= key_count ? gameplay_key_split : key_count;
    e2r_frame_dump_request.post_action_delay_seconds = post_action_delay_seconds;
    e2r_frame_dump_request.mouse_click_x[0] = 0;
    e2r_frame_dump_request.mouse_click_y[0] = 0;
    e2r_frame_dump_request.mouse_click_count = 0;
    e2r_frame_dump_request.mouse_click_interval_ms = 250;
    e2r_frame_dump_request.inject_mouse_click = 0;
    e2r_frame_dump_request.wait_for_requester_ready = wait_for_requester_ready;
    e2r_frame_dump_request.wait_for_gameplay_frame = wait_for_gameplay_frame;
    e2r_frame_dump_request.dump_all_surfaces = dump_all_surfaces;
    for (i = 0; i < key_count && i < 16; i++) {
        e2r_frame_dump_request.inject_keys[i] = keys[i];
        e2r_frame_dump_request.inject_key_groups[i] = groups != NULL ? groups[i] : i;
    }
    if (pthread_create(&thread, NULL, e2r_frame_dump_thread, &e2r_frame_dump_request) != 0) {
        fprintf(stderr, "failed to start key sequence dump thread\n");
        return 0;
    }
    pthread_detach(thread);
    return 1;
}

static unsigned e2r_parse_mouse_click_sequence(const char *value, unsigned *xs,
                                               unsigned *ys, unsigned max_clicks)
{
    char buffer[256];
    char *token;
    unsigned count = 0;

    snprintf(buffer, sizeof(buffer), "%s", value);
    token = strtok(buffer, ";");
    while (token != NULL && count < max_clicks) {
        char *separator = strchr(token, ',');
        if (separator == NULL) {
            separator = strchr(token, ':');
        }
        if (separator == NULL) {
            return 0;
        }
        *separator = '\0';
        xs[count] = (unsigned)strtoul(token, NULL, 10);
        ys[count] = (unsigned)strtoul(separator + 1, NULL, 10);
        count++;
        token = strtok(NULL, ";");
    }
    return count;
}

static int e2r_start_intro_menu_click_dump(const char *path, unsigned delay_seconds,
                                           unsigned inject_delay_seconds,
                                           unsigned mouse_x, unsigned mouse_y,
                                           unsigned post_click_delay_seconds)
{
    unsigned key = VK_ESCAPE;

    if (!e2r_start_key_sequence_dump(path, delay_seconds, inject_delay_seconds, &key, NULL, 1,
                                     250, 1, 0, post_click_delay_seconds, 0, 1)) {
        return 0;
    }
    e2r_frame_dump_request.mouse_click_x[0] = mouse_x;
    e2r_frame_dump_request.mouse_click_y[0] = mouse_y;
    e2r_frame_dump_request.mouse_click_count = 1;
    e2r_frame_dump_request.mouse_click_interval_ms = 250;
    e2r_frame_dump_request.inject_mouse_click = 1;
    return 1;
}

static int e2r_start_intro_menu_click_sequence_dump(const char *path,
                                                    unsigned delay_seconds,
                                                    unsigned inject_delay_seconds,
                                                    const unsigned *mouse_x,
                                                    const unsigned *mouse_y,
                                                    unsigned mouse_count,
                                                    unsigned click_interval_ms,
                                                    unsigned target_requester_id,
                                                    unsigned post_click_delay_seconds)
{
    unsigned key = VK_ESCAPE;
    unsigned i;

    if (mouse_count == 0 || mouse_count > E2R_MAX_MOUSE_CLICKS) {
        return 0;
    }
    if (!e2r_start_key_sequence_dump(path, delay_seconds, inject_delay_seconds, &key, NULL, 1,
                                     250, 1, 0, post_click_delay_seconds, 0, 1)) {
        return 0;
    }
    for (i = 0; i < mouse_count; i++) {
        e2r_frame_dump_request.mouse_click_x[i] = mouse_x[i];
        e2r_frame_dump_request.mouse_click_y[i] = mouse_y[i];
    }
    if (target_requester_id != 0) {
        for (i = 1; i < mouse_count; i++) {
            E2R_RequesterProbeQueueMouseClick(target_requester_id, mouse_x[i], mouse_y[i]);
        }
        E2R_RequesterProbeQueueTargetKey(target_requester_id, VK_ESCAPE);
        e2r_frame_dump_request.mouse_click_count = 1;
    }
    else {
        e2r_frame_dump_request.mouse_click_count = mouse_count;
    }
    e2r_frame_dump_request.mouse_click_interval_ms =
        click_interval_ms == 0 ? 250 : click_interval_ms;
    e2r_frame_dump_request.inject_mouse_click = 1;
    return 1;
}
#else
int E2R_TryPresentCurrentFrame(HWND hwnd)
{
    (void)hwnd;
    return 0;
}
#endif

static int e2r_run_host_backend_key_probe(void)
{
    WNDCLASSA wnd_class;
    HWND hwnd;
    MSG msg;
    unsigned poll;
    uintptr_t keydowns_before;

    memset(&wnd_class, 0, sizeof(wnd_class));
    wnd_class.lpfnWndProc = E2R_WndProc;
    wnd_class.lpszClassName = "E2RProbe";
    RegisterClassA(&wnd_class);
    hwnd = E2R_CreateWindowExA(0, "E2RProbe", "Ecstatica II backend key probe",
                               0, 0, 0, 64, 64, NULL, NULL, NULL, NULL);
    if (hwnd == NULL || hwnd->ptr == NULL) {
        fprintf(stderr, "host backend key probe failed: window unavailable\n");
        return 1;
    }
    keydowns_before = E2R_input_probe_keydown_count;
    if (!E2R_HostPushSyntheticKeyDown((E2R_HostWindow *)hwnd->ptr, VK_SPACE)) {
        fprintf(stderr, "host backend key probe failed: synthetic key unsupported\n");
        return 2;
    }
    for (poll = 0; poll < 8; poll++) {
        if (PeekMessageA(&msg, NULL, 0, 0, PM_REMOVE)) {
            fprintf(stderr, "host backend key probe message: msg=0x%04x wParam=0x%02lx\n",
                    msg.message, (unsigned long)msg.wParam);
            if (msg.message == WM_KEYDOWN && msg.wParam == VK_SPACE) {
                fprintf(stderr, "host backend key probe passed\n");
                return 0;
            }
        }
        if (E2R_input_probe_keydown_count != keydowns_before &&
            E2R_input_probe_last_key == VK_SPACE) {
            fprintf(stderr, "host backend key probe passed via direct dispatch\n");
            return 0;
        }
        Sleep(1);
    }
    fprintf(stderr, "host backend key probe failed: no WM_KEYDOWN for VK_SPACE\n");
    return 3;
}

static int e2r_run_host_backend_present_probe(void)
{
    enum { E2R_PROBE_WIDTH = 64, E2R_PROBE_HEIGHT = 64 };
    unsigned char pixels[E2R_PROBE_WIDTH * E2R_PROBE_HEIGHT];
    HWND hwnd;
    unsigned x;
    unsigned y;
    unsigned hash = 2166136261u;

    for (y = 0; y < E2R_PROBE_HEIGHT; y++) {
        for (x = 0; x < E2R_PROBE_WIDTH; x++) {
            pixels[(y * E2R_PROBE_WIDTH) + x] =
                (unsigned char)(((x * 3u) + (y * 5u)) & 0xffu);
            hash ^= pixels[(y * E2R_PROBE_WIDTH) + x];
            hash *= 16777619u;
        }
    }

    hwnd = E2R_CreateWindowExA(0, "E2RProbe", "Ecstatica II backend present probe",
                               0, 0, 0, 128, 128, NULL, NULL, NULL, NULL);
    if (hwnd == NULL || hwnd->ptr == NULL) {
        fprintf(stderr, "host backend presentation probe failed: window unavailable\n");
        return 1;
    }
    if (!E2R_HostPresentIndexed8((E2R_HostWindow *)hwnd->ptr, pixels,
                                 E2R_PROBE_WIDTH, E2R_PROBE_HEIGHT,
                                 E2R_PROBE_WIDTH, NULL)) {
        fprintf(stderr, "host backend presentation probe failed: present rejected\n");
        return 2;
    }
    fprintf(stderr,
            "host backend presentation probe passed: width=%u height=%u hash=%08x\n",
            (unsigned)E2R_PROBE_WIDTH, (unsigned)E2R_PROBE_HEIGHT, hash);
    return 0;
}

int main(int argc, char **argv)
{
    fprintf(stderr, "Ecstatica II data: %s\n", E2RECOMP_DATA_DIR);
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

    if (argc > 1 && strcmp(argv[1], "--host-backend-key-probe") == 0) {
        return e2r_run_host_backend_key_probe();
    }

    if (argc > 1 && strcmp(argv[1], "--host-backend-present-probe") == 0) {
        return e2r_run_host_backend_present_probe();
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
        unsigned groups[16];
        unsigned key_count = e2r_parse_virtual_key_sequence(argv[3], keys, groups, 16);
        unsigned inject_delay_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 2;
        unsigned interval_ms = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 250;
        unsigned delay_seconds = argc > 6 ? (unsigned)strtoul(argv[6], NULL, 10) : 6;
        if (key_count == 0) {
            fprintf(stderr, "unknown key sequence for --inject-key-sequence-surfaces: %s\n", argv[3]);
            return 3;
        }
        if (!e2r_start_key_sequence_dump(argv[2], delay_seconds, inject_delay_seconds, keys,
                                         groups,
                                         key_count, interval_ms, 1, 0, 0, 0, key_count)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 3 && strcmp(argv[1], "--inject-key-sequence-gameplay-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-key-sequence-gameplay-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned keys[16];
        unsigned groups[16];
        unsigned key_count = e2r_parse_virtual_key_sequence(argv[3], keys, groups, 16);
        unsigned inject_delay_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 2;
        unsigned interval_ms = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 250;
        unsigned timeout_seconds = argc > 6 ? (unsigned)strtoul(argv[6], NULL, 10) : 120;
        unsigned gameplay_key_split = argc > 7 ? (unsigned)strtoul(argv[7], NULL, 10) : 16;
        if (key_count == 0) {
            fprintf(stderr, "unknown key sequence for --inject-key-sequence-gameplay-surfaces: %s\n", argv[3]);
            return 3;
        }
        if (!e2r_start_key_sequence_dump(argv[2], timeout_seconds, inject_delay_seconds, keys,
                                         groups,
                                         key_count, interval_ms, 1, 0, 0, 1, gameplay_key_split)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 3 && strcmp(argv[1], "--inject-key-sequence-ready-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-key-sequence-ready-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned keys[16];
        unsigned groups[16];
        unsigned key_count = e2r_parse_virtual_key_sequence(argv[3], keys, groups, 16);
        unsigned ready_timeout_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 6;
        unsigned interval_ms = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 250;
        unsigned dump_seconds = argc > 6 ? (unsigned)strtoul(argv[6], NULL, 10) : 5;
        unsigned total_seconds = ready_timeout_seconds + dump_seconds + 1;
        if (key_count == 0) {
            fprintf(stderr, "unknown key sequence for --inject-key-sequence-ready-surfaces: %s\n", argv[3]);
            return 3;
        }
        if (!e2r_start_key_sequence_dump(argv[2], total_seconds, ready_timeout_seconds, keys,
                                         groups,
                                         key_count, interval_ms, 1, 1, dump_seconds, 0, key_count)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 4 && strcmp(argv[1], "--inject-intro-menu-click-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-intro-menu-click-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned mouse_x = (unsigned)strtoul(argv[3], NULL, 10);
        unsigned mouse_y = (unsigned)strtoul(argv[4], NULL, 10);
        unsigned inject_delay_seconds = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 6;
        unsigned post_click_delay_seconds = argc > 6 ? (unsigned)strtoul(argv[6], NULL, 10) : 4;
        unsigned total_seconds = inject_delay_seconds + post_click_delay_seconds + 8;
        if (!e2r_start_intro_menu_click_dump(argv[2], total_seconds, inject_delay_seconds,
                                             mouse_x, mouse_y,
                                             post_click_delay_seconds)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    if (argc > 3 && strcmp(argv[1], "--inject-intro-menu-click-sequence-surfaces") == 0) {
#if UINTPTR_MAX > UINT32_MAX
        fprintf(stderr,
                "--inject-intro-menu-click-sequence-surfaces needs a 32-bit build. Use the linux-clang32-debug CMake preset.\n");
        return 2;
#else
        unsigned mouse_x[E2R_MAX_MOUSE_CLICKS];
        unsigned mouse_y[E2R_MAX_MOUSE_CLICKS];
        unsigned mouse_count =
            e2r_parse_mouse_click_sequence(argv[3], mouse_x, mouse_y, E2R_MAX_MOUSE_CLICKS);
        unsigned inject_delay_seconds = argc > 4 ? (unsigned)strtoul(argv[4], NULL, 10) : 6;
        unsigned post_click_delay_seconds = argc > 5 ? (unsigned)strtoul(argv[5], NULL, 10) : 4;
        unsigned click_interval_ms = argc > 6 ? (unsigned)strtoul(argv[6], NULL, 10) : 250;
        unsigned target_requester_id = argc > 7 ? (unsigned)strtoul(argv[7], NULL, 0) : 0;
        unsigned total_seconds = inject_delay_seconds + post_click_delay_seconds +
                                 ((mouse_count + 1u) * ((click_interval_ms + 999u) / 1000u)) + 8;
        if (mouse_count == 0) {
            fprintf(stderr,
                    "unknown mouse click sequence for --inject-intro-menu-click-sequence-surfaces: %s\n",
                    argv[3]);
            return 3;
        }
        if (!e2r_start_intro_menu_click_sequence_dump(argv[2], total_seconds,
                                                      inject_delay_seconds,
                                                      mouse_x, mouse_y,
                                                      mouse_count, click_interval_ms,
                                                      target_requester_id,
                                                      post_click_delay_seconds)) {
            return 3;
        }
        fflush(stdout);
        E2R_WinMainThunk();
        return 0;
#endif
    }

    puts("Linux scaffold initialized. Pass --run-recon to enter the reconstructed game startup thunk.");
    puts("Pass --host-backend-key-probe to verify backend key events reach WM_KEYDOWN.");
    puts("Pass --host-backend-present-probe to verify backend indexed-8 presentation.");
    puts("Pass --dump-frame <path.pgm> [seconds] to write a bounded framebuffer inspection dump.");
    puts("Pass --dump-surfaces <prefix> [seconds] to write all four bounded framebuffer dumps.");
    puts("Pass --inject-key-dump <path.pgm> <key|vk> [inject_seconds] [dump_seconds] to probe input.");
    puts("Pass --inject-key-surfaces <prefix> <key|vk> [inject_seconds] [dump_seconds] to probe input surfaces.");
    puts("Pass --inject-key-sequence-surfaces <prefix> <key[,key...]> [inject_seconds] [interval_ms] [dump_seconds] to probe input sequences.");
    puts("Pass --inject-key-sequence-gameplay-surfaces <prefix> <key[,key...]> [inject_seconds] [interval_ms] [gameplay_timeout_seconds] [gameplay_key_split] to wait for gameplay before injecting later keys.");
    puts("Pass --inject-key-sequence-ready-surfaces <prefix> <key[,key...]> [ready_timeout_seconds] [interval_ms] [dump_seconds] to inject when requester-ready state appears.");
    puts("Pass --inject-intro-menu-click-surfaces <prefix> <x> <y> [esc_seconds] [post_click_seconds] to open the intro menu and click a game-coordinate point.");
    puts("Pass --inject-intro-menu-click-sequence-surfaces <prefix> <x,y[;x,y...]> [esc_seconds] [post_click_seconds] [click_interval_ms] [target_requester_id] to open the intro menu, click game-coordinate points, and queue Esc for the target requester.");
    puts("Press F12 in the SDL window to write a visibility packet; set E2R_VISIBILITY_DUMP_PREFIX to choose its prefix.");
    puts("Set E2R_VISIBILITY_DUMP_PREFIX plus optional E2R_VISIBILITY_DUMP_AFTER_MS and E2R_VISIBILITY_DUMP_SCENE_SLOT to auto-write one visibility packet.");
    return 0;
}
