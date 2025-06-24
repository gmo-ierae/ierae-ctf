// gcc chal.c -o chal -O3

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void load_flag() {
  char flag[128] = "";

  FILE *fp = fopen("flag.txt", "rb");
  if (!fp) {
    puts("Something went wrong. Call admin.");
    exit(1);
  }

  fread(flag, sizeof(char), 128, fp);
  fclose(fp);

  // puts(flag); // Sorry! No flag for you!
  memset(flag, 0, 128); // The secret should be cleared up
}

void echo(void) {
  unsigned int size;
  char *buf;

  printf("Size: ");
  scanf("%u%*c", &size);

  buf = alloca(size);
  if (!buf) {
    puts("Too large!");
    exit(1);
  }

  printf("Input: ");
  fgets(buf, size, stdin);

  sleep(1);

  printf("Output: %s\n", buf);
}

int main() {
  setbuf(stdout, NULL);

  puts("1. Load flag");
  puts("2. Echo");

  while (1) {
    int cmd;

    printf("Enter command: ");

    scanf("%d%*c", &cmd);

    if (cmd == 1) load_flag();
    else if (cmd == 2) echo();
    else {
      puts("Invalid command :(");
      return 0;
    }
  }
}
