// gcc chal.c -o chal

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void win(void) {
  char flag[128] = {};

  puts("Well done!");
  system("cat ./flag*");
  exit(0);
}

void show_menu(void) {
  puts("1. Push command to the end of sequence");
  puts("2. Pop command from sequence");
  puts("3. Execute command sequence");
  puts("4. Clear command sequence");
  puts("5. Show command sequence");
  puts("6. Exit");
  printf("Enter command: ");
}

#define BUF_SIZE 1024
char input_buf[BUF_SIZE+1];

char* read_str(void) {
  fgets(input_buf, BUF_SIZE+1, stdin);

  // Remove '\n'
  char *newline_ptr = strrchr(input_buf, '\n');
  if (newline_ptr) *newline_ptr = '\0';

  return input_buf;
}

int read_int(void) {
  return atoi(read_str());
}

int cur_idx;
char sequence_buf[BUF_SIZE+1];
void push_command(void) {
  puts("1. cat_flag");
  puts("2. whoami");
  puts("3. id");
  puts("4. echo");
  printf("Enter command: ");

  int idx = read_int();
  switch (idx) {
  case 1:
    puts("This command is only for admin. Sorry!");
    break;
  case 2:
    if (cur_idx+7 > BUF_SIZE) {
      puts("Error: sequence is full");
      break;
    }

    memcpy(&sequence_buf[cur_idx], "whoami\n", 7);
    cur_idx += 7;
    sequence_buf[cur_idx] = '\0';

    break;
  case 3:
    if (cur_idx+3 > BUF_SIZE) {
      puts("Error: sequence is full");
      break;
    }

    memcpy(&sequence_buf[cur_idx], "id\n", 3);
    cur_idx += 3;
    sequence_buf[cur_idx] = '\0';

    break;
  case 4:
    if (cur_idx+32 > BUF_SIZE) {
      puts("Error: sequence is full");
      break;
    }

    printf("Enter argument: ");
    char *arg = read_str();

    if (strchr(arg, '\n')) {
      puts("Don't try to hack, hacker!");
      break;
    }

    int arg_len = strlen(arg);
    if (arg_len > 26) arg_len = 26;

    char echo_with_arg[32];
    echo_with_arg[31] = '\n';
    memset(echo_with_arg, ' ', 31);
    memcpy(echo_with_arg, "echo ", 5);
    memcpy(echo_with_arg+5, arg, arg_len);

    memcpy(&sequence_buf[cur_idx], echo_with_arg, 32);
    cur_idx += 32;
    sequence_buf[cur_idx] = '\0';

    break;
  default:
    puts("Invalid command");
  }
}

void pop_command(void) {
  printf("Enter index to remove: ");

  int idx = read_int();
  if (idx < 0) {
    puts("Invalid index");
    return;
  }

  char *cur_line = sequence_buf;

  while (cur_line < &sequence_buf[cur_idx]) {
    char *ptr = strchr(cur_line, '\n');
    if (!ptr) { 
      // there must be newline at the end of buffer
      puts("Something went wrong...");
      exit(1); 
    }

    if (idx == 0) {
      // remove one line (i.e., cur_line ~ ptr)
      // to remove the command
      strcpy(cur_line, ptr+1);
      cur_idx = strlen(sequence_buf);
      return;
    }

    cur_line = ptr+1;
    idx--;
  }

  puts("Invalid index");
  return;
}

void execute_sequence(void) {
  char *cur_line = sequence_buf;

  while (cur_line < &sequence_buf[cur_idx]) {
    char *ptr = strchr(cur_line, '\n');
    if (!ptr) { 
      // there must be newline at the end of buffer
      puts("Something went wrong...");
      exit(1); 
    }

    if (strncmp(cur_line, "cat_flag\n", 9) == 0) {
      win();
    } else if (strncmp(cur_line, "whoami\n", 7) == 0) {
      system("whoami");
    } else if (strncmp(cur_line, "id\n", 3) == 0) {
      system("id");
    } else if (strncmp(cur_line, "echo ", 5) == 0) {
      *ptr = '\0';
      puts(cur_line+5);
      *ptr = '\n';
    }

    cur_line = ptr+1;
  }
}

void clear_sequence(void) {
  sequence_buf[0] = '\0';
  cur_idx = 0;
}

void show_sequence(void) {
  puts("Current sequence:");
  puts("===============================");
  printf("%s", sequence_buf);
  puts("===============================");
}

int main() {
  setbuf(stdout, NULL);

  while (1) {
    show_menu();

    int cmd = read_int();
    if (cmd == 6) break;

    switch (cmd) {
    case 1:
      push_command();
      break;
    case 2:
      pop_command();
      break;
    case 3:
      execute_sequence();
      break;
    case 4:
      clear_sequence();
      break;
    case 5:
      show_sequence();
      break;
    }
  }

  return 0;
}
