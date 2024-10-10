from pwn import *
from Crypto.Util.number import *

#config
context(os='linux', arch='i386')
context.log_level = 'debug'

HOST = "127.0.0.1"
PORT = 21449

conn = remote(HOST, PORT)

conn.sendlineafter(b'> Enter number:\n', b'2')
conn.sendlineafter(b'> Enter message:', b'Welcome_to_IERAE_DAYS_2023!!')
conn.sendlineafter(b'> Enter signature (Hex format):', b'0000')
print(conn.recvall())