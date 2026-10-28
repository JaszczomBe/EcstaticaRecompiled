#pragma once

#include "e2recomp_win32_compat.h"

typedef struct E2R_HostWindow E2R_HostWindow;
typedef void (*E2R_HostMessageCallback)(UINT msg, WPARAM wparam, LPARAM lparam,
                                        void *user);

E2R_HostWindow *E2R_HostCreateWindow(const char *title, int x, int y,
                                     unsigned width, unsigned height);
void E2R_HostDestroyWindow(E2R_HostWindow *window);
void E2R_HostShowWindow(E2R_HostWindow *window);
void E2R_HostPollEvents(E2R_HostWindow *window,
                        E2R_HostMessageCallback message_callback,
                        void *user);
int E2R_HostPushSyntheticKeyDown(E2R_HostWindow *window, UINT vk);
int E2R_HostPresentIndexed8(E2R_HostWindow *window, const unsigned char *pixels,
                            unsigned width, unsigned height, unsigned pitch,
                            const uint32_t *palette_rgb);
int E2R_HostDumpPresentation(E2R_HostWindow *window, const char *prefix);
#ifdef E2R_HOST_BACKEND_SDL
int E2R_HostDumpInspectionFrame(E2R_HostWindow *window, const char *prefix);
#else
static inline int E2R_HostDumpInspectionFrame(E2R_HostWindow *window, const char *prefix)
{ (void)window; (void)prefix; return -1; }
#endif

int E2R_IsCharacterActor(uintptr_t actor);
int E2R_IsObjectMeshActor(uintptr_t actor);

/* Read-only runtime snapshot for optional host-side actor diagnostics. */
#define E2R_ACTOR_CUE_CAPACITY 64
#define E2R_CYLINDER_RING_POINTS 8
enum E2R_ActorMarker {
    E2R_MARKER_OBJECT, E2R_MARKER_PLAYER, E2R_MARKER_CREATURE, E2R_MARKER_CORPSE,
    E2R_MARKER_DOOR, E2R_MARKER_DEBRIS, E2R_MARKER_POTION, E2R_MARKER_WEAPON, E2R_MARKER_ITEM
};
enum E2R_PotionStatus {
    E2R_POTION_NONE, E2R_POTION_PENDING, E2R_POTION_ACTIVE, E2R_POTION_FADING
};
typedef struct E2R_ActorCue {
    int id, x, y, z, is_joe, camera_z;
    /* Presentation categories: generated actors use original table bit 0x08;
     * objects have no active representation or owning script scene.
     * These runtime categories do not imply hostility or asset type. */
    int is_object, generated, visible_in_view, original_object_mesh;
    int marker_kind, health, actor_state;
    int poison_status, invisibility_status, healing;
    char name[48];
    /* Ground centre, upright tip and four ground-cross endpoints.
     * Q4 screen coordinates converted to pixels; depth zero means clipped. */
    int screen[6][3];
    /* Projected marker vertices; Joe retains the original diagnostic rings.
     * Other kinds use bottles, blades, boxes or diamonds. Zero depth clips. */
    int cylinder[E2R_CYLINDER_RING_POINTS * 2][3];
    int local_z_tip[3];
    int rotation_y;
    uint32_t action;
    unsigned action_duration, action_progress;
} E2R_ActorCue;
typedef struct E2R_ActorCueSnapshot {
    int scene_slot, origin_x, origin_z;
    int camera_ready, view_width, view_height;
    unsigned script_wait, requester_id, requester_state;
    int background_spawns_deferred;
    unsigned count;
    E2R_ActorCue actors[E2R_ACTOR_CUE_CAPACITY];
} E2R_ActorCueSnapshot;
void E2R_GetActorCues(E2R_ActorCueSnapshot *snapshot);
int E2R_GetDirectDrawPixels(uintptr_t object, const unsigned char **pixels,
                          unsigned *width, unsigned *height, unsigned *pitch);
