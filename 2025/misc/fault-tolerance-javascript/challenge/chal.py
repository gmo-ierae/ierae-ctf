#!/usr/bin/env python3

"""

Your task is to write a JavaScript code that works even if any one character of it is removed.
Specifically, you must give to this script a string `prog` that meets the following conditions:

  * For any integer i (0 <= i < `len(prog)`), `prog[:i] + prog[i+1:]` is recognized as a valid JavaScript code and outputs `"hello\n"`.
  * `len(prog)` must be smaller than or equal to 1500.

Do not try to save something to files and reuse it, as it would fail.

"""

import sys
import string
import random
import tempfile
import subprocess

def myassert(cond, msg):
  if not cond:
    print(msg)
    sys.exit(1)

def main():
  sys.stdout.write('Input length: ')

  prog_len = int(sys.stdin.readline()[:-1])
  myassert(1 <= prog_len, "Don't hack!")
  myassert(prog_len <= 1500, "len(prog) must be smaller than or equal to 1500")

  sys.stdout.write('Input prog: ')

  prog = ''
  for i in range(prog_len):
    prog += sys.stdin.read(1)
  myassert(prog_len == len(prog), "EOF detected")

  verified = False

  # fault tolerance
  for i in range(prog_len):
    print('\n# i={}'.format(i))

    code = prog[:i] + prog[i+1:]

    with tempfile.NamedTemporaryFile(mode='w') as f:
      f.write(code)
      f.flush()

      # check if the program outputs "hello\n"

      subprocess.run(['chmod', 'o+r', f.name])
      result = subprocess.run(['sudo', '-u', 'nobody', 'node', f.name], capture_output=True)
      myassert(result.returncode == 0, "node should exit normally")

      output = result.stdout
      print('output: {}'.format(output))

      myassert(output == b'hello\n', 'the program should output "hello\\n"')
      verified = True

  myassert(verified, 'How did you fool it?')

  with open('./flag.txt') as f:
    flag = f.read()

  print('Well done!')
  print('The flag is {}'.format(flag))

if __name__ == '__main__':
  main()
