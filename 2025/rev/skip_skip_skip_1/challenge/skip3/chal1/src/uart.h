#ifndef UART_H
#define UART_H

void uart_putc(char c);
void uart_puts(const char *str);
void uart_puts_hex(unsigned char* buf, unsigned int len);

char uart_getc(void);
void uart_gets(char *buf, unsigned int max_len);

#endif