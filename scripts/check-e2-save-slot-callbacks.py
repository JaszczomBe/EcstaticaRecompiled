#!/usr/bin/env python3
"""Compare original slot selection/edit-confirm callbacks; all save dispatches are intercepted."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
image = OriginalImage(args.exe)
source = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint32_t uint,undefined4;typedef uint64_t undefined8;
#define WORD(a) (*(int *)(a))
#define _DAT_0064353c WORD(0x64353c)
#define _DAT_00643644 WORD(0x643644)
static unsigned previews,writes,last_slot,preview_valid;
static char written_label[26];
__attribute__((used,noinline)) static unsigned preview(unsigned slot) { previews++;last_slot=slot;return preview_valid; }
static undefined8 FUN_0043c1b8(uint slot,uint unused) { return preview(slot); }
__attribute__((used,noinline)) static unsigned writer(uint slot,const char *label) { writes++;last_slot=slot;memcpy(written_label,label,26);return 0; }
static undefined8 FUN_00453920(uint slot,char *label) { return writer(slot,label); }
static uintptr_t FUN_0043aeac(void) { return 0; }
static void FUN_0043b9bc(uint record,short *item) { assert(!"Drawing excluded"); }
'''
harness += support() + function(source,'E2R_SelectRequesterSlot') + '\n'
code=image.code(0x43fadc,0x43fc2b)
harness += 'static const byte code[]={' + ','.join(map(str,code)) + '};\n'
harness += r'''
__attribute__((naked)) static void preview_hook(void) { __asm__("pushal; push %eax; call preview; add $4,%esp; mov %eax,28(%esp); popal; ret"); }
__attribute__((naked)) static void writer_hook(void) { __asm__("pushal; push %edx; push %eax; call writer; add $8,%esp; mov %eax,28(%esp); popal; ret"); }
__attribute__((naked)) static void requester_hook(void) { __asm__("xor %eax,%eax; ret"); }
static void hook(uint address,void *target) { *(byte *)address=0xe9;WORD(address+1)=(uint)target-address-5; }
static void seed(unsigned slot,unsigned confirmed) {
    memset((void *)0x642000,0xcc,0x3000);
    for(unsigned i=0;i<10;i++) {
        memset((void *)(0x643540+i*26),0,26);snprintf((char *)(0x643540+i*26),26,"Label %u",i);
        memset((void *)(0x643434+i*26),0,26);snprintf((char *)(0x643434+i*26),26,"Edited %u",i);
    }
    WORD(0x6443d0)=slot<<16;_DAT_00643644=confirmed;
    previews=writes=0;last_slot=~0u;memset(written_label,0,sizeof written_label);
}
int main(void) {
    assert(mmap((void *)0x430000,0x10000,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)0x430000);
    assert(mmap((void *)0x450000,0x10000,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)0x450000);
    assert(mmap((void *)0x640000,0x10000,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)0x640000);
    memcpy((void *)0x43fadc,code,sizeof code);hook(0x43c1b8,preview_hook);hook(0x43aeac,requester_hook);hook(0x453920,writer_hook);
    byte expected[0x3000];unsigned cases=0;
    for(unsigned save=0;save<2;save++)for(unsigned confirmed=0;confirmed<2;confirmed++)
    for(preview_valid=0;preview_valid<2;preview_valid++)for(unsigned slot=0;slot<10;slot++) {
        seed(slot,confirmed);struct E2R_Registers regs={0};e2r_original_call(save ? 0x43fb58 : 0x43fadc,&regs);
        memcpy(expected,(void *)0x642000,sizeof expected);
        unsigned expected_previews=previews,expected_writes=writes,expected_slot=last_slot;char expected_label[26];memcpy(expected_label,written_label,26);
        seed(slot,confirmed);E2R_SelectRequesterSlot(save,slot,confirmed);
        assert(e2r_memory_equal("slot callback fields",expected,(void *)0x642000,sizeof expected));
        assert(previews==expected_previews && writes==expected_writes && last_slot==expected_slot && !memcmp(written_label,expected_label,26));cases++;
    }
    printf("PASS: %u original-x86 slot selection, editable-label, empty-preview, highlight and confirmed-writer dispatch cases; file writes intercepted\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('original preview/writer/requester intercepted; all writes captured in memory',))
