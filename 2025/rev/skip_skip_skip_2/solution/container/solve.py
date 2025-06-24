from pwn import *
import hashlib
import itertools
import string
import sys

# Determined by RE + search
OFFSETS = [
    (1074 + 0 + 12 * 0) * 1024,
    (1074 + 0 + 12 * 1) * 1024,
    (1074 + 0 + 12 * 2) * 1024,
    (1074 + 1 + 12 * 3) * 1024,
    (1074 + 1 + 12 * 4) * 1024,
    (1074 + 1 + 12 * 5) * 1024,
    (1074 + 1 + 12 * 6) * 1024,
    (1074 + 2 + 12 * 7) * 1024,
    (1074 + 2 + 12 * 8) * 1024,
    (1074 + 2 + 12 * 9) * 1024,
    (1074 + 3 + 12 * 10) * 1024,
    (1074 + 3 + 12 * 11) * 1024,
    (1074 + 3 + 12 * 12) * 1024,
    (1074 + 3 + 12 * 13) * 1024,
    (1074 + 4 + 12 * 14) * 1024,
    (1074 + 4 + 12 * 15) * 1024,
    (1074 + 4 + 12 * 16) * 1024,
    (1074 + 5 + 12 * 17) * 1024,
    (1074 + 5 + 12 * 18) * 1024,
    (1074 + 5 + 12 * 19) * 1024,
    (1074 + 5 + 12 * 20) * 1024,
    (1074 + 6 + 12 * 21) * 1024,
    (1074 + 6 + 12 * 22) * 1024,
    (1074 + 6 + 12 * 23) * 1024,
    (1074 + 7 + 12 * 24) * 1024,
    (1074 + 7 + 12 * 25) * 1024,
    (1074 + 7 + 12 * 26) * 1024,
    (1074 + 7 + 12 * 27) * 1024,
    (1074 + 8 + 12 * 28) * 1024,
    (1074 + 8 + 12 * 29) * 1024,
    (1074 + 8 + 12 * 30) * 1024,
    (1074 + 9 + 12 * 31) * 1024,
]

def solve_pow(r):
    # Read the challenge line
    challenge_line = r.recvline().decode()

    # Parse prefix and difficulty from the challenge
    # Format: "Find a string X such that SHA256(prefix + X) starts with difficulty zeros"
    prefix = challenge_line.split('SHA256(')[1].split(' + X)')[0]
    difficulty = int(challenge_line.split('starts with ')[1].split(' zeros')[0])

    log.info(f"Prefix: {prefix}")
    log.info(f"Difficulty: {difficulty}")

    # Wait for "Enter X:" prompt
    r.recvuntil(b"Enter X:")

    # Brute force to find solution
    charset = string.ascii_lowercase + string.digits + string.ascii_uppercase
    found = False

    # Try different lengths
    for length in range(1, 20):  # Adjust max length if needed
        log.info(f"Trying length {length}")

        for attempt in itertools.product(charset, repeat=length):
            candidate = ''.join(attempt)
            test_hash = hashlib.sha256((prefix + candidate).encode()).hexdigest()

            if test_hash.startswith('0' * difficulty):
                log.success(f"Found solution: {candidate}")
                log.success(f"Hash: {test_hash}")
                r.sendline(candidate.encode())
                found = True
                break

        if found:
            break

    if not found:
        log.error("Could not find solution!")
        return False

    # Check response
    r.recvline().decode()
    response = r.recvline().decode()
    print(response)
    if "Correct" in response:
        log.success("PoW solved successfully!")
        return True
    else:
        log.error("PoW failed!")
        return False

def rc4_ksa(key, iteration=256):
    key_length = len(key)
    S = list(range(256))
    j = 0

    for i in range(iteration):
        j = (j + S[i] + key[i % key_length]) % 256
        S[i], S[j] = S[j], S[i]

    return S

def rc4_prga(S, plaintext):
    i = 0
    j = 0
    output = []

    for char in plaintext:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        output.append(char ^ K)

    return bytes(output)

def rc4_encrypt(key, plaintext, iteration=256):
    S = rc4_ksa(key, iteration=iteration)
    ciphertext = rc4_prga(S.copy(), plaintext)
    return ciphertext

def get_ct_sample(host, offset, plaintext):
    while True:
        try:
            r = remote(host, 58663)
            casenumber = r.recvline()
            solve_pow(r)

            resp = r.recvuntil(b"Enter trigger character (0x00 <= x <= 0xff):\n")
            casenumber = resp.splitlines()[0]
            r.sendline(b"0x0a")

            r.recvuntil(b"Enter trigger count (1 <= x):\n")
            r.sendline(b"5")

            r.recvuntil(b"Enter offset time in ns (0 <= x):\n")
            r.sendline(bytes(str(offset), 'ascii'))

            r.recvuntil(b"Enter input (hex):\n")
            r.sendline(plaintext.hex().encode())

            r.recvuntil(b"Encrypted data:\\r\\n")
            ciphertext = bytes.fromhex(r.recvuntil(b"\\r\\n").removesuffix(b"\\r\\n").decode())
            return ciphertext
        except pwnlib.exception.PwnlibException as e:
            print(f"Retrying: {e.__class__.__name__} {str(e)}")
        except EOFError as e:
            print(f"Retrying: {e.__class__.__name__} {str(e)}")
            pass

def main():
    host = sys.argv[1]

    flag = b""
    for i, os in enumerate(OFFSETS):
        ct_sample = get_ct_sample(host, os, b"A" * 31 + b"\n")
        print(ct_sample.hex())
        for ch in range(256):
            ct_cand = rc4_encrypt(flag + bytes((ch,)), b"A" * 31 + b"\x00", iteration = i + 1)
            if ct_sample == ct_cand:
                flag += bytes((ch,))
                print(flag)
                break
        else:
            assert False, "No cand ch found."

    assert flag == b"IERAE{9d33cf4fac8bb36ea2cbf7e98}"
    print("Correct flag. OK.")

if __name__ == '__main__':
    main()
