#!/usr/bin/env python3
"""Compare recovered polar outputs, splitting and motion query with original i386.

Floor/terrain is a deterministic intercepted service; actors, obstacle selection,
slide/turn arithmetic, height acceptance and output writes are real production C.
This is bounded query evidence, not real-map collision or gameplay acceptance.
"""
import argparse
import json
from pathlib import Path
import re
from e2_original import OriginalImage, run_fixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
parser.add_argument('--replay', type=Path, action='append', default=[],
                    help='Replay captured single-actor queries (default: saved courtyard samples)')
args = parser.parse_args()
if not args.replay:
    args.replay=[Path(__file__).with_name('fixtures')/'e2-courtyard-steering.json']
live=[]
for path in args.replay:
    for q in json.loads(path.read_text()):
        assert q['actor_next']==0 and q['actor_head']==q['floors'][0]['actor'],path
        assert len(q['floors'])==7 and 'after' in q,path
        live.append(q)
live_inputs=[q['position']+[q['facing'],q['radius'],q['slot'],q['flags'],q['ticks'],
             q['state'],q['gravity'],q['actor_flags']]+q['angles']+q['vector'] for q in live]
live_floors=[[[*f['coord'],int(bool(f['actor'])),int(f['terrain']),f['floor'],f['surface']]
              for f in q['floors']] for q in live]
live_after=[q['after']+[q['after_facing']] for q in live]
def c_array(value):
    return '{'+','.join(c_array(v) if isinstance(v,list) else str(v) for v in value)+'}'
image = OriginalImage(args.exe)
original = image.code
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
def function(name):
    m = re.search(r'^(?:static )?(?:void|short|undefined4) (?:__fastcall )?' + name +
                  r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    assert m, name
    return m.group()
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint32_t uint,undefined4;
typedef uint16_t ushort,undefined2;
typedef uint8_t byte;
#define __fastcall
static int IsBadReadPtr(const void *p,unsigned n) { return !p || !n; }
static int E2R_IsBadWritePtr(void *p,unsigned n) { return !p || !n; }
static short DAT_0047a34a,DAT_0047a366,DAT_0047a368,DAT_0047a72c;
static uintptr_t _DAT_0063726c,_DAT_00637378;
static int replay_mode,replay_index;
LIVE_ARRAYS
struct Query { short coord[3]; int actor,terrain; };
static struct Query trace[8192],expected_trace[8192];
static int queries,pattern;
__attribute__((used,noinline)) static int FUN_00448a48(uint coord,int actor,int *terrain) {
    assert(queries<8192);
    short *p=(short*)coord;
    struct Query *q=&trace[queries++];
    memcpy(q->coord,p,6);q->actor=actor;q->terrain=terrain!=0;
    if(replay_mode) {
        assert(queries<=7);
        const int *record=live_floors[replay_index][queries-1];
        for(int i=0;i<3;i++)assert(p[i]==record[i]);
        assert(actor==(record[3]?0x900000:0) && (terrain!=0)==record[4]);
        if(terrain)*terrain=record[6];
        return record[5];
    }
    if(terrain) *terrain=pattern==7?7:0;
    int i=(queries-1)%7;
    // Perimeter samples cover either side of +/-256 and opposing blockers.
    static int heights[]={0,1,255,256,257,-255,-256,-257};
    int change=pattern<8?heights[pattern]:
        pattern==8?(i==1?300:0):pattern==9?(i==2?300:0):
        pattern==10?(i==1||i==2?300:0):pattern==11?(i>=3?-300:0):
        pattern==12?(i==0||i>=3?-300:0):pattern==13?(p[0]&1?300:0):
        pattern==14?((p[2]>>3)&1?-300:300):0;
    return 3328-change;
}
__attribute__((naked)) static void floor_hook(void) {
    __asm__("pushal; push %ebx; push %edx; push %eax; call FUN_00448a48; "
            "add $12,%esp; mov %eax,28(%esp); popal; ret");
}
void FUN_00448cb4(uint,short*);
'''
for name in ('FUN_00422368','FUN_00422460','FUN_00422538',
             'E2R_SetIdentityMatrix','E2R_ApplyEulerMatrix','FUN_0042b074',
             'E2R_PolygonAngle16','E2R_MotionPolar','E2R_MotionPolar16',
             'FUN_00448c1c','FUN_00448cb4'):
    harness += function(name) + '\n'
for start,end in ((0x422330,0x422628),(0x427214,0x4273cc),(0x42b074,0x42b0f4),
                  (0x432c64,0x432de4),(0x448c1c,0x4495de)):
    harness += f'static const byte code_{start:x}[]={{' + ','.join(map(str,original(start,end))) + '};\n'
harness += r'''
static void map(int address,int n) {
    assert(mmap((void*)address,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void hook(int address,void *fn) {
    *(byte*)address=0xe9;*(int*)(address+1)=(int)fn-address-5;
}
static void original_polar(int address,short *angle,short *distance,int x,int z) {
    __asm__ volatile("call *%%edi" : "+a"(angle),"+d"(distance),"+b"(x),"+c"(z)
                     : "D"(address) : "memory","cc");
}
static void original_query(int address) {
    int actor=0x900000,vector=0x906000;
    __asm__ volatile("call *%%edi" : "+a"(actor),"+d"(vector)
                     : "D"(address) : "ebx","ecx","memory","cc");
}
static const short vectors[][3]={{0,0,0},{1,0,0},{-1,0,0},{0,1,1},{0,-1,-1},
 {64,64,64},{-64,-64,-64},{31,0,-63},{-63,0,31},{63,0,31},{31,0,63},
 {65,0,0},{-65,0,0},{0,129,-129},{129,65,31},{-129,-65,-31}};
static void setup(int mode,int seed,int v,int collision) {
    memset((void*)0x900000,0,0x10000);memset(trace,0,sizeof trace);queries=0;
    DAT_0047a34a=*(short*)0x47a34a=mode==1||mode==2||mode==3;
    DAT_0047a366=*(short*)0x47a366=mode==3||mode==4;
    DAT_0047a368=*(short*)0x47a368=mode==1;
    DAT_0047a72c=*(short*)0x47a72c=mode==5;
    _DAT_0063726c=*(int*)0x63726c=collision?0x900200:0;
    _DAT_00637378=*(int*)0x637378=seed%4+1;
    for(int j=0;j<4;j++) {
        int actor=0x900000+j*0x200;
        *(short*)(actor+0x84)=9988+(j?((seed*53+j*37)%401-200):0);
        *(short*)(actor+0x86)=3328+(j?((seed*43+j*17)%501-250):0);
        *(short*)(actor+0x88)=-17408+(j?((seed*61+j*73)%401-200):0);
        *(short*)(actor+0x9a)=128+(seed%3)*64;
        *(short*)(actor+0x90)=seed*971;
        *(short*)(actor+0x92)=seed*3127;
        *(short*)(actor+0x94)=seed*271;
        *(byte*)(actor+0x146)=seed%5==0?2:0;
        *(short*)(actor+0x96)=(short[]){1,7,180,183,1000}[seed%5];
        *(short*)(actor+0x82)=(short[]){4,5,8,11}[seed%4];
        *(short*)(actor+0x5a)=seed%2?1:0;
        *(byte*)(actor+3)=j?0x10:seed%3==0?1:0;
        *(int*)(actor+0x4c)=j<3?actor+0x200:0;
        if(j&&collision==2) { *(int*)(actor+0xf2)=0x905000;*(int*)0x905022=0x900000; }
        E2R_ApplyEulerMatrix((short*)(actor+0xc6),(short*)(actor+0x90));
    }
    for(int i=0;i<3;i++) *(short*)(0x90008a+i*2)=30000-i;
    memcpy((void*)0x906000,vectors[v],6);
}
static void setup_live(int index) {
    setup(0,0,0,0);
    const int *p=live_inputs[index];
    for(int i=0;i<3;i++)*(short*)(0x900084+i*2)=p[i];
    *(short*)0x900092=p[3];*(short*)0x90009a=p[4];*(short*)0x900096=p[5];
    *(byte*)0x900146=p[6];_DAT_00637378=*(int*)0x637378=p[7];
    *(short*)0x900082=p[8];*(short*)0x90005a=p[9];*(byte*)0x900003=p[10];
    *(short*)0x900090=p[11];*(short*)0x900094=p[12];
    for(int i=0;i<3;i++)*(short*)(0x906000+i*2)=p[13+i];
    _DAT_0063726c=*(int*)0x63726c=0x900000;*(int*)0x90004c=0;
    E2R_ApplyEulerMatrix((short*)0x9000c6,(short*)0x900090);
    replay_index=index;
}
int main(void) {
    map(0x420000,0x10000);map(0x430000,0x10000);map(0x440000,0x10000);
    map(0x470000,0x10000);map(0x590000,0x80000);map(0x630000,0x10000);map(0x900000,0x10000);
'''
for start in (0x422330,0x427214,0x42b074,0x432c64,0x448c1c):
    harness += f'    memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
    hook(0x448a48,floor_hook);
    for(int i=0;i<65536;i++) {
        *(short*)(0x59b590+i*2)=(short)lrint(sin(i*6.283185307179586/65536)*16384);
        *(short*)(0x5de590+i*2)=(short)lrint(cos(i*6.283185307179586/65536)*16384);
    }
    for(int i=0;i<256;i++) {
        *(byte*)(0x5fe990+i)=(byte)(atan(i*0.015625)*64.0*2.0*0.3183101550488765+0.5);
        *(byte*)(0x5fe890+i)=(byte)(atan(i*0.25)*64.0*2.0*0.3183101550488765+0.5);
    }
    unsigned polar_cases=0,query_cases=0;
    int inputs[]={-65535,-32767,-16385,-16384,-8192,-65,-1,0,1,65,8192,16384,16385,32767,65535};
    for(int i=0;i<15;i++)for(int j=0;j<15;j++) {
        short a,d,ea,ed;
        original_polar(0x4272a8,&ea,&ed,inputs[i],inputs[j]);
        E2R_MotionPolar(&a,&d,inputs[i],inputs[j]);assert(a==ea&&d==ed);polar_cases++;
        if(abs(inputs[i])<=32767&&abs(inputs[j])<=32767) {
            original_polar(0x427214,&ea,&ed,inputs[i],inputs[j]);
            E2R_MotionPolar16(&a,&d,inputs[i],inputs[j]);assert(a==ea&&d==ed);polar_cases++;
        }
    }
    static byte expected[0x10000];
    for(int mode=0;mode<6;mode++)for(int seed=0;seed<20;seed++)
    for(int v=0;v<16;v++)for(int collision=0;collision<3;collision++)
    for(pattern=0;pattern<16;pattern++) {
        setup(mode,seed,v,collision);original_query(0x448c1c);
        memcpy(expected,(void*)0x900000,sizeof expected);
        int expected_queries=queries;memcpy(expected_trace,trace,sizeof trace);
        setup(mode,seed,v,collision);FUN_00448c1c(0x900000,(int*)0x906000);
        if(memcmp(expected,(void*)0x900000,sizeof expected)||queries!=expected_queries||
           memcmp(expected_trace,trace,sizeof trace)) {
            fprintf(stderr,"mismatch mode=%d seed=%d v=%d collision=%d pattern=%d queries=%d/%d\n",
                    mode,seed,v,collision,pattern,queries,expected_queries);
            for(int i=0;i<0x10000;i++) if(expected[i]!=*(byte*)(0x900000+i))
                fprintf(stderr," byte +%x expected=%02x actual=%02x\n",i,expected[i],*(byte*)(0x900000+i));
            for(int i=0;i<queries&&i<expected_queries;i++)if(memcmp(&trace[i],&expected_trace[i],sizeof trace[i]))
                fprintf(stderr," query %d expected=%d,%d,%d actor=%x terrain=%d actual=%d,%d,%d actor=%x terrain=%d\n",i,
                  expected_trace[i].coord[0],expected_trace[i].coord[1],expected_trace[i].coord[2],expected_trace[i].actor,expected_trace[i].terrain,
                  trace[i].coord[0],trace[i].coord[1],trace[i].coord[2],trace[i].actor,trace[i].terrain);
            abort();
        }
        query_cases++;
    }
    replay_mode=1;
    for(int i=0;i<LIVE_COUNT;i++) {
        setup_live(i);original_query(0x448cb4);
        assert(queries==7);
        for(int j=0;j<3;j++)assert(*(short*)(0x900084+j*2)==live_after[i][j]);
        assert(*(short*)0x900092==live_after[i][3]);
        memcpy(expected,(void*)0x900000,sizeof expected);
        setup_live(i);FUN_00448cb4(0x900000,(short*)0x906000);
        assert(queries==7 && !memcmp(expected,(void*)0x900000,sizeof expected));
    }
    printf("PASS: %u original-i386 polar output cases and %u split/query actor/height/obstacle cases; %u recorded courtyard replays (floor service intercepted)\n",polar_cases,query_cases,LIVE_COUNT);
}
'''
harness=harness.replace('LIVE_ARRAYS',
    'static const int live_inputs[][16]='+c_array(live_inputs or [[0]*16])+';\n'+
    'static const int live_floors[][7][7]='+c_array(live_floors or [[[0]*7]*7])+';\n'+
    'static const int live_after[][4]='+c_array(live_after or [[0]*4])+';\n').replace('LIVE_COUNT',str(len(live)))
run_fixture(harness, cc=args.cc, asan=args.asan, timeout=90, keep=args.keep_harness, libraries=('-lm',),
            image=image, dependencies=('deterministic terrain/floor service',))
