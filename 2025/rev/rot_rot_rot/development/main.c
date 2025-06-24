#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

uint8_t ror8(uint8_t value, unsigned int count) {
    count %= 8;
    return (value >> count) | (value << (8 - count));
}

uint8_t rol8(uint8_t value, unsigned int count) {
    count %= 8;
    return (value << count) | (value >> (8 - count));
}

char rot13(char c) {
    if ((c >= 'a' && c <= 'm') || (c >= 'A' && c <= 'M'))
        return c + 13;
    else if ((c >= 'n' && c <= 'z') || (c >= 'N' && c <= 'Z'))
        return c - 13;
    return c;
}

uint32_t rol32(uint32_t value, unsigned int count) {
    count %= 32;
    return (value << count) | (value >> (32 - count));
}

uint32_t ror32(uint32_t value, unsigned int count) {
    count %= 32;
    return (value >> count) | (value << (32 - count));
}

uint32_t generate_key(uint32_t x) {
    x *= 0xe8601017;
    x ^= rol32(x, 13);
    x *= 0x9aa454ef;
    x ^= ror32(x, 5);
    x *= 0xa94dc8cf;
    x ^= rol32(x, 24);
    x *= 0xda41c486;
    x ^= ror32(x, 17);
    return x;
}

void encrypt_flag(const char* flag, char* output) {
    size_t length = strlen(flag);

    int rot_amount = 0;
    for (size_t i = 0; i < length; i++) {
        char rot13_char = rot13(flag[i]);

        rot_amount += 4;
        rot_amount %= 7;
        rot_amount += 1;

        char rotated_char;
        if (i % 2 == 0) {
            rotated_char = rol8((uint8_t)rot13_char, rot_amount);
        } else {
            rotated_char = ror8((uint8_t)rot13_char, rot_amount);
        }

        output[i] = rotated_char;
    }

    size_t rot_times = 0;
    for (size_t j = 0; j < length; j += 8) {
        size_t block_size = (length - j >= 8) ? 8 : (length - j);
        rot_times += 3;
        rot_times %= 7;
        rot_times += 1;
        for (size_t r = 0; r < rot_times; r++) {
            char first = output[j];
            for (size_t k = 0; k < block_size - 1; k++) {
                output[j + k] = output[j + k + 1];
            }
            output[j + block_size - 1] = first;
        }
    }

    uint32_t seed = 0;
    for (size_t i = 0; i < 4; i++) {
        seed |= ((uint32_t)(unsigned char)flag[i]) << (i * 8);
    }
    uint32_t key = generate_key(seed);
    for (size_t i = 0; i < length; i++) {
        output[i] ^= (char)(key & 0xff);
        key = generate_key(key);
    }
}

int main(int argc, char** argv) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <input> <output>\n", argv[0]);
        return 1;
    }
    
    const char* input_file = argv[1];
    const char* output_file = argv[2];
    
    FILE* in = fopen(input_file, "rb");
    if (!in) {
        fprintf(stderr, "Failed to open input file: %s\n", input_file);
        return 1;
    }
    fseek(in, 0, SEEK_END);
    size_t orig_length = ftell(in);
    fseek(in, 0, SEEK_SET);
    size_t pad = (8 - (orig_length % 8)) % 8;
    size_t length = orig_length + pad;
    char* flag = malloc(length + 1);
    if (!flag) {
        fprintf(stderr, "Failed to allocate memory\n");
        fclose(in);
        return 1;
    }
    size_t actual = fread(flag, 1, orig_length, in);
    if (actual != orig_length) {
        fprintf(stderr, "Failed to read input file: read %zu bytes, expected %zu\n", actual, orig_length);
        fclose(in);
        free(flag);
        return 1;
    }
    for (size_t i = orig_length; i < length; i++) flag[i] = ' ';
    flag[length] = '\0';
    fclose(in);
    char* encrypted = malloc(length);
    if (!encrypted) {
        fprintf(stderr, "Failed to allocate memory\n");
        free(flag);
        return 1;
    }

    encrypt_flag(flag, encrypted);
    
    FILE* fp = fopen(output_file, "wb");
    if (!fp) {
        fprintf(stderr, "Failed to open file: %s\n", output_file);
        free(encrypted);
        free(flag);
        return 1;
    }

    fwrite(encrypted, 1, length, fp);
    fclose(fp);
    
    free(encrypted);
    free(flag);
    return 0;
}