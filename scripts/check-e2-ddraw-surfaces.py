#!/usr/bin/env python3
"""Check actual compatibility DirectDraw storage through recovered Lock/Unlock callers."""
import argparse
from pathlib import Path

from e2_original import function, run_fixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
source = Path('E2Recomp/reconstructed/E2Recomp_stubs.c').read_text()
provider = source[source.index('static void *E2R_dd_obj[64];'):source.index('\nint acmMetrics')]
recon = Path('E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
typedef uint32_t undefined4,uint;typedef int32_t HRESULT;typedef int code();
typedef uint8_t undefined1;typedef uintptr_t UINT_PTR;
#define __fastcall
static uintptr_t _DAT_00ac4eb8,DAT_0047a279,DAT_0047d0cc,DAT_0047d0d0;
static uintptr_t DAT_0047d0c8,DAT_0047d0c4,_DAT_006366c0,_DAT_00ac4dac;
static const char s_Change_screen_mode_Failed___08lx_00476364[]="Mode failed %x";
static const char s_ERROR_0047635c[]="Error";
static void wsprintfA(char *target,const char *format,int result) { sprintf(target,format,result); }
static void MessageBoxA(uintptr_t hwnd,const char *text,const char *title,int flags) { assert(!"Unexpected mode error"); }
static uintptr_t _DAT_006401ec=640,_DAT_006401d4=480,_DAT_00636158,_DAT_0063615c;
static int IsBadReadPtr(const void *p,uintptr_t n) { return !p; }
static int E2R_IsBadWritePtr(const void *p,uintptr_t n) { return !p; }
static void FUN_00414e68(void) { assert(!"Unexpected recovered surface failure"); }
'''
harness += provider + '\n' + function(recon, 'FUN_00418a04') + '\n' + function(recon, 'FUN_00418b00')
harness += '\n' + function(recon, 'FUN_00458984')
harness += r'''
int main(void) {
    assert(mmap((void *)0x630000,0x10000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void *)0x630000);
    static unsigned char auxiliary[640*480];_DAT_00636158=(uintptr_t)auxiliary;
    for(unsigned cycle=0;cycle<100;cycle++) {
        void *dd=NULL,*primary=NULL,*offscreen=NULL,*back=NULL;
        assert(!DirectDrawCreate(NULL,&dd,NULL) && dd!=NULL);
        void **vt=*(void ***)dd;
        int (*mode)(void *,unsigned,unsigned,unsigned)=vt[21];
        int (*create)(void *,void *,void **,void *)=vt[6];
        assert(mode(dd,640,480,16)!=0);
        assert(!mode(dd,640,480,8));
        uint32_t desc[27]={0x6c,0x21};desc[5]=1;desc[26]=0x218;
        assert(!create(dd,desc,&primary,NULL));
        memset(desc,0,sizeof desc);desc[0]=0x6c;desc[1]=7;desc[2]=263;desc[3]=641;desc[26]=0x840;
        assert(!create(dd,desc,&offscreen,NULL) && primary!=offscreen);
        void **pv=*(void ***)primary,**ov=*(void ***)offscreen;
        unsigned (*addref)(void *)=pv[1],(*release)(void *)=pv[2];
        assert(addref(primary)==2 && release(primary)==1);
        unsigned caps=4;
        int (*attached)(void *,unsigned *,void **)=pv[12];
        assert(!attached(primary,&caps,&back) && back!=primary && back!=offscreen);
        DAT_0047d0cc=(uintptr_t)primary;DAT_0047d0d0=(uintptr_t)offscreen;DAT_0047a279=1u<<24;
        uint32_t pitch=0;unsigned base=FUN_00418a04(1,&pitch);
        assert(base && pitch==640 && base!=(unsigned)auxiliary);
        const unsigned char *view;unsigned view_width,view_height,view_pitch;
        assert(!E2R_GetDirectDrawPixels((uintptr_t)primary,&view,&view_width,&view_height,&view_pitch));
        memset((void *)base,0x31,640*480);FUN_00418b00(1,base);
        assert(E2R_GetDirectDrawPixels((uintptr_t)primary,&view,&view_width,&view_height,&view_pitch));
        assert((unsigned)view==base && view_width==640 && view_height==480 && view_pitch==640);
        unsigned primary_base=base;
        base=FUN_00418a04(0,&pitch);
        assert(base && pitch==644 && base!=primary_base);
        memset((void *)base,0x72,644*263);
        uint32_t lock_desc[27]={0x6c};
        int (*lock)(void *,void *,void *,unsigned,void *)=ov[25];
        int (*unlock)(void *,void *)=ov[32];
        assert(lock(offscreen,NULL,lock_desc,1,NULL)!=0);
        assert(unlock(primary,(void *)base)!=0);
        assert(unlock(offscreen,(void *)(base+1))!=0);
        FUN_00418b00(0,base);
        assert(!lock(offscreen,NULL,lock_desc,1,NULL));
        assert(lock_desc[0]==0x6c && lock_desc[2]==263 && lock_desc[3]==641 && lock_desc[4]==644 && lock_desc[9]==base);
        assert(*(unsigned char *)base==0x72);
        assert(!unlock(offscreen,(void *)base));
        int (*restore)(void *)=ov[27];assert(!restore(offscreen));
        base=FUN_00418a04(0,&pitch);assert(*(unsigned char *)base==0x72);FUN_00418b00(0,base);
        assert(FUN_00418a04(2,&pitch)==(unsigned)auxiliary && pitch==640);
        void **bv=*(void ***)back;
        int (*back_lock)(void *,void *,void *,unsigned,void *)=bv[25];
        int (*back_unlock)(void *,void *)=bv[32];
        lock_desc[0]=0x6c;assert(!back_lock(back,NULL,lock_desc,1,NULL));
        unsigned back_base=lock_desc[9];assert(back_base!=primary_base && back_base!=base);
        memset((void *)back_base,0x54,640*480);assert(!back_unlock(back,(void *)back_base));
        int (*flip)(void *,void *,unsigned)=pv[11];assert(!flip(primary,NULL,0));
        assert(E2R_GetDirectDrawPixels((uintptr_t)primary,&view,&view_width,&view_height,&view_pitch));
        assert((unsigned)view==back_base && view[0]==0x54);
        base=FUN_00418a04(1,&pitch);assert(base==back_base && *(unsigned char *)base==0x54);FUN_00418b00(1,base);
        assert(release(back)==1 && release(primary)==0);
        DAT_0047d0c8=(uintptr_t)dd;DAT_0047d0cc=0;
        FUN_00458984(640,480);
        assert(DAT_0047d0cc && DAT_0047d0d0 && DAT_0047d0cc!=DAT_0047d0d0);
        base=FUN_00418a04(1,&pitch);assert(base && pitch==640);FUN_00418b00(1,base);
        base=FUN_00418a04(0,&pitch);assert(base && pitch==640);FUN_00418b00(0,base);
        FUN_00458984(320,200);
        assert(DAT_0047d0cc && DAT_0047d0c4==0);
        base=FUN_00418a04(1,&pitch);assert(base && pitch==320);FUN_00418b00(1,base);
        FUN_00458984(640,480);
        base=FUN_00418a04(1,&pitch);assert(base && pitch==640);FUN_00418b00(1,base);
        unsigned (*dd_release)(void *)=vt[2];assert(dd_release(dd)==0);
        assert(lock(offscreen,NULL,lock_desc,1,NULL)!=0);
        desc[0]=1;assert(create(dd,desc,&primary,NULL)!=0 && primary==NULL);
        desc[0]=0x6c;desc[3]=0;assert(create(dd,desc,&primary,NULL)!=0 && primary==NULL);
    }
    puts("PASS: 100 DirectDraw create/attached/refcount/lock/restore/unlock/flip/release lifecycles; distinct storage, real pitch, invalid ownership, auxiliary isolation and recovered selector/mode callers");
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness,
            dependencies=('production compatibility provider and recovered lock/unlock callers',
                          'palette input-read validation intercepted; SDL presentation not exercised'))

