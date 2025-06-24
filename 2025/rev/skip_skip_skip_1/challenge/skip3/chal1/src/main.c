#include "uart.h"

#define FLAG_SIZE 32

__attribute__((section(".flag"))) volatile char flag[FLAG_SIZE] = "IERAE{DUMMY_FLAG}";

volatile int reveal_flag = 0;

void sleep() {
    for (volatile int j = 0; j < 500000; j++) {
        asm volatile ("");
    }
}

void main(void) {
    uart_puts("Welcome to Flag Provider Service!\n");
    sleep();

    uart_puts("\nThe flag is ......\n");
    sleep();

    uart_puts("*drumroll*\n");
    sleep();

    if (reveal_flag) {
        uart_puts(flag);
        uart_puts("\n");
    }
    else {
        uart_puts("Sorry, it's a secret!\n");
    }
    uart_puts("\nThank you for using our service!\n");
}
