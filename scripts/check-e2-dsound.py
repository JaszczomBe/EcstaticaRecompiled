#!/usr/bin/env python3
"""Exercise production DirectSound buffers and mixer without a physical device."""
import argparse
from pathlib import Path
from e2_original import run_fixture
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--asan',action='store_true')
p.add_argument('--sdl-library',type=Path,default=Path('build/Debug/clang21-i386-sdl/dep/SDL-build/libSDL3.a'))
p.add_argument('--keep-harness',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parent.parent
h=r'''
#include <assert.h>
#define E2R_HOST_BACKEND_SDL 1
#include "AUDIO"
#include "DSOUND"
void E2R_MusicRender(float *p,unsigned n) {memset(p,0,n*2*sizeof(*p));}
void E2R_MusicClose(void) {}
int main(void) {
    unsetenv("E2R_AUDIO");
    assert(!audio_output_enabled("dummy") && !audio_output_enabled("offscreen"));
    assert(audio_output_enabled("x11") && audio_output_enabled("wayland"));
    setenv("SDL_VIDEODRIVER","dummy",1);
    assert(E2R_HostAudioOpen() && output==NULL && !SDL_WasInit(SDL_INIT_AUDIO));
    E2R_HostAudioClose();
    setenv("E2R_AUDIO","on",1);
    assert(audio_output_enabled("dummy") && audio_output_enabled("offscreen"));
    setenv("SDL_AUDIODRIVER","dummy",1);
    assert(E2R_HostAudioOpen() && output!=NULL);
    E2R_HostAudioClose();
    setenv("E2R_AUDIO","off",1);
    assert(!audio_output_enabled("x11") && !audio_output_enabled("dummy"));
    void *device=NULL;assert(!DirectSoundCreate(NULL,&device,NULL));
    E2R_WaveFormat format={1,1,22050,22050,1,8,0};
    E2R_SoundDesc desc={20,0xe2,8,0,&format};
    SoundBuffer *a=NULL,*b=NULL;
    assert(!create_buffer(device,&desc,(void**)&a,NULL));
    assert(!create_buffer(device,&desc,(void**)&b,NULL));
    assert(a!=b&&a->pcm!=b->pcm);
    void *first=NULL,*second=NULL;unsigned n1,n2;
    unsigned char values[]={0,255,128,64,192,128,129,127};
    for(SoundBuffer *v=a;v;v=v==a?b:NULL) {
        assert(!buffer_lock(v,0,8,&first,&n1,&second,&n2,0)&&n1==8&&!n2&&!second);
        assert(buffer_lock(v,0,8,&first,&n1,&second,&n2,0)!=0);
        memcpy(first,values,8);assert(!buffer_unlock(v,first,8,NULL,0));
    }
    SDL_AudioSpec spec={SDL_AUDIO_S16,2,22050};
    SDL_AudioStream *test=SDL_CreateAudioStream(&spec,&spec);assert(test);
    assert(!buffer_play(a,0,0,0));
    audio_fill(NULL,test,8*4,0);int16_t actual[32];
    assert(SDL_GetAudioStreamData(test,actual,32)==32);
    for(unsigned i=0;i<8;i++)assert(actual[i*2]==((int)values[i]-128)*256&&actual[i*2+1]==actual[i*2]);
    unsigned status=1;assert(!buffer_status(a,&status)&&status==0);
    assert(!buffer_position(a,0)&&!buffer_play(a,0,0,1));
    assert(!buffer_volume(b,-2000)&&!buffer_pan(b,10000)&&!buffer_play(b,0,0,0));
    audio_fill(NULL,test,16*4,0);assert(SDL_GetAudioStreamData(test,actual,64)==64);
    assert(!buffer_status(a,&status)&&status==1);
    assert(a->voice->position==0&&b->voice->position==8&&!b->voice->playing);
    assert(actual[0]==-32768&&actual[1]==-32768); /* Saturating overlap. */
    assert(!buffer_stop(a));audio_fill(NULL,test,8*4,0);
    assert(SDL_GetAudioStreamData(test,actual,32)==32);
    for(unsigned i=0;i<16;i++)assert(actual[i]==0);
    assert(buffer_volume(a,1)!=0&&buffer_volume(a,-10001)!=0&&buffer_pan(a,10001)!=0);
    assert(buffer_position(a,8)!=0&&buffer_play(a,0,0,2)!=0);
    assert(buffer_addref(a)==2&&buffer_release(a)==1&&buffer_release(a)==0);
    assert(buffer_release(b)==0&&buffers==NULL&&voices==NULL);
    desc.bytes=0;assert(create_buffer(device,&desc,(void**)&a,NULL)!=0&&a==NULL);
    desc.bytes=8;format.bits=16;assert(create_buffer(device,&desc,(void**)&a,NULL)!=0);
    assert(device_release(device)==0);
    SDL_DestroyAudioStream(test);
    puts("PASS: distinct buffers, exact mixed PCM, overlap/clipping, gain/pan, loop, stop, position, bounds and release");
}
'''.replace('AUDIO',str(root/'E2Recomp/platform/e2recomp_audio.c'),1).replace('DSOUND',str(root/'E2Recomp/platform/e2recomp_dsound.c'),1)
run_fixture(h,asan=a.asan,keep=a.keep_harness,libraries=('-I'+str(root/'dep/SDL/include'),str(a.sdl_library.resolve()),'-lm','-ldl','-lpthread'))
