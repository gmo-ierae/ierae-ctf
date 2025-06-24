flag = open('flag.txt', 'r').read()
x = [ord(c) for c in flag]
x.reverse()
y = [i^0xff for i in x]
z = [~i for i in y]
open('output.txt', 'w').write(str(z))
