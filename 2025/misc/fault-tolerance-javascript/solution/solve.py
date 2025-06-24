from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv

is_remote = len(argv) >= 2

if is_remote:
  assert False
else :
  p = Socket('localhost', 9319)

with open('sol.js') as f:
  prog = f.read()

p.sendline('{}'.format(len(prog)))
p.send(prog)

while 1:
  print(p.recv(1024))
