from pwn import *

LENGTH = 15

def send_1(s):
    s.sendlineafter(b'> ', b'1')
    response = s.recvline().decode()
    return response.split('hint: ')[1].strip()

def send_2(s, result):
    s.sendlineafter(b'> ', b'2')
    s.sendlineafter(b'> ', result.encode())

def connect_and_interact():
    s = remote('localhost', 55555)
    hints = []

    for _ in range(100):
        hints.append(send_1(s))

    result = ''.join(next(iter(set(hints[0]) - {hint[i] for hint in hints if len(hint) > i})) for i in range(LENGTH))
    print(f"magic string: {result}")

    send_2(s, result)
    s.recvline() 
    print(f"Received FLAG: {s.recvline().decode()}")

if __name__ == "__main__":
    connect_and_interact()
