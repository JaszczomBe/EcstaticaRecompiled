#include "e2recomp_hud.h"
#include "e2recomp_win32_compat.h"

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int e2r_debug_overlay;
static int e2r_geometry_mode;
static int e2r_geometry_key_down;
static unsigned char *e2r_hud_pixels;
static size_t e2r_hud_capacity;

int E2R_DebugOverlaySelected(void)
{
    return e2r_debug_overlay;
}

int E2R_GeometryMode(void)
{
    return e2r_geometry_mode;
}

int E2R_HandleDisplayKey(unsigned message, unsigned key)
{
    if ((message != WM_KEYDOWN && message != WM_KEYUP) || (key < 0x70 || key > 0x72))
        return 0;
    if (key == 0x72) {
        if (message == WM_KEYDOWN && !e2r_geometry_key_down)
            e2r_geometry_mode = (e2r_geometry_mode + 1) % 3;
        e2r_geometry_key_down = message == WM_KEYDOWN;
        return 1;
    }
    if (message == WM_KEYDOWN) e2r_debug_overlay = key == 0x71;
    return 1;
}

typedef struct E2R_HudGraphic {
    char name[9];
    int high, width, height;
    unsigned char *pixels;
} E2R_HudGraphic;

/* 3 life frames, 2 armour frames, 3 hand icons, 5 capacity frames,
 * 18 magic icons and one magic meter, in both original resolutions. */
static E2R_HudGraphic e2r_hud_graphics[64];
static unsigned e2r_hud_graphic_count;

static const E2R_HudGraphic *e2r_hud_load(const char *name, int high)
{
    E2R_HudGraphic *graphic;
    unsigned char header[32];
    char path[64];
    DWORD read;
    HANDLE file;
    size_t bytes;

    for (unsigned i = 0; i < e2r_hud_graphic_count; ++i)
        if (e2r_hud_graphics[i].high == high && !strcmp(e2r_hud_graphics[i].name, name))
            return &e2r_hud_graphics[i];
    if (e2r_hud_graphic_count == sizeof(e2r_hud_graphics) / sizeof(e2r_hud_graphics[0]) ||
        strlen(name) > 8) return NULL;
    graphic = &e2r_hud_graphics[e2r_hud_graphic_count++];
    strcpy(graphic->name, name);
    graphic->high = high;
    snprintf(path, sizeof(path), "%s/%s.raw", high ? "graphics" : "lowgraph", name);
    file = CreateFileA(path, 0x80000000u, 3, NULL, 3, 0x80, NULL);
    if (file == INVALID_HANDLE_VALUE) goto failed;
    /* 0x44a206..0x44a274: 32-byte header, 768-byte palette, BE dimensions,
     * followed by width*height row-major indexed pixels. The game palette owns
     * the colours; the per-file palette is skipped, as in the original loader. */
    if (!ReadFile(file, header, sizeof(header), &read, NULL) || read != sizeof(header) ||
        memcmp(header, "mhwanh", 6)) goto close_failed;
    graphic->width = (header[8] << 8) | header[9];
    graphic->height = (header[10] << 8) | header[11];
    if (graphic->width <= 0 || graphic->height <= 0 ||
        graphic->width > 640 || graphic->height > 480) goto close_failed;
    bytes = (size_t)graphic->width * graphic->height;
    graphic->pixels = malloc(bytes);
    if (!graphic->pixels || SetFilePointer(file, 800, NULL, 0) != 800 ||
        !ReadFile(file, graphic->pixels, bytes, &read, NULL) || read != bytes) {
        free(graphic->pixels);
        graphic->pixels = NULL;
        goto close_failed;
    }
    CloseHandle(file);
    return graphic;
close_failed:
    CloseHandle(file);
failed:
    fprintf(stderr, "original HUD: cannot load %s\n", path);
    return graphic;
}

typedef struct E2R_HudTarget {
    unsigned char *pixels;
    unsigned width, height, pitch;
    int high;
} E2R_HudTarget;

static void e2r_hud_graphic(void *context, const char *name, int x, int y, int centered)
{
    E2R_HudTarget *target = context;
    const E2R_HudGraphic *graphic = e2r_hud_load(name, target->high);
    if (!graphic || !graphic->pixels) return;
    /* 0x45577c..0x45580f: only centered script graphics scale coordinates.
     * HUD callers pass ECX=0 and already use resolution-specific positions. */
    if (centered) {
        x = (target->high ? x * 2 : x) - graphic->width / 2;
        y = (target->high ? (y * 6 / 5) * 2 : y) - graphic->height / 2;
    }
    for (int row = 0; row < graphic->height; ++row) {
        if (y + row < 0 || (unsigned)(y + row) >= target->height) continue;
        for (int column = 0; column < graphic->width; ++column) {
            unsigned char value = graphic->pixels[row * graphic->width + column];
            /* 0x455668..0x455682 normalizes 0 and 1 to transparent 255. */
            if (value > 1 && value != 255 && x + column >= 0 &&
                (unsigned)(x + column) < target->width)
                target->pixels[(y + row) * target->pitch + x + column] = value;
        }
    }
}

static void e2r_hud_line(void *context, int page, int x0, int y0, int x1, int y1, int color)
{
    E2R_HudTarget *target = context;
    int left, right;
    /* The original updates physical pages 0/1 and the HUD background page 2.
     * A fresh presentation copy needs just one of these identical draws. */
    if (page != 0 || y0 != y1 || y0 < 0 || (unsigned)y0 >= target->height || x0 == x1) return;
    /* The recovered HUD emits horizontal segments only. Original
     * 0x41b63b..0x41b6c8 excludes the final endpoint, even when reversed. */
    left = x0 < x1 ? x0 : x1 + 1;
    right = x0 < x1 ? x1 : x0 + 1;
    if (left < 0) left = 0;
    if (right > (int)target->width) right = (int)target->width;
    if (left < right)
        memset(target->pixels + y0 * target->pitch + left, color, (size_t)(right - left));
}

const unsigned char *E2R_ComposeOriginalHud(const unsigned char *pixels,
                                         unsigned width, unsigned height, unsigned pitch)
{
    E2R_HudState state;
    E2R_GetOriginalHudState(&state);
    if (e2r_debug_overlay || !state.visible || !pixels || !width || !height ||
        width > 4096 || height > 4096 || pitch < width) return pixels;
    size_t bytes = (size_t)pitch * height;
    if (bytes > e2r_hud_capacity) {
        unsigned char *replacement = realloc(e2r_hud_pixels, bytes);
        if (!replacement) return pixels;
        e2r_hud_pixels = replacement;
        e2r_hud_capacity = bytes;
    }
    memcpy(e2r_hud_pixels, pixels, bytes);
    E2R_HudTarget target = {e2r_hud_pixels, width, height, pitch, state.high};
    E2R_HudPainter painter = {&target, e2r_hud_graphic, e2r_hud_line};
    E2R_DrawOriginalHudState(&state, &painter);
    return e2r_hud_pixels;
}
