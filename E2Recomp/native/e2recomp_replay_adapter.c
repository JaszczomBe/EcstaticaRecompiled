/* Pure observation at the compatibility pump boundary. No reconstructed calls,
 * projection, state repair, allocation, or clock reads. */
#include "E2Recomp_recon.h"
#include "EcstaticaReplay.h"
#include "EcstaticaInspect.h"
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#if defined(__has_feature)
#if __has_feature(address_sanitizer)
#include <sanitizer/asan_interface.h>
#define E2R_INSPECTION_ASAN 1
#endif
#endif
extern uint E2R_rand_seed_fallback;
static int64_t read_s16(uintptr_t p) {
  int16_t v;
  memcpy(&v, (const void *)p, 2);
  return v;
}
static uint32_t read_u32(uintptr_t p) {
  uint32_t v;
  memcpy(&v, (const void *)p, 4);
  return v;
}
static int resource(uintptr_t p) {
  return p && p >= 0x10000 && !IsBadReadPtr((void *)p, 2) ? (int)read_s16(p)
                                                          : -1;
}
static void sample_fields(void (*field)(const char *, int, const char *, int64_t)) {
#if UINTPTR_MAX <= UINT32_MAX
#define GLOBAL(name) field("world", 0, #name, (int64_t)name)
  GLOBAL(_DAT_00636588);
  GLOBAL(_DAT_00637378);
  GLOBAL(DAT_0047a76c);
  GLOBAL(_DAT_00643650);
  GLOBAL(DAT_0047a45e);
  GLOBAL(DAT_0047a450);
  GLOBAL(DAT_0047b7f0);
  GLOBAL(DAT_0047ab20);
  GLOBAL(_DAT_00479e78);
  GLOBAL(DAT_0047a788);
  GLOBAL(DAT_0047a34a);
  field("world", 0, "current_actor_id", resource(DAT_0047a470));
  field("rng", 0, "provider_context_present", _DAT_00ac5204 != 0);
  if (!_DAT_00ac5204)
    field("rng", 0, "fallback_seed", E2R_rand_seed_fallback);
  if (_DAT_00ac5204 && !IsBadReadPtr((void *)(_DAT_00ac5204 + 12), 4))
    field("rng", 0, "context_seed", read_u32(_DAT_00ac5204 + 12));
  uintptr_t camera = _DAT_0073cc3c;
  int camera_id = camera >= 0x67c728 && camera < 0x67c728 + 1200 * 28 &&
                          (camera - 0x67c728) % 28 == 0
                      ? (int)(camera - 0x67c728) / 28
                      : -1;
  field("world", 0, "camera", camera_id);
  if (camera_id >= 0)
    for (int i = 0; i < 7; ++i) {
      char name[20];
      snprintf(name, sizeof name, "camera_word_%d", i);
      field("camera", camera_id, name, read_s16(camera + i * 2));
    }
  for (int bank = 0; bank < 4; ++bank)
    for (int scan = 0; scan < 256; ++scan) {
      unsigned char value =
          *(const unsigned char *)(0x4c3890 + bank * 256 + scan);
      if (value)
        field("input", bank * 256 + scan, "value", value);
    }
  uintptr_t actor = _DAT_0063726c;
  unsigned order = 0;
  while (actor && order < 4096) {
    if (actor < 0x10000 || IsBadReadPtr((void *)actor, 0x18c)) {
      field("invalid", order, "active_actor", 1);
      break;
    }
    field("update_order", order++, "actor_id", read_s16(actor));
    uint32_t next = read_u32(actor + 0x4c);
    if (next == actor) {
      field("invalid", order, "self_cycle", 1);
      break;
    }
    actor = next;
  }
  if (actor && order == 4096)
    field("invalid", 0, "actor_list_limit", 1);
  /* Canonical IDs, not allocation order. Joe is table entry zero, never the
   * transient DAT_0047a470 actor context. */
  for (int id = 0; id < 5000; ++id) {
    actor = read_u32(0x630b60 + id * 4);
    if (!actor)
      continue;
    if (actor < 0x10000 || IsBadReadPtr((void *)actor, 0x18c)) {
      field("invalid", id, "actor_table", 1);
      continue;
    }
    field("actor", id, "id", read_s16(actor));
    static const struct {
      unsigned offset;
      const char *name;
    } fields[] = {{2, "flags"},
                  {0x82, "state"},
                  {0x84, "x"},
                  {0x86, "y"},
                  {0x88, "z"},
                  {0x90, "pitch"},
                  {0x92, "yaw"},
                  {0x94, "roll"},
                  {0x96, "previous_slot"},
                  {0xaa, "action_duration"},
                  {0xac, "action_progress"},
                  {0x162, "queued_action"},
                  {0x170, "motion_distance"},
                  {0x184, "durability"}};
    for (unsigned j = 0; j < sizeof fields / sizeof fields[0]; ++j)
      field("actor", id, fields[j].name, read_s16(actor + fields[j].offset));
    field("actor", id, "action_id", resource(read_u32(actor + 0xa6)));
    field("actor", id, "representation_id", resource(read_u32(actor + 0x11e)));
    field("actor", id, "scene_id", resource(read_u32(actor + 0x132)));
    field("actor", id, "table_flags", read_s16(0x64a178 + id * 2));
  }
  for (int id = 0; id < 2500; ++id) {
    uintptr_t scene = read_u32(0x62e450 + id * 4);
    if (!scene)
      continue;
    if (scene < 0x10000 || IsBadReadPtr((void *)scene, 8)) {
      field("invalid_scene", id, "unreadable", 1);
      continue;
    }
    field("scene", id, "camera", read_s16(scene + 2));
    uintptr_t child = read_u32(scene + 4);
    unsigned count = 0;
    while (child && count < 256) {
      if (child < 0x10000 || IsBadReadPtr((void *)child, 28)) {
        field("invalid_scene", id, "child", 1);
        break;
      }
      field("scene_child", id * 256 + count, "actor_id", read_s16(child));
      field("scene_child", id * 256 + count, "flags",
            *(unsigned char *)(child + 14));
      ++count;
      uintptr_t next = read_u32(child + 24);
      if (next == child) {
        field("invalid_scene", id, "cycle", 1);
        break;
      }
      child = next;
    }
    field("scene", id, "child_count", count);
  }
#undef GLOBAL
#endif
}
void E2R_SampleReplayCheckpoint(void) { sample_fields(E2R_ReplayField); }
#if E2R_ENABLE_RUNTIME_OPTIONS
void E2R_SampleInspection(void) {
  sample_fields(E2R_InspectField);
#if UINTPTR_MAX <= UINT32_MAX
  E2R_InspectField("world", 0, "simulation_time", (uint32_t)_DAT_00636588);
  E2R_InspectField("world", 0, "script_wait", DAT_0047a76c);
  E2R_InspectField("world", 0, "modal_state", _DAT_00643650);
  E2R_InspectField("script", 0, "last_opcode", E2R_action_last_opcode);
  /* Diagnostic address only: never used as a portable state identity. */
  E2R_InspectField("script", 0, "last_cursor_address", E2R_action_last_cursor);
  for (int id = 0; id < 5000; ++id) {
    uintptr_t actor = read_u32(0x630b60 + id * 4);
    if (!actor || IsBadReadPtr((void *)actor, 0x18c)) continue;
    uintptr_t node = read_u32(actor + 0xf2);
    E2R_InspectField("actor", id, "attachment_present", node != 0);
    if (node && IsBadReadPtr((void *)node, 0x26)) {
      E2R_InspectField("actor", id, "attachment_unreadable", 1);
      continue;
    }
#ifdef E2R_INSPECTION_ASAN
    if (node && __asan_region_is_poisoned((void *)node, 0x26)) {
      E2R_InspectField("actor", id, "attachment_unreadable", 1);
      continue;
    }
#endif
    if (node) {
      uintptr_t owner = read_u32(node + 0x22);
      int owner_id = -1;
      if (owner && !IsBadReadPtr((void *)owner, 2)) {
#ifdef E2R_INSPECTION_ASAN
        if (!__asan_region_is_poisoned((void *)owner, 2))
#endif
          owner_id = (int)read_s16(owner);
      }
      E2R_InspectField("actor", id, "attachment_owner_id", owner_id);
    }
  }
#endif
}
#endif
