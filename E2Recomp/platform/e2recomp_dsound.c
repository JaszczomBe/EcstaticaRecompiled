#include "e2recomp_audio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct SoundBuffer {
    void **methods;
    struct SoundBuffer *next;
    unsigned refs, flags, bytes;
    unsigned char *pcm;
    int volume, pan, locked;
    E2R_AudioVoice *voice;
} SoundBuffer;

static void *device_methods[11], *buffer_methods[21];
static void **device = device_methods;
static SoundBuffer *buffers;
static unsigned device_refs;
#define INVALID ((int)0x80070057u)
#define UNSUPPORTED ((int)0x80004001u)
#define NO_MEMORY ((int)0x8007000eu)

static int unsupported(void *self) { (void)self; return UNSUPPORTED; }
static unsigned buffer_addref(SoundBuffer *b) { return ++b->refs; }
static unsigned buffer_release(SoundBuffer *b)
{
    if (--b->refs) return b->refs;
    SoundBuffer **at = &buffers;
    while (*at != b) at = &(*at)->next;
    *at = b->next;
    E2R_HostAudioRelease(b->voice);
    free(b->pcm);
    free(b);
    return 0;
}
static int buffer_caps(SoundBuffer *b, unsigned *caps)
{
    if (!caps || caps[0] != 20) return INVALID;
    caps[1] = b->flags | 8; /* Software allocation. */
    caps[2] = b->bytes;
    caps[3] = caps[4] = 0;
    return 0;
}
static int buffer_status(SoundBuffer *b, unsigned *status)
{
    if (!status) return INVALID;
    *status = E2R_HostAudioPlaying(b->voice) ? 1 : 0;
    return 0;
}
static int buffer_lock(SoundBuffer *b, unsigned offset, unsigned bytes,
                       void **first, unsigned *first_bytes, void **second,
                       unsigned *second_bytes, unsigned flags)
{
    if (!first || !first_bytes || !second || !second_bytes || b->locked ||
        offset >= b->bytes || bytes > b->bytes || flags != 0) return INVALID;
    *first = b->pcm + offset;
    *first_bytes = bytes < b->bytes - offset ? bytes : b->bytes - offset;
    *second_bytes = bytes - *first_bytes;
    *second = *second_bytes ? b->pcm : NULL;
    b->locked = 1;
    return 0;
}
static int buffer_unlock(SoundBuffer *b, void *first, unsigned first_bytes,
                         void *second, unsigned second_bytes)
{
    if (!b->locked || first != b->pcm || first_bytes != b->bytes ||
        second || second_bytes) return INVALID;
    b->locked = 0;
    E2R_HostAudioRelease(b->voice);
    b->voice = E2R_HostAudioVoice(b->pcm, b->bytes);
    return b->voice ? 0 : NO_MEMORY;
}
static int buffer_volume(SoundBuffer *b, int volume)
{
    if (volume < -10000 || volume > 0) return INVALID;
    b->volume = volume;
    E2R_HostAudioGain(b->voice, b->volume, b->pan);
    return 0;
}
static int buffer_pan(SoundBuffer *b, int pan)
{
    if (pan < -10000 || pan > 10000) return INVALID;
    b->pan = pan;
    E2R_HostAudioGain(b->voice, b->volume, b->pan);
    return 0;
}
static int buffer_play(SoundBuffer *b, unsigned reserved, unsigned priority, unsigned flags)
{
    if (reserved || priority || flags > 1 || b->locked) return INVALID;
    if (!(b->flags & 1) && !b->voice) return INVALID;
    E2R_HostAudioPlay(b->voice, flags & 1);
    return 0;
}
static int buffer_stop(SoundBuffer *b)
{
    E2R_HostAudioStop(b->voice);
    return 0;
}
static int buffer_position(SoundBuffer *b, unsigned position)
{
    if (position >= b->bytes) return INVALID;
    E2R_HostAudioPosition(b->voice, position);
    return 0;
}
static int buffer_format(SoundBuffer *b, const E2R_WaveFormat *format)
{
    if (!(b->flags & 1) || !format || format->tag != 1) return INVALID;
    return 0;
}
static int create_buffer(void *self, const E2R_SoundDesc *desc, void **out, void *outer)
{
    (void)self;
    if (!out) return INVALID;
    *out = NULL;
    if (!desc || desc->size != 20 || outer) return INVALID;
    if (!(desc->flags & 1)) {
        const E2R_WaveFormat *f = desc->format;
        if (!desc->bytes || desc->bytes > 0x100000 || !f || f->tag != 1 ||
            f->channels != 1 || f->rate != 22050 || f->bits != 8 ||
            f->alignment != 1 || f->bytes_per_second != 22050) return INVALID;
    }
    SoundBuffer *b = calloc(1, sizeof(*b));
    if (!b) return NO_MEMORY;
    b->methods = buffer_methods;
    b->refs = 1;
    b->flags = desc->flags;
    b->bytes = desc->bytes;
    if (b->bytes) {
        b->pcm = malloc(b->bytes);
        if (!b->pcm) { free(b); return NO_MEMORY; }
        memset(b->pcm, 128, b->bytes);
    }
    b->next = buffers;
    buffers = b;
    *out = b;
    return 0;
}
static unsigned device_addref(void *self) { (void)self; return ++device_refs; }
static unsigned device_release(void *self)
{
    (void)self;
    if (device_refs && --device_refs) return device_refs;
    while (buffers) { buffers->refs = 1; buffer_release(buffers); }
    E2R_HostAudioClose();
    return 0;
}
static int cooperative(void *self, void *window, unsigned level)
{ (void)self; (void)window; return level == 2 ? 0 : INVALID; }
static int device_caps(void *self, unsigned *caps)
{
    (void)self;
    if (!caps || caps[0] != 96) return INVALID;
    memset(caps + 1, 0, 92);
    caps[1] = 0x3f;
    return 0;
}

int DirectSoundCreate(void *guid, void **out, void *outer)
{
    if (!out || guid || outer) return INVALID;
    *out = NULL;
    for (unsigned i = 0; i < 11; ++i) device_methods[i] = (void *)unsupported;
    for (unsigned i = 0; i < 21; ++i) buffer_methods[i] = (void *)unsupported;
    device_methods[1] = (void *)device_addref;
    device_methods[2] = (void *)device_release;
    device_methods[3] = (void *)create_buffer;
    device_methods[4] = (void *)device_caps;
    device_methods[6] = (void *)cooperative;
    buffer_methods[1] = (void *)buffer_addref;
    buffer_methods[2] = (void *)buffer_release;
    buffer_methods[3] = (void *)buffer_caps;
    buffer_methods[9] = (void *)buffer_status;
    buffer_methods[11] = (void *)buffer_lock;
    buffer_methods[12] = (void *)buffer_play;
    buffer_methods[13] = (void *)buffer_position;
    buffer_methods[14] = (void *)buffer_format;
    buffer_methods[15] = (void *)buffer_volume;
    buffer_methods[16] = (void *)buffer_pan;
    buffer_methods[18] = (void *)buffer_stop;
    buffer_methods[19] = (void *)buffer_unlock;
    E2R_HostAudioOpen();
    ++device_refs;
    *out = &device;
    return 0;
}
