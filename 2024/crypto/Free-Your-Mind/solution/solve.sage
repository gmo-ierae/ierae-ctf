from sage.all import *

UCF = UniversalCyclotomicField()
zeta = UCF.zeta(11).to_cyclotomic_field()

eta = zeta^2 + zeta^-2
NF.<omega> = NumberField(eta.minpoly())
deg = NF.degree()

# Since Hilbert's Theorem 90, We can compute an element such that `N(x) = 1`

PR = PolynomialRing(QQ, ["w"] + [f"x{i}" for i in range(deg)])
w = PR.gens()[0]
PQ = PR.quo(NF.gen().minpoly().subs(x=w)) # equivalent to NF but based on polynomial ring
gens = PQ.gens()
w = gens[0]

# we need to compute \phi \in \Gal_{K/\QQ}
phi = PQ.hom([NF.galois_group().gen()(NF.gen()).polynomial().subs(x=w)] + list(gens[1:]))

def norm(u):
    res = 1
    for _ in range(deg):
        res = phi(res)
        res *= u
    return res

beta = sum(x * w^i for i, x in enumerate(gens[1:]))

num = beta^2
for i in range(2, deg):
    num *= (phi^i)(beta)

denom = norm(beta)

num = num.lift()
denom = denom.lift()
gens = PR.gens()

nums = [num.subs(w=0)]
for i in range(1, deg):
    nums.append(((num - sum(x * w^j for j, x in enumerate(nums))) / w^i).lift().subs(w=0))
assert sum(num * w^j for j, num in enumerate(nums)) == num

L = [ZZ.random_element(2^16, 2^64) for _ in range(len(gens))]

v = {}
for j, ell in enumerate(L):
    v[gens[j]] = ell

res = []
denom = denom.subs(v)

for i, x in enumerate(nums):
    res.append(QQ(x.subs(v) / denom))

for x in res:
    print(x)

assert sum(omega^i * x for i, x in enumerate(res)).norm() == 1
