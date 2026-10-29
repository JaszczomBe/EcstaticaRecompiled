#!/usr/bin/env python3
"""Exercise production software instruments, PCM and music buffer ownership."""
import argparse,json
from pathlib import Path
from e2_original import run_fixture
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path,help='Installed original executable (asset location only)')
p.add_argument('--asan',action='store_true')
p.add_argument('--keep-harness',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parent.parent
h=r'''
#include <assert.h>
#include "CORE"
#include "MUSIC"
#include "AUDIO"
static unsigned char data[50000],backup[50000];
static float expected[22050*2],actual[22050*2];
int main(void) {
 setenv("E2R_AUDIO","off",1);unsetenv("E2R_MUSIC_TRACE");unsetenv("E2R_MUSIC_TAP");
 FILE *index=fopen(INDEX,"rb"),*archive=fopen(ARCHIVE,"rb");assert(index&&archive);
 fseek(index,(2500+5000+2000+500+700+12-1)*4,SEEK_SET);unsigned char b[4];assert(fread(b,1,4,index)==4);
 unsigned at=b[0]<<24|b[1]<<16|b[2]<<8|b[3];fseek(archive,at,SEEK_SET);assert(fread(b,1,4,archive)==4);
 unsigned bytes=b[0]<<24|b[1]<<16|b[2]<<8|b[3];assert(bytes<=sizeof data&&fread(data,1,bytes,archive)==bytes);
 memcpy(backup,data,bytes);
 assert(E2R_MusicAvailable()&&E2R_MusicInit(0)==0);E2R_MusicData(data,bytes,12);assert(!E2R_MusicPlay(data,1));
 E2R_MusicRender(expected,22050);assert(E2R_music_messages>32&&E2R_music_nonzero_frames>0);
 E2R_HostAudioClose();assert(E2R_MusicInit(0)==0);E2R_MusicData(data,bytes,12);assert(!E2R_MusicPlay(data,1));
 memset(data,0xdd,bytes); /* A later game load cannot alter callback-owned sequences. */
 E2R_MusicRender(actual,22050);assert(!memcmp(actual,expected,sizeof actual));
 assert(!E2R_MusicStop(0));unsigned long long events=E2R_music_messages;
 E2R_MusicRender(actual,22050);assert(events==E2R_music_messages);
 assert(!E2R_MusicRemove()&&E2R_MusicPlay(data,1)==1);E2R_HostAudioClose();
 setenv("E2R_SOUNDFONT","/nonexistent/e2r-test-bank.sf2",1);
 assert(!E2R_MusicAvailable()&&E2R_MusicInit(0)==1);E2R_HostAudioClose();
 printf("PASS: software General MIDI renders nonzero PCM with output disabled; copied sequence ownership, deterministic synthesis, stop/remove and missing-bank fallback\n");
}
'''
for key,path in dict(CORE='e2recomp_simd.c',MUSIC='e2recomp_music.c',AUDIO='e2recomp_audio.c').items():h=h.replace(key,str(root/'E2Recomp/platform'/path),1)
h=h.replace('INDEX',json.dumps(str(a.exe.parent/'OFFSETS'))).replace('ARCHIVE',json.dumps(str(a.exe.parent/'Files/ECSTATIC')))
run_fixture(h,asan=a.asan,keep=a.keep_harness,libraries=('-lm',))
