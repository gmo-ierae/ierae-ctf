#!/usr/bin/env sage

from sage.all import *
import flag
import sys
import os

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buffering=1)
sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', buffering=1)

# Initial configuration
UCF = UniversalCyclotomicField()
zeta = UCF.zeta(11).to_cyclotomic_field()

eta = zeta^2 + zeta^-2

# NF is a finite Galois extension of the rational field, hence NF is a simple extension of the rational field
NF.<omega> = NumberField(eta.minpoly())
deg = NF.degree()

CRITERIA = 2^16
BITS = 2048

def main():
    print("Welcome to *Number Theoretic* Encryption Oracle!")

    print("Enter your request key:")
    coeffs = []
    # you can enter any element of NF because omega's coefficient is controllable :)
    # ...but smaller value is prohibited to prevent cheating!
    for _ in range(deg):
        x = input().replace(" ", "")
        if "/" in x: 
            p, q = x.split("/")
            p = int(p)
            q = int(q)
            g = gcd(p, q)
            p /= g
            q /= g
            if abs(p) < CRITERIA or abs(q) < CRITERIA:
                print("You can't cheat!")
                return
            coeffs.append(QQ(p) / q)
        else:
            x = int(x)
            if abs(x) < CRITERIA:
                print("You can't cheat!")
                return
            coeffs.append(x)

    print("We got your request key")
    # your element is here
    alpha = sum(x * omega^i for i, x in enumerate(coeffs))

    # we use the norm of `alpha` for RSA's public key
    # class group order is not used here, because it is too complicated to compute :(
    e = alpha.norm()
    set_random_seed(int(str(alpha).encode().hex(), 16) * current_randstate().ZZ_seed()) # Add to the entropy pool
    p = random_prime(2^BITS)
    q = random_prime(2^BITS)

    N = p * q
    d = Mod(e, (p - 1) * (q - 1))^-1
    # print(f"{e = }") <- you don't need it because you can compute it, isn't it?
    print(f"{N = }")
    msg = ZZ(flag.FLAG.encode().hex(), 16)
    assert msg < N
    c = ZZ(Mod(msg, N)^e)
    assert Mod(c, N)^d == msg
    print(f"Enc(flag) = {c}") # Can you get the FLAG?

if __name__ == "__main__":
    try:
        main()
    except:
        print("Are you kidding me?")
