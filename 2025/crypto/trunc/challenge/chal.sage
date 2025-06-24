from sage.all import *
import secrets

q = 2**20
n = 512
m = 4 * n
c = 8

with open("flag.txt", "rb") as f:
    FLAG = f.read().strip()

def trunc_matrix(M, c):
    F = M.base_ring()
    modulus = 2**c
    return matrix(F, M.nrows(), M.ncols(), [F(Integer(x) - (Integer(x) % modulus)) for x in M.list()])

def keygen():
    U = random_matrix(Integers(q), m, n)
    A = trunc_matrix(U, c)
    s = vector(Zmod(q), [secrets.randbelow(q) for _ in range(n)])
    e = vector(Zmod(q), [ZZ(secrets.randbelow(400)) for _ in range(m)])
    return A, A * s + e

def encrypt_bit(x, A, b):
    S = [i for i in range(A.nrows()) if secrets.randbits(1)]
    if len(S) == 0:
        S = [secrets.randbelow(A.nrows())] 
    a_sum = sum([A[i] for i in S])
    b_sum = sum([b[i] for i in S])
    encoded_bit = (x * (q // 2)) % q
    return (a_sum, (encoded_bit + b_sum) % q)

def encrypt_message(message, A, b):
    bits = []
    for byte in message:
        for i in range(8):
            bits.append((byte >> i) & 1)
    ciphertext = [encrypt_bit(bit, A, b) for bit in bits]
    return ciphertext

def main():
    A, b = keygen()
    flag_ciphertext = encrypt_message(FLAG, A, b)
    print("q =", q)
    print("n =", n)
    print("m =", m)
    print("c =", c)
    print("A =", [list(A[i]) for i in range(A.nrows())])
    print("b =", list(b))
    print("flag_ciphertext =", flag_ciphertext)

if __name__ == "__main__":
    main()
