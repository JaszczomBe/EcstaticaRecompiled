#!/usr/bin/env python3
"""Check held-key release and stale gameplay modifiers across host metadata."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cc', default='clang-21')
parser.add_argument('--asan', action='store_true')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source = (root/'E2Recomp/reconstructed/E2Recomp_stubs.c').read_text()
def function(name):
    match = re.search(r'^static (?:unsigned|void) '+name+r'\([^\n]*\)\s*\{.*?\n\}',source,re.M|re.S)
    assert match, name
    return match.group()
keydown = function('E2R_feed_legacy_keydown')
keydown = keydown[:keydown.index('    char_key = E2R_virtual_key_to_char_queue(key);')]+'}\n'
harness = r'''
#include "E2Recomp/platform/e2recomp_win32_compat.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>
static unsigned char pressed_extended[128],held_extended[128],pressed_regular[128],held_regular[128];
static unsigned E2R_input_probe_last_scan_queue;
static uintptr_t DAT_00636846,DAT_00636852,DAT_0063684a,DAT_00636850,DAT_00479dfc;
static unsigned char *E2R_legacy_queue(uintptr_t address) {
    switch(address) {
    case 0x507490:return pressed_extended;
    case 0x4c3a90:return held_extended;
    case 0x4c3990:return pressed_regular;
    case 0x4c3b90:return held_regular;
    default:assert(0);return 0;
    }
}
'''+function('E2R_virtual_key_to_scan')+'\n'+keydown+function('E2R_feed_legacy_keyup')+r'''
int main(void) {
    unsigned keys[]={VK_LEFT,VK_UP,VK_RIGHT,VK_DOWN,VK_RMENU,VK_MENU,VK_SHIFT,VK_CONTROL,VK_SPACE,0x57,
                     0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69};
    unsigned cases=0;
    for(unsigned k=0;k<sizeof(keys)/sizeof(keys[0]);k++)for(int metadata=0;metadata<3;metadata++)
    for(int repeats=1;repeats<=8;repeats+=7) {
        memset(pressed_extended,0,128);memset(held_extended,0,128);
        memset(pressed_regular,0,128);memset(held_regular,0,128);
        held_extended[0x7e]=held_regular[0x7e]=0x5a;
        unsigned key=keys[k],scan=E2R_virtual_key_to_scan(key);
        int ext=key==VK_LEFT||key==VK_UP||key==VK_RIGHT||key==VK_DOWN||key==VK_RMENU;
        int alias=key>=0x61&&key<=0x69;
        LPARAM down=metadata==0?0:(scan<<16)|(metadata==2&&ext?1<<24:0)|1;
        LPARAM up=metadata==0?0:down|(uint32_t)0xc0000000;
        for(int i=0;i<repeats;i++)E2R_feed_legacy_keydown(key,down);
        assert(held_extended[scan]==(ext||alias)&&held_regular[scan]==!ext);
        E2R_feed_legacy_keyup(key,up);
        assert(!held_extended[scan]&&!held_regular[scan]);
        assert(pressed_extended[scan]==(ext||alias)&&pressed_regular[scan]==!ext);
        assert(held_extended[0x7e]==0x5a&&held_regular[0x7e]==0x5a);
        // Releasing an already released key must not revive held state.
        E2R_feed_legacy_keyup(key,up);assert(!held_extended[scan]&&!held_regular[scan]);cases++;
    }
    printf("PASS: %u production held-key release cases, including SDL metadata-free arrows, right Alt and keypad aliases\n",cases);
    unsigned modifiers[]={VK_SHIFT,VK_CONTROL,VK_MENU,VK_RMENU,0x58,0x5a,VK_UP,VK_SPACE};
    unsigned modifier_cases=0;
    for(unsigned k=0;k<sizeof(modifiers)/sizeof(modifiers[0]);k++)for(int mode=0;mode<2;mode++)
    for(int flags=0;flags<8;flags++)for(int metadata=0;metadata<3;metadata++) {
        DAT_00479dfc=mode;
        DAT_00636850=1;
        DAT_00636846=(flags>>0)&1;DAT_00636852=(flags>>1)&1;DAT_0063684a=(flags>>2)&1;
        unsigned shift=DAT_00636846,ctrl=DAT_00636852,alt=DAT_0063684a;
        unsigned key=modifiers[k],scan=E2R_virtual_key_to_scan(key);
        if(key==VK_SHIFT||key==0x5a)shift=0;
        if(key==VK_CONTROL||(key==0x5a&&mode))ctrl=0;
        if(key==VK_MENU||key==VK_RMENU||(key==0x58&&mode))alt=0;
        LPARAM up=metadata==0?0:(scan<<16)|(metadata==2&&(key==VK_RMENU||key==VK_UP)?1<<24:0)|(uint32_t)0xc0000000;
        E2R_feed_legacy_keyup(key,up);
        assert(DAT_00636846==shift&&DAT_00636852==ctrl&&DAT_0063684a==alt);
        assert(DAT_00636850==(key==VK_SPACE?0:1));
        E2R_feed_legacy_keyup(key,up);
        assert(DAT_00636846==shift&&DAT_00636852==ctrl&&DAT_0063684a==alt);
        assert(DAT_00636850==(key==VK_SPACE?0:1));
        modifier_cases++;
    }
    printf("PASS: %u gameplay modifier/Space release/preservation cases, including repeated release and X/Z control modes\n",modifier_cases);
}
'''
with tempfile.TemporaryDirectory(prefix='e2-key-release-') as tmp:
    c=Path(tmp)/'check.c';exe=Path(tmp)/'check';c.write_text(harness)
    flags=['-fsanitize=address','-fno-omit-frame-pointer'] if args.asan else []
    subprocess.run([args.cc,'-m32','-O1','-Wno-macro-redefined','-I',str(root),*flags,str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True,timeout=20)
