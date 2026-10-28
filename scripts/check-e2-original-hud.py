#!/usr/bin/env python3
"""Compare production HUD selections and bar endpoints with bounded original x86."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('exe', type=Path)
p.add_argument('--asan', action='store_true')
p.add_argument('--keep-harness', type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parent.parent
image = OriginalImage(a.exe)
source = (root/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
h = support() + r'''
#include <assert.h>
#include <stdbool.h>
typedef unsigned uint,undefined4;
#include <string.h>
#include <sys/mman.h>
typedef unsigned char byte;
#define WORD(a) (*(int *)(a))
#define SHORT(a) (*(short *)(a))
#define DAT_0047a43c WORD(0x47a43c)
#define DAT_0047a76c WORD(0x47a76c)
#define DAT_0047a448 WORD(0x47a448)
#define DAT_0047a34a WORD(0x47a34a)
#define DAT_0047a45e WORD(0x47a45e)
#define DAT_0047ab2c WORD(0x47ab2c)
#define _DAT_00630b60 WORD(0x630b60)
#define _DAT_00636588 WORD(0x636588)
#define E2R_WORD_AT(v,n) (*(unsigned short *)((char *)&(v)+(n)))
static int IsBadReadPtr(const void *p,unsigned n) {return !p;}
int E2R_InventoryPageActive(void) {return 0;}
'''
h += '#include "'+str(root/'E2Recomp/platform/e2recomp_hud.h')+'"\n'
for name in ('E2R_GetOriginalHudState', 'E2R_HudLifeLines', 'E2R_DrawOriginalHudState'):
    h += function(source, name)+'\n'
h += r'''
struct Graphic {char name[9];int x,y,center;};
static struct Graphic graphics[64];static unsigned graphic_count;
static int lines[256][6],line_count,cursors[3][2];
__attribute__((used,noinline)) static void graphic(void *ctx,const char *name,int x,int y,int center) {
    unsigned i;for(i=0;i<graphic_count;i++)if(!strcmp(name,graphics[i].name))break;
    assert(i<64);if(i==graphic_count)graphic_count++;
    strcpy(graphics[i].name,name);graphics[i].x=x;graphics[i].y=y;graphics[i].center=center;
}
__attribute__((used,noinline)) static void remove_graphic(const char *name) {
    for(unsigned i=0;i<graphic_count;i++)if(!strcmp(name,graphics[i].name)) {
        memmove(graphics+i,graphics+i+1,(--graphic_count-i)*sizeof(*graphics));return;
    }
}
static void line(void *ctx,int page,int x0,int y0,int x1,int y1,int color) {
    assert(line_count<256);int row[]={page,x0,y0,x1,y1,color};
    memcpy(lines[line_count++],row,sizeof row);
}
__attribute__((used,noinline)) static void move_original(int page,int x,int y) {assert(page>=0&&page<3);cursors[page][0]=x;cursors[page][1]=y;}
__attribute__((used,noinline)) static void line_original(int page,int x,int y) {
    line(0,page,cursors[page][0],cursors[page][1],x,y,SHORT(0x6366dc+page*2));
    move_original(page,x,y);
}
__attribute__((naked)) static void graphic_hook(void) {
    __asm__("pushal; push %ecx; push %ebx; push %edx; push %eax; push $0; call graphic; add $20,%esp; popal; ret");
}
__attribute__((naked)) static void remove_hook(void) {
    __asm__("pushal; push %eax; call remove_graphic; add $4,%esp; popal; ret");
}
__attribute__((naked)) static void move_hook(void) {
    __asm__("pushal; push %ebx; push %edx; push %eax; call move_original; add $12,%esp; popal; ret");
}
__attribute__((naked)) static void line_hook(void) {
    __asm__("pushal; push %ebx; push %edx; push %eax; call line_original; add $12,%esp; popal; ret");
}
static void map(unsigned address,unsigned size) {assert(mmap((void*)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)address);}
static void hook(unsigned at,void *to) {*(byte*)at=0xe9;WORD(at+1)=(unsigned)to-at-5;}
'''
ranges = ((0x4559bc,0x455e84), (0x456a3c,0x456f94), (0x456f94,0x457410),
          (0x457410,0x4575c4), (0x416221,0x416255), (0x475e30,0x475f74), (0x47ab44,0x47ace2))
for start, end in ranges:
    h += f'static const byte code_{start:x}[]={{'+','.join(map(str,image.code(start,end)))+'};\n'
toggle = function(source, 'FUN_00415d40')
start = toggle.index("  if ((*(byte *)0x004c39a7) !=")
end = toggle.index('  if (((DAT_00636844', start)
h += r'''
static int show_calls,hide_calls;
__attribute__((used,noinline)) static void FUN_004559bc(void) {show_calls++;}
__attribute__((used,noinline)) static void FUN_00455e84(void) {hide_calls++;}
__attribute__((naked)) static void show_hook(void) {__asm__("pushal; call FUN_004559bc; popal; ret");}
__attribute__((naked)) static void hide_hook(void) {__asm__("pushal; call FUN_00455e84; popal; ret");}
static void toggle_decision(void) {
 bool bVar3;undefined4 param_1=0,param_2=0,extraout_ECX_04=0,extraout_EDX_03=0,extraout_ECX_05=0,extraout_EDX_04=0;
''' + toggle[start:end] + '}\n'
h += r'''
int main(void) {
 map(0x410000,0x10000);map(0x450000,0x10000);map(0x470000,0x10000);
 map(0x4c0000,0x10000);map(0x630000,0x10000);map(0x900000,0x10000);
'''
for start, _ in ranges:
    h += f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
h += r'''
 hook(0x4555b0,graphic_hook);hook(0x455940,remove_hook);
 hook(0x41b078,move_hook);hook(0x41b34c,line_hook);
 E2R_HudPainter painter={0,graphic,line};unsigned cases=0;
 const int maxima[]={100,200,300};const int armours[]={0,100,101,200,201,300};
 for(int high=0;high<2;high++)for(int maximum=0;maximum<3;maximum++)
 for(int kind=0;kind<4;kind++)for(int magic=0;magic<=24;magic++) {
  memset((void*)0x900000,0,0x1000);_DAT_00630b60=0x900000;DAT_0047a43c=high;
  WORD(0x900054)=0x900200;WORD(0x900220)=kind==0?0:0x900400;
  WORD(0x90053a)=kind>=2?0x900600:0;*(byte*)0x900602=kind==3?0x10:0;
  SHORT(0x9000ee)=maxima[maximum];SHORT(0x900182)=armours[magic%6];
  SHORT(0x900184)=magic;SHORT(0x900782)=100+(magic%7)*100;
  SHORT(0x900784)=magic%5;SHORT(0x900786)=200+(magic%5)*100;
  E2R_HudState state;E2R_GetOriginalHudState(&state);
  graphic_count=0;line_count=0;struct E2R_Registers regs={0};
  e2r_original_call(0x4559bc,&regs);e2r_original_call(0x456f94,&regs);
  struct Graphic expected[64];unsigned count=graphic_count;memcpy(expected,graphics,sizeof expected);
  graphic_count=0;line_count=0;E2R_DrawOriginalHudState(&state,&painter);
  assert(graphic_count==count);
  for(unsigned i=0;i<count;i++) {
   unsigned j;for(j=0;j<graphic_count;j++)if(!strcmp(expected[i].name,graphics[j].name))break;
   if(j==graphic_count||memcmp(&expected[i],&graphics[j],sizeof(*graphics))) {
    fprintf(stderr,"graphic high=%d max=%d kind=%d magic=%d name=%s\n",high,maximum,kind,magic,expected[i].name);abort();
   }
  }
  cases++;
 }
 printf("PASS: %u original-x86 life/armour/hand/capacity/player-magic selections\n",cases);
 cases=0;
 for(int high=0;high<2;high++)for(int maximum=0;maximum<3;maximum++)
 for(int life=-1;life<=maxima[maximum];life+=7)for(int poison=0;poison<6;poison++) {
  DAT_0047a43c=high;SHORT(0x9000ee)=maxima[maximum];SHORT(0x9000ec)=life;
  DAT_0047ab2c=poison?100:0;_DAT_00636588=1000;
  WORD(0x90017c)=poison?0x900900:0;SHORT(0x900900)=5;WORD(0x900902)=1000+poison*21-10;
  E2R_HudState state;E2R_GetOriginalHudState(&state);state.held_present=0;state.magic=0;
  line_count=0;struct E2R_Registers regs={0};e2r_original_call(0x456a3c,&regs);
  int expected[256][6],count=line_count;memcpy(expected,lines,sizeof expected);
  line_count=0;E2R_HudLifeLines(&state,&painter);
  if(count!=line_count||memcmp(expected,lines,count*sizeof(*lines))) {
    fprintf(stderr,"life high=%d max=%d health=%d poison=%d counts=%d/%d\n",high,maximum,life,poison,count,line_count);
    for(int i=0;i<count&&i<line_count;i++)if(memcmp(expected[i],lines[i],sizeof(*lines))) {
     fprintf(stderr,"line %d expected=%d,%d,%d,%d,%d,%d actual=%d,%d,%d,%d,%d,%d\n",i,
      expected[i][0],expected[i][1],expected[i][2],expected[i][3],expected[i][4],expected[i][5],
      lines[i][0],lines[i][1],lines[i][2],lines[i][3],lines[i][4],lines[i][5]);break;
    }abort();
  }cases++;
 }
 printf("PASS: %u original-x86 life/poison line sequences across all three physical/background pages\n",cases);
 cases=0;
 for(int high=0;high<2;high++)for(int charge=-5;charge<=100;charge++) {
  DAT_0047a43c=high;WORD(0x900220)=0x900400;WORD(0x90053a)=0x900600;SHORT(0x900784)=charge;
  E2R_HudState state;E2R_GetOriginalHudState(&state);
  line_count=0;struct E2R_Registers regs={0};e2r_original_call(0x457410,&regs);
  int expected[256][6],count=line_count;memcpy(expected,lines,sizeof expected);
  line_count=0;E2R_DrawOriginalHudState(&state,&painter);
  // Life lines precede charge; compare the charge suffix exactly.
  assert(line_count>=count && !memcmp(expected,lines+line_count-count,count*sizeof(*lines)));cases++;
 }
 printf("PASS: %u original-x86 held-magic meter sequences\n",cases);
 byte before[0x1000];memcpy(before,(void*)0x900000,sizeof before);
 int duration=DAT_0047ab2c;E2R_HudState state;E2R_GetOriginalHudState(&state);
 assert(!memcmp(before,(void*)0x900000,sizeof before)&&duration==DAT_0047ab2c);
 for(int gate=0;gate<5;gate++) {
  DAT_0047a76c=gate==0;DAT_0047a448=gate==1;DAT_0047a34a=gate==2;DAT_0047a45e=gate==3?0x280000:0;
  E2R_GetOriginalHudState(&state);assert(state.visible==(gate==4));
 }
 memcpy((void*)0x416221,code_416221,sizeof code_416221);*(byte*)0x416255=0xc3;
 hook(0x4559bc,show_hook);hook(0x455e84,hide_hook);
 for(int flag=0;flag<256;flag++)for(int hidden=0;hidden<2;hidden++) {
  *(byte*)0x4c39a7=flag;DAT_0047a448=hidden;show_calls=hide_calls=0;
  struct E2R_Registers regs={0};e2r_original_call(0x416221,&regs);
  int expected[]={DAT_0047a448,*(byte*)0x4c39a7,show_calls,hide_calls};
  *(byte*)0x4c39a7=flag;DAT_0047a448=hidden;show_calls=hide_calls=0;toggle_decision();
  int actual[]={DAT_0047a448,*(byte*)0x4c39a7,show_calls,hide_calls};assert(!memcmp(expected,actual,sizeof expected));
 }
 puts("PASS: 512 original live-keyboard HUD visibility decisions; no standalone image-byte latch");
 puts("PASS: HUD observation preserves actor/timer memory and suppresses intro, modal and cinematic draws");
}
'''
run_fixture(h, asan=a.asan, keep=a.keep_harness, image=image,
            dependencies=['graphic registration/removal captured as final named-slot selections',
                          'line cursor/raster captured as exact page/endpoint/colour sequences'])
