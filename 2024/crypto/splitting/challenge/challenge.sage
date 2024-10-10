#!/usr/bin/env sage

from Crypto.Util.number import *
from os import getenv

FLAG = getenv("FLAG", "TEST{TEST_FLAG}").encode()
f = bytes_to_long(FLAG)

p = random_prime(2^128)
Fp = GF(p)
a, b = Fp.random_element(), Fp.random_element()
E = EllipticCurve(Fp, [a, b])

print(a)
print(b)
print(p)

gens = list(E.gens())
if len(gens) < 2:
    gens.append(ZZ(Fp.random_element()) * E.gens()[0])

res = []
while f > 0:
    r = Fp.random_element()
    res.append(ZZ(r) * gens[f & 1])
    f >>= 1

for R in res:
    print(R.xy())
