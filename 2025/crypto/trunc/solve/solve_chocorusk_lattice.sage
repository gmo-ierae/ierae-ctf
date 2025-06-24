from Crypto.Util.number import *

n, m, q, c = 80, 4 * 80, 2**16, 8

with open("output.txt") as f:
    for _ in range(4):
        f.readline()
    A = eval(f.readline().replace("A = ", ""))
    b = eval(f.readline().replace("b = ", ""))
    flag_ciphertext = eval(f.readline().replace("flag_ciphertext = ", ""))

m = 100
w1 = 200
mat = [[0]*(m+n+1) for _ in range(m+n+1)]
for i in range(n):
    for j in range(m):
        mat[i][j] = A[j][i]
for i in range(m):
    mat[n][i] = -b[i]
for i in range(m):
    mat[n+1+i][i] = q
for i in range(n):
    mat[i][m+i] = w1
mat[n][n+m] = 1

res = matrix(ZZ,mat).BKZ(block_size=14)
for v in res:
    if v[-1]!=0:
        print(v)
        if v[-1]==-1:
            v = [-w for w in v]
        v = [w//w1 for w in v]
        s = vector(Zmod(q), v[-n-1:-1])
        break

def decrypt_flag_with_key(flag_ciphertext, s):
    flag = []
    for i, ch in enumerate(flag_ciphertext):
        key = int(s[i % len(s)])
        flag.append((ch - key) % q)
    return flag

print(bytes(decrypt_flag_with_key(flag_ciphertext, s)))
