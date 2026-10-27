#!/usr/bin/env python3
"""Exercise production slot file routing in private directories; installed saves stay untouched."""
import argparse
import re
from pathlib import Path
from e2_original import function, run_fixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--asan', action='store_true')
parser.add_argument('--keep-harness', type=Path)
args = parser.parse_args()
source = Path('E2Recomp/platform/e2recomp_win32_compat.c').read_text()
source = re.sub(r',\n +', ', ', source)
harness = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <errno.h>
#include <dirent.h>
#include <limits.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
typedef uint32_t DWORD;typedef int BOOL;
typedef const char *LPCSTR;typedef void *LPVOID;typedef const void *LPCVOID;
typedef struct Handle { void *ptr; } *HANDLE;
typedef void *LPOVERLAPPED;
#define GENERIC_WRITE 0x40000000u
#define INVALID_HANDLE_VALUE ((HANDLE)(intptr_t)-1)
#define TRUE 1
#define FALSE 0
static char e2r_save_directory[PATH_MAX];
static void e2r_host_free(void *p) { free(p); }
static HANDLE e2r_alloc_handle(void *p) { HANDLE h=malloc(sizeof(*h));assert(h);h->ptr=p;return h; }
'''
for name in ('e2r_normalize_path', 'e2r_append_path_component', 'e2r_resolve_case_path',
             'e2r_resolve_known_data_path', 'E2R_ConfigureSaveDirectory', 'e2r_open_save_file',
             'CreateFileA', 'ReadFile', 'WriteFile', 'CloseHandle'):
    harness += function(source, name) + '\n'
harness += r'''
static void seed(const char *path,const char *text) {
    FILE *f=fopen(path,"wb");assert(f);assert(fwrite(text,1,strlen(text),f)==strlen(text));assert(!fclose(f));
}
static void content(const char *path,const char *expected) {
    char bytes[64]={0};FILE *f=fopen(path,"rb");assert(f);
    size_t size=fread(bytes,1,sizeof(bytes),f);assert(size==strlen(expected));assert(!memcmp(bytes,expected,size));fclose(f);
}
static HANDLE open_slot(const char *path,unsigned access,unsigned disposition) {
    return CreateFileA(path,access,3,NULL,disposition,0,NULL);
}
int main(void) {
    char root[]="/tmp/e2-save-storage-XXXXXX";assert(mkdtemp(root));
    assert(!chdir(root));assert(!mkdir("game",0700));assert(!mkdir("game/Saved",0700));assert(!mkdir("runtime",0700));
    seed("game/Saved/0000.ECS","original occupied");seed("game/Saved/0005.ECS","\r\n\r\n");
    char game[PATH_MAX],runtime[PATH_MAX];assert(realpath("game",game));assert(realpath("runtime",runtime));
    assert(!chdir(game));
    assert(open_slot("saved\\0005.ecs",GENERIC_WRITE,2)==INVALID_HANDLE_VALUE);
    assert(!E2R_ConfigureSaveDirectory(game,game));
    assert(E2R_ConfigureSaveDirectory(runtime,game));
    HANDLE h=open_slot("saved\\0000.ecs",0x80000000u,3);assert(h!=INVALID_HANDLE_VALUE);
    char bytes[32]={0};DWORD count=99;assert(ReadFile(h,bytes,sizeof(bytes),&count,NULL));
    assert(count==17 && !memcmp(bytes,"original occupied",17));assert(CloseHandle(h));
    assert(open_slot("saved/../0000.ecs",GENERIC_WRITE,2)==INVALID_HANDLE_VALUE);
    assert(open_slot("saved/zzzz.ecs",GENERIC_WRITE,2)==INVALID_HANDLE_VALUE);
    /* Only an empty original slot is used for real write/read/rewrite trials. */
    h=open_slot("saved/0005.ecs",GENERIC_WRITE,2);assert(h!=INVALID_HANDLE_VALUE);
    assert(WriteFile(h,"private",7,&count,NULL) && count==7);assert(CloseHandle(h));
    h=open_slot("SAVED/0005.ECS",0x80000000u,3);assert(h!=INVALID_HANDLE_VALUE);
    memset(bytes,0,sizeof(bytes));assert(ReadFile(h,bytes,sizeof(bytes),&count,NULL) && count==7 && !memcmp(bytes,"private",7));assert(CloseHandle(h));
    assert(!chdir(root));content("game/Saved/0000.ECS","original occupied");content("game/Saved/0005.ECS","\r\n\r\n");
    content("runtime/Saved/0005.ECS","private");
    assert(!symlink("../../game/Saved/0000.ECS","runtime/Saved/0006.ECS"));
    assert(!link("game/Saved/0000.ECS","runtime/Saved/0007.ECS"));
    assert(!chdir(game));
    assert(open_slot("saved/0006.ecs",GENERIC_WRITE,2)==INVALID_HANDLE_VALUE);
    assert(open_slot("saved/0007.ecs",GENERIC_WRITE,2)==INVALID_HANDLE_VALUE);
    assert(open_slot("saved/0005.ecs",GENERIC_WRITE,1)==INVALID_HANDLE_VALUE);
    h=open_slot("saved/0005.ecs",GENERIC_WRITE,3);assert(h!=INVALID_HANDLE_VALUE);assert(CloseHandle(h));
    assert(!chdir(root));content("runtime/Saved/0005.ECS","private");assert(!chdir(game));
    h=open_slot("saved/0005.ecs",GENERIC_WRITE,5);assert(h!=INVALID_HANDLE_VALUE);assert(CloseHandle(h));
    assert(!chdir(root));content("runtime/Saved/0005.ECS","");content("game/Saved/0000.ECS","original occupied");
    assert(!unlink("runtime/Saved/0006.ECS"));assert(!unlink("runtime/Saved/0007.ECS"));assert(!chdir(game));
    assert(open_slot("saved/0006.ecs",GENERIC_WRITE,3)==INVALID_HANDLE_VALUE);
    assert(open_slot("saved/0006.ecs",GENERIC_WRITE,5)==INVALID_HANDLE_VALUE);
    h=open_slot("saved/0006.ecs",GENERIC_WRITE,4);assert(h!=INVALID_HANDLE_VALUE);assert(CloseHandle(h));
    h=open_slot("saved/0006.ecs",0x80000000u,3);assert(h!=INVALID_HANDLE_VALUE);
    assert(!WriteFile(h,"x",1,&count,NULL) && count==0);assert(CloseHandle(h));
    assert(!chdir(root));content("game/Saved/0000.ECS","original occupied");content("game/Saved/0005.ECS","\r\n\r\n");
    unlink("runtime/Saved/0005.ECS");unlink("runtime/Saved/0006.ECS");
    unlink("game/Saved/0000.ECS");unlink("game/Saved/0005.ECS");
    rmdir("runtime/Saved");rmdir("runtime");rmdir("game/Saved");rmdir("game");assert(!chdir("/tmp"));assert(!rmdir(root));
    puts("PASS: private slot read/write routing, occupied installed slot preservation, binary reads, file dispositions, write failures and symlink/hardlink rejection");
}
'''
run_fixture(harness, asan=args.asan, keep=args.keep_harness,
            dependencies=('production compatibility file functions; private synthetic game/runtime directories',))
