from sage.all import *
from Crypto.Random import random, get_random_bytes
from Crypto.Util.number import getPrime, bytes_to_long
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

Q = getPrime(32)
N, k = 32, 2

PR.<x> = PolynomialRing(GF(Q))
R.<z> = PR.quotient_ring(x^N + 1)

def load_flag(filename='flag.txt'):
    with open(filename, 'rb') as file:
        return file.read().strip()

def centered_binomial_noise(size):
    return [sum(random.choice([-1, 1]) // 2 for _ in range(4)) for _ in range(size)]

def gen_small_poly_vector(size):
    while True:
        v = [R(centered_binomial_noise(N)) for _ in range(size)]
        if len(set(v)) == len(v):
            return vector(v)

def keygen():
    A = random_matrix(R, k, k)
    s = gen_small_poly_vector(k)
    e = gen_small_poly_vector(k)
    return s, (A, A * s + e)

def decompress(m):
    return R(m) * ((Q + 1) // 2)

def encrypt(pk, m):
    A, t = pk
    r = gen_small_poly_vector(k)
    e1 = gen_small_poly_vector(k)
    e2 = gen_small_poly_vector(1)
    u = A.T * r + e1
    v = t * r + e2[0] + decompress(m)
    return u, v

def aes_encrypt(key, data):
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_data = pad(data, AES.block_size)
    ciphertext = cipher.encrypt(padded_data)
    return iv + ciphertext

def main():
    aes_key = get_random_bytes(16)  
    s, pk = keygen()  
    A, t = pk
    FLAG = load_flag()  
    encrypted_flag = aes_encrypt(aes_key, FLAG)

    ciphertexts = []
    for i in range(0, len(aes_key), N // 8):
        aes_key_int = bytes_to_long(aes_key[i:i + N // 8])
        aes_key_bin = list(map(int, bin(aes_key_int)[2:].zfill(N)))
        encrypted_part = encrypt(pk, aes_key_bin)
        ciphertexts.append(encrypted_part)

    print(f"{Q = }")
    print(f"{A = }")
    print(f"{t = }")
    print(f"{ciphertexts = }")
    print(f"{encrypted_flag = }")

if __name__ == "__main__":
    main()
