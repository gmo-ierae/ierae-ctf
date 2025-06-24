from sage.all import *

error_bound = 400

def solve_extract_error(A, b, q, c):
    modulus = 2**c
    reduced_modulus = q // modulus
    buff = error_bound - modulus
    filtered_rows = []
    filtered_b = []
    for i in range(m):
        b_i = int(b[i])
        b_i_mod = b_i % modulus
        if buff < b_i_mod < modulus:
            A_row_mod = [(int(A[i, j]) // modulus) % reduced_modulus for j in range(A.ncols())]
            b_i_corr = (((b_i - b_i_mod) % q) // modulus) % reduced_modulus
            filtered_rows.append(A_row_mod)
            filtered_b.append(b_i_corr)
    X_good = matrix(Integers(reduced_modulus), filtered_rows)
    B_good = vector(Integers(reduced_modulus), filtered_b)
    s_candidate = X_good.solve_right(B_good)
    return vector(Zmod(q), [int(s_candidate[i]) for i in range(len(s_candidate))])

def decrypt(ciphertext, s):
    bits = []
    center = (q + 1) // 2
    for ct in ciphertext:
        a, b_val = ct
        a = vector(ZZ, list(a))
        diff = int((b_val - a.dot_product(s)) % q)
        if abs(diff - center) < min(diff, q - diff):
            bits.append(1)
        else:
            bits.append(0)
    plaintext_bytes = []
    for i in range(0, len(bits), 8):
        byte = sum(bits[i+j] << j for j in range(8))
        plaintext_bytes.append(byte)
    return bytes(plaintext_bytes)

def main():
    with open("output.txt", "r") as f:
        data = f.read()
    exec(data, globals())
    
    flag_ciphertext = globals().get("flag_ciphertext")
    A_data = globals().get("A")
    b_data = globals().get("b")
    A = matrix(Integers(q), A_data)
    b = vector(Integers(q), b_data)
    
    s_extract = solve_extract_error(A, b, q, c)
    decrypted_flag_extract = decrypt(flag_ciphertext, s_extract)
    print("Decrypted flag:", decrypted_flag_extract)
    
if __name__ == "__main__":
    main()
