#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>

#define SAMPLE_PER_SYMBOL   (4)
#define NOISE_GAIN          (0.4)
#define PHASE_OFFSET        (1.0 / 16.0)

float random_float()
{
    uint32_t r;

    FILE* file = fopen("/dev/urandom", "r");
    fread(&r, sizeof(r), 1, file);
    fclose(file);

    return r / (0xffffffff * 1.0);
}

void block_char_to_bit(char* inbuf, size_t inlen, uint8_t** outbuf, size_t* outlen)
{
    *outlen = inlen * 8;
    *outbuf = (uint8_t*)malloc(*outlen);

    for (int i = 0; i < *outlen; i++) {
        (*outbuf)[i] = (inbuf[i / 8] >> (i % 8)) & 1;
    }

    free(inbuf);
}

void block_pack_3bits(uint8_t* inbuf, size_t inlen, uint8_t** outbuf, size_t* outlen)
{
    size_t padding = (3 * 8) - inlen % (3 * 8);
    inlen += padding;
    inbuf = realloc(inbuf, inlen);
    for (int i = inlen - padding; i < inlen; i++) {
        inbuf[i] = 0;
    }

    *outlen = inlen / 3;
    *outbuf = (uint8_t*)malloc(*outlen);

    for (int i = 0; i < inlen; i += 3) {
        uint8_t bits = \
            (inbuf[i + 2] << 2) | \
            (inbuf[i + 1] << 1) | \
            (inbuf[i + 0] << 0);

        (*outbuf)[i / 3] = bits;
    }

    free(inbuf);
}

void block_map_symbol(uint8_t* inbuf, size_t inlen, uint8_t** outbuf, size_t* outlen)
{
    const uint8_t symbol_map[] = {
        0b000,
        0b011,
        0b111,
        0b100,
        0b001,
        0b010,
        0b110,
        0b101,
    };

    *outlen = inlen;
    *outbuf = (uint8_t*)malloc(*outlen);

    for (int i = 0; i < inlen; i++) {
        (*outbuf)[i] = symbol_map[inbuf[i]];
    }

    free(inbuf);
}

void block_mod_8psk(uint8_t* inbuf, size_t inlen, float** outbuf, size_t* outlen)
{
    *outlen = inlen * SAMPLE_PER_SYMBOL * 2 * sizeof(**outbuf);
    *outbuf = (float*)malloc(*outlen);

    for (int i = 0; i < inlen; i++) {
        const float phase = (M_PI * 2.0) * (inbuf[i] / 8.0) + (M_PI * 2.0) * PHASE_OFFSET;

        for (int j = 0; j < SAMPLE_PER_SYMBOL * 2; j += 2) {
            (*outbuf)[i * SAMPLE_PER_SYMBOL * 2 + j + 0] = cosf(phase);
            (*outbuf)[i * SAMPLE_PER_SYMBOL * 2 + j + 1] = sinf(phase);
        }
    }

    free(inbuf);
}

void block_add_noise(float* inbuf, size_t inlen, float** outbuf, size_t* outlen)
{
    *outlen = inlen;
    *outbuf = (float*)malloc(*outlen);

    for (int i = 0; i < inlen / sizeof(*inbuf); i += 2) {
        float r, h;
        r = (M_PI * 2.0) * random_float();
        h = random_float();
        (*outbuf)[i + 0] = inbuf[i + 0] + cosf(r) * (NOISE_GAIN * h);
        (*outbuf)[i + 1] = inbuf[i + 1] + sinf(r) * (NOISE_GAIN * h);
    }

    free(inbuf);
}

void write_file(const char* filename, void* outbuf, size_t outlen)
{
    FILE* file = fopen(filename, "w");
    fwrite(outbuf, outlen, 1, file);
    fclose(file);
}

int main(int argc, char** argv)
{
    void *inbuf, *outbuf;
    size_t inlen, outlen;

    inbuf = malloc(256);
    inlen = fread(inbuf, 1, 256, stdin);

    block_char_to_bit((char*)inbuf, inlen, (uint8_t**)&outbuf, &outlen);
    inbuf = outbuf;
    inlen = outlen;

#ifdef DEBUG
    write_file("debug1", outbuf, outlen);
#endif

    block_pack_3bits((uint8_t*)inbuf, inlen, (uint8_t**)&outbuf, &outlen);
    inbuf = outbuf;
    inlen = outlen;

#ifdef DEBUG
    write_file("debug2", outbuf, outlen);
#endif

    block_map_symbol((uint8_t*)inbuf, inlen, (uint8_t**)&outbuf, &outlen);
    inbuf = outbuf;
    inlen = outlen;

#ifdef DEBUG
    write_file("debug3", outbuf, outlen);
#endif

    block_mod_8psk((uint8_t*)inbuf, inlen, (float**)&outbuf, &outlen);
    inbuf = outbuf;
    inlen = outlen;

#ifdef DEBUG
    write_file("debug4", outbuf, outlen);
#endif

    block_add_noise((float*)inbuf, inlen, (float**)&outbuf, &outlen);
    inbuf = outbuf;
    inlen = outlen;

#ifdef DEBUG
    write_file("debug5", outbuf, outlen);
#endif

    fwrite(outbuf, 1, outlen, stdout);
    free(outbuf);
}
