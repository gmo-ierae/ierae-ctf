// gcc chal.c -o chal

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>

void win(int sig) {
  char flag[128] = {};

  puts("Well done!");
  system("cat ./flag*");
  exit(0);
}

int main() {
  // If you cause SEGV, then you will get flag
  signal(SIGSEGV, win);
  setbuf(stdout, NULL);
  
  unsigned long long int nrow, ncol;

  printf("Enter number of rows: ");
  scanf("%llu", &nrow);

  printf("Enter number of cols: ");
  scanf("%llu", &ncol);

  if (nrow * ncol < nrow) { // this is integer overflow right?
    puts("Don't hack!");
    exit(1);
  }

  char *matrix = malloc(nrow*ncol);
  if (!matrix) {
    puts("Too large!");
    exit(1);
  }

  for (unsigned long long int i=0; i<nrow; i++) {
    for (unsigned long long int j=0; j<ncol; j++) {
      matrix[i*ncol+j] = (i+j) % 2;
    }
  }

  puts("I made Ichimatsu design for you!");
  for (unsigned long long int i=0; i<nrow; i++) {
    for (unsigned long long int j=0; j<ncol; j++) {
      printf("%d ", matrix[i*ncol+j]);
    }
    puts("");
  }
}
