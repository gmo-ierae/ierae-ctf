import datetime
import ctypes
from Crypto.Cipher import AES

crt = ctypes.CDLL('msvcrt.dll')

crt.srand.argtypes = [ctypes.c_uint]
crt.srand.restype = None
crt.rand.argtypes = []
crt.rand.restype = ctypes.c_int

def srand(seed):
    crt.srand(seed)

def rand():
    return crt.rand()

def rand_range(min_val, max_val):
    rand_value = rand()
    rand_value *= rand()
    rand_value *= rand()
    rand_value &= 0xffffffff
    max_dword32 = 2**32 - 1
    return min_val + rand_value // (max_dword32 // (max_val - min_val + 1) + 1)

def unshuffle_data(data):
    size = len(data)
    swaps = []
    for i in range(size):
        j = rand_range(0, size - 1)
        swaps.append((i, j))
    unshuffled_data = bytearray(data)
    for i, j in reversed(swaps):
        unshuffled_data[i], unshuffled_data[j] = unshuffled_data[j], unshuffled_data[i]
    return unshuffled_data

def decrypt_aes_cbc(encrypted_data, key, iv):
    aes = AES.new(key, AES.MODE_CBC, iv=iv)
    decrypted = aes.decrypt(encrypted_data)
    return decrypted

def main():
    # Read the encrypted file
    with open('flag.png.laika', 'rb') as f:
        encrypted_data = f.read()

# zipinfo -v ./laika.zip
#   statement.png
#   file last modified on (UT extra field modtime): 2024 Sep 17 12:49:20 local

#   flag.png.laika
#   file last modified on (UT extra field modtime): 2024 Sep 17 12:49:20 local

    mod_date = datetime.datetime(2024, 9, 17, 12, 49, 20)
    localtime = {
        'wYear': mod_date.year,
        'wMonth': mod_date.month,
        'wDayOfWeek': mod_date.isoweekday() % 7, # 0: Sunday, 1: Monday, ..,, 6: Saturday
        'wDay': mod_date.day,
        'wHour': mod_date.hour,
        'wMinute': mod_date.minute,
        'wSecond': mod_date.second,
        'wMilliseconds': 0
    }
    for msec in range(1000):
        if msec % 50 == 0:
            print(f"Current msec: {msec:04d}")
        localtime['wMilliseconds'] = msec

        seed = 1
        for key in localtime:
            seed = (seed * 131243 + localtime[key]) & 0xffffffff

        srand(seed)

        # Key and IV (should be the same as used in encryption)
        key = bytes([rand() & 0xff for _ in range(32)])  # Replace with actual key
        iv = bytes([rand() & 0xff for _ in range(16)])   # Replace with actual IV

        # Unshuffle the data
        unshuffled_data = unshuffle_data(encrypted_data)

        # Decrypt the data
        decrypted_head = decrypt_aes_cbc(unshuffled_data[:16], key, iv)
        PNG_MAGIC = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'

        if decrypted_head.startswith(PNG_MAGIC):
            decrypted_data = decrypt_aes_cbc(unshuffled_data, key, iv)
            with open('decrypted_flag.png', 'wb') as f:
                f.write(decrypted_data)
            print("Decryption succeeded")
            break

if __name__ == '__main__':
    main()
