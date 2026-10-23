#!/usr/bin/env python3
"""Exercise production requester text copying and empty-message fallback."""
import argparse
from pathlib import Path
from e2_original import function,run_fixture
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--asan',action='store_true');a=p.parse_args()
source=Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness=r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
#include <sys/uio.h>
#include <unistd.h>
typedef uint32_t undefined4,uint;typedef uint64_t undefined8,ulonglong;typedef uint8_t undefined1;
#define __fastcall
#define CONCAT44(a,b) (((uint64_t)(uint32_t)(a)<<32)|(uint32_t)(b))
static uint32_t DAT_0047a45e;
#define E2R_WORD_AT(value,offset) (*(short*)((char*)&value+offset))
static int IsBadReadPtr(const void *p,unsigned n){char byte;struct iovec local={&byte,1},remote={(void*)p,1};return n && process_vm_readv(getpid(),&local,1,&remote,1,0)!=1;}
static void E2R_InitRequesterRecord(uintptr_t first,...){(void)first;}
static void E2R_InitRequesterItem(uintptr_t first,...){(void)first;}
static int observed;
static void LAB_0043c594(void){}
static void E2R_InspectObserve(const char *kind,int64_t id,int64_t lines){assert(!strcmp(kind,"requester") && id==0x2e && lines>0);observed++;}
static undefined8 FUN_0043b384(undefined4 address,undefined4 unused){assert(address==0x47a630);assert(*(char*)0x64403a);return 0;}
'''
for name in ('E2R_IsReadableCString','E2R_ResolveMenuStringList','FUN_0043cbf0'):harness+=function(source,name)+'\n'
harness+=r'''
int main(void){
 assert(mmap((void*)0x470000,0x10000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x470000);
 assert(mmap((void*)0x640000,0x10000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x640000);
 undefined4 empty[]={0};
 FUN_0043cbf0(0,0);assert(strstr((char*)0x64403a,"Internal game error"));
 FUN_0043cbf0((uintptr_t)empty,0);assert(strstr((char*)0x64403a,"Internal game error"));
 const char *lines[]={"Normal title","Normal details",0};
 FUN_0043cbf0((uintptr_t)lines,0);assert(!strcmp((char*)0x64403a,lines[0]));assert(!strcmp((char*)0x64406d,lines[1]));
 assert(observed==3);puts("PASS: null/empty requesters show readable error text; valid lines and modal observations retained");
}
'''
run_fixture(harness,asan=a.asan)
