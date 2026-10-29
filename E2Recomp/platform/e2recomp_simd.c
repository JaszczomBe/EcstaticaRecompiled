/* SIMD_W95.DLL 0x100011e0..0x10001b2b: host-owned music sequencer.
 * Preserve its timer rounding, event order and authored per-track loops.
 * Original-x86 fixtures own the equivalence boundary. */
#include "e2recomp_simd.h"
#include <string.h>

static uint32_t simd_word(const uint8_t *p)
{
    return p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static uint8_t simd_byte(E2R_SimdSequence *s, E2R_SimdTrack *t)
{
    static const uint8_t idle[] = {255,255,255,127,154,0,0,0};
    if (t->cursor >= 0xfffffff0u && t->cursor - 0xfffffff0u < sizeof(idle))
        return idle[t->cursor++ - 0xfffffff0u];
    if (t->cursor >= s->bytes) { s->error = 1; t->active = 0; return 0; }
    return s->data[t->cursor++];
}

static uint32_t simd_delta(E2R_SimdSequence *s, E2R_SimdTrack *t)
{
    uint32_t result = 0;
    for (unsigned i = 0; i < 5; ++i) {
        uint8_t b = simd_byte(s, t);
        result = (result << 7) + (b & 127);
        if (!(b & 128)) return result;
    }
    s->error = 1;
    t->active = 0;
    return 0;
}

static void simd_message(E2R_SimdSequence *s, unsigned channel, unsigned op,
                         unsigned a, unsigned b)
{
    if (s->output) s->output(s->user, (channel | op) | (a << 8) | (b << 16));
}

static void simd_volume(E2R_SimdSequence *s, E2R_SimdTrack *t)
{
    int16_t product = (int16_t)((int8_t)t->volume * s->master);
    simd_message(s, t->channel, 0xb0, 7, (uint8_t)(product >> 8));
}

static void simd_tempo(E2R_SimdSequence *s)
{
    s->increment = (float)((double)s->tempo * s->beat / (60000.0f / 20));
}

void E2R_SimdInit(E2R_SimdSequence *s, E2R_MidiOutput output, void *user)
{
    memset(s, 0, sizeof(*s));
    s->beat = 96;
    s->tempo = 120;
    s->master = 256;
    s->fraction = 0;
    s->output = output;
    s->user = user;
}

int E2R_SimdStop(E2R_SimdSequence *s, int tune)
{
    if (s->count < 1 || s->count > 16) return 7;
    if (tune > 0 && tune != s->tune) return 8;
    for (unsigned i = 0; i < 16; ++i) {
        simd_message(s, s->tracks[i].channel, 0xb0, 123, 0);
        s->tracks[i].active = 0;
    }
    s->tune = 0;
    return 0;
}

int E2R_SimdPlay(E2R_SimdSequence *s, const uint8_t *data, unsigned bytes, int tune)
{
    if (bytes < 8 || tune <= 0 || tune > (int8_t)data[0]) return 6;
    uint32_t table = simd_word(data + 4);
    if (table > bytes || (unsigned)tune * 4 > bytes - table) return 6;
    uint32_t at = simd_word(data + table + (tune - 1) * 4);
    if (at > bytes || bytes - at < 3) return 6;
    int count = (int8_t)data[at + 2];
    if (count < 0 || count > 16 || (unsigned)count * 4 > bytes - at - 3) return 6;
    for (int i = 0; i < count; ++i) {
        if (simd_word(data + at + 3 + i * 4) >= bytes) return 6;
    }
    E2R_SimdStop(s, 0);
    s->data = data;
    s->bytes = bytes;
    s->error = 0;
    s->tune = tune;
    s->beat = (int8_t)data[at];
    s->tempo = data[at + 1];
    s->count = count;
    for (int i = 0; i < count; ++i) {
        E2R_SimdTrack *t = s->tracks + i;
        t->cursor = t->loop = simd_word(data + at + 3 + i * 4);
        t->delay = simd_delta(s, t);
        t->active = 1;
        t->muted = 0;
        t->volume = 127;
    }
    simd_tempo(s);
    /* Original 0x100016e0 repeats the first track, without advancing it. */
    for (int i = 0; i < 16; ++i)
        if (s->tracks[0].active) simd_volume(s, s->tracks);
    for (int i = 0; i < 16; ++i) simd_message(s, i, 0xb0, 121, 0);
    return s->error ? 6 : 0;
}

static void simd_command(E2R_SimdSequence *s, E2R_SimdTrack *t, uint8_t op)
{
    unsigned a, b;
    switch (op) {
    case 0x90:
        a = simd_byte(s, t);
        if (!t->muted) simd_message(s, t->channel, 0x80, a, 0);
        break;
    case 0x91:
        t->active = 0;
        for (int i = 0, active = 0; i < 16; ++i) {
            active += s->tracks[i].active == 1;
            if (i == 15 && !active) s->tune = 0;
        }
        simd_message(s, t->channel, 0xb0, 123, 0);
        break;
    case 0x92:
        simd_message(s, t->channel, 0xc0, simd_byte(s, t), 0);
        break;
    case 0x93:
        s->tempo = simd_byte(s, t);
        simd_tempo(s);
        break;
    case 0x94:
        simd_message(s, t->channel, 0xb0, 100, 0);
        simd_message(s, t->channel, 0xb0, 101, 0);
        simd_message(s, t->channel, 0xb0, 6, simd_byte(s, t));
        break;
    case 0x95:
        simd_message(s, t->channel, 0xe0, 0, simd_byte(s, t));
        break;
    case 0x96:
        t->volume = simd_byte(s, t);
        simd_volume(s, t);
        break;
    case 0x97: simd_byte(s, t); break;
    case 0x98: t->cursor = t->loop; break;
    case 0x99:
        if (!t->muted) simd_message(s, t->channel, 0x80, t->note, 0);
        break;
    case 0x9a:
        /* Original idle stream at 0x10009010: long delta followed by 0x9a. */
        t->cursor = 0xfffffff0u;
        break;
    case 0x9b: simd_message(s, t->channel, 0xb0, 10, simd_byte(s, t)); break;
    case 0x9c: t->loop = t->cursor; break;
    case 0x9d:
        a = simd_byte(s, t);
        b = simd_byte(s, t);
        simd_message(s, t->channel, 0xb0, b, a);
        break;
    case 0x9e: case 0x9f: break;
    case 0xa0: s->sync = (s->sync + 1) & 0x7fff; break;
    default: s->error = 1; t->active = 0; break;
    }
}

void E2R_SimdTick(E2R_SimdSequence *s)
{
    float sum = s->fraction + s->increment;
    int advance = (int)sum;
    s->fraction = sum - advance;
    if (s->busy) {
        /* Original reentrant branch also repeatedly visits track zero. */
        s->tracks[0].delay -= advance * 16;
        return;
    }
    for (unsigned i = 0; i < 16; ++i) {
        E2R_SimdTrack *t = s->tracks + i;
        if (!t->active) continue;
        t->delay -= advance;
        unsigned bound = 0;
        while (t->active && t->delay < 0 && !s->error) {
            if (++bound > 65536) { s->error = 1; t->active = 0; break; }
            uint8_t op = simd_byte(s, t);
            if (op < 128) {
                t->note = op;
                unsigned velocity = simd_byte(s, t);
                if (!t->muted) simd_message(s, t->channel, 0x90, op, velocity);
            } else if (op < 0x90) t->channel = op & 127;
            else simd_command(s, t, op);
            t->delay += simd_delta(s, t);
        }
    }
}
