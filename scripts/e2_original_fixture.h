/* Shared register-only x86 trampoline and first-byte memory diagnostics.
 * Stack-argument callees need a fixture-specific adapter. No ABI is guessed. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
struct E2R_Registers { uint32_t eax, edx, ebx, ecx, esi, edi, ebp; };
#if !defined(__i386__)
#error Original register fixtures require i386
#endif
__attribute__((naked,unused)) static void e2r_original_call(uint32_t address, struct E2R_Registers *registers) {
    __asm__("pushal; push 40(%esp); push 40(%esp); mov 4(%esp),%ebp; "
            "mov 0(%ebp),%eax; mov 4(%ebp),%edx; mov 8(%ebp),%ebx; "
            "mov 12(%ebp),%ecx; mov 16(%ebp),%esi; mov 20(%ebp),%edi; mov 24(%ebp),%ebp; "
            "call *(%esp); pushal; mov 36(%esp),%ebp; "
            "mov 28(%esp),%eax; mov %eax,0(%ebp); mov 20(%esp),%eax; mov %eax,4(%ebp); "
            "mov 16(%esp),%eax; mov %eax,8(%ebp); mov 24(%esp),%eax; mov %eax,12(%ebp); "
            "mov 4(%esp),%eax; mov %eax,16(%ebp); mov 0(%esp),%eax; mov %eax,20(%ebp); "
            "mov 8(%esp),%eax; mov %eax,24(%ebp); add $40,%esp; popal; ret");
}
static int e2r_memory_equal(const char *label, const void *expected, const void *actual, size_t bytes) {
    const uint8_t *a=expected,*b=actual;
    for(size_t i=0;i<bytes;i++) if(a[i]!=b[i]) {
        fprintf(stderr,"%s: first mismatch offset=0x%zx expected=0x%02x actual=0x%02x\n",label,i,a[i],b[i]);
        return 0;
    }
    return 1;
}
