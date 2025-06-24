#ifndef RC4_H
#define RC4_H

#include <stdint.h>
#include <stddef.h>

#define RC4_KEY_SIZE 32
#define RC4_STATE_SIZE 256

void rc4_init(uint8_t *state, const uint8_t *key);
void rc4_crypt(uint8_t *state, uint8_t *data, size_t datalen);

#endif