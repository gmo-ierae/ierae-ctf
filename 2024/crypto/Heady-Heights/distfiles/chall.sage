from sage.all import *
import flag

BITS = 88
K = 8


def random(lower_bound=0, upper_bound=2 ^ BITS, bits=None):
    return ZZ.random_element(lower_bound, upper_bound)


def random_bits(bits):
    return random(2 ^ (bits - 1), 2 ^ bits)


p = next_prime(random_bits(BITS))
m = ZZ(flag.FLAG.encode().hex(), 16)

a, b, E = None, None, None
P = None
Q = None
R = None

while True:
    a = random_bits(BITS)
    b = random_bits(BITS)
    E = EllipticCurve(Zmod(p ^ K), [a, b])
    try:
        P = E.lift_x(1337)
        break
    except:
        continue

while True:
    secret_key = random(upper_bound=p ^ (K - 1))
    x0 = (secret_key * m) % (p ^ K)
    try:
        R = E.lift_x(x0)
        break
    except:
        continue

Q = secret_key * P


def xy(P):
    t = P.xy()
    return ZZ(t[0]), ZZ(t[1])


x1, y1 = xy(P)
x2, y2 = xy(Q)
x3, y3 = xy(R)

print((x1, x2, x3))
print((y1, y2, y3))
