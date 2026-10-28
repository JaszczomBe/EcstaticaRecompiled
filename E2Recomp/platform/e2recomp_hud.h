#pragma once

#include <stddef.h>

/* Original visual state, observed without advancing scripts or timers. */
typedef struct E2R_HudState {
    int visible, high, life, maximum_life, poison_limit, armour, magic;
    int hand_present, held_present, held_rod, capacity, held_magic, charge;
} E2R_HudState;

typedef struct E2R_HudPainter {
    void *context;
    void (*graphic)(void *context, const char *name, int x, int y, int centered);
    void (*line)(void *context, int page, int x0, int y0, int x1, int y1, int color);
} E2R_HudPainter;

void E2R_GetOriginalHudState(E2R_HudState *state);
void E2R_DrawOriginalHudState(const E2R_HudState *state, const E2R_HudPainter *painter);

typedef struct E2R_InventoryState {
    int items[15];
    int timer, timer_total, power, kills, gold, progress;
} E2R_InventoryState;

typedef struct E2R_InventoryPainter {
    void *context;
    void (*graphic)(void *context, const char *name, int x, int y);
    void (*masked_pixel)(void *context, int x, int y, int color);
} E2R_InventoryPainter;

void E2R_GetInventoryState(E2R_InventoryState *state);
void E2R_DrawInventoryState(const E2R_InventoryState *state, const E2R_InventoryPainter *painter);
int E2R_BeginInventoryPage(void);
void E2R_EndInventoryPage(void);
int E2R_InventoryPageActive(void);

/* Process-local presentation policy. Both key edges are consumed by the host. */
int E2R_DebugOverlaySelected(void);
enum { E2R_GEOMETRY_ORIGINAL, E2R_GEOMETRY_MIXED, E2R_GEOMETRY_BOXES };
int E2R_GeometryMode(void);
int E2R_HandleDisplayKey(unsigned message, unsigned key);
const unsigned char *E2R_ComposeOriginalHud(const unsigned char *pixels,
                                         unsigned width, unsigned height, unsigned pitch);
