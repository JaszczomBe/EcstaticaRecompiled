#!/usr/bin/env python3
"""Compare forward skeletal poses and camera-space origins with original x86.

Runs the original bone solver, endpoint, rotations, scale and vector helpers.
No skeletal dependency is intercepted. This does not qualify rasterization.
"""
import argparse
from pathlib import Path
from e2_original import OriginalImage, function, run_fixture, support

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('exe', type=Path)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
image = OriginalImage(args.exe)
source = (Path(__file__).resolve().parent.parent / 'E2Recomp/reconstructed/E2Recomp_recon.c').read_text()
harness = support() + r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/mman.h>
typedef uint8_t byte;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;
int E2R_IsCharacterActor(uintptr_t actor){return 0;}
#define __fastcall
#define DAT_0047a279 (*(int*)0x47a279)
#define DAT_0047a2a4 (*(int*)0x47a2a4)
#define DAT_0047a43c (*(short*)0x47a43c)
#define DAT_0047a34a (*(short*)0x47a34a)
#define DAT_0047a34c (*(short*)0x47a34c)
#define DAT_0047a366 (*(short*)0x47a366)
#define _DAT_00637240 (*(int*)0x637240)
#define _DAT_006401c8 (*(int*)0x6401c8)
#define _DAT_0064020c (*(int*)0x64020c)
#define _DAT_006401ec (*(int*)0x6401ec)
#define _DAT_006401cc (*(int*)0x6401cc)
#define _DAT_006401fc (*(int*)0x6401fc)
#define _DAT_006401d4 (*(int*)0x6401d4)
static int E2R_actor_calc_context;
static int IsBadReadPtr(const void *p,unsigned n){return !p||!n;}
static int E2R_IsBadWritePtr(const void *p,unsigned n){return !p||!n;}
static void FUN_00426f84(void){abort();}
static int drawn_node,drawn_surface;
static void FUN_004307d0(int node,int surface){drawn_node=node;drawn_surface=surface;}
__attribute__((naked)) static void draw_hook(void){__asm__("mov %eax,drawn_node; mov %edx,drawn_surface; ret");}
void FUN_00423858(uint parent,uint mode);
'''
for name in ('E2R_InitActorShadeTable', 'E2R_UseProxyMesh', 'E2R_SetIdentityMatrix', 'FUN_00422368', 'FUN_00422460',
             'FUN_00422538', 'E2R_ApplyEulerMatrix', 'E2R_TransformVector14',
             'E2R_PolygonAngle16', 'E2R_RotatePolygonNormal', 'E2R_PoseAsin14',
             'E2R_Product14', 'E2R_Sine16', 'E2R_Cosine16', 'FUN_00423674', 'FUN_00424164', 'FUN_00432e08', 'FUN_00423858', 'FUN_00424ed0', 'FUN_00432ecc', 'E2R_Perspective14', 'FUN_00423070', 'FUN_00425538'):
    harness += function(source, name) + '\n'
ranges = [(0x414f00, 0x414f40), (0x415167, 0x41535c), (0x432ecc, 0x433689), (0x425538, 0x4257e0), (0x423070, 0x42315e), (0x423858, 0x424318), (0x423674, 0x423858), (0x424ed0, 0x424f9b),
          (0x422330, 0x422abc), (0x432c64, 0x432ecc), (0x45dd04, 0x45df0e)]
for start, end in ranges:
    harness += f'static const byte code_{start:x}[]={{' + ','.join(map(str, image.code(start, end))) + '};\n'
harness += r'''
__attribute__((naked)) static void original_shade_table(void){
 __asm__("pushal; sub $56,%esp; mov $0x415167,%eax; call *%eax; add $56,%esp; popal; ret");
}
static void map(uint at,uint size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)at);}
static uint rng=0x23858;
static uint next(void){rng=rng*1664525u+1013904223u;return rng;}
static void setup(int kind,int seed){
 memset((void*)0x900000,0,0x10000);
 *(int*)0x637240=seed&1;*(int*)0x6368d8=*(int*)0x6368dc=0;
 E2R_actor_calc_context=0x909000;
 int parent=0x900000;
 E2R_ApplyEulerMatrix((short*)(parent+6),(short*)(parent+0x90));
 *(int*)(parent+0x1e)=0x901000;*(short*)(parent+4)=seed&1?7:0;
 *(int*)(parent+0x11e)=0x905000;
 *(int*)0x905026=0x905040;
 for(int i=0;i<3;i++){
  *(short*)(parent+0x18+i*2)=(short)(seed*719+i*373);
  *(short*)(parent+0x80+i*2)=(short)(seed*173+i*197);
  *(short*)(parent+0x6e + i*2)=(short)(seed*11+i*37);
  *(short*)(0x905004+i*2)=(short)(seed*19+i*73);
  *(short*)(0x905044+i*2)=(short)(seed*43+i*157);
 }
 for(int j=0;j<5;j++){
  int node=0x901000+j*0x200;
  *(short*)(node+4)=j==4?4:7;
  *(int*)(node+0x22)=parent;
  *(int*)(node+0x1e)=j<2?node+0x200:0;
  *(int*)(node+0x44)=j?node-0x200:parent;
  *(int*)(node+0xca)=j==0?0x901600:0;
  *(byte*)(node+2)=(seed&2)?0x10:0;
  *(int*)(node+0x11e)=j==4?0x905080:0;
  for(int i=0;i<3;i++){
   *(short*)(node+0x26+i*2)=(short)(seed*1973+i*577+j*719);
   *(short*)(node+0x2c+i*2)=(short)(seed%17*11+j*73+i*41);
   *(short*)(node+0x6e + i*2)=i==2?200:0;
   *(short*)(node+0x68+i*2)=*(short*)(node+0xb0+i*2)=256+i*32;
   *(short*)(node+0xb6+i*2)=i==2?200:0;
  }
  E2R_ApplyEulerMatrix((short*)(node+0xec),(short*)(node+0x26));
  *(short*)(node+0xa8)=100;
 }
 if(kind==1||kind==2){
  *(int*)0x90112e=0x904000;*(int*)0x904022=0x904400;
  *(byte*)0x904403=kind==1?0x80:0;
  for(int i=0;i<3;i++)*(short*)(0x904010+i*2)=(short)(seed*31+i*97);
 }
 if(kind>=3){
  *(byte*)0x901002|=0x20|(seed&4?0x80:0);
  // Frozen and computed endpoint targets, folded and stretched limbs.
  *(byte*)0x901402|=0x40;
  *(short*)0x901430=kind==3?40:kind==4?600:0;
  *(short*)0x90142c=kind==5?0:seed%53;
  *(short*)0x90142e=kind==5?0:seed%29;
  *(int*)0x9014ca=0x901800;
 }
}
int main(void){
 map(0x410000,0x10000);map(0x500000,0x80000);map(0x420000,0x20000);map(0x450000,0x10000);map(0x470000,0x10000);
 map(0x580000,0x90000);map(0x630000,0x20000);map(0x900000,0x10000);
'''
for start, _ in ranges:
    harness += f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
harness += r'''
 *(byte*)0x4307d0=0xe9;*(int*)0x4307d1=(uint)draw_hook-0x4307d0-5;
 *(byte*)0x41535c=0xc3;
 original_shade_table();
 static byte shade_expected[0x40000];memcpy(shade_expected,(void*)0x507590,sizeof shade_expected);
 memset((void*)0x507590,0,sizeof shade_expected);E2R_InitActorShadeTable();
 assert(e2r_memory_equal("actor shade table",shade_expected,(void*)0x507590,sizeof shade_expected));
 puts("PASS: 262144 original-x86 actor palette/shade entries");
 for(int i=0;i<65536;i++){
  double phase=i*6.28318/65536.0;
  *(short*)(0x59b590+i*2)=sin(phase)*16384.5;*(short*)(0x5de590+i*2)=cos(phase)*16384.5;
 }
 for(int i=-16384;i<16384;i++)*(short*)(0x593590+i*2)=asin(i/16384.0)*10430.38716064159;
 for(int i=0;i<256;i++){
  *(byte*)(0x5fe990+i)=atan(i*0.015625)*64*2*0.3183101550488765+0.5;
  *(byte*)(0x5fe890+i)=atan(i*0.25)*64*2*0.3183101550488765+0.5;
 }
 unsetenv("E2R_PROXY_MESH_BYPASS");unsetenv("E2R_PLAYER_MESH");
 static byte expected[0x10000];int cases=0;
 for(int kind=0;kind<6;kind++)for(int seed=0;seed<512;seed++)for(int mode=0;mode<2;mode++){
  setup(kind,seed);struct E2R_Registers regs={.eax=0x900000,.edx=mode};e2r_original_call(0x423858,&regs);
  memcpy(expected,(void*)0x900000,sizeof expected);int q0=*(int*)0x6368d8,q1=*(int*)0x6368dc;
  setup(kind,seed);FUN_00423858(0x900000,mode);
  if(!e2r_memory_equal("forward pose",expected,(void*)0x900000,sizeof expected)||q0!=*(int*)0x6368d8||q1!=*(int*)0x6368dc){
   fprintf(stderr,"forward pose kind=%d seed=%d mode=%d\n",kind,seed,mode);return 1;
  }
  assert(E2R_actor_calc_context==0x909000);cases++;
 }
 printf("PASS: %d original-x86 forward skeletal pose cases\n",cases);
 for(int mode=0;mode<3;mode++)for(int seed=0;seed<2048;seed++){
  memset((void*)0x900000,0x5a,0x200);
  DAT_0047a34a=mode!=0;DAT_0047a366=mode==2;
  for(int i=0;i<9;i++)*(short*)(0x6372aa+i*2)=next();
  for(int i=0;i<3;i++){*(short*)(0x900080+i*2)=next();*(short*)(0x6372c2+i*2)=next();}
  byte initial[0x200];memcpy(initial,(void*)0x900000,sizeof initial);
  struct E2R_Registers regs={.eax=0x900000};e2r_original_call(0x424ed0,&regs);
  memcpy(expected,(void*)0x900000,sizeof initial);memcpy((void*)0x900000,initial,sizeof initial);
  E2R_actor_calc_context=0x900000;FUN_00424ed0();
  if(!e2r_memory_equal("camera origin",expected,(void*)0x900000,sizeof initial))return 1;
 }
 puts("PASS: 6144 original-x86 camera-space node origin cases");
 for(int mode=0;mode<4;mode++)for(int seed=0;seed<2048;seed++){
  memset((void*)0x900000,0,0x200);
  DAT_0047a34a=mode!=0;DAT_0047a366=mode>=2;DAT_0047a34c=mode==3;
  _DAT_006401ec=640;_DAT_006401d4=480;
  _DAT_006401c8=11;_DAT_0064020c=207;_DAT_006401cc=17;_DAT_006401fc=155;
  *(short*)0x47a37e=-139;*(short*)0x47a380=371;
  // The production guard rejects high host-stack addresses; keep angles in
  // mapped game storage so the fixture really constructs a nonzero matrix.
  short *angles=(short*)0x900300;
  for(int i=0;i<3;i++)angles[i]=(short)next();
  E2R_ApplyEulerMatrix((short*)0x900032,angles);
  assert(*(short*)0x900032 || *(short*)0x900034 || *(short*)0x900036);
  for(int i=0;i<3;i++)*(short*)(0x900068+i*2)=1+next()%1800;
  *(short*)0x900096=512+next()%15000;
  *(short*)0x900092=*(short*)0x900128=(int)(next()%16000)-8000;
  *(short*)0x900094=*(short*)0x90012a=(int)(next()%12000)-6000;
  E2R_actor_calc_context=0x900000;FUN_00432e08();
  byte initial[0x200];memcpy(initial,(void*)0x900000,sizeof initial);
  struct E2R_Registers regs={.eax=0x900000};e2r_original_call(0x432ecc,&regs);
  memcpy(expected,(void*)0x900000,sizeof initial);memcpy((void*)0x900000,initial,sizeof initial);
  FUN_00432ecc();
  if(!e2r_memory_equal("ellipsoid projection",expected,(void*)0x900000,sizeof initial)){
   fprintf(stderr,"ellipsoid projection mode=%d seed=%d\n",mode,seed);return 1;
  }
 }
 puts("PASS: 8192 original-x86 ellipsoid projected-basis cases");
 // Captured Joe pelvis: the old component swap flattened a 52/60/43 shape
 // to 56/3 with slope 54. Original 0x433210..0x43331e gives 53/57/-1.
 memset((void*)0x900000,0,0x200);DAT_0047a34a=0;DAT_0047a366=0;
 short live_matrix[9]={-15033,-2026,6193,1708,13801,8660,-6288,8591,-12454};
 memcpy((void*)0x900032,live_matrix,18);
 *(short*)0x900068=52;*(short*)0x90006a=60;*(short*)0x90006c=43;
 *(short*)0x900096=4615;*(short*)0x900128=-1271;*(short*)0x90012a=-405;
 E2R_actor_calc_context=0x900000;FUN_00432e08();
 byte live_initial[0x200];memcpy(live_initial,(void*)0x900000,sizeof live_initial);
 struct E2R_Registers live_regs={.eax=0x900000};e2r_original_call(0x432ecc,&live_regs);
 memcpy(expected,(void*)0x900000,sizeof live_initial);
 assert(*(short*)0x9000da==53 && *(short*)0x9000dc==57 && *(short*)0x9000de==-1);
 memcpy((void*)0x900000,live_initial,sizeof live_initial);FUN_00432ecc();
 if(!e2r_memory_equal("captured Joe projection",expected,(void*)0x900000,sizeof live_initial))return 1;
 puts("PASS: captured Joe pelvis projects to original 53/57/-1 instead of distorted 56/3/54");
 cases=0;
 for(int mode=0;mode<4;mode++)for(int seed=0;seed<1024;seed++){
  memset((void*)0x900000,0,0x800);
  DAT_0047a34a=mode!=0;DAT_0047a366=mode>=2;DAT_0047a34c=mode==3;
  DAT_0047a279=(seed&1)<<24;DAT_0047a43c=seed&2;DAT_0047a2a4=0x180000;
  *(int*)0x900022=0x900400;*(byte*)0x900403=seed&4;
  // The production guard rejects high host-stack addresses; keep angles in
  // mapped game storage so the fixture really constructs a nonzero matrix.
  short *angles=(short*)0x900300;
  for(int i=0;i<3;i++)angles[i]=(short)next();
  E2R_ApplyEulerMatrix((short*)0x900006,angles);
  assert(*(short*)0x900006 || *(short*)0x900008 || *(short*)0x90000a);
  for(int i=0;i<3;i++){
   *(short*)(0x6372bc+i*2)=seed&8?next():0;
   *(short*)(0x900068+i*2)=1+next()%1800;
  }
  *(short*)0x900096=seed%37?512+next()%15000:0;
  *(short*)0x900092=*(short*)0x900128=(int)(next()%16000)-8000;
  *(short*)0x900094=*(short*)0x90012a=(int)(next()%12000)-6000;
  E2R_actor_calc_context=0x900000;FUN_00432e08();
  byte initial[0x800];memcpy(initial,(void*)0x900000,sizeof initial);
  drawn_node=drawn_surface=-1;
  struct E2R_Registers regs={.eax=0x900000};e2r_original_call(0x425538,&regs);
  memcpy(expected,(void*)0x900000,sizeof initial);int original_node=drawn_node,original_surface=drawn_surface;
  memcpy((void*)0x900000,initial,sizeof initial);drawn_node=drawn_surface=-1;
  E2R_actor_calc_context=0x909000;FUN_00425538(0x900000);
  assert(E2R_actor_calc_context==0x909000);
  if(drawn_node!=original_node||drawn_surface!=original_surface||
     !e2r_memory_equal("ellipsoid camera/draw",expected,(void*)0x900000,sizeof initial)){
   fprintf(stderr,"ellipsoid camera/draw mode=%d seed=%d\n",mode,seed);return 1;
  }
  cases++;
 }
 printf("PASS: %d original-x86 ellipsoid camera composition/projection/draw-selector cases\n",cases);
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness, image=image, libraries=('-lm',))
