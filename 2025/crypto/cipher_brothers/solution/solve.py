from ptrlib import *
from Crypto.Util.number import *
import math

def kronecker(x, p):
	if math.gcd(x, p) != 1:
		return 0
	if pow(x, (p - 1) // 2, p) == 1:
		return 1
	return -1

def app(red):
	s = Process(["python3", "server.py"])
	s.sendline(str(red).encode("utf-8"))
	p = eval(s.recvline().split()[1])
	g = eval(s.recvline().split()[1])
	h = eval(s.recvline().split()[1])
	c1 = eval(s.recvline().split()[1])
	c2 = eval(s.recvline().split()[1])
	s.interactive()
	s.close()

	return p, g, h, c1, c2

def is_m_qr(c1, c2, p, g, h):
	if kronecker(h, p) == 1:
		if kronecker(c2, p) == 1:
			return 1
		else:
			return -1
	if kronecker(c1, p) == 1:
		# r is even
		# -> h^r is qr
		if kronecker(c2, p) == 1:
			return 1
		else:
			return -1
	# r is odd
	# -> h^r is nqr
	if kronecker(c2, p) == 1:
		return -1
	else:
		return 1

def enc(m, p, g, h):
	r = randint(0, p - 1)
	c1 = pow(g, r, p)
	c2 = (m * pow(h, r, p)) % p
	return (c1, c2)

red = 256
m = b'01111101'
while True:
	red <<= 1
	while True:
		p, g, h, c1, c2 = app(red)
		k1 = kronecker(int(b'0' + m, 2), p)
		k2 = kronecker(int(b'1' + m, 2), p)
		if k1 != k2:
			break
	is_qr = is_m_qr(c1, c2, p, g, h)
	if k1 == is_qr:
		m = b'0' + m
	else:
		m = b'1' + m
	print(m)
	print(long_to_bytes(int(m, 2)))

