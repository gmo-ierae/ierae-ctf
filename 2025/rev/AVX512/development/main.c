#define _GNU_SOURCE
#include <signal.h>
#include <sys/types.h>
#include <stdio.h>
#include <ucontext.h>
#include <stdint.h>
#include <sys/syscall.h>

#define SA_RESTORER   0x04000000

const static uint8_t offsets[] = {
    #include "offsets.arr"
};

const static uint8_t main_inner[] __attribute__((section(".text")))  = {
    #include "main.arr"
};

static uint64_t var_decode(long long *index) {
    uint64_t result = 0;
    while (1) {
        result |= (offsets[*index] & 0b1111111);
        if (offsets[(*index)++] & 0x80) break;
        result <<= 7;
    }
    return result;
}

static void handler(int sig, siginfo_t *si, ucontext_t *ctx) {
    const int64_t diff = ctx->uc_mcontext.gregs[REG_RIP] - (int64_t) main_inner;
    if (diff > 0 && diff <= sizeof(main_inner)) {
        // const long long rbx = ctx->uc_mcontext.gregs[REG_RBX];
        const uint64_t offset = var_decode(&ctx->uc_mcontext.gregs[REG_RBX]);
        // fprintf(stderr, "SIGTRAP: 0x%llx (rbx: %lld, off: %lu)", ctx->uc_mcontext.gregs[REG_RIP], rbx, offset);
        // fprintf(stderr, " (rax: 0x%llx, rdx: 0x%llx)", ctx->uc_mcontext.gregs[REG_RAX], ctx->uc_mcontext.gregs[REG_RDX]);
        ctx->uc_mcontext.gregs[REG_RIP] = (diff + offset) % sizeof(main_inner) + (uint64_t) main_inner;
        // fprintf(stderr, " -> 0x%llx (0x%llx)\n", ctx->uc_mcontext.gregs[REG_RIP], ctx->uc_mcontext.gregs[REG_RIP] - (long long) main_inner);
    }

    // sleep(1);
}

void __attribute__((naked)) __restore_rt() {
    __asm__ __volatile__ ("syscall" : : "a"(15) : "rcx", "r11", "memory");
}

static __inline long __syscall2(long n, long a1, long a2)
{
	unsigned long ret;
	__asm__ __volatile__ ("syscall" : "=a"(ret) : "a"(n), "D"(a1), "S"(a2)
						  : "rcx", "r11", "memory");
	return ret;
}

static __inline long __syscall3(long n, long a1, long a2, long a3)
{
	unsigned long ret;
	__asm__ __volatile__ ("syscall" : "=a"(ret) : "a"(n), "D"(a1), "S"(a2),
						  "d"(a3) : "rcx", "r11", "memory");
	return ret;
}

static __inline long __syscall4(long n, long a1, long a2, long a3, long a4)
{
	unsigned long ret;
	register long r10 __asm__("r10") = a4;
	__asm__ __volatile__ ("syscall" : "=a"(ret) : "a"(n), "D"(a1), "S"(a2),
						  "d"(a3), "r"(r10): "rcx", "r11", "memory");
	return ret;
}

__attribute__((__constructor__))
static void ctor(void) {
    struct k_sigaction {
        void (*handler)();
        unsigned long flags;
        void (*restorer)(void);
        unsigned mask[2];
    } sa = {
        .handler = handler,
        .flags = SA_SIGINFO | SA_RESTORER,
        .restorer = __restore_rt,
        .mask = {0}
    };
    __syscall4(SYS_rt_sigaction, SIGTRAP, (long long) &sa, 0, 8);

    // enable trap
    __asm__ __volatile__ (
        "pushf\n"
        "orb $0x01, 1(%rsp)\n"
        "popf\n"
    );
}

static const char str[] = {'w', 'r', 'o', 'n', 'g', '\n'};

int __attribute__((naked)) main() {
    // inline assembly to call inner
    __asm__ __volatile__ (
        "call main_inner"
        :
        : 
        : "memory", "rax", "rbx", "rcx", "rdx", "rsi", "rdi"
    );
    __asm__ __volatile__ ("syscall\nret" : : "a"(SYS_write), "D"(1), "S"(str),
						  "d"(sizeof str) : "rcx", "r11", "memory");
}