#!/usr/bin/env python3
"""Check read-only actor projection and SDL marker presentation with fixtures.

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
#include "e2recomp_actor_markers.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <limits.h>
int E2R_ReplayCaptureIncomplete(void) { return 0; }
uintptr_t _DAT_0073cc3c, _DAT_0063726c, _DAT_006401ec, _DAT_006401d4,
          _DAT_00640118, _DAT_00640114, DAT_0047a34a, DAT_0047a43c,
          DAT_0047a76c, _DAT_00643650, DAT_0047a45e, _DAT_006366b4, _DAT_0063668c;
BOOL IsBadReadPtr(const void *p, UINT_PTR n) {
    if ((uintptr_t)p >= 0x937000 && (uintptr_t)p + n <= 0x938000) return 0;
    return (uintptr_t)p < 0x470000 || (uintptr_t)p + n > 0x6b0000;
}
BOOL E2R_IsBadWritePtr(const void *p, UINT_PTR n) { return !p || !n; }
'''
for name in ('FUN_00422368', 'FUN_00422460', 'FUN_00422538',
             'E2R_TransformVector14', 'E2R_Perspective14'):
    harness += function(recon, name) + '\n'
harness += native[native.index('static void e2r_cue_name('):native.index('/* Host diagnostics only:')] + '\n'
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
    assert(mmap((void*)0x937000,0x1000,PROT_READ|PROT_WRITE,
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
    assert(e2r_marker_kind("korc2","korc",0x1049,0,0)==E2R_MARKER_CREATURE);
    assert(e2r_marker_kind("kdorr","door",0x1049,0,0)==E2R_MARKER_DOOR);
    assert(e2r_marker_kind("mhpot7","potion",0x829,0,0)==E2R_MARKER_POTION);
    assert(e2r_marker_kind("fakepot2","potion",0x829,0,0)==E2R_MARKER_POTION);
    assert(e2r_marker_kind("nschwrt1","nothing",0x6d,0,0)==E2R_MARKER_WEAPON);
    assert(e2r_marker_kind("munze1","coins",0x809,0,0)==E2R_MARKER_ITEM);
    assert(e2r_marker_kind("kdorr","",0x1c48,0,E2R_MARKER_DOOR)==E2R_MARKER_DOOR);
    short potion_top[3],corpse_top[3],door_top[3];
    e2r_marker_offset(E2R_MARKER_POTION,12,potion_top);
    e2r_marker_offset(E2R_MARKER_CORPSE,4,corpse_top);
    e2r_marker_offset(E2R_MARKER_DOOR,4,door_top);
    assert(potion_top[1]==-208 && corpse_top[1]==-80 && door_top[1]==-1024);
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
    // Exercise real snapshot classification and retained identity after death.
    _DAT_006366b4=0x6a0000;_DAT_0063668c=0x6a8000;
    memset((void*)_DAT_006366b4,0,40000);memset((void*)_DAT_0063668c,0,4000);
    for(int i=0;i<980;i++)memcpy((void*)(_DAT_006366b4+i*2),"n",2);
    strcpy((char*)_DAT_006366b4+1960,"kdorr");strcpy((char*)_DAT_0063668c,"door");
    *(short*)0x692000=0;*(uint32_t*)(object+0x11e)=0x692000;*(short*)(object+2)=0x1049;
    *(short*)(object+0x82)=7;E2R_GetActorCues(&state);
    assert(state.actors[1].marker_kind==E2R_MARKER_DOOR);
    // Workshop door 980's observed first-node shape: thin X, broad Z,
    // centre (0,-406,-194). Opposite headings put the leaf on opposite sides
    // of its actor/hinge; a centred or X-wide slab fails these checks.
    byte *door_node=(byte*)0x693000;
    short door_rel[3]={0,-406,-194},door_half[3]={32,382,231};
    *(uint32_t*)(object+0x1e)=(uintptr_t)door_node;
    *(uint32_t*)(door_node+0x22)=(uintptr_t)object;
    memcpy(door_node+0x2c,door_rel,6);memcpy(door_node+0x68,door_half,6);
    for(int yaw=-16384;yaw<=16384;yaw+=32768) {
        memcpy(object+6,identity,sizeof identity);
        FUN_00422460((uintptr_t)(object+6),(ushort)yaw);
        memcpy(before,(void*)0x470000,0x240000);
        E2R_GetActorCues(&state);
        assert(!memcmp(before,(void*)0x470000,0x240000));
        E2R_ActorCue *door=&state.actors[1];
        int lo=640,hi=0;
        for(int i=0;i<8;i++) {
            assert(door->cylinder[i][2]>0);
            if(door->cylinder[i][0]<lo)lo=door->cylinder[i][0];
            if(door->cylinder[i][0]>hi)hi=door->cylinder[i][0];
        }
        int hinge=door->screen[0][0];
        assert(hi-lo>50);
        if(yaw>0)assert(lo<hinge-50 && hi<hinge+10);
        else assert(hi>hinge+50 && lo>hinge-10);
    }
    *(uint32_t*)(object+0x1e)=0;
    *(short*)(object+0x82)=11;*(uint32_t*)(object+0x11e)=0;E2R_GetActorCues(&state);
    assert(state.actors[1].marker_kind==E2R_MARKER_DEBRIS);
    *(short*)(object+0x82)=7;*(uint32_t*)(object+0x11e)=0x692000;
    strcpy((char*)_DAT_0063668c,"korc");E2R_GetActorCues(&state);
    assert(state.actors[1].marker_kind==E2R_MARKER_CREATURE);
    // Living creatures retain the projected local +Z direction line after
    // replacing their cylinders. Verify both headings beyond the body outline.
    for(int yaw=-16384;yaw<=16384;yaw+=32768) {
        memcpy(object+6,identity,sizeof identity);
        FUN_00422460((uintptr_t)(object+6),(ushort)yaw);
        E2R_GetActorCues(&state);
        E2R_ActorCue *creature=&state.actors[1];
        int x=creature->local_z_tip[0],y=creature->local_z_tip[1];
        assert(x>=0 && x<640 && y>=0 && y<480 && creature->local_z_tip[2]>0);
        assert((x>creature->screen[0][0])==(yaw>0));
        clear(s);assert(e2r_cue_marker(s,creature,cyan));
        assert(((Uint32*)((byte*)s->pixels+y*s->pitch))[x]==cyan);
        creature->marker_kind=E2R_MARKER_CORPSE;
        clear(s);assert(e2r_cue_marker(s,creature,cyan));
        assert(((Uint32*)((byte*)s->pixels+y*s->pitch))[x]==0);
    }
    *(short*)(object+0x82)=11;*(uint32_t*)(object+0x11e)=0;E2R_GetActorCues(&state);
    assert(state.actors[1].marker_kind==E2R_MARKER_CORPSE);
    *(short*)(object+0x82)=7;*(uint32_t*)(object+0x11e)=0x692000;
    strcpy((char*)_DAT_0063668c,"potion");strcpy((char*)_DAT_006366b4+1960,"mhpot7");
    *(short*)(object+2)=0x829;E2R_GetActorCues(&state);
    assert(state.actors[1].marker_kind==E2R_MARKER_POTION);
    SDL_Surface *shapes=SDL_CreateSurface(640,480,SDL_PIXELFORMAT_ARGB8888);assert(shapes);
    for(int kind=E2R_MARKER_OBJECT;kind<=E2R_MARKER_ITEM;kind++) {
        E2R_ActorCue marker=state.actors[1];marker.marker_kind=kind;
        // Reuse the actual camera transform for every world-space shape.
        for(int j=0;j<16;j++) {
            short off[3],relative[3],projected[3];e2r_marker_offset(kind,j,off);
            for(int k=0;k<3;k++)relative[k]=object_pos[k]+off[k];
            E2R_TransformVector14(projected,relative,identity);
            E2R_Perspective14(projected,1024*4096,1);
            marker.cylinder[j][0]=(projected[0]>>4)+320;
            marker.cylinder[j][1]=(projected[1]>>4)+240;
            marker.cylinder[j][2]=projected[2];
        }
        clear(shapes);assert(e2r_cue_marker(shapes,&marker,cyan));assert(pixels(shapes)>12);
    }
    SDL_DestroySurface(shapes);
    _DAT_006366b4=_DAT_0063668c=0;
    *(uint32_t*)(object+0x11e)=0;object[2]=0;
    position(0,0,4096); memcpy(joe+6,identity,sizeof identity);
    *(short*)(joe+0x92)=0;
    byte *indexed=malloc(640*480); assert(indexed); memset(indexed,17,640*480);
    E2R_HostWindow *window=E2R_HostCreateWindow("Cylinder fixture",0,0,640,640); assert(window);
    DAT_0047a45e=0;
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
    E2R_GetActorCues(&state);
    int object_x=state.actors[1].cylinder[0][0],object_y=state.actors[1].cylinder[0][1];
    assert(((Uint32*)((byte*)window->present_surface->pixels+object_y*window->present_surface->pitch))[object_x]==object_color);
    assert(E2R_HostDumpPresentation(window,argv[1])==2);
    // Modal requesters must remain legible with markers enabled.
    DAT_0047a45e=0x280000;
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[480]==plain);
    DAT_0047a45e=0;
    // RGB conversion on the next frame erases the previous cylinder.
    position(768,0,4096);
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    assert(((Uint32*)((byte*)window->present_surface->pixels+120*window->present_surface->pitch))[352]==plain);
    // Health and effects stay visible when Joe's marker is offscreen. Timer
    // reads must preserve the real packed pool, and reject invalid/cyclic links.
    byte *timer=(byte*)0x9373dc;
    *(short*)(joe+0xec)=70;
    *(uint32_t*)(joe+0xa6)=0x694000;
    *(short*)0x694000=391;
    *(uint32_t*)(joe+0x17c)=(uintptr_t)timer;
    *(short*)timer=5;*(uint32_t*)(timer+6)=(uintptr_t)(timer+10);
    *(short*)(timer+10)=387;
    byte saved_timers[1000];memcpy(saved_timers,timer,sizeof saved_timers);
    memcpy(before,(void*)0x470000,0x240000);
    E2R_GetActorCues(&state);
    assert(state.actors[0].health==70 && state.actors[0].healing);
    assert(state.actors[0].poison_status==E2R_POTION_ACTIVE);
    assert(state.actors[0].invisibility_status==E2R_POTION_ACTIVE);
    assert(!memcmp(saved_timers,timer,sizeof saved_timers));
    assert(!memcmp(before,(void*)0x470000,0x240000));
    // An unrelated actor's status cannot enter Joe's readout.
    *(uint32_t*)(joe+0x17c)=0;*(uint32_t*)(object+0x17c)=(uintptr_t)timer;
    *(short*)0x694000=11;E2R_GetActorCues(&state);
    assert(!state.actors[0].healing && !state.actors[0].poison_status && !state.actors[0].invisibility_status);
    *(uint32_t*)(joe+0x17c)=(uintptr_t)timer;*(short*)timer=409;
    *(uint32_t*)(timer+6)=(uintptr_t)timer;
    E2R_GetActorCues(&state);assert(state.actors[0].poison_status==E2R_POTION_PENDING);
    *(uint32_t*)(joe+0x17c)=0x9373dd;
    E2R_GetActorCues(&state);assert(!state.actors[0].poison_status);
    *(short*)0x694000=387;E2R_GetActorCues(&state);
    assert(state.actors[0].invisibility_status==E2R_POTION_FADING);
    *(uint32_t*)(joe+0x17c)=0;
    position(30000,0,4096);
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    SDL_Surface *present=window->present_surface;
    // The doubled H in HEALTH begins at (12,438); its left stroke is 2x14.
    for(int y=438;y<452;y++)for(int x=12;x<14;x++)
        assert(((Uint32*)((byte*)present->pixels+y*present->pitch))[x]==cyan);
    char status_path[1024];snprintf(status_path,sizeof status_path,"%s-status",argv[1]);
    assert(E2R_HostDumpPresentation(window,status_path)==2);
    DAT_0047a45e=0x280000;
    assert(E2R_HostPresentIndexed8(window,indexed,640,480,640,NULL));
    assert(((Uint32*)((byte*)present->pixels+438*present->pitch))[12]==plain);
    E2R_HostDestroyWindow(window); SDL_DestroySurface(s); free(indexed); free(before);
    puts("PASS: marker projection, door hinge/axes, living creature vectors, clipping, categories, visibility, read-only state and trail-free SDL presentation (synthetic actors)");
}
'''
with tempfile.TemporaryDirectory(prefix='e2-cylinder-check-') as tmp:
    source = Path(tmp) / 'check.c'
    exe = Path(tmp) / 'check'
    source.write_text(harness)
    includes = [root / 'E2Recomp/reconstructed', root / 'E2Recomp/platform', root / 'dep/SDL/include', root / 'src/replay/include']
    flags = ['-fsanitize=address', '-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc, '-m32', '-O1', '-g', '-fno-pie', '-no-pie',
                    '-fms-extensions', '-Wno-macro-redefined', '-DE2R_HOST_BACKEND_SDL=1', *flags,
                    *[f'-I{p}' for p in includes], str(source), str(library),
                    '-lm', '-ldl', '-lpthread', '-o', str(exe)], check=True)
    env = os.environ.copy()
    env.update(SDL_VIDEODRIVER='dummy', E2R_PROXY_MESH_BYPASS='0')
    subprocess.run([str(exe), str(args.output.resolve())], env=env, check=True, timeout=20)
