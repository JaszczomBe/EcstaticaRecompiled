#!/usr/bin/env python3
"""Compare installed HUD sprite raster and line pixels against bounded original x86."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, run_fixture, support

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('exe', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--keep-harness', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parent.parent
image = OriginalImage(a.exe)
h = support() + '#include "'+str(root/'E2Recomp/platform/e2recomp_hud.c')+'"\n'
h += r'''
#include <assert.h>
#include <ctype.h>
#include <unistd.h>
typedef unsigned char byte;
#include <sys/mman.h>
static E2R_HudState test_state;
void E2R_GetOriginalHudState(E2R_HudState *state) {*state=test_state;}
void E2R_DrawOriginalHudState(const E2R_HudState *s,const E2R_HudPainter *p) {p->graphic(p->context,"life1",25,8,0);}
HANDLE CreateFileA(LPCSTR path,DWORD access,DWORD share,LPVOID security,DWORD creation,DWORD flags,HANDLE template) {
    char actual[64];strcpy(actual,path);char *slash=strchr(actual,'/');assert(slash);
    for(char *c=slash+1;*c;c++)*c=toupper((unsigned char)*c);
    actual[0]=toupper(actual[0]);FILE *file=fopen(actual,"rb");
    return file?(HANDLE)file:INVALID_HANDLE_VALUE;
}
BOOL ReadFile(HANDLE file,LPVOID buffer,DWORD bytes,DWORD *read,LPVOID overlapped) {
    *read=fread(buffer,1,bytes,(FILE *)file);return !ferror((FILE *)file);
}
DWORD SetFilePointer(HANDLE file,LONG distance,PLONG high,DWORD method) {assert(method==0);return fseek((FILE*)file,distance,SEEK_SET)?-1:ftell((FILE*)file);}
BOOL CloseHandle(HANDLE file) {return !fclose((FILE*)file);}
static byte expected[704*480],actual[704*480];
__attribute__((naked)) static void lock_hook(void) {__asm__("movl $704,(%edx); mov $expected,%eax; ret");}
__attribute__((naked)) static void empty_hook(void) {__asm__("ret");}
__attribute__((naked)) static void original_sprite(const byte *pixels,int x,int y,int width,int height) {
    __asm__("pushal; mov 36(%esp),%eax; mov 40(%esp),%ebx; mov 44(%esp),%ecx; "
            "mov 48(%esp),%esi; mov 52(%esp),%edi; push %edi; push %esi; mov $2,%edx; "
            "mov $0x41831c,%edi; call *%edi; popal; ret");
}
static void map(unsigned address,unsigned size) {assert(mmap((void*)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)address);}
static void hook(unsigned at,void *to) {*(byte*)at=0xe9;*(int*)(at+1)=(unsigned)to-at-5;}
'''
for start,end in ((0x41831c,0x418484),(0x41b540,0x41b740),(0x41b078,0x41b08c)):
    h += f'static const unsigned char code_{start:x}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
h += r'''
int main(int argc,char **argv) {
 assert(argc==2&&!chdir(argv[1]));
 map(0x410000,0x10000);map(0x470000,0x10000);map(0x630000,0x20000);map(0x900000,640*480*2+4096);
 memcpy((void*)0x41831c,code_41831c,sizeof code_41831c);
 memcpy((void*)0x41b540,code_41b540,sizeof code_41b540);
 memcpy((void*)0x41b078,code_41b078,sizeof code_41b078);
 hook(0x418a04,lock_hook);hook(0x418b00,empty_hook);
 hook(0x41c884,empty_hook);hook(0x41ca90,empty_hook);hook(0x41bd1c,empty_hook);hook(0x41c518,empty_hook);
 *(int*)0x47a43c=1;*(int*)0x6401ec=640;*(int*)0x6401d4=480;*(int*)0x63666c=0x900000;
 const char *names[]={"life1","life2","life3","armour2","armour3","hndicon1","swdicon1","rodicon1",
 "bar1","bar2","bar3","bar4","bar5","magic1","magic1b","magic1c","magic1d","magic1e","magic1f",
 "magic2","magic2b","magic2c","magic2d","magic2e","magic2f","magic3","magic3b","magic3c","magic3d","magic3e","magic3f","magibar1"};
 unsigned cases=0;
 for(int n=0;n<32;n++)for(int position=0;position<3;position++) {
  const E2R_HudGraphic *g=e2r_hud_load(names[n],1);assert(g&&g->pixels);
  byte *normalized=malloc(g->width*g->height);assert(normalized);
  for(int i=0;i<g->width*g->height;i++)normalized[i]=g->pixels[i]<=1?255:g->pixels[i];
  memset(expected,73,sizeof expected);memset(actual,73,sizeof actual);
  int x=position==0?25:position==1?640-g->width:0;
  int y=position==0?8:position==1?480-g->height:0;
  original_sprite(normalized,x,y,g->width,g->height);
  E2R_HudTarget target={actual,640,480,704,1};e2r_hud_graphic(&target,names[n],x,y,0);
  assert(e2r_memory_equal(names[n],expected,actual,sizeof expected));free(normalized);cases++;
 }
 printf("PASS: %u installed original HUD sprite/padded-pitch pixel comparisons\n",cases);
 cases=0;
 for(int x0=-20;x0<=660;x0+=17)for(int x1=-20;x1<=660;x1+=19)for(int y=0;y<480;y+=79) {
  memset(expected,73,sizeof expected);memset(actual,73,sizeof actual);
  *(short*)0x6366dc=11;*(short*)0x6366a8=2;
  struct E2R_Registers regs={.eax=0,.edx=x0,.ebx=y};e2r_original_call(0x41b078,&regs);
  regs=(struct E2R_Registers){.eax=0,.edx=x1,.ebx=y};e2r_original_call(0x41b540,&regs);
  E2R_HudTarget target={actual,640,480,704,1};e2r_hud_line(&target,0,x0,y,x1,y,11);
  assert(e2r_memory_equal("line",expected,actual,sizeof expected));cases++;
 }
 printf("PASS: %u original-x86 HUD line pixels with clipping, reverse and zero-length segments\n",cases);
 memset(actual,73,sizeof actual);byte before[sizeof actual];memcpy(before,actual,sizeof actual);
 test_state.visible=1;test_state.high=1;
 assert(!E2R_DebugOverlaySelected());const byte *composed=E2R_ComposeOriginalHud(actual,640,480,704);
 assert(composed!=actual&&!memcmp(actual,before,sizeof actual));
 byte saved[sizeof actual];memcpy(saved,composed,sizeof saved);
 assert(E2R_HandleDisplayKey(WM_KEYDOWN,0x71));assert(E2R_HandleDisplayKey(WM_KEYDOWN,0x71));
 assert(E2R_HandleDisplayKey(WM_KEYUP,0x71));assert(E2R_ComposeOriginalHud(actual,640,480,704)==actual);
 assert(E2R_HandleDisplayKey(WM_KEYDOWN,0x70));assert(!E2R_HandleDisplayKey(WM_KEYDOWN,0x7b));
 composed=E2R_ComposeOriginalHud(actual,640,480,704);assert(!memcmp(saved,composed,sizeof saved));
 test_state.visible=0;assert(E2R_ComposeOriginalHud(actual,640,480,704)==actual);
 puts("PASS: independent idempotent mode keys, untouched source pages, repeatable composition and modal suppression");
}
'''
# Use the fixture runner's isolated process; the data directory is an explicit
# argv, and all asset access in this fixture is read-only.
# run_fixture accepts no argv: adapt main's data-directory input as a literal.
h=h.replace('assert(argc==2&&!chdir(argv[1]));','assert(!chdir('+repr(str(a.exe.resolve().parent)).replace("'",'"')+'));')
run_fixture(h,asan=a.asan,keep=a.keep_harness,image=image,
            dependencies=['file reads use installed RAW assets, no palette replacement',
                          'surface locking/unlocking and video synchronization intercepted',
                          'snapshot/planner stubbed only for isolated composition-policy checks'])
