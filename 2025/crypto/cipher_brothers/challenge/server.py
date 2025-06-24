from Crypto.Util.number import *

with open("flag.txt", "r") as f:
	FLAG = f.read().strip().encode("utf-8")

def primitive_root(p):
	g = getRandomRange(2, p - 1)
	while pow(g, (p - 1) // 2, p) == 1:
		g = getRandomRange(2, p -1)
	return g

def key_generation(nbits=256):
	while True:
		q = getPrime(nbits - 1)
		p = 2 * q + 1
		if isPrime(p):
			break
	g = primitive_root(p)
	x = getRandomRange(0, p)
	h = pow(g, x, p)
	return (p, g, h)

def enc(m, p, g, h):
	r = getRandomRange(0, p)
	c1 = pow(g, r, p)
	c2 = (m * pow(h, r, p)) % p
	return (c1, c2)

p, g, h = key_generation()
m = bytes_to_long(FLAG)
red = int(input())
c1, c2 = enc(m % red, p, g, h)

print("p:", p)
print("g:", g)
print("h:", h)
print("c1:", c1)
print("c2:", c2)
