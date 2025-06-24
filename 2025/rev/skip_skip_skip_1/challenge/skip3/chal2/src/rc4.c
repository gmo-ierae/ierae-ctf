#include "rc4.h"

void rc4_init(uint8_t *state, const uint8_t *key) {
    int i, j;
    uint8_t temp;
    
    for (i = 0; i < 256; i++) {
        state[i] = i;
    }
    
    for (i = 0, j = 0; i < 256; i++) {
        j = (j + state[i] + key[i & (RC4_KEY_SIZE - 1)]) & 0xFF;
        temp = state[i];
        state[i] = state[j];
        state[j] = temp;
    }
}

void rc4_crypt(uint8_t *state, uint8_t *data, size_t datalen) {
    size_t n;
    uint8_t temp, k;
    uint8_t i = 0, j = 0;
    
    for (n = 0; n < datalen; n++) {
        i = (i + 1) & 0xFF;
        j = (j + state[i]) & 0xFF;
        
        temp = state[i];
        state[i] = state[j];
        state[j] = temp;
        
        k = state[(state[i] + state[j]) & 0xFF];
        data[n] ^= k;
    }
}