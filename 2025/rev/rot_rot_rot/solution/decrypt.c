#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

// Bitwise rotations
static inline uint8_t rol8(uint8_t value, int count) {
    count &= 7;
    return (value << count) | (value >> (8 - count));
}
static inline uint8_t ror8(uint8_t value, int count) {
    count &= 7;
    return (value >> count) | (value << (8 - count));
}
static inline uint32_t rol32(uint32_t value, int count) {
    count &= 31;
    return (value << count) | (value >> (32 - count));
}
static inline uint32_t ror32(uint32_t value, int count) {
    count &= 31;
    return (value >> count) | (value << (32 - count));
}

// rot13 single byte
static inline uint8_t rot13_byte(uint8_t c) {
    if ((c >= 'a' && c <= 'm') || (c >= 'A' && c <= 'M')) return c + 13;
    if ((c >= 'n' && c <= 'z') || (c >= 'N' && c <= 'Z')) return c - 13;
    return c;
}

// key generation
uint32_t generate_key(uint32_t x) {
    x = (uint32_t)(x * 0xe8601017U);
    x ^= rol32(x, 13);
    x = (uint32_t)(x * 0x9aa454efU);
    x ^= ror32(x, 5);
    x = (uint32_t)(x * 0xa94dc8cfU);
    x ^= rol32(x, 24);
    x = (uint32_t)(x * 0xda41c486U);
    x ^= ror32(x, 17);
    return x;
}

// decrypt function
void decrypt(const uint8_t *data, uint8_t *out, size_t length, uint32_t seed) {
    // step1: XOR
    uint32_t key = generate_key(seed);
    uint8_t *buf = malloc(length);
    for (size_t i = 0; i < length; i++) {
        buf[i] = data[i] ^ (uint8_t)(key & 0xFF);
        key = generate_key(key);
    }
    // step2: block rotation
    uint8_t *out2 = malloc(length);
    int rot_times = 0;
    for (size_t j = 0; j < length; j += 8) {
        size_t block_size = (length - j >= 8) ? 8 : (length - j);
        rot_times = ((rot_times + 3) % 7) + 1;
        int r = rot_times % block_size;
        for (size_t k = 0; k < block_size; k++) {
            size_t src = (k + block_size - r) % block_size;
            out2[j + k] = buf[j + src];
        }
    }
    free(buf);
    // step3: per-byte rotation + rot13
    int rot_amount = 0;
    for (size_t i = 0; i < length; i++) {
        rot_amount = ((rot_amount + 4) % 7) + 1;
        uint8_t c = out2[i];
        uint8_t x = (i % 2 == 0) ? ror8(c, rot_amount) : rol8(c, rot_amount);
        out[i] = rot13_byte(x);
    }
    free(out2);
}

// check if all characters of the decrypted text are printable
int is_printable(const uint8_t *data, size_t length) {
    for (size_t i = 0; i < length; i++) {
        if (data[i] > 0x7E) return 0;
    }
    return 1;
}

int main(int argc, char **argv) {
    if (argc < 2 || argc > 3) {
        fprintf(stderr, "Usage: %s <encrypted_file> [seed]\n", argv[0]);
        return 1;
    }
    // read file
    FILE *f = fopen(argv[1], "rb");
    if (!f) {
        perror("fopen");
        return 1;
    }
    fseek(f, 0, SEEK_END);
    size_t length = ftell(f);
    fseek(f, 0, SEEK_SET);
    uint8_t *data = malloc(length);
    if (fread(data, 1, length, f) != length) {
        perror("fread");
        fclose(f);
        return 1;
    }
    fclose(f);
    uint8_t *plain = malloc(length + 1);
    plain[length] = '\0';

    if (argc == 3) {
        // if length of argv[2] is fewer than 4, return error
        if (strlen(argv[2]) < 4) {
            fprintf(stderr, "Error: seed must be 4 bytes long.\n");
            free(data);
            free(plain);
            return 1;
        }
        // convert argv[2] to uint32_t
        uint32_t seed = 0;
        for (size_t i = 0; i < 4; i++) {
            seed |= ((uint32_t)(unsigned char)argv[2][i]) << (i * 8);
        }
        decrypt(data, plain, length, seed);
        printf("Used seed: 0x%08X\n", seed);
        printf("Decrypted text:\n%s\n", plain);
        printf("Decrypted text (hex):\n");
        for (size_t i = 0; i < length; i++) printf("%02X", plain[i]);
        printf("\n");
        free(data);
        free(plain);
        return 0;
    }

    uint64_t cnt = 0;
    // brute force
    for (uint8_t a = 0x20; a < 0x7F; a++) {
        for (uint8_t b = 0x20; b < 0x7F; b++) {
            for (uint8_t c = 0x20; c < 0x7F; c++) {
                for (uint8_t d = 0x20; d < 0x7F; d++) {
                    uint32_t seed = (uint32_t)a | ((uint32_t)b << 8) | ((uint32_t)c << 16) | ((uint32_t)d << 24);
                    decrypt(data, plain, length, seed);

                    cnt += 1;
                    if (cnt % 0x800000 == 0) {
                        printf("Trying seed %08lx: %08X => ", cnt, seed);
                        for (size_t i = 0; i < length; i++) {
                            printf("%02X", plain[i]);
                        }
                        printf("\n");
                    }

                    uint32_t prefix = 0;
                    for (size_t i = 0; i < 4; i++) {
                        prefix |= ((uint32_t)(unsigned char)plain[i]) << (i * 8);
                    }
                    if (prefix == seed) {
                        printf("Found seed bytes: '%c%c%c%c' (0x%02x%02x%02x%02x)\n", a,b,c,d, a,b,c,d);
                        printf("Decrypted text:\n%s\n", plain);
                        printf("Decrypted text (hex):\n");
                        for (size_t i = 0; i < length; i++) {
                            printf("%02X", plain[i]);
                        }
                        printf("\n");
                    }
                }
            }
        }
    }
    free(data);
    free(plain);
    return 1;
}