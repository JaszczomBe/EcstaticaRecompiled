#pragma once
#include <stdint.h>

int E2R_MusicAvailable(void);
void E2R_MusicData(const void *data, unsigned bytes, int resource);
void E2R_MusicRender(float *stereo, unsigned frames);
void E2R_MusicClose(void);
short E2R_MusicInit(unsigned device);
short E2R_MusicPlay(const void *data, short tune);
short E2R_MusicStop(short tune);
short E2R_MusicRemove(void);
