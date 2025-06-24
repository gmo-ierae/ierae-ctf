#!/usr/bin/env python3
import subprocess
from pwn import *

with open("solution.bc", "rb") as f:
    sol = f.read()

while True:
    with remote('localhost', 12450) as sok:
        _, pow, _ = sok.recvuntil(b'solution: ').splitlines()
        output = subprocess.check_output(pow, shell=True)
        sok.send(output)

        sok.recvuntil(b'number of bytes: ')

        sok.sendline(str(len(sol)).encode())
        sok.send(sol)

        resp = sok.recvall()
        if resp:
            print(resp)
            break
