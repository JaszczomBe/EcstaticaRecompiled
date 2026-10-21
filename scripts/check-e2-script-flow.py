#!/usr/bin/env python3
"""Check script cursor skipping and nested record ownership against original i386.

The comparison intercepts the interpreter at its entry to check record/actor/node
arguments. Nested dispatch checks use the production dispatcher with a fixture
interpreter; they do not claim complete script evaluation or gameplay.
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
parser.add_argument('--keep-harness', type=Path, help='Retain fixture source/executable for debugger inspection')
args = parser.parse_args()
pe = args.exe.read_bytes()
header = struct.unpack_from('<I', pe, 0x3c)[0]
count = struct.unpack_from('<H', pe, header + 6)[0]
optional = struct.unpack_from('<H', pe, header + 20)[0]


def original(start, end):
    for i in range(count):
        at = header + 24 + optional + i * 40
        _, va, size, raw = struct.unpack_from('<IIII', pe, at + 8)
        va += 0x400000
        if va <= start < end <= va + size:
            return pe[raw + start - va:raw + end - va]
    raise ValueError(start)


source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#include <sys/mman.h>
typedef uint16_t ushort;
typedef uint8_t byte;
typedef uint32_t uint,undefined4;
#define __fastcall
static short *E2R_action_dispatch_node;
static ushort *E2R_script_node_context;
static uintptr_t observed[5];
static int nested;
static void E2R_DispatchScriptRecord(ushort*,ushort*,ushort*,ushort*,ushort*);
__attribute__((force_align_arg_pointer)) void observe(uintptr_t code,uintptr_t actor,uintptr_t other,uintptr_t child,uintptr_t node) {
    uintptr_t values[]={code,actor,other,child,node}; memcpy(observed,values,sizeof values);
}
void FUN_0044f508(ushort *actor,ushort *other,ushort *child) {
    observe((uintptr_t)E2R_action_dispatch_node,(uintptr_t)actor,(uintptr_t)other,
            (uintptr_t)child,(uintptr_t)E2R_script_node_context);
    if(nested) {
        short *parent=E2R_action_dispatch_node; ushort *node=E2R_script_node_context;
        nested=0;
        E2R_DispatchScriptRecord((ushort*)0x900200,other,actor,child,(ushort*)0x900400);
        assert(E2R_action_dispatch_node==parent && E2R_script_node_context==node);
    }
}
__attribute__((naked)) void interpreter_hook(void) {
    __asm__("pushal; push %ebx; push 40(%esp); push %ecx; push %edx; push %eax; call observe; add $20,%esp; popal; ret $4");
}
'''
for name in ('FUN_0044e74c', 'FUN_0044e7a4', 'FUN_0044f2fc', 'FUN_0044f320', 'E2R_DispatchScriptRecord'):
    match = re.search(r'^(?:static )?(?:void|undefined4) (?:__fastcall )?' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.M | re.S)
    assert match, name
    harness += match.group() + '\n'
# Extract the production diagnostic branches, including their signed token decoding.
for opcode in ('0x27', '0x29', '0x2a'):
    at = source.index('      case ' + opcode + ':', source.index('void __fastcall FUN_0044f508('))
    end = source.index('        if (', source.index('        }\n', at) + len('        }\n'))
    branch = source[at:end]
    # Wrap the case in a one-case switch so its real break retains its meaning.
    harness += f'int proxy_{opcode}(int *local_2c) {{ switch(1) {{ case 1:\n' + branch.split(':\n',1)[1] + ' } return (int)local_2c; }\n'
for at, end in ((0x44e745, 0x44e810), (0x44f2fc, 0x44f32c), (0x450af6, 0x450b17), (0x450b8a, 0x450bab), (0x450c20, 0x450c3e)):
    code = original(at, end)
    harness += f'static const unsigned char code_{at:x}[]={{' + ','.join(map(str, code)) + '};\n'
harness += r'''
__attribute__((naked)) int advance_original(int cursor,int length,int fn) {
    __asm__("push %ebx; push %esi; push %edi; sub $0x50,%esp; mov 0x60(%esp),%eax; mov %eax,0x44(%esp); mov 0x64(%esp),%ecx; mov %ecx,%esi; call *0x68(%esp); add $0x50,%esp; pop %edi; pop %esi; pop %ebx; ret");
}
static void map(int address,int n) {
    assert(mmap((void*)address,n,PROT_READ|PROT_WRITE|PROT_EXEC,
                MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
}
static void skip_original(int fn,int *cursor) {
    __asm__ volatile("call *%%edi" : "+a"(cursor) : "D"(fn) : "memory","cc");
}
static void wrapper_original(int fn,uintptr_t code,uintptr_t actor,uintptr_t node) {
    __asm__ volatile("call *%%edi" : "+a"(code), "+d"(actor), "+b"(node) : "D"(fn) : "ecx","memory","cc");
}
int main(void) {
    map(0x440000,0x20000); map(0x900000,0x20000);
    memcpy((void*)0x44e745,code_44e745,sizeof code_44e745);
    memcpy((void*)0x44f2fc,code_44f2fc,sizeof code_44f2fc);
    *(unsigned char*)0x44f508=0xe9;
    *(int32_t*)0x44f509=(intptr_t)interpreter_hook-0x44f50d;
    memcpy((void*)0x450af6,code_450af6,sizeof code_450af6);
    memcpy((void*)0x450b8a,code_450b8a,sizeof code_450b8a);
    memcpy((void*)0x450c20,code_450c20,sizeof code_450c20);
    unsigned char return_cursor[]={0x8b,0x44,0x24,0x48,0xc3};
    memcpy((void*)0x450c58,return_cursor,sizeof return_cursor);
    setenv("E2R_PROXY_MESH_BYPASS","1",1);
    int (*proxy[])(int*)={proxy_0x27,proxy_0x29,proxy_0x2a};
    int advance[]={0x450af6,0x450b8a,0x450c20};
    unsigned graphics=0;
    for(int op=0;op<3;op++) for(int length=-16;length<=64;length++) {
        short *words=(short*)0x914000;
        words[op==0?3:1]=0xe000|(length&0xfff);
        int result=proxy[op]((int*)words);
        int expected=advance_original((int)words,length,advance[op]);
        assert(result==expected);graphics++;
    }
    unsigned cases=0;
    short *tokens=(short*)0x914000;
    for(int depth=0;depth<8;depth++) for(int terminator=4;terminator<=6;terminator++) {
        int length=0;
        for(int i=0;i<depth;i++) { tokens[length++]=3; tokens[length++]=0x42; }
        for(int i=0;i<depth;i++) tokens[length++]=6;
        tokens[length++]=terminator; tokens[length++]=6;
        int a=(int)tokens,b=a;
        skip_original(0x44e7a4,&a); FUN_0044e7a4(&b); assert(a==b);
        a=b=(int)tokens;
        skip_original(0x44e74c,&a); FUN_0044e74c(&b); assert(a==b);
        cases+=2;
    }
    // The original keeps sign-extended high bits for encoded string tokens.
    // Surrounding mapped tokens are terminators, so both branches stay bounded.
    for(int length=0;length<64;length++) {
        for(int i=0;i<0x10000;i++) ((short*)0x900000)[i]=6;
        tokens[0]=(short)(0xe000+length);
        for(int mode=0;mode<2;mode++) {
            int a=(int)tokens,b=a;
            skip_original(mode?0x44e74c:0x44e7a4,&a);
            if(mode) FUN_0044e74c(&b); else FUN_0044e7a4(&b);
            assert(a==b); cases++;
        }
    }
    for(int i=0;i<32;i++) {
        uintptr_t code=0x900000+i*16,actor=0x901000+i*32,node=0x902000+i*32;
        wrapper_original(0x44f320,code,actor,node);
        uintptr_t expected[5]; memcpy(expected,observed,sizeof expected);
        E2R_action_dispatch_node=(short*)0x903000; E2R_script_node_context=(ushort*)0x903100;
        FUN_0044f320(code,(ushort*)actor,(ushort*)node);
        assert(!memcmp(expected,observed,sizeof expected));
        assert(E2R_action_dispatch_node==(short*)0x903000 && E2R_script_node_context==(ushort*)0x903100);
        wrapper_original(0x44f2fc,code,actor,node); memcpy(expected,observed,sizeof expected);
        FUN_0044f2fc(code); assert(!memcmp(expected,observed,sizeof expected));
        nested=1; E2R_DispatchScriptRecord((ushort*)code,(ushort*)actor,(ushort*)actor,NULL,(ushort*)node);
        assert(!nested && E2R_action_dispatch_node==(short*)0x903000 && E2R_script_node_context==(ushort*)0x903100);
    }
    printf("PASS: %u original-x86 script cursor cases, 64 script-wrapper inputs and 32 nested ownership cases; %u diagnostic graphics operand spans\n",cases,graphics);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-script-flow-') as tmp:
    c = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    c.write_text(harness)
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-fno-pie', '-no-pie', *flags,
                    str(c), '-o', str(exe)], check=True)
    if args.keep_harness:
        import shutil
        shutil.copyfile(c, args.keep_harness.with_suffix('.c'))
        shutil.copy2(exe, args.keep_harness)
    subprocess.run([str(exe)], check=True, timeout=20)
