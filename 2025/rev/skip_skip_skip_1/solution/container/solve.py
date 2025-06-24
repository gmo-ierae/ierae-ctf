from pwn import *
import hashlib
import itertools
import string
import sys

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

def main():
    r = remote(sys.argv[1], 63693)
    casenumber = r.recvline()
    solve_pow(r)

    resp = r.recvuntil(b"Enter trigger character (0x00 <= x <= 0xff):\n")
    casenumber = resp.splitlines()[0]
    r.sendline(b"0x0a")

    r.recvuntil(b"Enter trigger count (1 <= x):\n")
    r.sendline(b"4")

    r.recvuntil(b"Enter offset time in ns (0 <= x):\n")
    r.sendline(bytes(str((9437734912 - 6291977216) - 1024 * 12), 'ascii'))

    r.recvuntil(b"Enter input (hex):\n")
    r.sendline(b"0a")

    resp = r.recv()
    if b"IERAE{514ac1684b9c7a95cf26e0bf9}" in resp:
        print("Got flag. OK.")
        exit(0)
    else:
        print("No flag got. NG.")
        exit(1)

if __name__ == '__main__':
    main()
