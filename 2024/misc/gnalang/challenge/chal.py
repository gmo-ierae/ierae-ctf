#!/usr/bin/env python3

"""
Your task is to write a polyglot of JavaScript and shell script.
The polyglot must meet the following conditions:

 - The polyglot must be executable in `sh` and `node` both.
 - `sh` and `node` must exit normally when executing the polyglot.
 - `sh` and `node` must return the same output when executing the polyglot.
 - `sh` must never cause error for each executed command.
 - The polyglot must output "Yes\n" when the string given from stdin is a palindrome. "No\n" otherwise.
 - The polyglot must be a palindrome.
 - The polyglot must not contain the following tokens: '$', '#', "//", "<!--", "-->", '\n', ' '.
 - The polyglot must not write anything to file as a shell script (because it fails and causes error)

Sample Input  #1
ABCDEEDCBA
----------------
Sample Output #1
Yes

----------------
Note that inputs do not contain '\n' while outputs should contain '\n'.

================

Sample Input  #2
ABCDE
----------------
Sample Output #2
No

----------------

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
  sys.stdout.write('Input program: ')
  sys.stdout.flush()

  prog = sys.stdin.readline()
  myassert(prog[-1] == '\n', "the program should end with '\n'")

  prog = prog[:-1] # trim

  # disallowed chars
  myassert(not '$' in prog, "$ should not be contained")
  myassert(not '#' in prog, "# should not be contained")
  myassert(not ' ' in prog, "' ' should not be contained")
  myassert(not '\n' in prog, "'\\n' should not be contained")
  myassert(not '//' in prog, "\"//\" should not be contained")
  myassert(not '<!--' in prog, "\"<!--\" should not be contained")
  myassert(not '-->' in prog, "\"-->\" should not be contained")

  # should be a palindrome
  myassert(prog == prog[::-1], "the program should be a palindrome")

  with tempfile.NamedTemporaryFile(mode='w') as sh_f:
    sh_f.write('set -eu\n') # no error should be allowed
    sh_f.write(prog)
    sh_f.flush()

    with tempfile.NamedTemporaryFile(mode='w') as js_f:
      js_f.write(prog)
      js_f.flush()

      # verify program with 100 testcases
      for i in range(100):
        testcase = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))

        is_palindrome = random.randint(0, 1)
        if is_palindrome:
          testcase = testcase + testcase[::-1]

        subprocess.run(['chmod', 'o+r', sh_f.name])
        sh_result = subprocess.run(['sudo', '-u', 'nobody', 'sh', sh_f.name], 
                                      input=testcase.encode(), capture_output=True)
        myassert(sh_result.returncode == 0, "sh should exit normally")
        sh_output = sh_result.stdout
        print('sh output: {}'.format(sh_output))

        subprocess.run(['chmod', 'o+r', js_f.name])
        js_result = subprocess.run(['sudo', '-u', 'nobody', 'node', js_f.name], 
                                      input=testcase.encode(), capture_output=True)
        myassert(js_result.returncode == 0, "node should exit normally")
        js_output = js_result.stdout
        print('js output: {}'.format(js_output))

        # output must be the same between js and sh
        myassert(sh_output == js_output, "sh and node should return the same output")

        # the program must judge if the given string is a palindrome
        if is_palindrome:
          myassert(sh_output == b'Yes\n', "the program should output Yes")
        else:
          myassert(sh_output == b'No\n', "the program should output No")

  with open('./flag.txt') as f:
    flag = f.read()

  sys.stdout.write('Well done!\n')
  sys.stdout.write('The flag is {}\n'.format(flag))
  sys.stdout.flush()

if __name__ == '__main__':
  main()
