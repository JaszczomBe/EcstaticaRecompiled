#!/usr/bin/env python3
"""Compare original 0x458e7c PCM and playback calls, and original sound pool allocation."""
import argparse
from pathlib import Path
import struct
from e2_original import OriginalImage, function, run_fixture, support

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('exe', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--keep-harness', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parent.parent
image = OriginalImage(a.exe)
source = (root/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
h = support() + r'''
#include <assert.h>
#include <string.h>
#include <sys/mman.h>
typedef int code();typedef unsigned short ushort;typedef unsigned undefined4,uint;typedef unsigned char byte;
typedef unsigned long long undefined8;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define DAT_0047d1f0 (*(unsigned*)0x47d1f0)
#include "AUDIO_HEADER"
static int *E2R_fan_parse_stream;
__attribute__((used,noinline,force_align_arg_pointer)) static int E2R_ReadFanWordByte(int *s) {
    assert(s[1]>0);unsigned char *c=(void*)s[0];s[0]++;s[1]--;return *c;
}
static int failures;
static int FUN_0043cbb4(int x) {assert(0);return 0;}
static int FUN_0043cac0(int a,int b) {assert(0);return 0;}
static int FUN_0043cbd0(int x) {assert(0);return 0;}
static int *fake_vt[21],**fake_buffer=fake_vt;
static void *device_vt[11],**fake_device=device_vt;
static unsigned char pcm[1024*1024],expected[1024*1024];
static E2R_WaveFormat format;
static unsigned count,volume,pan,status,position,play_count,stop_count,release_count,create_count;
static int status_error;
static unsigned sound_node[15];
static int create(void *self,E2R_SoundDesc *desc,void **out,void *outer) {
    assert(self==&fake_device&&!outer&&desc->size==20&&desc->flags==0xe2);
    format=*desc->format;count=desc->bytes;assert(count<=sizeof pcm);create_count++;
    *out=&fake_buffer;return 0;
}
static int lock(void *self,unsigned offset,unsigned bytes,void **one,unsigned *n1,void **two,unsigned *n2,unsigned flags) {
    assert(self==&fake_buffer&&!offset&&bytes==count&&!flags);
    *one=pcm;*n1=count;*two=0;*n2=0;return 0;
}
static int unlock(void *self,void *one,unsigned n1,void *two,unsigned n2) {
    assert(self==&fake_buffer&&one==pcm&&n1==count&&!two&&!n2);return 0;
}
static int caps(void *self,unsigned *out) {assert(out[0]==20);out[1]=8;return 0;}
static int vol(void *self,int value) {volume=value;return 0;}
static int balance(void *self,int value) {pan=value;return 0;}
static int get_status(void *self,unsigned *out) {*out=status;return status_error;}
static int pos(void *self,unsigned value) {assert(!value);position++;return 0;}
static int play(void *self,unsigned reserved,unsigned priority,unsigned flags) {
    assert(!reserved&&!priority&&!flags);play_count++;return 0;
}
static int release(void *self) {release_count++;return 0;}
static int stop(void *self) {stop_count++;return 0;}
#define WRAP(name,args,call) static int __attribute__((stdcall)) name##_win args {return name call;}
WRAP(create,(void*a,E2R_SoundDesc*b,void**c,void*d),(a,b,c,d))
WRAP(lock,(void*a,unsigned b,unsigned c,void**d,unsigned*e,void**f,unsigned*g,unsigned i),(a,b,c,d,e,f,g,i))
WRAP(unlock,(void*a,void*b,unsigned c,void*d,unsigned e),(a,b,c,d,e))
WRAP(caps,(void*a,unsigned*b),(a,b))
WRAP(vol,(void*a,int b),(a,b))
WRAP(balance,(void*a,int b),(a,b))
WRAP(get_status,(void*a,unsigned*b),(a,b))
WRAP(pos,(void*a,unsigned b),(a,b))
WRAP(play,(void*a,unsigned b,unsigned c,unsigned d),(a,b,c,d))
WRAP(release,(void*a),(a))
WRAP(stop,(void*a),(a))
static void vtables(int win) {
    device_vt[3]=win?(void*)create_win:(void*)create;
    fake_vt[2]=win?(void*)release_win:(void*)release;
    fake_vt[3]=win?(void*)caps_win:(void*)caps;
    fake_vt[9]=win?(void*)get_status_win:(void*)get_status;
    fake_vt[11]=win?(void*)lock_win:(void*)lock;
    fake_vt[12]=win?(void*)play_win:(void*)play;
    fake_vt[13]=win?(void*)pos_win:(void*)pos;
    fake_vt[15]=win?(void*)vol_win:(void*)vol;
    fake_vt[16]=win?(void*)balance_win:(void*)balance;
    fake_vt[18]=win?(void*)stop_win:(void*)stop;
    fake_vt[19]=win?(void*)unlock_win:(void*)unlock;
    DAT_0047d1f0=(unsigned)&fake_device;
}
__attribute__((naked,used)) static void zero_hook(void) {
    __asm__("pushal; push %ebx; push %edx; push %eax; call memset; add $12,%esp; popal; ret");
}
__attribute__((naked,used)) static void byte_hook(void) {
    __asm__("pushal; push %eax; call E2R_ReadFanWordByte; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
static int reclaimed;
static unsigned char pool_expected[12000];
static undefined8 FUN_004531bc(int a,int b) {assert(0);return 0;}
static void FUN_00414e68(void) {assert(0);}
static void map(unsigned at,unsigned bytes) {
    assert(mmap((void*)at,bytes,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);
}
static void jump(unsigned at,void *target) {
    *(byte*)at=0xe9;*(unsigned*)(at+1)=(unsigned)target-at-5;
}
'''.replace('AUDIO_HEADER', str(root/'E2Recomp/platform/e2recomp_audio.h'))
h += r'''
#define DAT_0047a4a0 (*(int*)0x47a4a0)
#define DAT_00479dd0 (*(int*)0x479dd0)
#define DAT_0047a470 (*(int*)0x47a470)
static int requested,dispatched,arguments[4],polar_inputs[2],polar_distance;
__attribute__((used)) static int channel_value;
__attribute__((used)) static unsigned original_event=0x42fce0;
static int FUN_0042fc84(int a,int b) {return 7;}
static void FUN_00451a54(int a,int sound) {requested=sound;}
__attribute__((used,noinline,force_align_arg_pointer)) static void FUN_00413ea4(int resource,int close,int volume,int channel) {
    dispatched++;int row[]={resource,close,volume,channel};memcpy(arguments,row,sizeof row);
}
__attribute__((used,noinline,force_align_arg_pointer)) static void E2R_NpcPolar16(short *angle,short *distance,short x,short z) {
    *angle=0;*distance=polar_distance;polar_inputs[0]=x;polar_inputs[1]=z;
}
__attribute__((naked,used)) static void polar_hook(void) {
    __asm__("pushal; push %ecx; push %ebx; push %edx; push %eax; call E2R_NpcPolar16; add $16,%esp; popal; ret");
}
__attribute__((naked,used)) static void dispatch_hook(void) {
    __asm__("pushal; push %ecx; push %ebx; push %edx; push %eax; call FUN_00413ea4; add $16,%esp; popal; ret");
}
__attribute__((naked,used)) static void request_hook(void) {
    __asm__("mov %eax,requested; ret");
}
__attribute__((naked,used)) static void remap_hook(void) {__asm__("mov $7,%eax; ret");}
__attribute__((naked,used)) static void event_call(void) {
    __asm__("push channel_value; call *original_event; ret");
}
'''
h += function(source, 'FUN_0042fce0')+'\n'
h += function(source, 'FUN_00458e7c')+'\n'
h += function(source, 'FUN_00458c24')+'\n'
h += function(source, 'FUN_004537d8')+'\n'
h += r'''
typedef unsigned short undefined2;typedef unsigned long long ulonglong;
static void FUN_00414e5c(int x) {assert(0);}
static int IsBadReadPtr(const void *p,unsigned n) {return !p;}
#define _DAT_00637258 (*(short**)0x637258)
#define DAT_00479e44 (*(int*)0x479e44)
__attribute__((naked,used)) static void name_hook(void) {__asm__("mov $0,%eax; ret");}
__attribute__((naked,used)) static void noop_hook(void) {__asm__("ret");}
'''
for name in ('FUN_00458bec','FUN_004537bc','FUN_00452994'):
    h += function(source,name)+'\n'

for start,end in ((0x44248c,0x442490),(0x452994,0x452a56),(0x458bec,0x458c24),(0x4537bc,0x4537d8),(0x42fce0,0x42fe5e),(0x458c24,0x458d18),(0x458e7c,0x4590c0),(0x4537d8,0x453841)):
    h += 'static unsigned char code_'+hex(start)[2:]+'[]={'+','.join(map(str,image.code(start,end)))+'};\n'
h += r'''
int main(void) {
    map(0x420000,0x10000);map(0x410000,0x4000);map(0x620000,0x20000);map(0x450000,0x10000);map(0x470000,0x10000);map(0x730000,0x10000);
    map(0x440000,0x10000);
    memcpy((void*)0x452994,code_452994,sizeof code_452994);
    memcpy((void*)0x458bec,code_458bec,sizeof code_458bec);
    memcpy((void*)0x4537bc,code_4537bc,sizeof code_4537bc);
    jump(0x44248c,name_hook);jump(0x45f0a1,noop_hook);
    memcpy((void*)0x42fce0,code_42fce0,sizeof code_42fce0);
    jump(0x427160,polar_hook);jump(0x413ea4,dispatch_hook);
    jump(0x451a54,request_hook);jump(0x42fc84,remap_hook);
    memcpy((void*)0x458c24,code_458c24,sizeof code_458c24);
    memcpy((void*)0x458e7c,code_458e7c,sizeof code_458e7c);
    memcpy((void*)0x4537d8,code_4537d8,sizeof code_4537d8);
    jump(0x45f8d0,zero_hook);jump(0x45f38a,byte_hook);
    FILE *archive=fopen(ARCHIVE,"rb"),*index=fopen(INDEX,"rb");assert(archive&&index);
    unsigned assets=0;unsigned long bytes=0;
    for(unsigned id=0;id<700;id++) {
        unsigned char entry[4];assert(!fseek(index,(2500+5000+2000+500)*4+id*4,SEEK_SET));
        assert(fread(entry,1,4,index)==4);
        unsigned offset=entry[0]<<24|entry[1]<<16|entry[2]<<8|entry[3];
        if(offset==0xffffffffu)continue;
        assert(!(offset&0x80000000u));
        unsigned char header[89];assert(!fseek(archive,offset,SEEK_SET));assert(fread(header,1,89,archive)==89);
        assert(!memcmp(header,"FANT",4)&&header[76]=='S');
        unsigned length=header[83]|header[84]<<8|header[85]<<16|header[86]<<24;
        /* Flags/rate precede the little-endian length at byte 83. */
        assert(length>=32&&length<=sizeof pcm);
        unsigned char *data=malloc(length);assert(data);
        assert(!fseek(archive,offset+89,SEEK_SET));assert(fread(data,1,length,archive)==length);
        unsigned char result_header[32];E2R_WaveFormat expected_format;
        for(int original=1;original>=0;original--) {
            vtables(original);memset(sound_node,0,sizeof sound_node);
            sound_node[3]=length-32;
            E2R_WaveFormat f={1,1,22050,22050,1,8,0};
            unsigned context[106]={0,length-32,(unsigned)&f};
            int stream[7]={(unsigned)data,(int)length,0,0x40};
            memset(pcm,0x35,sizeof pcm);
            if(original) {
                struct E2R_Registers r={(unsigned)context,(unsigned)sound_node,(unsigned)stream};
                e2r_original_call(0x458e7c,&r);assert(!r.eax);
                memcpy(expected,pcm,count);memcpy(result_header,(byte*)sound_node+24,32);expected_format=format;
            } else {
                assert(!FUN_00458e7c((unsigned)context,(unsigned)sound_node,(unsigned)stream));
                assert(e2r_memory_equal("original PCM",expected,pcm,count));
                assert(e2r_memory_equal("original header",result_header,(byte*)sound_node+24,32));
                assert(!memcmp(&format,&expected_format,16));
                for(unsigned j=0;j<count;j++)assert(pcm[j]==(byte)(data[j+32]+128));
            }
            assert(stream[1]==0&&context[9]==0&&sound_node[2]==(unsigned)pcm);
        }
        bytes+=length-32;assets++;free(data);
    }
    fclose(archive);fclose(index);
    for(unsigned st=0;st<4;st++)for(int err=0;err<2;err++)for(int v=0;v<=127;v++) {
        unsigned expect_volume=0,expect_position=0,expect_play=0;
        for(int original=1;original>=0;original--) {
            vtables(original);sound_node[14]=(unsigned)&fake_buffer;
            status=st;status_error=err;position=play_count=0;
            if(original) {
                struct E2R_Registers r={(unsigned)sound_node,v};e2r_original_call(0x458c24,&r);
                expect_volume=volume;expect_position=position;expect_play=play_count;
            } else {
                FUN_00458c24((unsigned)sound_node,v);
                assert(volume==expect_volume&&position==expect_position&&play_count==expect_play);
            }
            assert((int)volume==(v-127)*50);
        }
    }
    unsigned event_cases=0;
    unsigned char player[256]={0},owner[256]={0},node[64]={0};
    DAT_0047a470=(unsigned)player;
    *(short*)(player+0x84)=100;*(short*)(player+0x86)=200;*(short*)(player+0x88)=-300;
    *(short*)(owner+0x84)=2000;*(short*)(owner+0x86)=-1800;*(short*)(owner+0x88)=3000;
    *(unsigned*)(0x62d960+7*4)=(unsigned)sound_node;
    int distances[]={0,63,1024,8191,8192,32767,-32768,32000};
    int percents[]={-10,0,75,100,101};
    int overrides[]={0,1,64,127};
    for(int gate=0;gate<4;gate++)for(int kind=0;kind<3;kind++)
    for(int near=0;near<2;near++)for(int v=0;v<4;v++)
    for(int percent=0;percent<5;percent++)for(int distance=0;distance<8;distance++) {
        DAT_0047a4a0=gate&1;DAT_00479dd0=gate&2;
        *(unsigned*)(node+0x22)=(unsigned)(kind==1?player:owner);
        *(short*)((byte*)sound_node+22)=percents[percent];polar_distance=distances[distance];
        int expected_args[4],expected_polar[2],expected_dispatched=0,expected_requested=0;
        for(int original=1;original>=0;original--) {
            dispatched=requested=0;memset(arguments,0,sizeof arguments);memset(polar_inputs,0,sizeof polar_inputs);
            int nod=kind?(unsigned)node:0;channel_value=5;
            if(original) {
                struct E2R_Registers r={0,nod,near,overrides[v]};
                e2r_original_call((unsigned)event_call,&r);
                memcpy(expected_args,arguments,sizeof arguments);memcpy(expected_polar,polar_inputs,sizeof polar_inputs);
                expected_dispatched=dispatched;expected_requested=requested;
            } else {
                FUN_0042fce0(0,nod,near,overrides[v],5);
                assert(dispatched==expected_dispatched&&requested==expected_requested);
                assert(!memcmp(arguments,expected_args,sizeof arguments));
                assert(!memcmp(polar_inputs,expected_polar,sizeof polar_inputs));
            }
        }
        event_cases++;
    }
    for(unsigned slot=0;slot<200;slot++) {
        memset((void*)0x73ccbc,0x31,12000);
        *(unsigned short*)(0x73ccbc+slot*60+6)=0x8000;
        struct E2R_Registers r={0};e2r_original_call(0x4537d8,&r);
        assert(r.eax==0x73ccbc+slot*60);memcpy(pool_expected,(void*)0x73ccbc,12000);
        memset((void*)0x73ccbc,0x31,12000);*(unsigned short*)(0x73ccbc+slot*60+6)=0x8000;
        assert((unsigned)FUN_004537d8(0,0)==r.eax);
        assert(e2r_memory_equal("original pool slot",pool_expected,(void*)0x73ccbc,12000));
    }
    for(unsigned removed=0;removed<3;removed++) {
        unsigned char expected_pool[180],expected_table[12];int expected_total=0,expected_head=0;
        for(int original=1;original>=0;original--) {
            memset((void*)0x73ccbc,0,180);vtables(original);release_count=stop_count=0;
            for(unsigned i=0;i<3;i++) {
                unsigned node=0x73ccbc+i*60;
                *(short*)node=i;*(unsigned*)(node+2)=i<2?node+60:0;
                *(unsigned*)(node+12)=100;*(unsigned*)(node+56)=(unsigned)&fake_buffer;
                *(unsigned*)(0x62d960+i*4)=node;
            }
            _DAT_00637258=(short*)0x73ccbc;DAT_00479e44=300;
            if(original) {
                struct E2R_Registers r={0x73ccbc+removed*60};e2r_original_call(0x452994,&r);
                memcpy(expected_pool,(void*)0x73ccbc,180);memcpy(expected_table,(void*)0x62d960,12);
                expected_head=(int)_DAT_00637258;expected_total=DAT_00479e44;
            } else {
                FUN_00452994(0x73ccbc+removed*60,0);
                assert(e2r_memory_equal("original sound cleanup",expected_pool,(void*)0x73ccbc,180));
                assert(!memcmp(expected_table,(void*)0x62d960,12));
                assert(expected_head==(int)_DAT_00637258&&expected_total==DAT_00479e44);
            }
            assert(release_count==1&&stop_count==1&&DAT_00479e44==200);
        }
    }
    printf("PASS: %u original resources, %lu PCM bytes; 1024 volume/status/retrigger comparisons; %u event attenuation/gate cases; 200 original pool slots; head/middle/tail cleanup\n",assets,bytes,event_cases);
}
'''
h = h.replace('ARCHIVE', '"'+str(a.exe.resolve().parent/'Files/ECSTATIC')+'"').replace('INDEX', '"'+str(a.exe.resolve().parent/'OFFSETS')+'"')
run_fixture(h, asan=a.asan, keep=a.keep_harness, image=image,
            dependencies=('DirectSound vtable call capture', 'memset', 'binary stream getc'))
