from scryptos import long_to_bytes, pb32, gcd, RSA
import base64
import random
import gmpy2


def generate_prime(bits=2048) -> int:
    while True:
        p = gmpy2.next_prime(random.randint(2**2048, 2**2049))
        if gcd(p - 1, 65537) == 1:
            return int(p)


def encode_to_mpint(num: int) -> bytes:
    if num == 0:
        return b"\x00\x00\x00\x00"
    b = long_to_bytes(num)
    if b[0] & (1 << 7):
        b = b"\x00" + b
    return pb32(len(b)) + b


def encode_to_rfc4253_str(s: str) -> bytes:
    return pb32(len(s)) + s.encode()


def encode_to_ssh_rsa(e: int, n: int, comment: str) -> str:
    raw = encode_to_rfc4253_str("ssh-rsa") + encode_to_mpint(e) + encode_to_mpint(n)
    return f"ssh-rsa {base64.b64encode(raw).decode()} {comment}"


def main():
    e = 65537
    p = generate_prime()
    q1 = generate_prime()
    q2 = generate_prime()
    n1 = p * q1
    n2 = p * q2
    alice_pubkey = encode_to_ssh_rsa(e, n1, "alice")
    bob_pubkey = encode_to_ssh_rsa(e, n2, "bob")
    open("key_1.pub", "w").write(alice_pubkey)
    open("key_2.pub", "w").write(bob_pubkey)
    open("key_1.priv", "wb").write(RSA(e, n1, p=p, q=q1).to_pem())
    open("key_2.priv", "wb").write(RSA(e, n2, p=p, q=q2).to_pem())
    prefix_ls = 'command="/bin/ls"'
    prefix_flag = 'command="/bin/print_flag"'
    open("authorized_keys", "w").write(
        f"{prefix_ls} {alice_pubkey}\n{prefix_flag} {bob_pubkey}\n"
    )


if __name__ == "__main__":
    main()
