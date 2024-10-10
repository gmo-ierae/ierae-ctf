// gcc chal.c -o chal -O3 -no-pie

#include <stdio.h>
#include <stdlib.h>

_Thread_local char buf[16];

int main() {
  long long int idxs[11] = {};
  long long int vals[11] = {};

  for (int i=0; i<11; i++) {
    scanf("%lld%lld", &idxs[i], &vals[i]);
    if (idxs[i] < 0 || 0x3000 <= idxs[i]) continue; // Idiot
    buf[idxs[i]] = vals[i];
  }

  exit(0);
}
