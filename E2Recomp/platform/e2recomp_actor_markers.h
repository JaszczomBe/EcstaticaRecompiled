#ifndef E2RECOMP_ACTOR_MARKERS_H
#define E2RECOMP_ACTOR_MARKERS_H

#include "e2recomp_host_backend.h"
#include <string.h>

/* Host presentation only. Dimensions are illustrative, never collision bounds. */
static inline int e2r_marker_contains(const char *name, const char *part)
{
    char lower[48];
    unsigned i;
    for (i = 0; name[i] && i + 1 < sizeof(lower); ++i)
        lower[i] = name[i] >= 'A' && name[i] <= 'Z' ? name[i] + 'a' - 'A' : name[i];
    lower[i] = 0;
    return strstr(lower, part) != NULL;
}

static inline int e2r_marker_kind(const char *name, const char *rep,
                                   unsigned flags, int generated, int previous)
{
    if (e2r_marker_contains(rep, "door")) return E2R_MARKER_DOOR;
    if (strcmp(rep, "potion") == 0) return E2R_MARKER_POTION;
    if (e2r_marker_contains(rep, "sword") || e2r_marker_contains(name, "schwrt") ||
        e2r_marker_contains(name, "sword") || e2r_marker_contains(name, "korax"))
        return E2R_MARKER_WEAPON;
    if (strcmp(rep, "coins") == 0 || strcmp(rep, "trophy") == 0 ||
        (flags & 4u)) return E2R_MARKER_ITEM;
    if (rep[0] == 0 && previous != E2R_MARKER_OBJECT) return previous;
    if (generated || (flags & 0x1000u)) return E2R_MARKER_CREATURE;
    return E2R_MARKER_OBJECT;
}

static inline const char *e2r_marker_label(int kind)
{
    switch (kind) {
    case E2R_MARKER_PLAYER: return "JOE";
    case E2R_MARKER_CREATURE: return "CREATURE";
    case E2R_MARKER_CORPSE: return "CORPSE";
    case E2R_MARKER_DOOR: return "DOOR";
    case E2R_MARKER_DEBRIS: return "BROKEN DOOR";
    case E2R_MARKER_POTION: return "POTION";
    case E2R_MARKER_WEAPON: return "WEAPON";
    case E2R_MARKER_ITEM: return "ITEM";
    default: return "PROP";
    }
}

static inline void e2r_marker_offset(int kind, int point, short offset[3])
{
    static const short ring[8][2] = {
        {256,0},{181,181},{0,256},{-181,181},
        {-256,0},{-181,-181},{0,-256},{181,-181}
    };
    static const short corners[4][2] = {{-1,-1},{1,-1},{1,1},{-1,1}};
    int q = point & 3, level = point / 4;
    offset[0] = offset[1] = offset[2] = 0;
    if (kind == E2R_MARKER_PLAYER) {
        offset[0] = ring[point & 7][0];
        offset[1] = point < 8 ? 0 : -1024;
        offset[2] = ring[point & 7][1];
    } else if (kind == E2R_MARKER_POTION) {
        int radius = level < 2 ? 64 : 24;
        static const short heights[4] = {0,-112,-144,-208};
        offset[0] = corners[q][0] * radius;
        offset[1] = heights[level];
        offset[2] = corners[q][1] * radius;
    } else if (kind == E2R_MARKER_WEAPON) {
        static const short blade[8][3] = {
            {-20,0,0},{20,0,0},{0,0,560},{0,-20,32},
            {-112,0,48},{112,0,48},{0,0,-112},{0,20,32}
        };
        memcpy(offset, blade[point & 7], sizeof(short) * 3);
    } else if (kind == E2R_MARKER_ITEM || kind == E2R_MARKER_CORPSE) {
        static const short diamond[6][3] = {
            {-1,0,0},{0,0,1},{1,0,0},{0,0,-1},{0,-1,0},{0,1,0}
        };
        int radius = kind == E2R_MARKER_CORPSE ? 320 : 88;
        int height = kind == E2R_MARKER_CORPSE ? 40 : 88;
        const short *p = diamond[point % 6];
        offset[0] = p[0] * radius;
        offset[1] = p[1] * height - height;
        offset[2] = p[2] * (kind == E2R_MARKER_CORPSE ? 180 : radius);
    } else {
        /* Original door leaves are broad along model Z, thin along X. */
        int width = kind == E2R_MARKER_DOOR ? 40 : kind == E2R_MARKER_DEBRIS ? 320 : 160;
        int depth = kind == E2R_MARKER_DOOR ? 320 : kind == E2R_MARKER_DEBRIS ? 40 : 160;
        int height = kind == E2R_MARKER_DOOR ? 1024 :
                     kind == E2R_MARKER_DEBRIS ? 48 :
                     kind == E2R_MARKER_CREATURE ? 896 : 320;
        if (kind == E2R_MARKER_CREATURE) width = point < 4 ? 112 : 208;
        offset[0] = corners[q][0] * width;
        offset[1] = (point & 7) < 4 ? 0 : -height;
        offset[2] = corners[q][1] * depth;
    }
}
#endif
