#!/usr/bin/env python3
"""Validate the production loose-archive visibility index using original assets."""
import argparse
from pathlib import Path
import re
import struct
import subprocess
import tempfile

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive',type=Path)
parser.add_argument('offsets',type=Path)
parser.add_argument('--asan',action='store_true')
parser.add_argument('--cc',default='clang-21')
args=parser.parse_args()
archive=args.archive.read_bytes(); offsets=args.offsets.read_bytes()
assert len(offsets)==56240
expected=struct.unpack_from('>1200i',offsets,51440)
for offset in expected:
    if offset<0:continue
    assert archive[offset:offset+4]==b'VisM'
    assert offset+6+struct.unpack_from('<H',archive,offset+4)[0]*4<=len(archive)
source=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
match=re.search(r'^static int E2R_IndexFlatArchiveVisibility\([^\n]+\)\s*\{.*?\n\}',source,re.M|re.S)
assert match
harness=r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint32_t uint,undefined4;typedef void *HLOCAL;
static byte *index_data;static int index_size,mode,allocations;
static uint E2R_OpenReadStream(const char *path) {
    assert(!strcmp(path,"OFFSETS"));if(mode==1)return 0;
    uint *stream=calloc(7,4);byte *data=malloc(index_size);
    memcpy(data,index_data,index_size);allocations+=2;
    stream[1]=index_size-(mode==2);stream[5]=(uintptr_t)data;
    return (uintptr_t)stream;
}
static void LocalFree(void *p) { assert(p && allocations>0);allocations--;free(p); }
static byte *read_all(char *path,int *size) {
    FILE *file=fopen(path,"rb");assert(file);fseek(file,0,SEEK_END);*size=ftell(file);rewind(file);
    byte *data=malloc(*size);assert(fread(data,1,*size,file)==(size_t)*size);fclose(file);return data;
}
'''+match.group()+r'''
int main(int argc,char **argv) {
    assert(argc==3);int size;byte *data=read_all(argv[1],&size);
    index_data=read_all(argv[2],&index_size);
    assert(mmap((void*)0x646000,0x3000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);
    int count=E2R_IndexFlatArchiveVisibility(data,data+size);assert(count==EXPECTED_COUNT);
    for(int id=0;id<1200;id++) {
        byte *p=index_data+51440+id*4;
        uint expected=(uint)p[0]<<24|(uint)p[1]<<16|(uint)p[2]<<8|p[3];
        assert(*(uint*)(0x6467a8+id*4)==expected);
    }
    assert(allocations==0);
    int offset=*(int*)(0x6467a8+347*4);byte saved_magic=data[offset];
    for(mode=1;mode<=5;mode++) {
        memset((void*)0x6467a8,0xa5,4800);
        if(mode==3)data[offset]='X';
        const byte *end=data+size;if(mode==4)end=data+offset+5;if(mode==5)end=data+offset+6;
        assert(E2R_IndexFlatArchiveVisibility(data,end)==0);
        for(int id=0;id<1200;id++) assert(*(uint*)(0x6467a8+id*4)==0xa5a5a5a5);
        assert(allocations==0);data[offset]=saved_magic;
    }
    printf("PASS: %d original visibility offsets and five missing/truncated/mismatched index/archive cases\n",count);
    free(data);free(index_data);
}
'''
harness=harness.replace('EXPECTED_COUNT',str(sum(o>=0 for o in expected)))
with tempfile.TemporaryDirectory(prefix='e2-visibility-index-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-fno-pie','-no-pie',*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe),str(args.archive.resolve()),str(args.offsets.resolve())],check=True,timeout=30)
