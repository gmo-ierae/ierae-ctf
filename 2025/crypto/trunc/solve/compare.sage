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

def babai_cvp(B, w):
    n = B.nrows()
    BB, _ = B.gram_schmidt()
    e = w
    for i in range(n)[::-1]:
        coeff = e.dot_product(BB[i]) / BB[i].dot_product(BB[i])
        e -= coeff.round() * B[i]
    return w - e

def _solve_LWE(A, b, q, reduction_fn, partial_error=False, c=None):
    m, n = A.nrows(), A.ncols()
    if partial_error:
        b = shift_b(b, q, c)
    basis = block_matrix([[A.change_ring(ZZ).transpose()], [q * matrix.identity(m)]])
    basis_reduced = reduction_fn(basis)[n:]
    v = babai_cvp(basis_reduced, b.change_ring(ZZ))
    return vector(Integers(q), A.solve_right(v))

def shift_b(b, q, c):
    mask = 2**c
    return vector(Integers(q), [(int(x) - (int(x) % mask)) % q for x in b])

def solve_LWE(A, b, q):
    return _solve_LWE(A, b, q, lambda B: B.LLL())

def solve_LWE_with_partial_error_removal(A, b, q, c):
    return _solve_LWE(A, b, q, lambda B: B.LLL(), partial_error=True, c=c)

def solve_LWE_BKZ(A, b, q, bkz_block_size=20):
    return _solve_LWE(A, b, q, lambda B: B.BKZ(block_size=bkz_block_size))

def solve_LWE_BKZ_with_partial_error_removal(A, b, q, c, bkz_block_size=20):
    return _solve_LWE(A, b, q, lambda B: B.BKZ(block_size=bkz_block_size), partial_error=True, c=c)

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
    
    A_data = globals().get("A")
    b_data = globals().get("b")
    flag_ciphertext = globals().get("flag_ciphertext")
    
    if A_data is None or b_data is None or flag_ciphertext is None:
        print("Missing A, b, or flag_ciphertext in the imported data.")
        return
    
    A = matrix(Integers(q), A_data)
    b = vector(Integers(q), b_data)
    
    # 0) solve_extract_error
    s_extract = solve_extract_error(A, b, q, c)
    if s_extract is None:
        print("solve_extract_error failed: insufficient unambiguous rows or unsolvable system.")
    else:
        decrypted_flag = decrypt(flag_ciphertext, s_extract)
        print("Decrypted FLAG (extract error):", decrypted_flag)
    
    # 1) solve_extract_error
    s_lll = solve_LWE(A, b, q)
    decrypted_flag = decrypt(flag_ciphertext, s_lll)
    print("Decrypted FLAG (LLL):", decrypted_flag)
    
    # 2) solve_LWE_with_partial_error_removal
    s_lll_filtered = solve_LWE_with_partial_error_removal(A, b, q, c)
    decrypted_flag = decrypt(flag_ciphertext, s_lll_filtered)
    print("Decrypted FLAG (Filtered LLL):", decrypted_flag)
    
    # 3) solve_LWE_BKZ
    bkz_block_size = 20
    s_bkz = solve_LWE_BKZ(A, b, q, bkz_block_size)
    decrypted_flag = decrypt(flag_ciphertext, s_bkz)
    print("Decrypted FLAG (BKZ):", decrypted_flag)
    
    # 4) solve_LWE_BKZ_with_partial_error_removal
    s_bkz_filtered = solve_LWE_BKZ_with_partial_error_removal(A, b, q, c, bkz_block_size)
    decrypted_flag = decrypt(flag_ciphertext, s_bkz_filtered)
    print("Decrypted FLAG (Filtered BKZ):", decrypted_flag)

if __name__ == "__main__":
    main()
