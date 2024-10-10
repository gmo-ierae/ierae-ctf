from pwn import tubes,process,remote,context
import random
import sys


# ---- from https://zenn.dev/hk_ilohas/articles/mersenne-twister-previous-state#%E9%81%8E%E5%8E%BB%E3%81%AE%E5%86%85%E9%83%A8%E7%8A%B6%E6%85%8B%E3%81%AE%E5%BE%A9%E5%85%83
def untemper(x):
    x = unBitshiftRightXor(x, 18)
    x = unBitshiftLeftXor(x, 15, 0xefc60000)
    x = unBitshiftLeftXor(x, 7, 0x9d2c5680)
    x = unBitshiftRightXor(x, 11)
    return x

def unBitshiftRightXor(x, shift):
    i = 1
    y = x
    while i * shift < 32:
        z = y >> shift
        y = x ^ z
        i += 1
    return y


def unBitshiftLeftXor(x, shift, mask):
    i = 1
    y = x
    while i * shift < 32:
        z = y << shift
        y = x ^ (z & mask)
        i += 1
    return y

def get_prev_state(state):
    for i in range(623, -1, -1):
        result = 0
        tmp = state[i]
        tmp ^= state[(i + 397) % 624]
        if ((tmp & 0x80000000) == 0x80000000):
            tmp ^= 0x9908b0df
        result = (tmp << 1) & 0x80000000
        tmp = state[(i - 1 + 624) % 624]
        tmp ^= state[(i + 396) % 624]
        if ((tmp & 0x80000000) == 0x80000000):
            tmp ^= 0x9908b0df
            result |= 1
        result |= (tmp << 1) & 0x7fffffff
        state[i] = result
    return state

# ----

context.log_level = 'info'

#io = remote('127.0.0.1', 19937)
io = process([sys.executable, './challenge.py'])


io.recvuntil(b'Enter your choice (1-3)\n> ')

outputs = []
required_outputs = 624

while len(outputs) < required_outputs:
    io.sendline(b'1')
    io.recvuntil(b'Here are your random data:\n')
    for _ in range(16):
        line = io.recvline().strip()
        num = int(line)
        outputs.append(num)
    io.recvuntil(b'Enter your choice (1-3)\n> ')

outputs = outputs[:624]
state = [untemper(output) for output in outputs]

state = get_prev_state(state)


mt = random.Random()
state = (3, tuple(state + [623]), None)
mt.setstate(state)

answer = mt.getrandbits(32)


io.sendline(b'2')
io.sendlineafter(b'> ', str(answer).encode())

print(io.recvallS())
