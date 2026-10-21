#!/usr/bin/env python3
"""Check read-only actor projection and SDL cylinder presentation with fixtures.

Uses the actual snapshot function, recovered camera math and SDL backend. Requires
a built SDL/i386 Debug target and clang -m32 support; no game data is needed.
Synthetic positions test drawing, not gameplay or original actor placement.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--build-dir', type=Path, default=Path('build/Debug/clang21-i386-sdl'))
parser.add_argument('--asan', action='store_true')
parser.add_argument('--output', type=Path, default=Path('/tmp/e2-cylinder-fixture'))
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
build = args.build_dir.resolve()
library = build / 'dep/SDL-build/libSDL3.a'
if not library.is_file():
    parser.error('Build the SDL Debug preset first, or specify --build-dir')


def function(source, name):
    match = re.search(r'void (?:__fastcall )?' + name + r'\([^\n]*\)\s*\{.*?\n\}', source, re.S)
    if not match:
        raise ValueError(f'Missing production function {name}')
    return match.group()


recon = (root / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
native = (root / 'E2Recomp/native/e2recomp_native_main.c').read_text()
harness = r'''
#define E2R_LOG_NO_WRAP 1
#include "E2Recomp_recon.h"
#include "e2recomp_host_backend.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <limits.h>
uintptr_t _DAT_0073cc3c, _DAT_0063726c, _DAT_006401ec, _DAT_006401d4,
          _DAT_00640118, _DAT_00640114, DAT_0047a34a, DAT_0047a43c,
          DAT_0047a76c, _DAT_00643650, DAT_0047a45e;
BOOL IsBadReadPtr(const void *p, UINT_PTR n) {
    return (uintptr_t)p < 0x470000 || (uintptr_t)p + n > 0x6b0000;
}
BOOL E2R_IsBadWritePtr(const void *p, UINT_PTR n) { return !p || !n; }
'''
for name in ('FUN_00422368', 'FUN_00422460', 'FUN_00422538',
             'E2R_TransformVector14', 'E2R_Perspective14'):
    harness += function(recon, name) + '\n'
harness += function(native, 'E2R_GetActorCues') + '\n'
harness += '#include "' + str(root / 'E2Recomp/platform/e2recomp_host_backend_sdl.c') + '"\n'
harness += r'''
static byte *joe = (byte*)0x690000;
static void position(int x,int y,int z) {
    short p[3] = {x,y,z}; memcpy(joe+0x84,p,sizeof p);
}
static unsigned pixels(SDL_Surface *s) {
    unsigned n=0;
    for(int y=0;y<s->h;y++) for(int x=0;x<s->w;x++)
        n += ((Uint32*)((byte*)s->pixels+y*s->pitch))[x] != 0;
    return n;
}
static void clear(SDL_Surface *s) { assert(SDL_FillSurfaceRect(s,NULL,0)); }
int main(int argc,char **argv) {
    assert(argc==2);
    assert(mmap((void*)0x470000,0x240000,PROT_READ|PROT_WRITE,
                MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0) != MAP_FAILED);
    for(int i=0;i<65536;i++) {
        double phase=i*6.28318/65536.0;
        *(short*)(0x59b590+i*2)=(short)(sin(phase)*16384.5);
        *(short*)(0x5de590+i*2)=(short)(cos(phase)*16384.5);
    }
    _DAT_0073cc3c=0x67c728; _DAT_0063726c=(uintptr_t)joe;
    _DAT_006401ec=640; _DAT_006401d4=480; _DAT_00640118=320; _DAT_00640114=240;
    DAT_0047a43c=1;
    *(short*)(_DAT_0073cc3c+12)=1024;
    *(uint32_t*)0x630b60=(uintptr_t)joe;
    short identity[9]={16384,0,0,0,16384,0,0,0,16384};
    memcpy(joe+6,identity,sizeof identity);
    position(0,0,4096);
    *(uint32_t*)(joe+0xa6)=0x12345678;
    *(uint16_t*)(joe+0xaa)=100; *(uint16_t*)(joe+0xac)=25;
    DAT_0047a76c=1; DAT_0047a45e=0x2e0000;
    byte *before=malloc(0x240000); assert(before);
    memcpy(before,(void*)0x470000,0x240000);
    E2R_ActorCueSnapshot near,far,moved,turned,state;
    E2R_GetActorCues(&near);
    assert(!memcmp(before,(void*)0x470000,0x240000));
    assert(near.camera_ready && near.count==1 && near.scene_slot==0);
    assert(near.actors[0].screen[0][0]==320 && near.actors[0].screen[0][1]==240);
    assert(near.script_wait==1 && near.requester_id==0x2e);
    setenv("E2R_DEFER_BACKGROUND_SPAWNS","1",1);
    E2R_GetActorCues(&state);
    assert(state.background_spawns_deferred && !memcmp(before,(void*)0x470000,0x240000));
    unsetenv("E2R_DEFER_BACKGROUND_SPAWNS");
    assert(near.actors[0].action==0x12345678 && near.actors[0].action_progress==25);
    position(0,0,8192); E2R_GetActorCues(&far);
    int near_width=near.actors[0].cylinder[0][0]-near.actors[0].cylinder[4][0];
    int far_width=far.actors[0].cylinder[0][0]-far.actors[0].cylinder[4][0];
    int near_height=240-near.actors[0].screen[1][1];
    int far_height=240-far.actors[0].screen[1][1];
    assert(abs(near_width-2*far_width)<=2 && abs(near_height-2*far_height)<=2);
    position(512,0,4096); E2R_GetActorCues(&moved);
    assert(moved.actors[0].screen[0][0] > near.actors[0].screen[0][0]);
    *(short*)(joe+0x92)=16384;
    FUN_00422460((uintptr_t)(joe+6),16384);
    E2R_GetActorCues(&turned);
    assert(turned.actors[0].rotation_y==16384);
    assert(turned.actors[0].local_z_tip[0]!=moved.actors[0].local_z_tip[0]);
    SDL_Surface *s=SDL_CreateSurface(640,480,SDL_PIXELFORMAT_ARGB8888); assert(s);
    Uint32 cyan=SDL_MapSurfaceRGB(s,56,224,244);
    clear(s); assert(e2r_cue_cylinder(s,&near.actors[0],cyan)); assert(pixels(s)>100);
    clear(s); assert(e2r_cue_cylinder(s,&far.actors[0],cyan)); assert(pixels(s)>50);
    position(-2600,0,4096); E2R_GetActorCues(&state);
    assert(state.actors[0].screen[0][0]<0);
    clear(s); assert(e2r_cue_cylinder(s,&state.actors[0],cyan)); assert(pixels(s)>0);
    position(0,0,-4096); E2R_GetActorCues(&state);
    clear(s); assert(!e2r_cue_cylinder(s,&state.actors[0],cyan)); assert(!pixels(s));
    position(0,0,128); E2R_GetActorCues(&state);
    int rejected=0;
    for(int i=0;i<16;i++) rejected += state.actors[0].cylinder[i][2]==0;
    assert(rejected>0);
    clear(s); e2r_cue_cylinder(s,&state.actors[0],cyan);
    int a[3]={INT_MIN,240,1}, b[3]={INT_MAX,240,1};
    clear(s); assert(e2r_cylinder_line(s,a,b,cyan)); assert(pixels(s)==1280);
    a[1]=b[1]=-100;
    clear(s); assert(!e2r_cylinder_line(s,a,b,cyan)); assert(!pixels(s));
    a[2]=0; b[1]=240;
    assert(!e2r_cylinder_line(s,a,b,cyan));
    DAT_0047a34a=1; E2R_GetActorCues(&state); assert(!state.camera_ready);
    DAT_0047a34a=0;
    *(uint32_t*)0x630b60=0; E2R_GetActorCues(&state); assert(!state.count);
    *(uint32_t*)0x630b60=(uintptr_t)joe;
    *(uint32_t*)(joe+0x4c)=(uintptr_t)joe;
    E2R_GetActorCues(&state); assert(state.count==1); // bounded self-link
    *(uint32_t*)(joe+0x4c)=0;
    byte *object=(byte*)0x691000;
    *(short*)object=980;*(uint32_t*)(0x630b60+980*4)=(uintptr_t)object;
    *(uint32_t*)(joe+0x4c)=(uintptr_t)object;
    short object_pos[3]={1024,0,4096};memcpy(object+0x84,object_pos,6);
    E2R_GetActorCues(&state);
    assert(state.count==2 && state.actors[1].is_object && !state.actors[1].visible_in_view);
    object[2]=8;E2R_GetActorCues(&state);
    assert(state.actors[1].is_object && state.actors[1].visible_in_view);
    *(uint32_t*)(object+0x132)=0x692000;E2R_GetActorCues(&state);
    assert(!state.actors[1].is_object); // scripted character before representation installation
    *(uint32_t*)(object+0x132)=0;
    *(short*)(0x64a178+980*2)=8;E2R_GetActorCues(&state);
    assert(state.actors[1].generated && !state.actors[1].is_object);
    *(short*)(0x64a178+980*2)=0;*(uint32_t*)(object+0x11e)=0x692000;
    E2R_GetActorCues(&state);assert(!state.actors[1].is_object && !state.actors[1].generated);
    *(uint32_t*)(object+0x11e)=0;object[2]=0;
    position(0,0,4096); memcpy(joe+6,identity,sizeof identity);
    *(short*)(joe+0x92)=0;
    byte *indexed=malloc(640*480); assert(indexed); memset(indexed,17,640*480);
    E2R_HostWindow *window=E2R_HostCreateWindow("Cylinder fixture",0,0,640,640); assert(window);
    unsetenv("E2R_ACTOR_CUES"); unsetenv("E2R_ACTOR_CYLINDERS");
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    Uint32 plain=SDL_MapSurfaceRGBA(window->present_surface,17,17,17,255);
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[320]==plain);
    setenv("E2R_ACTOR_CYLINDERS","1",1);
    memcpy(before,(void*)0x470000,0x240000);
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    assert(!memcmp(before,(void*)0x470000,0x240000));
    for(int i=0;i<640*480;i++) assert(indexed[i]==17);
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[352]!=plain);
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[480]==plain);
    object[2]=8;memcpy(before,(void*)0x470000,0x240000);
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    assert(!memcmp(before,(void*)0x470000,0x240000));
    Uint32 object_color=SDL_MapSurfaceRGB(window->present_surface,140,180,160);
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[480]==object_color);
    assert(E2R_HostDumpPresentation(window,argv[1])==2);
    // RGB conversion on the next frame erases the previous cylinder.
    position(768,0,4096);
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[352]==plain);
    E2R_HostDestroyWindow(window); SDL_DestroySurface(s); free(indexed); free(before);
    puts("PASS: cylinder projection, clipping, object/generated categories, visibility filtering, read-only state and trail-free SDL presentation (synthetic actors)");
}
'''
with tempfile.TemporaryDirectory(prefix='e2-cylinder-check-') as tmp:
    source = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    source.write_text(harness)
    includes = [root / 'E2Recomp/reconstructed', root / 'E2Recomp/platform', root / 'dep/SDL/include']
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-g', '-fno-pie', '-no-pie',
                    '-fms-extensions', '-Wno-macro-redefined', *flags,
                    *[f'-I{p}' for p in includes], str(source), str(library),
                    '-lm', '-ldl', '-lpthread', '-o', str(exe)], check=True)
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', E2R_PROXY_MESH_BYPASS='0')
    subprocess.run([str(exe), str(args.output.resolve())], env=env, check=True, timeout=20)
