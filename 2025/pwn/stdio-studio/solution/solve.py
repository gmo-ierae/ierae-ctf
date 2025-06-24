from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv

is_remote = len(argv) >= 2

if is_remote:
  assert False
else :
  p = Socket('localhost', 33335)

p.sendline('1')
p.sendline('2')
p.sendline(str(0x50))
p.shutdown('send')

print(p.recv(1024))
print(p.recv(1024))
print(p.recv(1024))
