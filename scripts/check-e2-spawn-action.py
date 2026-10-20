#!/usr/bin/env python3
"""Compare recovered spawn-event ownership and matrix angles with original i386.

Resource loading, posing and activation are intercepted for the event contract;
angle decomposition executes original matrix/angle instructions directly.
"""
import argparse
from pathlib import Path
import re,struct,subprocess,tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('exe',type=Path);p.add_argument('--asan',action='store_true');a=p.parse_args()
s=(Path(__file__).resolve().parent.parent/'E2Recomp/reconstructed/E2Recomp_recon.c').read_text();pe=a.exe.read_bytes();h=struct.unpack_from('<I',pe,60)[0];n=struct.unpack_from('<H',pe,h+6)[0];opt=struct.unpack_from('<H',pe,h+20)[0]
def original(start,end):
 for i in range(n):
  at=h+24+opt+i*40;_,va,size,raw=struct.unpack_from('<IIII',pe,at+8);va+=0x400000
  if va<=start<end<=va+size:return pe[raw+start-va:raw+end-va]
 raise ValueError(hex(start))
def function(name):
 m=re.search(r'^(?:static )?(?:short|void|undefined4) (?:__fastcall )?'+name+r'\([^\n]*\)\s*\{.*?\n\}',s,re.M|re.S);assert m,name;return m.group()
c=r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <math.h>
#include <sys/mman.h>
typedef uint8_t byte,undefined1;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;
#define __fastcall
static int E2R_actor_calc_context,E2R_actor_load_id_override;
static int trace[64][3],calls;
__attribute__((used,noinline)) static void record(int x,int y,int z,int w,int leaf) {
 assert(calls<64);trace[calls][0]=leaf;trace[calls][1]=x;
 trace[calls++][2]=(leaf==5||leaf==7)?y:0;
 if(leaf==8)*(short*)x=-1;
 if(leaf==5)memcpy((void*)x,(void*)y,6);
 if(leaf==7) {*(short*)x=1234;*(short*)(x+2)=-2345;*(short*)(x+4)=3456;}
}
#define HOOK(name,leaf) __attribute__((naked)) static void name(void) { \
 __asm__("pushal; push $" #leaf "; push %ecx; push %ebx; push %edx; push %eax; call record; add $20,%esp; popal; ret"); }
HOOK(free_hook,8) HOOK(pose_hook,1) HOOK(reset_hook,2) HOOK(load_hook,3) HOOK(action_hook,4) HOOK(copy_hook,5) HOOK(activate_hook,6) HOOK(angles_hook,7)
static void FUN_00424318(void){record(E2R_actor_calc_context,0,0,0,1);}
static void FUN_00420c10(int actor){record(actor,0,0,0,2);}
static void E2R_LoadPopulationActor(int id){record(id,0,0,0,3);}
static void FUN_00451880(int unused,int action){record(action,0,0,0,4);}
static void FUN_00422aa0(uint dest,undefined2 *src){record(dest,(int)src,0,0,5);}
static void FUN_00426c3c(void){record(E2R_actor_calc_context,0,0,0,6);}
static void fake_angles(uint dest,ushort *src){record(dest,(int)src,0,0,7);}
static int IsBadReadPtr(void *p,int n){return !p;}
static int E2R_IsBadWritePtr(void *p,int n){return !p;}
'''
for f in ['E2R_SetIdentityMatrix','FUN_00422368','FUN_00422460','FUN_00422538','E2R_ApplyEulerMatrix','E2R_TransformVector14','E2R_PolygonAngle16','FUN_0042d46c','FUN_0045186c']:
 c+=function(f)+'\n'
# Exercise the production root/FK branch; attachment and IK branches remain outside this fixture.
pose=function('FUN_00424318').replace('FUN_00424318(void)','native_pose(void)').replace('undefined4 native_pose','void native_pose')
a0=pose.index('  else {\n    FUN_00420ec4')
a1=pose.index('  sVar2 = 0;',a0)
pose=pose[:a0]+'  else { abort(); }\n'+pose[a1:]
a0=pose.index('    else {\n      iVar5 = *(int *)(iVar8 + 0x1e);')
a1=pose.index('    local_34 = *(int *)(local_34 + 0x48);',a0)
pose=pose[:a0]+'    else { abort(); }\n'+pose[a1:]
c+=pose+'\n'
# Extract the repaired queued-action completion block itself, including list advancement.
start=s.index('    /* Original 0x427ade retains the actor')
end=s.index('  E2R_TraceActorUpdateStage("27584.before-idle-test"',start)
queue=s[start:end].rstrip();assert queue.endswith('}');queue=queue[:-1]
c+=function('FUN_004538b8')+'\n'
c+="""
#define CONCAT21(a,b) (((uint)(ushort)(a)<<8)|(byte)(b))
static void native_queue(short *local_6c,uint uVar25) {
 int extraout_EDX_01,extraout_EDX_02=0,extraout_var=0,extraout_var_00=0;
 uint uVar16;ushort uVar12;
"""+queue+'\n}\n'
c+='#define FUN_0042d46c fake_angles\n'+function('FUN_0042f9c0')+'\n#undef FUN_0042d46c\n'
ranges=[(0x427ade,0x427b50),(0x424318,0x424860),(0x45de8b,0x45df0e),(0x42f9c0,0x42faf8),(0x45186c,0x451880),(0x422330,0x422628),(0x42274c,0x4228b8),(0x4228b8,0x422aa0),(0x42d46c,0x42d554),(0x432c64,0x432de4),(0x45dd04,0x45de8b)]
for start,end in ranges:c+=f'static const byte code_{start:x}[]={{'+','.join(map(str,original(start,end)))+'};\n'
c+=r'''
static void map(int at,int size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);}
static void hook(int at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(int)fn-at-5;}
static int orientation;
static void run_spawn(int node,int id,int action,int independent){
 __asm__ volatile("push orientation; call *%%edi" : "+a"(node),"+d"(id),"+b"(action),"+c"(independent):"D"(0x42f9c0):"memory","cc");
}
static void run_angles(int destination,int matrix){
 __asm__ volatile("call *%%edi" : "+a"(destination),"+d"(matrix):"D"(0x42d46c):"ebx","ecx","memory","cc");
}
__attribute__((naked)) static void run_queue(int actor,int kind){
 __asm__("pushal; mov 36(%esp),%edx; mov 40(%esp),%edi; mov $0x906000,%ebp; mov $0x427ade,%eax; call *%eax; popal; ret");
}
static void run_pose(int actor){
 __asm__ volatile("call *%%edi" : "+a"(actor):"D"(0x424318):"ebx","ecx","edx","memory","cc");
}
static void setup(int attachment,int missing,int seed){
 memset((void*)0x900000,0,0x10000);memset(trace,0,sizeof trace);calls=0;
 E2R_actor_calc_context=0x907000;E2R_actor_load_id_override=-1;
 *(int*)(0x630b60+3803*4)=missing==1?0:0x902000;
 *(int*)(0x62ba20+1877*4)=missing==2?0:0x903000;
 *(int*)0x900022=0x900800;*(int*)0x900044=0x900400;*(int*)0x900444=0x900800;
 *(short*)0x900800=117;*(int*)0x9008f2=attachment?0x901000:0;
 *(int*)0x901022=0x901800;*(short*)0x901800=284;*(int*)0x901044=0x901400;
 for(int i=0;i<3;i++){*(short*)(0x900080+i*2)=seed*371+i*913;*(short*)(0x900890+i*2)=seed*701+i*33;}
 *(int*)0x9020a6=0x12345678;*(ushort*)0x902002=seed*1537;
 *(byte*)0x902146=seed*53;*(short*)0x90218a=-1;
}
int main(void){
 map(0x420000,0x20000);map(0x450000,0x20000);map(0x590000,0x80000);map(0x620000,0x30000);map(0x900000,0x10000);
'''
for start,end in ranges:c+=f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
c+=r'''
 for(int i=0;i<65536;i++) {*(short*)(0x59b590+i*2)=lrint(sin(i*6.283185307179586/65536)*16384);*(short*)(0x5de590+i*2)=lrint(cos(i*6.283185307179586/65536)*16384);}
 for(int i=0;i<256;i++){*(byte*)(0x5fe990+i)=atan(i*0.015625)*64*2*0.3183101550488765+0.5;*(byte*)(0x5fe890+i)=atan(i*0.25)*64*2*0.3183101550488765+0.5;}
 *(byte*)0x427b50=0xc3;hook(0x4538b8,free_hook);
 byte queue_initial[0x10000],queue_expected[0x10000];
 for(int kind=0;kind<5;kind++)for(int seed=0;seed<1024;seed++) {
  memset(queue_initial,seed,sizeof queue_initial);
  *(int*)(queue_initial+0x602a)=0x900000;
  *(int*)(queue_initial+0x17c)=0x904000;
  *(int*)(queue_initial+0x4006)=0x904100;
  calls=0;memcpy((void*)0x900000,queue_initial,sizeof queue_initial);run_queue(0x900000,kind);memcpy(queue_expected,(void*)0x900000,sizeof queue_expected);
  memcpy((void*)0x900000,queue_initial,sizeof queue_initial);native_queue((short*)0x900000,kind);
  if(memcmp(queue_expected,(void*)0x900000,sizeof queue_expected)){fprintf(stderr,"queued action mismatch kind=%d seed=%d\n",kind,seed);abort();}
 }
 byte pose_expected[0x1000];
 for(int seed=0;seed<2048;seed++) {
  static byte initial[0x1000];memset(initial,0,sizeof initial);
  for(int j=0;j<3;j++) {
   int node=0x900000+j*0x200;
   *(int*)(initial+j*0x200+0x48)=j<2?node+0x200:0;
   *(short*)(initial+j*0x200+4)=seed%2?7:3;
   *(byte*)(initial+j*0x200+2)=seed%3?0:0x10;
   short *angles=(short*)0x908300;angles[0]=seed*1973+j*137;angles[1]=seed*7919+j*211;angles[2]=seed*10457+j*3127;
   memcpy(initial+j*0x200+(j?0x26:0x90),angles,6);
   for(int k=0;k<3;k++) {
    *(short*)(initial+j*0x200+0x84+k*2)=seed*913+j*337+k*797;
    *(short*)(initial+j*0x200+0x2c+k*2)=seed*379+j*731+k*137;
    *(short*)(initial+j*0x200+0x6e +k*2)=seed*701+j*173+k*293;
   }
   if(j)E2R_ApplyEulerMatrix((short*)(initial+j*0x200+0xec),angles);
  }
  memcpy((void*)0x900000,initial,sizeof initial);run_pose(0x900000);memcpy(pose_expected,(void*)0x900000,sizeof initial);
  memcpy((void*)0x900000,initial,sizeof initial);E2R_actor_calc_context=0x900000;native_pose();
  if(memcmp(pose_expected,(void*)0x900000,sizeof initial)){fprintf(stderr,"FK mismatch seed=%d\n",seed);abort();}
 }
 // Decompose real rotations with original pre-multiply and atan instructions.
 for(int seed=0;seed<4096;seed++) {
  short *angles=(short*)0x908300;angles[0]=seed*1973;angles[1]=seed*7919;angles[2]=seed*10457;
  E2R_ApplyEulerMatrix((short*)0x908000,angles);
  run_angles(0x908100,0x908000);
  FUN_0042d46c(0x908200,(ushort*)0x908000);
  if(memcmp((void*)0x908100,(void*)0x908200,6)) {fprintf(stderr,"angles mismatch seed=%d original=%d,%d,%d native=%d,%d,%d\n",seed,*(short*)0x908100,*(short*)0x908102,*(short*)0x908104,*(short*)0x908200,*(short*)0x908202,*(short*)0x908204);abort();}
 }
 hook(0x424318,pose_hook);hook(0x420c10,reset_hook);hook(0x451f5c,load_hook);hook(0x451880,action_hook);hook(0x422aa0,copy_hook);hook(0x426c3c,activate_hook);hook(0x42d46c,angles_hook);
 byte expected[0x10000];int expected_trace[64][3];int cases=0;
 for(int attached=0;attached<2;attached++)for(int independent=0;independent<2;independent++)for(orientation=0;orientation<2;orientation++)for(int missing=0;missing<3;missing++)for(int seed=0;seed<32;seed++) {
  setup(attached,missing,seed);run_spawn(0x900000,3803,1877,independent);
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_trace,trace,sizeof trace);int count=calls;
  setup(attached,missing,seed);FUN_0042f9c0(0x900000,3803,1877,independent,orientation);
  assert(calls==count);assert(!memcmp(expected_trace,trace,sizeof trace));assert(!memcmp(expected,(void*)0x900000,sizeof expected));assert(E2R_actor_calc_context==0x907000);cases++;
 }
 printf("PASS: 5120 original queued-action completions, 2048 original root/FK poses, 4096 original matrix angle decompositions and %d spawn-event ownership/memory/call cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-spawn-action-') as tmp:
 src=Path(tmp)/'check.c';exe=Path(tmp)/'check';src.write_text(c)
 subprocess.run(['clang-21','-m32','-O1','-Wno-int-conversion','-fno-pie','-no-pie',*(['-fsanitize=address','-fno-omit-frame-pointer'] if a.asan else []),str(src),'-lm','-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=30)
