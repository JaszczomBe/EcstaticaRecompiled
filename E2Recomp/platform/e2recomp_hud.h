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

/* Process-local presentation policy. Both key edges are consumed by the host. */
int E2R_DebugOverlaySelected(void);
int E2R_HandleDisplayKey(unsigned message, unsigned key);
const unsigned char *E2R_ComposeOriginalHud(const unsigned char *pixels,
                                         unsigned width, unsigned height, unsigned pitch);
