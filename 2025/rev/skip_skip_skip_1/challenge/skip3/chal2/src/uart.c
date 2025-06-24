#include "uart.h"

#define UART0_BASE 0x101f1000
#define UART0_DR   (*(volatile unsigned int *)(UART0_BASE + 0x00))
#define UART0_FR   (*(volatile unsigned int *)(UART0_BASE + 0x18))

void uart_putc(char c) {
    while (UART0_FR & (1 << 5));
    UART0_DR = c;
}

void uart_puts(const char *str) {
    while (*str) {
        uart_putc(*str++);
    }
}

void uart_puts_hex(unsigned char* buf, unsigned int len) {
    const char hex_digits[] = "0123456789abcdef";
    for (unsigned int i = 0; i < len; i++) {
        uart_putc(hex_digits[(buf[i] >> 4) & 0x0F]);
        uart_putc(hex_digits[(buf[i] >> 0) & 0x0F]);
    }
}

char uart_getc(void) {
    while (UART0_FR & (1 << 4));
    return UART0_DR & 0xFF;
}

void uart_gets(char *buf, unsigned int max_len) {
    unsigned int i = 0;
    char c;
    while (i < max_len - 1) {
        c = uart_getc();
        if (c == '\n' || c == '\r') {
            break;
        }
        buf[i++] = c;
    }
    buf[i] = '\0';
}