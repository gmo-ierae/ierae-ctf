// gcc chal.c -o chal

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <sys/param.h>

void win(int sig) {
  char flag[128] = {};

  puts("Well done!");
  system("cat ./flag*");
  exit(0);
}

void show_menu(void) {
  puts("1. Create new buffer and load file content");
  puts("2. Copy some buffer to another");
  puts("3. Exit");
  printf("Enter command: ");
}

char input_buf[PATH_MAX+1];

char* read_str(void) {
  fgets(input_buf, PATH_MAX+1, stdin);

  // Remove '\n'
  char *newline_ptr = strrchr(input_buf, '\n');
  if (newline_ptr) *newline_ptr = '\0';

  return input_buf;
}

int read_int(void) {
  return atoi(read_str());
}

struct buffer {
  size_t buf_size;
  char *buf_ptr;
};

#define MAX_BUF_NUM 2

int available_idx = 0;
struct buffer bufs[MAX_BUF_NUM];

void create_new_buf() {
  if (available_idx >= MAX_BUF_NUM) {
    printf("You can't create more than %d buffers\n", MAX_BUF_NUM);
    exit(1);
  }

  struct buffer *dst = &bufs[available_idx++];

  printf("Enter file name: ");
  char *fname = read_str();

  FILE *fp = fopen(fname, "r");
  if (!fp) {
    puts("Your specified file doesn't exist");
    exit(1);
  }

  // Get file size to allocate buffer
  fseek(fp, 0, SEEK_END);

  int size = ftell(fp);
  char *ptr = malloc(sizeof(char)*(size+1)); // plus 1 for '\0'
  if (!ptr) {
    puts("malloc failed");
    exit(1);
  }

  // Read file content
  fseek(fp, 0, SEEK_SET);

  fread(ptr, sizeof(char), size, fp);
  ptr[size] = '\0';
  fclose(fp);

  dst->buf_ptr = ptr;
  dst->buf_size = size;

  printf("Read %d bytes from %s\n", size, fname);
}

void copy() {
  if (available_idx < 2) {
    puts("This command needs at least two buffers");
    exit(1);
  }

  printf("Enter source index: ");
  int src_idx = read_int();
  if (src_idx < 0 || available_idx <= src_idx) {
    puts("Source index is invalid");
    exit(1);
  }

  printf("Enter destination index: ");
  int dst_idx = read_int();
  if (dst_idx < 0 || available_idx <= dst_idx) {
    puts("Destination index is invalid");
    exit(1);
  }

  if (src_idx == dst_idx) {
    puts("Source and destination should be different");
    exit(1);
  }

  struct buffer *src = &bufs[src_idx];
  struct buffer *dst = &bufs[dst_idx];
  size_t copy_size = src->buf_size;
  if (dst->buf_size < copy_size) copy_size = dst->buf_size;

  memcpy(dst->buf_ptr, src->buf_ptr, copy_size);
  printf("Copied %llu bytes from buf #%d to buf #%d\n", copy_size, src_idx, dst_idx);
}

int main() {
  // If you cause SEGV, then you will get flag
  signal(SIGSEGV, win);
  setbuf(stdout, NULL);

  while (1) {
    show_menu();

    int cmd = read_int();
    if (cmd == 3) break;

    switch (cmd) {
    case 1:
      create_new_buf();
      break;
    case 2:
      copy();
      break;
    }
  }

  return 0;
}
