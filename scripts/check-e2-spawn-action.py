#!/usr/bin/env python3
"""Compare recovered NPC poses, spawn ownership and matrix angles with original i386.

Endpoint/IK/attached-root poses execute against original instructions. Resource
loading, posing and activation are intercepted only for event contract checks.
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
static void FUN_00426f84(void) {abort();}
typedef uint8_t byte,undefined1;typedef uint16_t ushort,undefined2;typedef uint32_t uint,undefined4;typedef uint64_t undefined8;
#define __fastcall
static int E2R_actor_calc_context,E2R_actor_load_id_override;
static uint event_rng,event_draws;
__attribute__((used,noinline)) static uint event_random(void) {
 event_draws++;event_rng=event_rng*0x41c64e6du+0x3039u;return event_rng>>16&0x7fff;
}
static undefined8 FUN_0045fc10(uint unused,uint preserved) {return (undefined8)event_random()|((undefined8)preserved<<32);}
__attribute__((naked)) static void random_hook(void) {
 __asm__("pushal; call event_random; mov %eax,28(%esp); popal; ret");
}
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
HOOK(node_query_hook,9) HOOK(bones_hook,10) HOOK(free_hook,8) HOOK(pose_hook,1) HOOK(reset_hook,2) HOOK(load_hook,3) HOOK(action_hook,4) HOOK(copy_hook,5) HOOK(activate_hook,6) HOOK(angles_hook,7)
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
for f in ['E2R_SetIdentityMatrix','FUN_00422628','FUN_00422368','FUN_00422460','FUN_00422538','E2R_ApplyEulerMatrix','E2R_TransformVector14','E2R_PolygonAngle16','FUN_0042d46c','FUN_0045186c']:
 c+=function(f)+'\n'
# Exercise the complete production reverse-chain pose, including endpoint/IK and attachment.
c+='static short E2R_PoseAsin14(short ratio);\n'
for f in ['E2R_RotatePolygonNormal','E2R_PoseAsin14','FUN_00423674','FUN_00424164','FUN_00420ec4']:
 c+=function(f)+'\n'
event23 = re.search(r'case 0x23:\s*(psVar7 = \(short \*\)FUN_0042d61c\([^;]*;)',s).group(1)
c+='__attribute__((used)) static volatile int event23_node;\nstatic uint capture_event23(int node) {event23_node=node;return 0;}\n'
c+='#define FUN_0042d61c capture_event23\nstatic void native_event23(short *unaff_ESI) {short *psVar7;'+event23+'}\n#undef FUN_0042d61c\n'
event20 = re.search(r'case 0x20:\s*(psVar7 = \(short \*\)FUN_0042d554\([^;]*;)',s).group(1)
c+='#define FUN_0042d554 capture_event23\nstatic void native_event20(short *unaff_ESI) {short *psVar7;'+event20+'}\n#undef FUN_0042d554\n'
c+='__attribute__((naked)) static void event23_hook(void) {__asm__("mov %eax,event23_node; ret");}\n'
c+='static void E2R_RotatePolygonNormal(short normal[3],short angle,int axis);\n'
for f in ['E2R_TransposeMatrix14','E2R_MultiplyMatrix14','FUN_0042d36c','FUN_0042d948','FUN_0042d554','FUN_0042d61c']:
 c+=function(f)+'\n'
c+=function('FUN_00424318').replace('FUN_00424318(void)','native_pose(void)').replace('undefined4 native_pose','void native_pose')+'\n'
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
c+='static void FUN_0042efdc(int node) {record(node,0,0,0,9); }\nstatic void FUN_00423858(int actor,int mode) {record(actor,mode,0,0,10); }\n'
c+=function('FUN_0042faf8')+'\n'
c+='#define FUN_0042d46c fake_angles\n'+function('FUN_0042f85c')+'\n'+function('FUN_0042f9c0')+'\n#undef FUN_0042d46c\n'
ranges=[(0x42c087,0x42c08e),(0x42d554,0x42d61c),(0x42d948,0x42db6c),(0x42d36c,0x42d46c),(0x42d61c,0x42d72c),(0x42c098,0x42c09f),(0x42f85c,0x42f9c0),(0x4154ff,0x415553),(0x45f556,0x45f573),(0x42faf8,0x42fc0a),(0x427ade,0x427b50),(0x424318,0x424860),(0x45de8b,0x45df0e),(0x42f9c0,0x42faf8),(0x45186c,0x451880),(0x422330,0x42274c),(0x423674,0x423858),(0x424164,0x424318),(0x420ec4,0x421074),(0x432de4,0x432e08),(0x42274c,0x4228b8),(0x4228b8,0x422aa0),(0x42d46c,0x42d554),(0x432c64,0x432de4),(0x45dd04,0x45de8b)]
for start,end in ranges:c+=f'static const byte code_{start:x}[]={{'+','.join(map(str,original(start,end)))+'};\n'
c+=r'''
static void map(int at,int size){assert(mmap((void*)at,size,7,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)!=MAP_FAILED);}
static void hook(int at,void *fn){*(byte*)at=0xe9;*(int*)(at+1)=(int)fn-at-5;}
// The only replacement in the original table initializer is its CRT asin.
// Keep the original x87 arithmetic, truncation helper, indices and stores.
__attribute__((naked)) static void asin_hook(void){
 __asm__("pushal; sub $16,%esp; fstpl (%esp); call asin; add $16,%esp; popal; ret");
}
__attribute__((naked)) static void run_asin_init(void){
 __asm__("pushal; sub $56,%esp; mov $0x4154ff,%eax; call *%eax; add $56,%esp; popal; ret");
}
static int orientation;
static void run_spawn(int node,int id,int action,int independent){
 __asm__ volatile("push orientation; call *%%edi" : "+a"(node),"+d"(id),"+b"(action),"+c"(independent):"D"(0x42f9c0):"memory","cc");
}
static void run_event(int node){
 __asm__ volatile("call *%%edi" : "+a"(node):"D"(0x42f85c):"ebx","ecx","edx","memory","cc");
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
static void run_chain(int node){
 int unused=17;
 __asm__ volatile("call *%%edi" : "+a"(node),"+d"(unused):"D"(0x42faf8):"ebx","ecx","memory","cc");
}
static void run_node(int node){
 __asm__ volatile("call *%%edi" : "+a"(node):"D"(0x423674):"ebx","ecx","edx","memory","cc");
}
static void compare_pose(byte *expected,int seed,const char *kind){
 for(int i=0;i<0x1000;i++)if(expected[i]!=*(byte*)(0x900000+i)){
  fprintf(stderr,"%s mismatch seed=%d offset=%x original=%02x recovered=%02x\n",kind,seed,i,expected[i],*(byte*)(0x900000+i));abort();
 }
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
 map(0x410000,0x10000);map(0x470000,0x2000);map(0x420000,0x20000);map(0x450000,0x20000);map(0x580000,0x90000);map(0x620000,0x30000);map(0x900000,0x10000);
'''
for start,end in ranges:c+=f'memcpy((void*)0x{start:x},code_{start:x},sizeof code_{start:x});\n'
table_loop=re.search(r'  for \(x = -16384; x < 16384; \+\+x\)\n    \*\(short \*\).*?;',function('FUN_00414f40'),re.S).group()
c+=r'''
 *(byte*)0x415553=0xc3;hook(0x45f574,asin_hook);
 *(double*)0x471391=0.00006103515625;*(double*)0x4713a9=10430.38716064159;
 run_asin_init();
 short expected_asin[32768];memcpy(expected_asin,(void*)0x58b590,sizeof expected_asin);
 memset((void*)0x58b590,0,sizeof expected_asin);
 int x;
'''+table_loop+r'''
 assert(!memcmp(expected_asin,(void*)0x58b590,sizeof expected_asin));
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
   if(j) { E2R_ApplyEulerMatrix((short*)0x908400,angles);memcpy(initial+j*0x200+0xec,(void*)0x908400,18); }
  }
  memcpy((void*)0x900000,initial,sizeof initial);run_pose(0x900000);memcpy(pose_expected,(void*)0x900000,sizeof initial);
  memcpy((void*)0x900000,initial,sizeof initial);E2R_actor_calc_context=0x900000;native_pose();
  if(memcmp(pose_expected,(void*)0x900000,sizeof initial)){fprintf(stderr,"FK mismatch seed=%d\n",seed);abort();}
 }
 // Exercise each endpoint coordinate basis, frozen nodes and Euler/tip outputs.
 for(int seed=0;seed<4096;seed++) {
  static byte initial[0x1000];memset(initial,0,sizeof initial);
  memcpy((void*)0x900000,initial,sizeof initial);
  *(int*)0x900022=0x900800;
  *(byte*)0x900003=(seed%4==0?1:seed%4==1?0:seed%4==2?2:0x42);
  for(int i=0;i<3;i++) {
   *(short*)(0x900110+i*2)=seed*1973+i*337;
   *(short*)(0x900026+i*2)=seed*7919+i*1237;
   *(short*)(0x90006e +i*2)=seed*913+i*797;
   *(short*)(0x900884+i*2)=seed*37%4096+i*337;
   *(short*)(0x90088a+i*2)=seed*17%2048+i*173;
   *(short*)(0x908300+i*2)=seed*10457+i*3127;
  }
  E2R_ApplyEulerMatrix((short*)0x900806,(short*)0x908300);
  E2R_ApplyEulerMatrix((short*)0x9008c6,(short*)0x900026);
  memcpy(initial,(void*)0x900000,sizeof initial);
  run_node(0x900000);memcpy(pose_expected,(void*)0x900000,sizeof initial);
  memcpy((void*)0x900000,initial,sizeof initial);FUN_00423674(0x900000);
  compare_pose(pose_expected,seed,"endpoint");
 }
 // Two-link reverse chains: all endpoint bases, zero distance/segment lengths,
 // alternate matrices, endpoint roll alignment, and reverse-link skip patterns.
 for(int seed=0;seed<8192;seed++) {
  static byte initial[0x1000];memset((void*)0x900000,0,sizeof initial);
  int root=0x900000,node=0x900200,middle=0x900400,endpoint=0x900600;
  *(short*)(root+4)=7;*(int*)(root+0x48)=node;
  *(int*)(node+0x22)=root;*(int*)(middle+0x22)=root;*(int*)(endpoint+0x22)=root;
  *(int*)(node+0x1e)=middle;*(int*)(middle+0x1e)=endpoint;
  *(int*)(node+0x48)=seed%3?middle:0;
  *(int*)(middle+0x48)=seed%2?endpoint:0;
  *(short*)(middle+4)=seed%2?4:3;
  *(byte*)(node+2)=0x20|(seed%2?0x80:0)|(seed%5?0:0x10);
  *(byte*)(middle+2)=seed%3?0:0x10;
  *(byte*)(endpoint+3)=seed%4==0?1:seed%4==1?0:seed%4==2?2:0x42;
  for(int i=0;i<3;i++) {
   *(short*)(root+0x84+i*2)=seed*37%4096+i*337;
   *(short*)(root+0x8a+i*2)=seed*17%2048+i*173;
   *(short*)(root+0x90+i*2)=seed*1973+i*1237;
   *(short*)(node+0x2c+i*2)=seed*71%2048+i*97;
   *(short*)(node+0x26+i*2)=seed*10457+i*3127;
   *(short*)(node+0x6e +i*2)=seed%8==0?0:seed*13%1024+i*79;
   *(short*)(middle+0x6e +i*2)=seed%8==0?0:seed*23%1024+i*73;
   *(short*)(endpoint+0x110+i*2)=seed%8==0?*(short*)(node+0x2c+i*2):seed*29%4096+i*83;
   *(short*)(endpoint+0x18+i*2)=seed*31%4096+i*89;
   *(short*)(endpoint+0x26+i*2)=seed*7919+i*211;
  }
  *(short*)(middle+0x30)=seed%8==0?0:seed%8==1?-*(short*)(node+0x72):301;
  *(short*)(endpoint+0x30)=seed%8==0?0:seed%8==2?-*(short*)(middle+0x72):503;
  E2R_ApplyEulerMatrix((short*)(root+0xc6),(short*)(root+0x90));
  E2R_ApplyEulerMatrix((short*)(node+0xec),(short*)(node+0x26));
  E2R_ApplyEulerMatrix((short*)(middle+0xec),(short*)(endpoint+0x26));
  E2R_ApplyEulerMatrix((short*)(endpoint+6),(short*)(endpoint+0x26));
  if(seed%32==0) {
   memset((void*)(root+0x84),0,6);memset((void*)(root+0x90),0,6);
   memset((void*)(node+0x2c),0,6);memset((void*)(endpoint+0x18),0,6);
   *(byte*)(endpoint+3)=1;
  }
  memcpy(initial,(void*)root,sizeof initial);
  run_pose(root);memcpy(pose_expected,(void*)root,sizeof initial);
  memcpy((void*)root,initial,sizeof initial);E2R_actor_calc_context=root;native_pose();
  compare_pose(pose_expected,seed,"IK");
 }
 // Attached root uses the original node type (7 versus other), its offset/Euler
 // fields and inherited flag propagation before traversing the FK chain.
 for(int seed=0;seed<1024;seed++) {
  static byte initial[0x1000];memset((void*)0x900000,0,sizeof initial);
  *(int*)0x9000f2=0x900800;*(int*)0x900822=0x900c00;
  *(short*)0x900800=seed%2?7:4;*(int*)0x900048=0x900200;
  *(byte*)0x900003=seed&4;*(byte*)0x900c03=seed&8?4:0;
  if(seed&16) {*(int*)0x900cf2=0x900a00;*(int*)0x900a22=0x900e00;*(byte*)0x900e03=seed&32?4:0;}
  for(int i=0;i<3;i++) {
   *(short*)(0x900800+0x80+i*2)=seed*37%4096+i*337;
   *(short*)(0x9000f6+i*2)=seed*17%2048+i*173;
   *(short*)(0x900102+i*2)=seed*13+i*137;
   *(short*)(0x9000fc+i*2)=seed*1973+i*211;
   *(short*)(0x900108+i*2)=seed*7919+i*3127;
  }
  E2R_ApplyEulerMatrix((short*)0x900806,(short*)0x900108);
  memcpy(initial,(void*)0x900000,sizeof initial);
  run_pose(0x900000);memcpy(pose_expected,(void*)0x900000,sizeof initial);
  memcpy((void*)0x900000,initial,sizeof initial);E2R_actor_calc_context=0x900000;native_pose();
  compare_pose(pose_expected,seed,"attachment");
 }
 // Decompose real rotations with original pre-multiply and atan instructions.
 for(int seed=0;seed<4096;seed++) {
  short *angles=(short*)0x908300;angles[0]=seed*1973;angles[1]=seed*7919;angles[2]=seed*10457;
  E2R_ApplyEulerMatrix((short*)0x908000,angles);
  run_angles(0x908100,0x908000);
  FUN_0042d46c(0x908200,(ushort*)0x908000);
  if(memcmp((void*)0x908100,(void*)0x908200,6)) {fprintf(stderr,"angles mismatch seed=%d original=%d,%d,%d native=%d,%d,%d\n",seed,*(short*)0x908100,*(short*)0x908102,*(short*)0x908104,*(short*)0x908200,*(short*)0x908202,*(short*)0x908204);abort();}
 }
 // Event 0x23 must restore all three local rotations, reverse links and flag.
 // Pose is intercepted here; its full FK/IK paths are compared above.
 hook(0x424318,pose_hook);
 for(int seed=0;seed<8192;seed++) {
  static byte initial[0x1000],expected_ik[0x1000];int expected_calls[64][3];
  memset((void*)0x900000,0,0x1000);
  for(int j=0;j<5;j++) {
   int node=0x900000+j*0x200;
   *(int*)(node+0x22)=0x900c00;
   if(j<4) *(int*)(node+0x44)=node+0x200;
   *(int*)(node+0x48)=seed+j*7919;
   short angles[3]={(short)(seed*1973+j*313),(short)(seed*7919+j*173),(short)(seed*10457+j*331)};
   E2R_ApplyEulerMatrix((short*)(node+6),angles);
   memset((void*)(node+0x26),0x5a,6);
  }
  *(byte*)0x900002=(seed&1)?0xa1:0x80;
  *(int*)0x90001e=0x900200;*(int*)0x90021e=0x900400;
  memcpy(initial,(void*)0x900000,sizeof initial);
  calls=0;memset(trace,0,sizeof trace);
  __asm__ volatile("pushal; mov $0x900000,%%eax; mov $0x42d61c,%%edx; call *%%edx; popal":::"memory","cc");
  memcpy(expected_ik,(void*)0x900000,sizeof initial);int count=calls;
  memcpy(expected_calls,trace,sizeof trace);
  memcpy((void*)0x900000,initial,sizeof initial);calls=0;memset(trace,0,sizeof trace);
  E2R_actor_calc_context=0x907000;FUN_0042d61c(0x900000);
  if(memcmp(expected_ik,(void*)0x900000,sizeof initial)||calls!=count||memcmp(expected_calls,trace,sizeof trace)||E2R_actor_calc_context!=0x907000) {
   fprintf(stderr,"IK restore mismatch seed=%d calls=%d/%d\n",seed,calls,count);abort();
  }
 }
 puts("PASS: 8192 original event-0x23 three-node local rotations/reverse links/flags/owner-context cases (pose dependency intercepted)");
 // Match direction/roll alignment and event-0x20 endpoint pinning.
 for(int kind=0;kind<2;kind++)for(int seed=0;seed<4096;seed++) {
  static byte initial[0x1000],expected_enable[0x1000];int expected_calls[64][3];
  memset((void*)0x900000,0,0x1000);
  for(int j=0;j<5;j++) {
   int node=0x900000+j*0x200;
   *(int*)(node+0x22)=0x900c00;
   if(j<4)*(int*)(node+0x44)=node+0x200;
   *(int*)(node+0x48)=seed+j*7919;
   short angles[3]={(short)(seed*1973+j*313),(short)(seed*7919+j*173),(short)(seed*10457+j*331)};
   E2R_ApplyEulerMatrix((short*)(node+6),angles);
   memcpy((void*)(node+0xec),(void*)(node+6),18);
   for(int i=0;i<3;i++) {
    *(short*)(node+0x18+i*2)=seed*71%4096+j*173+i*337;
    *(short*)(node+0x26+i*2)=seed*1973+j*313+i*211;
   }
  }
  short root_angles[3]={(short)(seed*7919),(short)(seed*10457),(short)(seed*1973)};
  E2R_ApplyEulerMatrix((short*)0x900c06,root_angles);
  for(int i=0;i<3;i++)*(short*)(0x900c84+i*2)=seed*917%2048+i*211;
  *(byte*)0x900002=(seed&1?0x10:0)|(seed&2?0x80:0)|(seed&4?0x20:0);
  *(int*)0x90001e=0x900200;*(int*)0x90021e=0x900400;
  memcpy(initial,(void*)0x900000,sizeof initial);calls=0;memset(trace,0,sizeof trace);
  int entry=kind?0x42d554:0x42d948;
  __asm__ volatile("pushal; mov %0,%%edx; mov $0x900000,%%eax; call *%%edx; popal"::"r"(entry):"memory","cc");
  memcpy(expected_enable,(void*)0x900000,sizeof initial);int count=calls;memcpy(expected_calls,trace,sizeof trace);
  memcpy((void*)0x900000,initial,sizeof initial);calls=0;memset(trace,0,sizeof trace);E2R_actor_calc_context=0x907000;
  if(kind)FUN_0042d554(0x900000);else FUN_0042d948(0x900000);
  if(memcmp(expected_enable,(void*)0x900000,sizeof initial)||calls!=count||memcmp(expected_calls,trace,sizeof trace)||E2R_actor_calc_context!=0x907000) {
   for(int i=0;i<0x1000;i++)if(expected_enable[i]!=*(byte*)(0x900000+i)){fprintf(stderr,"enable mismatch kind=%d seed=%d offset=%x original=%02x native=%02x\n",kind,seed,i,expected_enable[i],*(byte*)(0x900000+i));break;}
   abort();
  }
 }
 puts("PASS: 4096 original direction/roll cases and 4096 original event-0x20 endpoint/rotation/flag/owner cases (pose dependency intercepted)");
 hook(0x42d61c,event23_hook);*(byte*)0x42c09f=0xc3;
 for(int node=0x900000;node<0x901000;node+=16) {
  __asm__ volatile("pushal; mov %0,%%esi; mov $0x42c098,%%eax; call *%%eax; popal"::"r"(node):"memory","cc");
  assert(event23_node==node);event23_node=0;native_event23((short*)node);assert(event23_node==node);
 }
 puts("PASS: 256 original event-0x23 selected-node caller handoffs");

 hook(0x42d554,event23_hook);*(byte*)0x42c08e=0xc3;
 for(int node=0x900000;node<0x901000;node+=16) {
  __asm__ volatile("pushal; mov %0,%%esi; mov $0x42c087,%%eax; call *%%eax; popal"::"r"(node):"memory","cc");
  assert(event23_node==node);event23_node=0;native_event20((short*)node);assert(event23_node==node);
 }
 puts("PASS: 256 original event-0x20 selected-node caller handoffs");

 hook(0x424318,pose_hook);hook(0x42efdc,node_query_hook);hook(0x423858,bones_hook);
 for(int kind=0;kind<4;kind++)for(int attached=0;attached<2;attached++)for(int seed=0;seed<32;seed++) {
  static byte initial[0x10000],expected_chain[0x10000];int trace_expected[64][3];
  memset((void*)0x900000,0,sizeof initial);
  for(int j=0;j<5;j++) {
   int node=0x900000+j*0x200;
   *(int*)(node+0x22)=0x900800;
   if(j<4)*(int*)(node+0x44)=node+0x200;
   *(int*)(node+0x48)=seed*917+j*71;
  }
  *(byte*)0x900002=kind?0x20:0;
  *(int*)0x90001e=kind>1?0x900200:0;
  *(int*)0x90021e=kind>2?0x900400:0;
  *(int*)0x90013a=attached?0x901000:0;
  *(int*)0x90101e=0x901200;*(int*)0x90124c=0x901400;
  memcpy(initial,(void*)0x900000,sizeof initial);
  calls=0;memset(trace,0,sizeof trace);run_chain(0x900000);
  int count=calls;memcpy(trace_expected,trace,sizeof trace);memcpy(expected_chain,(void*)0x900000,sizeof initial);
  memcpy((void*)0x900000,initial,sizeof initial);calls=0;memset(trace,0,sizeof trace);E2R_actor_calc_context=0x907000;
  FUN_0042faf8(0x900000);
  assert(calls==count);assert(!memcmp(trace_expected,trace,sizeof trace));assert(!memcmp(expected_chain,(void*)0x900000,sizeof initial));assert(E2R_actor_calc_context==0x907000);
 }
 hook(0x424318,pose_hook);hook(0x420c10,reset_hook);hook(0x451f5c,load_hook);hook(0x451880,action_hook);hook(0x422aa0,copy_hook);hook(0x426c3c,activate_hook);hook(0x42d46c,angles_hook);
 byte expected[0x10000];int expected_trace[64][3];int cases=0;
 for(int attached=0;attached<2;attached++)for(int independent=0;independent<2;independent++)for(orientation=0;orientation<2;orientation++)for(int missing=0;missing<3;missing++)for(int seed=0;seed<32;seed++) {
  setup(attached,missing,seed);run_spawn(0x900000,3803,1877,independent);
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_trace,trace,sizeof trace);int count=calls;
  setup(attached,missing,seed);FUN_0042f9c0(0x900000,3803,1877,independent,orientation);
  assert(calls==count);assert(!memcmp(expected_trace,trace,sizeof trace));assert(!memcmp(expected,(void*)0x900000,sizeof expected));assert(E2R_actor_calc_context==0x907000);cases++;
 }
 hook(0x45fc10,random_hook);
 for(int attached=0;attached<2;attached++)for(int missing=0;missing<3;missing++)for(int seed=0;seed<1024;seed++) {
  setup(attached,missing,seed);
  *(int*)0x630b74=missing==1?0:0x902000;*(int*)0x62ba24=missing==2?0:0x903000;
  short angles[3]={(short)(seed*1973),(short)(seed*7919),(short)(seed*10457)};
  memcpy((void*)0x908300,angles,6);E2R_ApplyEulerMatrix((short*)0x900006,(short*)0x908300);
  static byte initial[0x10000];memcpy(initial,(void*)0x900000,sizeof initial);
  event_rng=seed*917u;event_draws=0;run_event(0x900000);
  assert(event_draws==3);uint expected_rng=event_rng;
  memcpy(expected,(void*)0x900000,sizeof expected);memcpy(expected_trace,trace,sizeof trace);int count=calls;
  memcpy((void*)0x900000,initial,sizeof initial);calls=0;memset(trace,0,sizeof trace);
  event_rng=seed*917u;event_draws=0;E2R_actor_calc_context=0x907000;FUN_0042f85c(0x900000);
  assert(event_draws==3 && event_rng==expected_rng);assert(calls==count);
  assert(!memcmp(expected_trace,trace,sizeof trace));assert(!memcmp(expected,(void*)0x900000,sizeof expected));
  assert(E2R_actor_calc_context==0x907000);
 }
 printf("PASS: 6144 original event-7 node/attachment/resource/memory/RNG cases\n");
 printf("PASS: 32768 original inverse-sine entries, 256 node-chain handoffs, 5120 original queued-action completions, 2048 root/FK, 4096 endpoint, 8192 IK and 1024 attached-root original poses, 4096 original matrix angle decompositions and %d spawn-event ownership/memory/call cases\n",cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-spawn-action-') as tmp:
 src=Path(tmp)/'check.c';exe=Path(tmp)/'check';src.write_text(c)
 subprocess.run(['clang-21','-m32','-O1','-Wno-int-conversion','-fno-pie','-no-pie',*(['-fsanitize=address','-fno-omit-frame-pointer'] if a.asan else []),str(src),'-lm','-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True,timeout=30)
