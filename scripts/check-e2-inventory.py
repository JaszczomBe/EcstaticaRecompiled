#!/usr/bin/env python3
"""Compare recovered inventory selections, digits and timer-mask pixels with original x86."""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source = (root / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
image = OriginalImage(args.exe)
h = support() + r'''
#include <assert.h>
#include <string.h>
#include <sys/mman.h>
typedef unsigned char byte;
typedef unsigned uint,undefined4;
#define WORD(a) (*(int *)(a))
#define SHORT(a) (*(short *)(a))
static int DAT_0047ab14=-19001;
static int DAT_0047ab18=-19002;
#define DAT_0047ab1c WORD(0x47ab1c)
#define DAT_0047ab20 WORD(0x47ab20)
#define DAT_0047ab24 WORD(0x47ab24)
static int DAT_0047ab28=-19003;
static unsigned missing;
static const char *names[]={"ringicon","amuicon1","lampicon","shdicon1","shdicon2",
 "scrlicon","amuicon2","kingicon","elder1","elder2","elder3","elder4","elder5","elder6","elder7"};
__attribute__((used,noinline)) static int lookup(const char *name) {
 for(int i=0;i<15;i++)if(!strcmp(name,names[i]))return missing&(1<<i)?-1:i;
 abort();
}
static int FUN_00441ea4(unsigned name,int unused) {return lookup((const char*)name);}
'''
h += '#include "' + str(root / 'E2Recomp/platform/e2recomp_hud.h') + '"\n'
for name in ('E2R_GetInventoryState', 'E2R_InventoryNumber', 'E2R_DrawInventoryState'):
    h += function(source, name) + '\n'
h += r'''
struct Graphic {char name[12];int x,y;};
static struct Graphic graphics[64];static unsigned count;
static byte pixels[640*480];
__attribute__((used,noinline)) static void graphic(void *context,const char *name,int x,int y) {
 assert(count<64);struct Graphic *g=graphics+count++;
 memset(g,0,sizeof(*g));strcpy(g->name,name);g->x=x;g->y=y;
}
__attribute__((used,noinline)) static unsigned read_pixel(int page,int x,int y) {
 assert(page==0&&x>=0&&x<640&&y>=0&&y<480);return pixels[y*640+x];
}
__attribute__((used,noinline)) static void write_pixel(int page,int x,int y) {
 assert(page==0&&x>=0&&x<640&&y>=0&&y<480);pixels[y*640+x]=SHORT(0x6366dc);
}
static void masked(void *context,int x,int y,int color) {
 assert(x>=0&&x<640&&y>=0&&y<480);if(pixels[y*640+x]==7)pixels[y*640+x]=color;
}
__attribute__((naked)) static void lookup_hook(void) {
 __asm__("pushal; push %eax; call lookup; add $4,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void graphic_hook(void) {
 __asm__("pushal; push %ebx; push %edx; push %eax; push $0; call graphic; add $16,%esp; popal; ret");
}
__attribute__((naked)) static void read_hook(void) {
 __asm__("pushal; push %ebx; push %edx; push %eax; call read_pixel; add $12,%esp; mov %eax,28(%esp); popal; ret");
}
__attribute__((naked)) static void write_hook(void) {
 __asm__("pushal; push %ebx; push %edx; push %eax; call write_pixel; add $12,%esp; popal; ret");
}
__attribute__((naked)) static void empty_hook(void) {__asm__("ret");}
static void map(unsigned address,unsigned size) {assert(mmap((void*)address,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)address);}
static void hook(unsigned at,void *to) {*(byte*)at=0xe9;WORD(at+1)=(unsigned)to-at-5;}
'''
for start, end in ((0x4561c8, 0x456924), (0x475f90, 0x476088), (0x4161c5, 0x4161f0)):
    code = image.code(start, end) + (b'\xc3' if start == 0x4161c5 else b'')
    h += f'static const byte code_{start:x}[]={{' + ','.join(map(str, code)) + '};\n'
# Compare the actual repaired caller's queue/gate fragment as well.
caller = function(source, 'FUN_00415d40')
start = caller.index('  if ((*(byte *)0x004c39ac')
end = caller.index('  if ((*(byte *)0x004c39af', start)
h += r'''
static int opens;
#define DAT_0047a34a SHORT(0x47a34a)
#define DAT_0047a788 SHORT(0x47a788)
static void FUN_00455fe8(int unused) {opens++;}
__attribute__((naked)) static void open_hook(void) {__asm__("pushal; incl opens; popal; ret");}
static void enter_decision(void) {
 int param_1=0,param_2=0,extraout_ECX_02=0,extraout_EDX_02=0;
''' + caller[start:end] + '}\n'
h += r'''
int main(void) {
 map(0x410000,0x10000);map(0x440000,0x20000);map(0x470000,0x10000);
 map(0x4c0000,0x10000);map(0x630000,0x10000);map(0x670000,0x10000);map(0xac0000,0x10000);
 memcpy((void*)0x4561c8,code_4561c8,sizeof code_4561c8);
 memcpy((void*)0x475f90,code_475f90,sizeof code_475f90);
 memcpy((void*)0x4161c5,code_4161c5,sizeof code_4161c5);
 hook(0x441ea4,lookup_hook);hook(0x455850,graphic_hook);
 hook(0x41b994,read_hook);hook(0x41b920,write_hook);
 hook(0x456f94,empty_hook);hook(0x456a3c,empty_hook);hook(0x455fe8,open_hook);
 E2R_InventoryPainter painter={0,graphic,masked};unsigned cases=0;
 const int counters[]={0,1,70,99999,100001,-1,-12345,2147483647};
 const int visited[]={0,1,10,480,990,1000,1001,1199,1200};
 const int powers[]={100,150,200,201};
 for(int scenario=0;scenario<256;scenario++) {
  missing=scenario%4==0?0x7fff:scenario%4==1?0:scenario*127&0x7fff;
  for(int i=0;i<15;i++)SHORT(0x670c38+i*2)=scenario%3==0?8:((scenario+i)%3==1?0:0xffff);
  memset((void*)0xac4b00,0,150);int bits=visited[scenario%9];
  for(int i=0;i<bits;i++)*(byte*)(0xac4b00+i/8)|=1<<(i%8);
  WORD(0x47ab18)=counters[scenario%8];WORD(0x47ab14)=counters[(scenario+3)%8];
  DAT_0047ab20=scenario%7*17;DAT_0047ab24=scenario%2?103:0;
  WORD(0x47ab28)=powers[scenario%4];DAT_0047ab1c=42;
  E2R_InventoryState state;E2R_GetInventoryState(&state);
  count=0;memset(pixels,7,sizeof pixels);for(unsigned i=0;i<sizeof pixels;i+=11)pixels[i]=73;
  byte original[sizeof pixels];memcpy(original,pixels,sizeof pixels);
  struct E2R_Registers regs={0};e2r_original_call(0x4561c8,&regs);
  struct Graphic expected[64];unsigned n=count;memcpy(expected,graphics,sizeof expected);
  byte expected_pixels[sizeof pixels];memcpy(expected_pixels,pixels,sizeof pixels);
  assert(DAT_0047ab1c==state.progress);
  count=0;memcpy(pixels,original,sizeof pixels);E2R_DrawInventoryState(&state,&painter);
  if(n!=count||memcmp(expected,graphics,n*sizeof(*graphics))) {
   fprintf(stderr,"selection mismatch scenario=%d count=%u/%u\n",scenario,n,count);abort();
  }
  assert(e2r_memory_equal("timer mask",expected_pixels,pixels,sizeof pixels));cases++;
 }
 printf("PASS: %u original-x86 status selections, digit sequences, progress and timer-mask pixel cases\n",cases);
 cases=0;
 for(int key=0;key<256;key++)for(int gate=0;gate<3;gate++) {
  *(byte*)0x4c39ac=key;DAT_0047a34a=gate;DAT_0047a788=0;opens=0;
  struct E2R_Registers regs={0};e2r_original_call(0x4161c5,&regs);
  int expected[]={*(byte*)0x4c39ac,DAT_0047a788,opens};
  *(byte*)0x4c39ac=key;DAT_0047a34a=gate;DAT_0047a788=0;opens=0;
  enter_decision();int actual[]={*(byte*)0x4c39ac,DAT_0047a788,opens};
  assert(!memcmp(expected,actual,sizeof expected));cases++;
 }
 printf("PASS: %u live Enter queue consumption/eligibility decisions\n",cases);
}
'''
run_fixture(h, asan=args.asan, keep=args.keep_harness, image=image,
            dependencies=('packed scene-name lookup', 'temporary-graphic emission', 'pixel get/set',
                          'legacy registered graphics/HUD leaves', 'icon-page dispatch'))
