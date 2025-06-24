from sys import argv
import subprocess

def main():
  if len(argv) < 2:
    print(f'{argv[0]} (file)')
    return 

  with open(argv[1], 'r') as f:
    prog = f.read()

  for i in range(len(prog)):
    if i%10 == 0:
      print(i)

    code = prog[:i] + prog[i+1:]

    with open('under_test.js', 'w') as f:
      f.write(code)

    p = subprocess.Popen(["node", 'under_test.js'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()

    if stderr:
      print('{}: ERROR'.format(i))
      print('stdout: {}'.format(stdout))
      print('stderr: {}'.format(stderr))
      print('==============')
      print(code)
      print('==============')
      input()
    elif stdout != b'hello\n':
      print('{}: NOT HELLO'.format(i))
      print('stdout: {}'.format(stdout))


if __name__ == '__main__':
  main()
