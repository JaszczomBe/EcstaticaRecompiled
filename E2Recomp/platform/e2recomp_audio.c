#include "e2recomp_audio.h"
#include "e2recomp_music.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef E2R_HOST_BACKEND_SDL
#include <SDL3/SDL.h>
#endif

struct E2R_AudioVoice {
    struct E2R_AudioVoice *next;
    unsigned char *pcm;
    unsigned bytes, position;
    int playing, loop;
    float left, right;
};

static E2R_AudioVoice *voices;
static FILE *tap;
static unsigned tap_bytes;
/* Observational counters: only inspected under the stream lock or after close. */
uint64_t E2R_audio_frames, E2R_audio_nonzero_frames;
static int opened;
#ifdef E2R_HOST_BACKEND_SDL
static SDL_AudioStream *output;
#define AUDIO_LOCK() do { if (output) SDL_LockAudioStream(output); } while (0)
#define AUDIO_UNLOCK() do { if (output) SDL_UnlockAudioStream(output); } while (0)

static void audio_fill(void *user, SDL_AudioStream *stream, int needed, int total)
{
    int16_t pcm[512 * 2];
    float music[512 * 2];
    (void)user;
    (void)total;
    while (needed > 0) {
        unsigned frames = (unsigned)(needed + 3) / 4;
        if (frames > 512) frames = 512;
        E2R_MusicRender(music, frames);
        for (unsigned i = 0; i < frames; ++i) {
            float left = music[i * 2] * 32768, right = music[i * 2 + 1] * 32768;
            for (E2R_AudioVoice *v = voices; v; v = v->next) {
                if (!v->playing) continue;
                int sample = ((int)v->pcm[v->position++] - 128) * 256;
                left += sample * v->left;
                right += sample * v->right;
                if (v->position == v->bytes) {
                    if (v->loop) v->position = 0;
                    else v->playing = 0;
                }
            }
            pcm[i * 2] = (int16_t)fmaxf(-32768, fminf(32767, left));
            pcm[i * 2 + 1] = (int16_t)fmaxf(-32768, fminf(32767, right));
            E2R_audio_frames++;
            if (pcm[i * 2] || pcm[i * 2 + 1]) E2R_audio_nonzero_frames++;
        }
        if (tap && tap_bytes < 8 * 1024 * 1024) {
            unsigned bytes = frames * 4;
            if (bytes > 8 * 1024 * 1024 - tap_bytes) bytes = 8 * 1024 * 1024 - tap_bytes;
            tap_bytes += (unsigned)fwrite(pcm, 1, bytes, tap);
        }
        if (!SDL_PutAudioStreamData(stream, pcm, (int)frames * 4)) break;
        needed -= (int)frames * 4;
    }
}
#else
#define AUDIO_LOCK() ((void)0)
#define AUDIO_UNLOCK() ((void)0)
#endif

void E2R_HostAudioLock(void) { AUDIO_LOCK(); }
void E2R_HostAudioUnlock(void) { AUDIO_UNLOCK(); }

int E2R_HostAudioOpen(void)
{
    if (opened) return 1;
    opened = 1;
    atexit(E2R_HostAudioClose);
#ifdef E2R_HOST_BACKEND_SDL
    const char *mode = getenv("E2R_AUDIO");
    if (mode && strcmp(mode, "off") == 0) return 1;
    SDL_AudioSpec spec = { SDL_AUDIO_S16, 2, 22050 };
    if (SDL_InitSubSystem(SDL_INIT_AUDIO))
        output = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,
                                           &spec, audio_fill, NULL);
    if (output == NULL) {
        fprintf(stderr, "audio output unavailable: %s; continuing silently\n", SDL_GetError());
        return 1;
    }
    const char *path = getenv("E2R_AUDIO_TAP");
    if (path && *path) tap = fopen(path, "wbx");
    if (!SDL_ResumeAudioStreamDevice(output)) {
        SDL_DestroyAudioStream(output);
        output = NULL;
    }
    fprintf(stderr, "audio output: driver=%s active=%d format=s16 stereo rate=22050\n",
            SDL_GetCurrentAudioDriver(), output != NULL);
#endif
    return 1;
}

void E2R_HostAudioClose(void)
{
#ifdef E2R_HOST_BACKEND_SDL
    if (output) SDL_DestroyAudioStream(output);
    output = NULL;
#endif
    E2R_MusicClose();
    while (voices) E2R_HostAudioRelease(voices);
    if (tap) fclose(tap);
    tap = NULL;
    opened = 0;
}

E2R_AudioVoice *E2R_HostAudioVoice(const unsigned char *pcm, unsigned bytes)
{
    if (!bytes) return NULL;
    E2R_AudioVoice *v = calloc(1, sizeof(*v));
    if (!v) return NULL;
    v->pcm = malloc(bytes);
    if (!v->pcm) { free(v); return NULL; }
    memcpy(v->pcm, pcm, bytes);
    v->bytes = bytes;
    v->left = v->right = 1;
    AUDIO_LOCK();
    v->next = voices;
    voices = v;
    AUDIO_UNLOCK();
    return v;
}

void E2R_HostAudioRelease(E2R_AudioVoice *voice)
{
    if (!voice) return;
    AUDIO_LOCK();
    E2R_AudioVoice **at = &voices;
    while (*at && *at != voice) at = &(*at)->next;
    if (*at) *at = voice->next;
    AUDIO_UNLOCK();
    free(voice->pcm);
    free(voice);
}

void E2R_HostAudioPlay(E2R_AudioVoice *voice, int loop)
{
    if (!voice) return;
    AUDIO_LOCK();
    if (voice->position == voice->bytes) voice->position = 0;
    voice->loop = loop;
    voice->playing = 1;
    AUDIO_UNLOCK();
}

void E2R_HostAudioStop(E2R_AudioVoice *voice)
{
    if (!voice) return;
    AUDIO_LOCK();
    voice->playing = 0;
    AUDIO_UNLOCK();
}

void E2R_HostAudioPosition(E2R_AudioVoice *voice, unsigned position)
{
    if (!voice) return;
    AUDIO_LOCK();
    voice->position = position;
    AUDIO_UNLOCK();
}

int E2R_HostAudioPlaying(E2R_AudioVoice *voice)
{
    if (!voice) return 0;
    AUDIO_LOCK();
    int result = voice->playing;
    AUDIO_UNLOCK();
    return result;
}

void E2R_HostAudioGain(E2R_AudioVoice *voice, int volume, int pan)
{
    if (!voice) return;
    float gain = volume <= -10000 ? 0 : powf(10, volume / 2000.0f);
    AUDIO_LOCK();
    voice->left = gain * (pan > 0 ? powf(10, -pan / 2000.0f) : 1);
    voice->right = gain * (pan < 0 ? powf(10, pan / 2000.0f) : 1);
    AUDIO_UNLOCK();
}
