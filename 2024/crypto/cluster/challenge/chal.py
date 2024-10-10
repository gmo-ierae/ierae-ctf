from secret import p, q, r, flag
from Crypto.Util.number import isPrime, bytes_to_long

N = p * q * r

assert isPrime(p) and p.bit_length() < 1024
assert isPrime(q) and q.bit_length() < 1024
assert isPrime(r) and r.bit_length() < 1024
assert p ** 2 + q ** 2 + r ** 2 + (p * q + q * r + r * p) == 6 * N



m = bytes_to_long(flag)
e = 65537
c = pow(m, e, N)

print(f'{c = }')