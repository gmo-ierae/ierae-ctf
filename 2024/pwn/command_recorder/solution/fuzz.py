from time import *
from random import randint
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

DISTINCT_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'

seq = []
num_line = 0

def reg(p, x):
  seq.append(x)
  p.sendline(x)

while 1:
  cmd = randint(1, 2)

  if cmd == 1 or num_line == 0:
    reg(p, '1')
    ver = randint(2, 4)
    if ver == 2 or ver == 3:
      reg(p, str(ver))
    else :
      reg(p, '4')
      reg(p, DISTINCT_CHARS)
  elif cmd == 2:
    reg(p, '2')
    ver = randint(0, num_line-1)
    reg(p, str(ver))

  p.sendline('5')
  p.recvuntil('=\n') 
  payload = p.recvuntil('=')[:-1]
  p.recvuntil('=\n') 
  print(payload)
  for l in payload.split(b'\n'):
    if len(l) == 8 and l in DISTINCT_CHARS.encode():
      print("Found!!!!!")
      print(seq)
      input()
  num_line = payload.count(b'\n')

  if len(seq) >= 300:
    while 1:
      for i in range(num_line):
        p.sendline('2')
        p.sendline('0')
        
      p.sendline('5')
      p.recvuntil('=\n') 
      payload = p.recvuntil('=')[:-1]
      p.recvuntil('=\n') 
      if not payload:
        break

    seq = []
    num_line = 0

p.sh()
