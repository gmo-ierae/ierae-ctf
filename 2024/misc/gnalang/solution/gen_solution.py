import sys

assert len(sys.argv) >= 2

with open(sys.argv[1]) as f:
  s = f.read()

s = s.rstrip('\n')

assert not '//' in s
assert not '$' in s
assert not '#' in s
if '\n' in s:
  print('Warning: newline contained')
#assert not '\n' in s

with open('solve.sh', 'w') as f:
  #f.write("set -eu\n" + s + s[::-1])
  
  for l in s.split('\n'):
    l = l.replace(' ', '\x09')
    f.write(l + l[:-1][::-1] + '\n')
