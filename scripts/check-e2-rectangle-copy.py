#!/usr/bin/env python3
"""Compare dirty-rectangle copies and surface ownership with original i386 code.

Runs original dispatch/copy/lock/unlock instructions from E2WIN95.EXE with mock
COM surfaces and port/CRT hooks. Compares bytes, padding and lock/restore/unlock
calls against recovered C. Requires Clang -m32 and Linux/i386 execution.
"""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
sections = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(sections):
        off = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, off + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(f'Unmapped original range {start:x}..{end:x}')


source = (Path(__file__).resolve().parent.parent /
          'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
functions = []
for name in ('FUN_00418a04', 'FUN_00418b00', 'FUN_0045cf10',
             'FUN_0045cf23', 'FUN_00418514', 'FUN_00418484'):
    match = re.search(r'(?:void|undefined[2468]) (?:__fastcall )?' + name +
                      r'\([^\n]*\)\s*\{.*?\n\}', source, re.S)
    if not match:
        raise ValueError(f'Missing recovered function {name}')
    functions.append(match.group())

harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint8_t byte, undefined1;
typedef uint16_t undefined2;
typedef uint32_t uint, undefined4;
typedef uint64_t undefined6;
typedef int code();
#define __fastcall
#define DAT_0047a43c (*(uint*)0x47a43c)
#define DAT_0047a279 (*(uint*)0x47a279)
#define DAT_00477060 (*(uint*)0x477060)
#define DAT_0047d0cc (*(uint*)0x47d0cc)
#define DAT_0047d0d0 (*(uint*)0x47d0d0)
#define _DAT_00636158 (*(uint*)0x636158)
#define _DAT_0063615c (*(uint*)0x63615c)
#define _DAT_006401ec (*(uint*)0x6401ec)
#define _DAT_006401d4 (*(uint*)0x6401d4)
static int E2R_IsBadWritePtr(const void *p, unsigned n) { return !p || !n; }
static void FUN_00414e68(void) { fputs("Unexpected surface failure\n",stderr); abort(); }
static byte storage[4][8192], initial[4][8192], expected[4][8192];
static uint physical[2], vt[64], dst_pitch;
static int lock_loss, unlock_loss, dst_offset;
struct Event { uint kind, object, value; };
static struct Event events[16], expected_events[16];
static unsigned event_count;
static void record(uint kind,uint object,uint value) {
    if(event_count>=16) abort();
    events[event_count++]=(struct Event){kind,object,value};
}
static void out(uint16_t port,uint value) { record(4,port,value); }
static int lock_impl(void *self,void *rect,void *desc,uint flags,void *event) {
    record(1,(uintptr_t)self,flags);
    if(rect || event || flags!=1 || desc!=(void*)0x636864) abort();
    uint *d=desc;
    if(d[0]!=0x6c) abort();
    for(int i=1;i<27;i++) if(d[i]) abort();
    if(lock_loss) { lock_loss=0; return (int)0x887601c2; }
    d[4]=dst_pitch;
    d[9]=(uintptr_t)(storage[self==(void*)&physical[0]?0:1]+dst_offset);
    return 0;
}
static int restore_impl(void *self) { record(2,(uintptr_t)self,0); return 0; }
static int unlock_impl(void *self,void *base) {
    record(3,(uintptr_t)self,(uintptr_t)base);
    if(base!=storage[self==(void*)&physical[0]?0:1]+dst_offset) abort();
    if(unlock_loss) { unlock_loss=0; return (int)0x887601c2; }
    return 0;
}
static int lock_c(void *a,void *b,void *c,uint d,void *e) { return lock_impl(a,b,c,d,e); }
static int restore_c(void *a) { return restore_impl(a); }
static int unlock_c(void *a,void *b) { return unlock_impl(a,b); }
static int __attribute__((stdcall)) lock_x86(void *a,void *b,void *c,uint d,void *e) {
    return lock_impl(a,b,c,d,e);
}
static int __attribute__((stdcall)) restore_x86(void *a) { return restore_impl(a); }
static int __attribute__((stdcall)) unlock_x86(void *a,void *b) { return unlock_impl(a,b); }
static void choose_abi(int recovered) {
    vt[25]=recovered?(uintptr_t)lock_c:(uintptr_t)lock_x86;
    vt[27]=recovered?(uintptr_t)restore_c:(uintptr_t)restore_x86;
    vt[32]=recovered?(uintptr_t)unlock_c:(uintptr_t)unlock_x86;
}
__attribute__((naked)) static void clear_x86(void) {
    __asm__("pushal; push %ebx; push %edx; push %eax; call memset; add $12,%esp; popal; ret");
}
__attribute__((used)) static void mask_impl(uint mask) { out(0x3c5,mask&15); out(0x3ce,8); }
__attribute__((naked)) static void mask_x86(void) {
    __asm__("pushal; push %eax; call mask_impl; add $4,%esp; popal; ret");
}
__attribute__((used)) static void reset_impl(void) { out(0x3ce,0xff08); }
__attribute__((naked)) static void reset_x86(void) {
    __asm__("pushal; call reset_impl; popal; ret");
}
__attribute__((naked)) static void copy_x86(int surface,int x,int y,int width,int height) {
    __asm__("push %ebp; push %ebx; push %esi; push %edi;"
            "mov 20(%esp),%eax; mov 24(%esp),%edx; mov 28(%esp),%ebx;"
            "mov 32(%esp),%ecx; push 36(%esp); mov $0x418484,%esi; call *%esi;"
            "pop %edi; pop %esi; pop %ebx; pop %ebp; ret");
}
static void map(uint p,uint n) {
    if(mmap((void*)p,n,PROT_READ|PROT_WRITE|PROT_EXEC,
            MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==MAP_FAILED) {
        perror("mmap original"); exit(2);
    }
}
static void hook(uint p,void (*target)(void)) {
    *(byte*)p=0xe9; *(int32_t*)(p+1)=(intptr_t)target-p-5;
}
'''
harness += '\n'.join(functions)
caller = re.search(r'void FUN_00424bd8\(void\)\s*\{.*?\n\}', source, re.S)
if not caller:
    raise ValueError('Missing dirty-rectangle caller FUN_00424bd8')
harness += r'''
#define DAT_0047a34a (*(uint*)0x47a34a)
struct RectCall { int surface,x,y,width,height; };
static struct RectCall rect_calls[150], expected_rect_calls[150];
static unsigned rect_count;
__attribute__((used)) static void record_copy(int s,int x,int y,int w,int h) {
    if(rect_count>=150) abort();
    rect_calls[rect_count++]=(struct RectCall){s,x,y,w,h};
}
static void FUN_0041760c(int a,uint b,uint c,int d,byte *e,int f) { abort(); }
__attribute__((naked)) static void record_copy_x86(void) {
    __asm__("pushal; push 36(%esp); push %ecx; push %ebx; push %edx; push %eax;"
            "call record_copy; add $20,%esp; popal; ret $4");
}
__attribute__((naked)) static void caller_x86(void) {
    __asm__("pushal; mov $0x424bd8,%eax; call *%eax; popal; ret");
}
#define FUN_00418484 record_copy
'''
harness += caller.group() + '\n#undef FUN_00418484\n'
harness += r'''
static void reset(int recovered,int surface,int overlap,int losses) {
    memcpy(storage,initial,sizeof storage);
    memset(events,0,sizeof events); event_count=0;
    memset((void*)0x636864,0xa5,0x6c);
    for(int s=0;s<4;s++) *(uint*)(0x636150+s*4)=(uintptr_t)storage[s];
    dst_offset=overlap==2;
    if(overlap && surface<2) {
        /* Surface 2 is the source: exercise original forward-copy overlap too. */
        _DAT_00636158=(uintptr_t)(storage[surface]+(overlap==1));
    }
    lock_loss=losses&1; unlock_loss=(losses>>1)&1;
    choose_abi(recovered);
}
int main(void) {
    map(0x410000,0x60000); map(0x470000,0x10000); map(0x630000,0x20000);
'''
for start, end in ((0x418484, 0x41858b), (0x418a04, 0x418b97),
                   (0x424bd8, 0x424cbc)):
    blob = original(start, end)
    harness += 'memcpy((void*)0x%x,(byte[]){%s},%d);\n' % (
        start, ','.join(str(b) for b in blob), len(blob))
harness += r'''
    hook(0x45f8d0,clear_x86); hook(0x45cf10,mask_x86); hook(0x45cf23,reset_x86);
    physical[0]=(uintptr_t)vt; physical[1]=(uintptr_t)vt;
    DAT_0047d0cc=(uintptr_t)&physical[0]; DAT_0047d0d0=(uintptr_t)&physical[1];
    _DAT_006401d4=32;
    for(unsigned i=0;i<sizeof initial;i++) ((byte*)initial)[i]=(i*37+i/79+11)&255;
    unsigned cases=0;
    for(int mode=0;mode<2;mode++) for(int front=0;front<2;front++)
    for(int surface=0;surface<4;surface++) for(int k=0;k<128;k++) {
        int x=(int[]){0,1,3,7,31,63,80,95}[k%8];
        int width=(int[]){0,1,2,3,9,16,32,64}[(k/8)%8];
        if(x+width>96) width=96-x;
        int y=(k/17)%8, height=(int[]){-1,0,1,2,4,7}[(k/11)%6];
        int losses=(k/19)%4;
        int overlap=mode && surface<2 && k%13==0 ? 1+(k/13)%2 : 0;
        DAT_0047a43c=mode; DAT_0047a279=front<<24;
        DAT_00477060=k&1?127:96;
        _DAT_006401ec=DAT_00477060;
        dst_pitch=(uint[]){97,113,128}[k%3];
        reset(0,surface,overlap,losses);
        copy_x86(surface,x,y,width,height);
        memcpy(expected,storage,sizeof storage);
        memcpy(expected_events,events,sizeof events);
        unsigned expected_count=event_count;
        reset(1,surface,overlap,losses);
        FUN_00418484(surface,x,y,width,height);
        if(memcmp(expected,storage,sizeof storage) || expected_count!=event_count ||
           memcmp(expected_events,events,sizeof events)) {
            fprintf(stderr,"Mismatch mode=%d front=%d surface=%d rect=%d,%d,%d,%d k=%d\n",
                    mode,front,surface,x,y,width,height,k);
            return 1;
        }
        cases++;
    }
    printf("PASS: %u original-x86 rectangle copies, padding and lock/restore/unlock/port sequences\n",cases);
    hook(0x418484,record_copy_x86);
    DAT_0047a34a=0;
    for(int front=0;front<2;front++) for(int k=0;k<128;k++) {
        DAT_0047a279=front<<24;
        *(int*)(0x47a29c+front*4)=4;
        short *rects=(short*)(0x6368e0+front*0x4b0);
        for(int r=0;r<4;r++) {
            rects[r*4]=(k+r*13)%80-10;
            rects[r*4+1]=rects[r*4]+(k+r)%7-1;
            rects[r*4+2]=(k+r*7)%50-10;
            rects[r*4+3]=rects[r*4+2]+(k+3*r)%5-1;
        }
        memset(rect_calls,0,sizeof rect_calls); rect_count=0;
        caller_x86();
        unsigned n=rect_count;
        memcpy(expected_rect_calls,rect_calls,sizeof rect_calls);
        memset(rect_calls,0,sizeof rect_calls); rect_count=0;
        FUN_00424bd8();
        if(n!=rect_count || memcmp(expected_rect_calls,rect_calls,sizeof rect_calls)) {
            fprintf(stderr,"Dirty-rectangle caller mismatch front=%d k=%d original=%u recovered=%u\n",front,k,n,rect_count);
            for(unsigned j=0;j<n || j<rect_count;j++) {
                struct RectCall a=expected_rect_calls[j],b=rect_calls[j];
                fprintf(stderr,"%u: original %d,%d,%d,%d,%d recovered %d,%d,%d,%d,%d\n",
                    j,a.surface,a.x,a.y,a.width,a.height,b.surface,b.x,b.y,b.width,b.height);
            }
            return 1;
        }
    }
    puts("PASS: 256 original-x86 dirty-list dispatches, signed bounds and inclusive extents");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='e2-rectangle-copy-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie',
                    '-Wno-deprecated-non-prototype', *flags, str(c), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
