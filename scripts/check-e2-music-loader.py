#!/usr/bin/env python3
"""Compare the production music archive loader with original 0x4142e4."""
import argparse,json
from pathlib import Path
from e2_original import OriginalImage,function,run_fixture,support
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path)
p.add_argument('--asan',action='store_true')
p.add_argument('--keep-harness',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parent.parent
image=OriginalImage(a.exe)
h=support()+r'''
#include <assert.h>
#include <string.h>
#include <sys/mman.h>
typedef uint32_t undefined4,uint;typedef uint8_t byte;typedef uint64_t undefined8;typedef uint64_t longlong;
typedef void *HLOCAL;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
#define DAT_00479e3c (*(uint32_t*)0x479e3c)
#define DAT_0047ab10 (*(uint32_t*)0x47ab10)
#define DAT_00479dbc (*(uint32_t*)0x479dbc)
#define DAT_0047a724 (*(uint32_t*)0x47a724)
#define _DAT_006365d4 0
static undefined8 FUN_004142b8(int a,int b) {assert(0);return 0;}
static undefined4 E2R_OpenReadStream(char*p) {assert(0);return 0;}
static void LocalFree(void*p) {assert(0);}
static unsigned errors;
__attribute__((used,noinline,force_align_arg_pointer)) static undefined8 FUN_0043cac0(unsigned a,unsigned b) {errors++;return 0;}
__attribute__((naked,used)) static void error_hook(void) {__asm__("pushal; push %edx; push %eax; call FUN_0043cac0; add $8,%esp; popal; ret");}
static unsigned registered_bytes;static int registered_id;
static void E2R_MusicData(void*p,unsigned n,int id) {registered_bytes=n;registered_id=id;}
__attribute__((naked,used)) static void noop_hook(void) {__asm__("ret");}
static unsigned char buffer[50000],expected[50000];
static unsigned stream[7];
static void map(unsigned a,unsigned n) {assert(mmap((void*)a,n,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)a);}
static void jump(unsigned a,void*p) {*(byte*)a=0xe9;*(unsigned*)(a+1)=(uintptr_t)p-a-5;}
__attribute__((used,noinline,force_align_arg_pointer)) static void seek(unsigned *s,unsigned off) {s[0]=s[5]+off;s[1]=s[2]-s[0];}
__attribute__((used,noinline,force_align_arg_pointer)) static unsigned word(unsigned*s) {assert(s[1]>=4);byte*p=(void*)s[0];s[0]+=4;s[1]-=4;return p[0]<<24|p[1]<<16|p[2]<<8|p[3];}
__attribute__((used,noinline,force_align_arg_pointer)) static unsigned readbyte(unsigned*s) {assert(s[1]);s[1]--;return *(byte*)s[0]++;}
__attribute__((naked,used)) static void seek_hook(void) {__asm__("pushal; push %edx; push %eax; call seek; add $8,%esp; popal; ret");}
__attribute__((naked,used)) static void word_hook(void) {__asm__("pushal; push %eax; call word; add $4,%esp; mov %eax,28(%esp); popal; ret");}
__attribute__((naked,used)) static void byte_hook(void) {__asm__("pushal; push %eax; call readbyte; add $4,%esp; mov %eax,28(%esp); popal; ret");}
__attribute__((used)) static unsigned original_entry=0x4142e4;
__attribute__((naked,used)) static unsigned original_load(unsigned id) {__asm__("mov 4(%esp),%eax; call *original_entry; ret");}
'''
h+=function((root/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text(),'FUN_004142e4')+'\n'
h+='static unsigned char code[]={'+','.join(map(str,image.code(0x4142e4,0x41468e)))+'};\n'
h+=r'''
int main(void) {
 map(0x410000,0x10000);map(0x430000,0x10000);map(0x440000,0x10000);map(0x450000,0x10000);map(0x470000,0x10000);map(0x640000,0x10000);
 memcpy((void*)0x4142e4,code,sizeof code);jump(0x45f296,seek_hook);jump(0x441444,word_hook);jump(0x45f38a,byte_hook);jump(0x45f0a1,noop_hook);jump(0x43cac0,error_hook);
 FILE*f=fopen(ARCHIVE,"rb"),*index=fopen(INDEX,"rb");assert(f&&index);fseek(f,0,SEEK_END);unsigned size=ftell(f);rewind(f);
 byte*data=malloc(size);assert(data&&fread(data,1,size,f)==size);
 stream[5]=(uintptr_t)data;stream[2]=(uintptr_t)data+size;DAT_0047a724=(uintptr_t)stream;DAT_0047ab10=1;DAT_00479e3c=(uintptr_t)buffer;
 fseek(index,(2500+5000+2000+500+700)*4,SEEK_SET);
 for(unsigned i=0;i<960;i++){byte b[4];assert(fread(b,1,4,index)==4);*(unsigned*)(0x6458a8+i*4)=b[0]<<24|b[1]<<16|b[2]<<8|b[3];}
 unsigned cases=0,loaded=0,missing=0;
 for(unsigned device=1;device<=10;device++)for(unsigned id=1;id<=96;id++){
  DAT_00479dbc=device;memset(buffer,0xcc,sizeof buffer);seek(stream,0);errors=0;unsigned result=original_load(id);unsigned original_errors=errors;
  memcpy(expected,buffer,sizeof buffer);unsigned cursor=stream[0],remaining=stream[1];
  memset(buffer,0xcc,sizeof buffer);seek(stream,0);registered_bytes=0;registered_id=0;errors=0;
  assert((unsigned)FUN_004142e4(id,0)==result);assert(errors==original_errors);
  assert(!memcmp(buffer,expected,sizeof buffer));assert(stream[0]==cursor&&stream[1]==remaining);
  int offset=*(int*)(0x6458a4+(device-1)*384+id*4);
  if(offset<0){assert(!registered_bytes);missing++;}else if(word((unsigned[]){(uintptr_t)data+offset,4})>48000){assert(!registered_bytes&&!result);}else{assert(registered_id==id&&registered_bytes==word((unsigned[]){(uintptr_t)data+offset,4}));loaded++;}
  cases++;
 }
 printf("PASS: %u original archive loader cases, %u loaded resources, %u preserved missing-offset buffers; exact bytes, length and stream cursor\n",cases,loaded,missing);
}
'''.replace('ARCHIVE',json.dumps(str(a.exe.parent/'Files/ECSTATIC'))).replace('INDEX',json.dumps(str(a.exe.parent/'OFFSETS')))
run_fixture(h,asan=a.asan,keep=a.keep_harness,image=image,dependencies=('file opening/allocation excluded; seek and byte/BE32 reads intercepted',))
