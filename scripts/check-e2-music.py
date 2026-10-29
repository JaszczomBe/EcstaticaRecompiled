#!/usr/bin/env python3
"""Bounded event/state comparison against the installed original SIMD_W95.DLL."""
import argparse
import json
from pathlib import Path
from e2_original import OriginalImage, run_fixture, support

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('dll', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--ticks', type=int, default=10000)
p.add_argument('--keep-harness', type=Path)
a = p.parse_args()
assert 1 <= a.ticks <= 100000
root = Path(__file__).resolve().parent.parent
image = OriginalImage(a.dll)
h = support() + r'''
#include <assert.h>
#include <string.h>
#include <sys/mman.h>
#include "CORE"
static uint32_t messages[2][65536], counts[2];
static unsigned side;
static void output(void *u,uint32_t m) {assert(counts[side]<65536);messages[side][counts[side]++]=m;}
__attribute__((stdcall,force_align_arg_pointer)) static int midi(void *dev,uint32_t m) {output(NULL,m);return 0;}
static void jump(uint32_t at,void *f) {*(uint8_t*)at=0xe9;*(uint32_t*)(at+1)=(uintptr_t)f-at-5;}
typedef int (__attribute__((stdcall)) *Play)(void*,int);
typedef int (__attribute__((stdcall)) *Stop)(int);
static Play play=(Play)0x10001760;
static Stop stop=(Stop)0x10001890;
static void (*tick)(void)=(void*)0x10001230;
static uint8_t data[50000];
static unsigned id, frame;
static uint32_t offset(uint32_t p) {
    if (!p) return 0;
    if (p>=0x10009010 && p<0x10009018) return p-0x10009010+0xfffffff0u;
    return p-(uintptr_t)data;
}
#define CHECK(x,y) do {if((x)!=(y)){fprintf(stderr,"track %u tick %u: %s=%lld != %s=%lld\n",id,frame,#x,(long long)(x),#y,(long long)(y));abort();}}while(0)
static void compare(E2R_SimdSequence *s) {
    CHECK(s->error,0);CHECK(counts[0],counts[1]);
    for(unsigned i=0;i<counts[0];i++)CHECK(messages[0][i],messages[1][i]);
    CHECK(s->tune,*(int16_t*)0x10009028);CHECK(s->count,*(int16_t*)0x10009038);
    CHECK(s->tempo,*(uint8_t*)0x10009020);CHECK(s->beat,*(int8_t*)0x1000901c);
    CHECK(s->fraction,*(float*)0x10009048);CHECK(s->increment,*(float*)0x1000904c);
    CHECK(s->sync,*(int16_t*)0x1000902c);
    for(unsigned i=0;i<16;i++) {
        uint8_t *o=(void*)(0x10006008+i*20);E2R_SimdTrack *t=s->tracks+i;
        CHECK(t->cursor,offset(*(uint32_t*)o));CHECK(t->loop,offset(*(uint32_t*)(o+4)));
        CHECK(t->delay,*(int32_t*)(o+8));CHECK(t->channel,o[12]);CHECK(t->note,o[13]);
        CHECK(t->active,o[14]);CHECK(t->muted,o[15]);CHECK(t->volume,o[16]);
    }
    counts[0]=counts[1]=0;
}
'''.replace('CORE', str(root/'E2Recomp/platform/e2recomp_simd.c'))
for at, size, raw, _ in image.sections:
    data = image.code(at, at+size)
    h += f'static unsigned char section_{at:x}[]={{'+','.join(map(str, data))+'};\n'
h += r'''
int main(void) {
    assert(mmap((void*)0x10000000,0xd000,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)0x10000000);
'''
for at, size, raw, _ in image.sections:
    h += f'memcpy((void*)0x{at:x},section_{at:x},sizeof section_{at:x});\n'
h += r'''
    jump(0x1000259e,midi);
    FILE *index=fopen(INDEX,"rb"),*archive=fopen(ARCHIVE,"rb");assert(index&&archive);
    unsigned assets=0;uint64_t events=0;
    for(id=1;id<=96;id++) {
        unsigned char word[4];fseek(index,(2500+5000+2000+500+700)*4+(id-1)*4,SEEK_SET);
        assert(fread(word,1,4,index)==4);
        unsigned at=word[0]<<24|word[1]<<16|word[2]<<8|word[3];if(at==0xffffffffu)continue;
        fseek(archive,at,SEEK_SET);assert(fread(word,1,4,archive)==4);
        unsigned bytes=word[0]<<24|word[1]<<16|word[2]<<8|word[3];assert(bytes<48000);
        assert(fread(data,1,bytes,archive)==bytes);
        memset((void*)0x10006000,0,0x2000);
        memcpy((void*)0x10009000,section_10009000,sizeof section_10009000);
        *(uint8_t*)0x10009000=1;
        E2R_SimdSequence s;E2R_SimdInit(&s,output,NULL);
        side=0;int original=play(data,1);
        side=1;CHECK(E2R_SimdPlay(&s,data,bytes,1),original);frame=0;compare(&s);
        for(frame=1;frame<=TICKS;frame++) {
            side=0;tick();side=1;E2R_SimdTick(&s);events+=counts[0];compare(&s);
        }
        side=0;int status=stop(0);side=1;CHECK(E2R_SimdStop(&s,0),status);compare(&s);
        /* Restart retains cached channel/note values and fractional phase. */
        side=0;original=play(data,1);side=1;CHECK(E2R_SimdPlay(&s,data,bytes,1),original);compare(&s);
        assets++;
    }
    printf("PASS: %u original GM resources, %u ticks each, %llu MIDI messages; event order, state, stop/restart and preserved defects\n",assets,TICKS,(unsigned long long)events);
}
'''.replace('INDEX',json.dumps(str(a.dll.parent/'OFFSETS'))).replace('ARCHIVE',json.dumps(str(a.dll.parent/'Files/ECSTATIC'))).replace('TICKS',str(a.ticks))
run_fixture(h,asan=a.asan,keep=a.keep_harness,libraries=('-lm',),image=image,dependencies=('MIDI short-message sink intercepted; DLL initialization/OS timer excluded',))
print(json.dumps({'dll_sha256':image.sha256,'ranges':image.ranges}))
