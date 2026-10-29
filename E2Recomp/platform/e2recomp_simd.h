#pragma once

#include <stdint.h>

typedef void (*E2R_MidiOutput)(void *user, uint32_t message);
typedef struct E2R_SimdTrack {
    uint32_t cursor, loop;
    int32_t delay;
    uint8_t channel, note, active, muted, volume;
} E2R_SimdTrack;
typedef struct E2R_SimdSequence {
    const uint8_t *data;
    unsigned bytes;
    E2R_SimdTrack tracks[16];
    int16_t tune, count, master, sync;
    int8_t beat;
    uint8_t tempo, busy;
    float fraction, increment;
    int error;
    E2R_MidiOutput output;
    void *user;
} E2R_SimdSequence;

void E2R_SimdInit(E2R_SimdSequence *s, E2R_MidiOutput output, void *user);
int E2R_SimdPlay(E2R_SimdSequence *s, const uint8_t *data, unsigned bytes, int tune);
int E2R_SimdStop(E2R_SimdSequence *s, int tune);
void E2R_SimdTick(E2R_SimdSequence *s);
