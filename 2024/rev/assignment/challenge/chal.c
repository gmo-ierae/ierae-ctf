// gcc chal.c -o chal
#include <stdio.h>
#include <string.h>

char flag[34]; 

int main(int argc, char *argv[]) {
    flag[28] = '3';
  flag[1] = 'E';
  flag[2] = 'R';
  flag[20] = 'r';
  flag[26] = 'a';
  flag[10] = '_';
  flag[32] = '}';
  flag[9] = 'e';
  flag[22] = 'n';
  flag[17] = '_';
  flag[6] = 's';
  flag[7] = '0';
  flag[15] = '0';
  flag[16] = 'm';
  flag[21] = '1';
  flag[24] = '_';
  flag[12] = '4';
  flag[25] = '5';
  flag[31] = 'c';
  flag[3] = 'A';
  flag[0] = 'I';
  flag[29] = '5';
  flag[18] = 's';
  flag[19] = 't';
  flag[11] = 'r';
  flag[8] = 'm';
  flag[5] = '{';
  flag[4] = 'E';
  flag[27] = '9';
  flag[30] = '4';
  flag[23] = 'g';
  flag[13] = 'n';
  flag[14] = 'd';

  if (argc >= 2 && !strcmp(flag, argv[1])) {
    puts(flag);
  }
}
