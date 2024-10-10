import random
random.seed(131243)

template = open('template.lua', 'r').read()
flag = open('flag.txt', 'r').read().strip()

code = template.replace('FLAG_LEN', f'{len(flag):d}')

validate_flag = ''

for i in range(len(flag)):
    flag_char = ord(flag[i])
    xor_key = random.randint(1, 255)
    validate_flag += f'if string.byte(input, {i+1:d}) ~ {xor_key:d} ~= {flag_char^xor_key:d} then goto wrong end\n'

code = code.replace('VALIDATE_FLAG', validate_flag)
open('LuzDaLua.lua', 'w').write(code)

