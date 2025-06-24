#include "uart.h"
#include "rc4.h"

#define INPUT_SIZE 32

__attribute__((section(".flag"))) volatile char flag[RC4_KEY_SIZE] = "IERAE{DUMMY_FLAG}";

char input[INPUT_SIZE];
char state[RC4_STATE_SIZE];

void main(void) {
    uart_puts("Welcome to Secure Encryption Service!\n\n");

    uart_puts("Input:\n");
    uart_gets(input, sizeof(input));
    uart_puts("\n");

    uart_puts("Initializing the encryption engine...\n");
    rc4_init((uint8_t *)state, (uint8_t *)flag);
    for (int i = 0; i < RC4_KEY_SIZE; i++) {
        flag[i] = 0;
    }
    uart_puts("Encrypting your data...\n");
    rc4_crypt((uint8_t *)state, (uint8_t *)input, sizeof(input));

    uart_puts("Encrypted data:\n");
    uart_puts_hex((unsigned char *)input, sizeof(input));
    uart_puts("\n");

    uart_puts("Encryption complete.\n");
    uart_puts("\nThank you for using our service!\n");
}
