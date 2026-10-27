#!/usr/bin/env python3
"""Exercise actual hosted write/close ownership at high i386 addresses in private storage."""
import argparse
from pathlib import Path
from e2_original import function, run_fixture

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asan',action='store_true')
parser.add_argument('--keep-harness',type=Path)
args=parser.parse_args()
source=Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness=r'''
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint32_t uint,undefined4,DWORD;
typedef uint64_t undefined8,ulonglong;typedef void *HANDLE,*HLOCAL;typedef int code();
#define __fastcall
#define INVALID_HANDLE_VALUE ((HANDLE)(intptr_t)-1)
#define E2R_STREAM_MAGIC 0xe25eed01u
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
static uintptr_t E2R_hosted_streams[1024];static int *E2R_fan_parse_stream;
static uint *live[128];static unsigned frees,closes,allocations,fail_open,fail_write,fail_close;
static uint * _DAT_00ac520c;static code *PTR_FUN_0047d3b0,*PTR_FUN_0047d3b4;
static void *LocalAlloc(unsigned flags,unsigned bytes) {
    assert(allocations<128 && bytes<=4096);unsigned slot=allocations++;
    void *p=mmap((void *)(0x71000000u+slot*0x10000u),4096,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    assert(p!=(void *)-1);live[slot]=p;return p;
}
static void LocalFree(void *p) {
    for(unsigned i=0;i<allocations;i++)if(live[i]==p){assert(!munmap(p,4096));live[i]=NULL;frees++;return;}
    assert(!"Free of an unowned stream");
}
static int IsBadReadPtr(const void *p,unsigned n) {
    for(unsigned i=0;i<allocations;i++)if(live[i] && (uintptr_t)p>=(uintptr_t)live[i] && (uintptr_t)p+n<=(uintptr_t)live[i]+4096)return 0;
    return 1;
}
static HANDLE CreateFileA(const char *path,unsigned access,unsigned share,void *security,unsigned creation,unsigned flags,void *template) {
    assert(access==0x40000000u && creation==2);
    return fail_open ? INVALID_HANDLE_VALUE : fopen(path,"wb");
}
static int WriteFile(HANDLE handle,const void *p,unsigned n,unsigned *written,void *overlapped) {
    *written=0;if(fail_write)return 0;*written=fwrite(p,1,n,handle);return *written==n;
}
static int CloseHandle(HANDLE handle) { closes++;return !fclose(handle) && !fail_close; }
static uint FUN_0045eca5(uint a,int b) { assert(!"Legacy CRT stream reached");return 1; }
'''
for name in ('E2R_RegisterHostedStream','E2R_UnregisterHostedStream','E2R_OpenWriteStream',
             'E2R_WriteHostedStreamByte','FUN_0045ec6c'):
    harness+=function(source,name)+'\n'
harness+=r'''
int main(void) {
    char root[]="/tmp/e2-save-streams-XXXXXX";assert(mkdtemp(root));assert(!chdir(root));
    uint *stream=(uint *)E2R_OpenWriteStream("0005.ECS");assert(stream && (uint)stream>=0x70000000u);
    for(unsigned i=0;i<256;i++)assert(E2R_WriteHostedStreamByte(stream,i)==i);
    assert((uint)FUN_0045ec6c(0,(uint)stream)==0 && frees==1 && closes==1);
    assert((uint)FUN_0045ec6c(0,(uint)stream)==0xffffffffu);
    FILE *f=fopen("0005.ECS","rb");assert(f);for(unsigned i=0;i<256;i++)assert(fgetc(f)==i);assert(fgetc(f)==EOF);fclose(f);
    for(unsigned failure=0;failure<2;failure++) {
        stream=(uint *)E2R_OpenWriteStream("0005.ECS");assert(stream);
        fail_write=failure==0;fail_close=failure==1;
        if(fail_write)assert(E2R_WriteHostedStreamByte(stream,42)==-1);
        assert((uint)FUN_0045ec6c(0,(uint)stream)==0xffffffffu);
        fail_write=fail_close=0;
    }
    fail_open=1;assert(!E2R_OpenWriteStream("0005.ECS"));fail_open=0;
    stream=LocalAlloc(0,28);stream[6]=E2R_STREAM_MAGIC;stream[5]=(uint)LocalAlloc(0,128);assert(E2R_RegisterHostedStream(stream));
    E2R_fan_parse_stream=(int *)stream;
    assert((uint)FUN_0045ec6c(0,(uint)stream)==0 && !E2R_fan_parse_stream);
    assert(frees==5 && closes==3);
    assert(!unlink("0005.ECS"));assert(!chdir("/tmp"));assert(!rmdir(root));
    puts("PASS: actual high-address hosted binary writes/read-close ownership, byte preservation, double-close rejection, sticky write error, close failure and parser-context release");
}
'''
run_fixture(harness,asan=args.asan,keep=args.keep_harness,
            dependencies=('production hosted stream lifecycle; binary host I/O in a private temporary directory',))
