from Crypto.Util.number import *

n, m, q, c = 512, 4 * 512, 2**20, 8

with open("output2.txt") as f:
    for _ in range(4):
        f.readline()
    A = eval(f.readline().replace("A = ", ""))
    b = eval(f.readline().replace("b = ", ""))
    flag_ciphertext = eval(f.readline().replace("flag_ciphertext = ", ""))

A1 = []
b1 = []
for i in range(m):
    if b[i]%(2**8)>(400-256):
        A1.append([v//(2**8) for v in A[i]])
        b1.append(b[i]//(2**8))
print(len(b1))
s = matrix(Zmod(q//(2**8)), A1).solve_right(vector(Zmod(q//(2**8)), b1))
s = vector(Zmod(q), [int(v) for v in s])
print(s)

flag_bin = ""
for u,v in flag_ciphertext:
    w = vector(Zmod(q), u).dot_product(s)-Zmod(q)(v)
    # print(w)
    if q//4 < int(w) < 3*q//4:
        flag_bin += "1"
    else:
        flag_bin += "0"

flag = []
for i in range(0, len(flag_bin), 8):
    flag.append(int(flag_bin[i:i+8][::-1], 2))
print(bytes(flag))
