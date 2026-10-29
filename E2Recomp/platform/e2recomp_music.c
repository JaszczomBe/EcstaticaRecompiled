#include "e2recomp_music.h"
#include "e2recomp_simd.h"
#include "e2recomp_audio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define TSF_IMPLEMENTATION
#include "../../dep/TinySoundFont/tsf.h"

static tsf *synth;
static int attempted, initialized, registered_id;
static const void *registered;
static unsigned registered_bytes, phase, tap_bytes;
static uint8_t playing_data[50000];
static E2R_SimdSequence sequence;
static FILE *trace, *tap;
uint64_t E2R_music_frames, E2R_music_nonzero_frames, E2R_music_messages;

static void music_message(void *user, uint32_t message)
{
    unsigned channel = message & 15, a = (message >> 8) & 127, b = (message >> 16) & 127;
    (void)user;
    E2R_music_messages++;
    switch (message & 0xf0) {
    case 0x80: tsf_channel_note_off(synth, channel, a); break;
    case 0x90: tsf_channel_note_on(synth, channel, a, b / 127.0f); break;
    case 0xb0: tsf_channel_midi_control(synth, channel, a, b); break;
    case 0xc0: tsf_channel_set_presetnumber(synth, channel, a, channel == 9); break;
    case 0xe0: tsf_channel_set_pitchwheel(synth, channel, a | (b << 7)); break;
    }
}

int E2R_MusicAvailable(void)
{
    if (attempted) return synth != NULL;
    attempted = 1;
    const char *bank = getenv("E2R_SOUNDFONT");
    if (bank && *bank) synth = tsf_load_filename(bank);
    else {
        bank = "/usr/share/sounds/sf2/TimGM6mb.sf2";
        synth = tsf_load_filename(bank);
        if (!synth) {
            bank = "/usr/share/sounds/sf2/FluidR3_GM.sf2";
            synth = tsf_load_filename(bank);
        }
    }
    if (!synth) {
        fprintf(stderr,"music: no readable SoundFont; MIDI device unavailable (set E2R_SOUNDFONT)\n");
        return 0;
    }
    tsf_set_output(synth, TSF_STEREO_INTERLEAVED, 22050, -6);
    tsf_set_max_voices(synth, 256);
    for (int i = 0; i < 16; ++i) tsf_channel_set_presetnumber(synth, i, 0, i == 9);
    E2R_SimdInit(&sequence, music_message, NULL);
    const char *path = getenv("E2R_MUSIC_TRACE");
    if (path && *path) trace = fopen(path,"wx");
    path = getenv("E2R_MUSIC_TAP");
    if (path && *path) tap = fopen(path,"wbx");
    fprintf(stderr,"music: General MIDI software port bank=%s rate=22050 gain=-6dB\n",bank);
    return 1;
}

short E2R_MusicInit(unsigned device)
{
    (void)device;
    if (!E2R_MusicAvailable()) return 1;
    E2R_HostAudioOpen();
    E2R_HostAudioLock();
    initialized = 1;
    E2R_HostAudioUnlock();
    return 0;
}

short E2R_MusicRemove(void)
{
    if (!initialized) return 1;
    E2R_MusicStop(0);
    E2R_HostAudioLock();
    initialized = 0;
    E2R_HostAudioUnlock();
    return 0;
}

void E2R_MusicData(const void *data, unsigned bytes, int resource)
{
    registered = data;
    registered_bytes = bytes;
    registered_id = resource;
}

short E2R_MusicPlay(const void *data, short tune)
{
    if (!initialized) return 1;
    if (data != registered || !registered_bytes || registered_bytes > sizeof(playing_data)) return 6;
    E2R_HostAudioLock();
    memcpy(playing_data, data, registered_bytes);
    int result = E2R_SimdPlay(&sequence, playing_data, registered_bytes, tune);
    E2R_HostAudioUnlock();
    if (trace) {
        uint32_t hash = 2166136261u;
        const uint8_t *p = data;
        for (unsigned i = 0; i < registered_bytes; ++i) hash = (hash ^ p[i]) * 16777619u;
        fprintf(trace,"play resource=%d bytes=%u hash=%08x tune=%d result=%d\n",registered_id,registered_bytes,hash,tune,result);
        fflush(trace);
    }
    return result;
}

short E2R_MusicStop(short tune)
{
    if (!initialized) return 1;
    E2R_HostAudioLock();
    int result = E2R_SimdStop(&sequence, tune);
    E2R_HostAudioUnlock();
    if (trace) { fprintf(trace,"stop tune=%d result=%d\n",tune,result); fflush(trace); }
    return result;
}

/* Called only under SDL's stream lock. No reconstructed state is read here. */
void E2R_MusicRender(float *stereo, unsigned frames)
{
    if (frames > 512) {
        E2R_MusicRender(stereo, 512);
        E2R_MusicRender(stereo + 1024, frames - 512);
        return;
    }
    memset(stereo, 0, frames * 2 * sizeof(*stereo));
    if (!initialized) return;
    unsigned done = 0;
    while (done < frames) {
        unsigned count = 441 - phase; /* Original 20 ms timer at 22050 Hz. */
        if (count > frames - done) count = frames - done;
        tsf_render_float(synth, stereo + done * 2, count, 0);
        done += count;
        phase += count;
        if (phase == 441) { phase = 0; E2R_SimdTick(&sequence); }
    }
    int16_t pcm[512 * 2];
    for (unsigned i = 0; i < frames; ++i) {
        E2R_music_frames++;
        if (stereo[i*2] != 0 || stereo[i*2+1] != 0) E2R_music_nonzero_frames++;
        for (unsigned c = 0; c < 2; ++c) {
            float value = stereo[i*2+c] * 32768;
            pcm[i*2+c] = (int16_t)fmaxf(-32768,fminf(32767,value));
        }
    }
    if (tap && tap_bytes < 8 * 1024 * 1024) {
        unsigned bytes = frames * 4;
        if (bytes > 8 * 1024 * 1024 - tap_bytes) bytes = 8 * 1024 * 1024 - tap_bytes;
        tap_bytes += (unsigned)fwrite(pcm,1,bytes,tap);
    }
}

void E2R_MusicClose(void)
{
    initialized = 0;
    if (synth) tsf_close(synth);
    synth = NULL;
    if (trace) fclose(trace);
    if (tap) fclose(tap);
    trace = tap = NULL;
    registered = NULL;
    registered_bytes = phase = tap_bytes = 0;
    attempted = 0;
}
