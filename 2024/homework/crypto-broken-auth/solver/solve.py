from scryptos import ub32, StreamReader, bytes_to_long, gcd, RSA
import base64
import os


def read_ssh_pubkey(pubkey: str) -> (int, int):
    assert pubkey.startswith("ssh-rsa ")
    sr = StreamReader(base64.b64decode(pubkey.split(" ")[1]))
    tag_name_len = ub32(sr.read(4))
    tag_name = sr.read(tag_name_len)
    assert tag_name == b"ssh-rsa"
    e_len = ub32(sr.read(4))
    e = bytes_to_long(sr.read(e_len))
    n_len = ub32(sr.read(4))
    n = bytes_to_long(sr.read(n_len))
    return (e, n)


def main():
    e1, n1 = read_ssh_pubkey(open("key_1.pub").read())
    e2, n2 = read_ssh_pubkey(open("key_2.pub").read())

    assert e1 == e2
    g = gcd(n1, n2)

    open("recovered_key1.priv", "wb").write(RSA(e=e1, n=n1, p=g).to_pem())
    open("recovered_key2.priv", "wb").write(RSA(e=e2, n=n2, p=g).to_pem())
    
    os.system("chmod 600 recovered_key2.priv && ssh flag@domain.name -p5555 -i recovered_key2.priv 2>/dev/null")
    
    # flag: echo "gcd(Veni, Vidi, Vici)" | sha1sum

if __name__ == "__main__":
    main()
