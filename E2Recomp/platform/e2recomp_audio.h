#pragma once

#include <stdint.h>

/* DirectSound 3 layouts, with native pointers at the compatibility boundary. */
typedef struct E2R_WaveFormat {
    uint16_t tag, channels;
    uint32_t rate, bytes_per_second;
    uint16_t alignment, bits, extra;
} E2R_WaveFormat;
typedef struct E2R_SoundDesc {
    uint32_t size, flags, bytes, reserved;
    E2R_WaveFormat *format;
} E2R_SoundDesc;

int DirectSoundCreate(void *guid, void **device, void *outer);

/* Host voices own copies. Device threads never access reconstructed state. */
typedef struct E2R_AudioVoice E2R_AudioVoice;
int E2R_HostAudioOpen(void);
void E2R_HostAudioClose(void);
void E2R_HostAudioLock(void);
void E2R_HostAudioUnlock(void);
E2R_AudioVoice *E2R_HostAudioVoice(const unsigned char *pcm, unsigned bytes);
void E2R_HostAudioRelease(E2R_AudioVoice *voice);
void E2R_HostAudioPlay(E2R_AudioVoice *voice, int loop);
void E2R_HostAudioStop(E2R_AudioVoice *voice);
void E2R_HostAudioPosition(E2R_AudioVoice *voice, unsigned position);
int E2R_HostAudioPlaying(E2R_AudioVoice *voice);
void E2R_HostAudioGain(E2R_AudioVoice *voice, int volume, int pan);
