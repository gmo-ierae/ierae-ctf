from pwn import *
import argparse

# context.log_level = 'debug'
context.log_level = 'error'

def parse_args():
    parser = argparse.ArgumentParser(description='Exploit for Fortress')
    parser.add_argument('--host', type=str, default='localhost', help='Host to connect to')
    parser.add_argument('--port', type=int, default=20001, help='Port to connect to')
    parser.add_argument('--binary', type=str, default=None, help='Path to the fortress binary')
    return parser.parse_args()

class Fortress():
    B64_TABLE = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    B64_DECODE_TABLE = {c: i for i, c in enumerate(B64_TABLE)}

    SBOX = [
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
    ]

    INV_SBOX = [
        0x52, 0x09, 0x6a, 0xd5, 0x30, 0x36, 0xa5, 0x38, 0xbf, 0x40, 0xa3, 0x9e, 0x81, 0xf3, 0xd7, 0xfb,
        0x7c, 0xe3, 0x39, 0x82, 0x9b, 0x2f, 0xff, 0x87, 0x34, 0x8e, 0x43, 0x44, 0xc4, 0xde, 0xe9, 0xcb,
        0x54, 0x7b, 0x94, 0x32, 0xa6, 0xc2, 0x23, 0x3d, 0xee, 0x4c, 0x95, 0x0b, 0x42, 0xfa, 0xc3, 0x4e,
        0x08, 0x2e, 0xa1, 0x66, 0x28, 0xd9, 0x24, 0xb2, 0x76, 0x5b, 0xa2, 0x49, 0x6d, 0x8b, 0xd1, 0x25,
        0x72, 0xf8, 0xf6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xd4, 0xa4, 0x5c, 0xcc, 0x5d, 0x65, 0xb6, 0x92,
        0x6c, 0x70, 0x48, 0x50, 0xfd, 0xed, 0xb9, 0xda, 0x5e, 0x15, 0x46, 0x57, 0xa7, 0x8d, 0x9d, 0x84,
        0x90, 0xd8, 0xab, 0x00, 0x8c, 0xbc, 0xd3, 0x0a, 0xf7, 0xe4, 0x58, 0x05, 0xb8, 0xb3, 0x45, 0x06,
        0xd0, 0x2c, 0x1e, 0x8f, 0xca, 0x3f, 0x0f, 0x02, 0xc1, 0xaf, 0xbd, 0x03, 0x01, 0x13, 0x8a, 0x6b,
        0x3a, 0x91, 0x11, 0x41, 0x4f, 0x67, 0xdc, 0xea, 0x97, 0xf2, 0xcf, 0xce, 0xf0, 0xb4, 0xe6, 0x73,
        0x96, 0xac, 0x74, 0x22, 0xe7, 0xad, 0x35, 0x85, 0xe2, 0xf9, 0x37, 0xe8, 0x1c, 0x75, 0xdf, 0x6e,
        0x47, 0xf1, 0x1a, 0x71, 0x1d, 0x29, 0xc5, 0x89, 0x6f, 0xb7, 0x62, 0x0e, 0xaa, 0x18, 0xbe, 0x1b,
        0xfc, 0x56, 0x3e, 0x4b, 0xc6, 0xd2, 0x79, 0x20, 0x9a, 0xdb, 0xc0, 0xfe, 0x78, 0xcd, 0x5a, 0xf4,
        0x1f, 0xdd, 0xa8, 0x33, 0x88, 0x07, 0xc7, 0x31, 0xb1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xec, 0x5f,
        0x60, 0x51, 0x7f, 0xa9, 0x19, 0xb5, 0x4a, 0x0d, 0x2d, 0xe5, 0x7a, 0x9f, 0x93, 0xc9, 0x9c, 0xef,
        0xa0, 0xe0, 0x3b, 0x4d, 0xae, 0x2a, 0xf5, 0xb0, 0xc8, 0xeb, 0xbb, 0x3c, 0x83, 0x53, 0x99, 0x61,
        0x17, 0x2b, 0x04, 0x7e, 0xba, 0x77, 0xd6, 0x26, 0xe1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0c, 0x7d,
    ]

    FORTRESS_BLOCK_SIZE = 32

    def __init__(self, host: str, port: int, binary: str):
        self.host = host
        self.port = port
        self.binary = binary
        self.test_plain = b'\x00' * 64
        self.num_skip_round = 0
        self.normal_enc = self.getEncryptedData(self.test_plain)

    @staticmethod
    def b64encode(data: bytes, paddingBits: int = 0) -> str:
        encoded = ''
        for i in range(0, len(data), 3):
            block = data[i:i+3]
            if len(block) == 3:
                encoded += Fortress.B64_TABLE[block[0] >> 2]
                encoded += Fortress.B64_TABLE[((block[0] & 0x03) << 4) | (block[1] >> 4)]
                encoded += Fortress.B64_TABLE[((block[1] & 0x0f) << 2) | (block[2] >> 6)]
                encoded += Fortress.B64_TABLE[block[2] & 0x3f]
            elif len(block) == 2:
                encoded += Fortress.B64_TABLE[block[0] >> 2]
                encoded += Fortress.B64_TABLE[((block[0] & 0x03) << 4) | (block[1] >> 4)]
                encoded += Fortress.B64_TABLE[((block[1] & 0x0f) << 2) | (paddingBits & 0x03)]
                encoded += '='
            else:
                encoded += Fortress.B64_TABLE[block[0] >> 2]
                encoded += Fortress.B64_TABLE[((block[0] & 0x03) << 4) | (paddingBits & 0x0f)]
                encoded += '=='
        return encoded

    @staticmethod
    def b64decode(data: str) -> bytes:
        if isinstance(data, bytes):
            data = data.decode()
        decoded = bytearray()
        for i in range(0, len(data), 4):
            block = data[i:i+4]
            if block[-2:] == '==':
                block = [Fortress.B64_DECODE_TABLE[c] for c in block[:-2]]
                decoded.append(((block[0] << 2) | (block[1] >> 4)) & 0xff)
            elif block[-1] == '=':
                block = [Fortress.B64_DECODE_TABLE[c] for c in block[:-1]]
                decoded.append(((block[0] << 2) | (block[1] >> 4)) & 0xff)
                decoded.append(((block[1] << 4) | (block[2] >> 2)) & 0xff)
            else:
                block = [Fortress.B64_DECODE_TABLE[c] for c in block]
                decoded.append(((block[0] << 2) | (block[1] >> 4)) & 0xff)
                decoded.append(((block[1] << 4) | (block[2] >> 2)) & 0xff)
                decoded.append(((block[2] << 6) | block[3]) & 0xff)
        return bytes(decoded)

    @staticmethod
    def mul(dt, n):
        x = 0
        i = 8
        while i > 0:
            x <<= 1
            if x & 0x100:
                x = (x ^ 0x1b) & 0xff
            if n & i:
                x ^= dt
            i >>= 1
        return x

    @staticmethod
    def mul1(value: int) -> int:
        assert(abs(value) < 256)
        return value

    @staticmethod
    def mul2(value: int) -> int:
        assert(abs(value) < 256)
        return Fortress.mul(value, 2)
    
    @staticmethod
    def mul3(value: int) -> int:
        assert(abs(value) < 256)
        return Fortress.mul(value, 3)
    
    @staticmethod
    def mul9(value: int) -> int:
        assert(abs(value) < 256)
        return Fortress.mul(value, 9)
    
    @staticmethod
    def mul11(value: int) -> int:
        assert(abs(value) < 256)
        return Fortress.mul(value, 11)
    
    @staticmethod
    def mul13(value: int) -> int:
        assert(abs(value) < 256)
        return Fortress.mul(value, 13)

    @staticmethod
    def mul14(value: int) -> int:
        assert(abs(value) < 256)
        return Fortress.mul(value, 14)

    @staticmethod
    def subBytes(state: bytes) -> bytes:
        return bytes([Fortress.SBOX[b] for b in state])
    
    @staticmethod
    def shiftRows(state: bytes) -> bytes:
        return bytes([
            state[0], state[5], state[10], state[15],
            state[4], state[9], state[14], state[3],
            state[8], state[13], state[2], state[7],
            state[12], state[1], state[6], state[11]
        ])

    @staticmethod
    def mixColumns(state: bytes) -> bytes:
        state = bytearray(state)
        for i in range(0, len(state), 4):
            a = state[i]
            b = state[i + 1]
            c = state[i + 2]
            d = state[i + 3]
            state[i] = Fortress.mul2(a) ^ Fortress.mul3(b) ^ c ^ d
            state[i + 1] = a ^ Fortress.mul2(b) ^ Fortress.mul3(c) ^ d
            state[i + 2] = a ^ b ^ Fortress.mul2(c) ^ Fortress.mul3(d)
            state[i + 3] = Fortress.mul3(a) ^ b ^ c ^ Fortress.mul2(d)
        return bytes(state)

    @staticmethod
    def aesencIns(state: bytes) -> bytes:
        state = Fortress.subBytes(state)
        state = Fortress.shiftRows(state)
        state = Fortress.mixColumns(state)
        return state
    
    @staticmethod
    def invSubBytes(state: bytes) -> bytes:
        return bytes([Fortress.INV_SBOX[b] for b in state])

    @staticmethod
    def invShiftRows(state: bytes) -> bytes:
        return bytes([
            state[0], state[13], state[10], state[7],
            state[4], state[1], state[14], state[11],
            state[8], state[5], state[2], state[15],
            state[12], state[9], state[6], state[3]
        ])
    
    @staticmethod
    def invMixColumns(state: bytes) -> bytes:
        state = bytearray(state)
        for i in range(0, len(state), 4):
            a = state[i]
            b = state[i + 1]
            c = state[i + 2]
            d = state[i + 3]
            state[i] = Fortress.mul14(a) ^ Fortress.mul11(b) ^ Fortress.mul13(c) ^ Fortress.mul9(d)
            state[i + 1] = Fortress.mul9(a) ^ Fortress.mul14(b) ^ Fortress.mul11(c) ^ Fortress.mul13(d)
            state[i + 2] = Fortress.mul13(a) ^ Fortress.mul9(b) ^ Fortress.mul14(c) ^ Fortress.mul11(d)
            state[i + 3] = Fortress.mul11(a) ^ Fortress.mul13(b) ^ Fortress.mul9(c) ^ Fortress.mul14(d)
        return bytes(state)
    
    @staticmethod
    def aesdecIns(state: bytes) -> bytes:
        state = Fortress.invMixColumns(state)
        state = Fortress.invShiftRows(state)
        state = Fortress.invSubBytes(state)
        return state

    def setNumSkipRound(self, num_skip_round: int):
        self.num_skip_round = num_skip_round
        self.normal_enc = self.getEncryptedData(self.test_plain)

    def getConnection(self):
        if self.binary:
            return process(self.binary)
        return remote(self.host, self.port)

    def getEncryptedData(self, data: bytes):
        r = self.getConnection()
        if self.num_skip_round:
            r.recvuntil(b'> ')
            r.sendline(b'1')
            r.recvuntil(b': ')
            r.sendline(Fortress.b64encode(b'\x00' * self.FORTRESS_BLOCK_SIZE).encode())
            r.recvuntil(b': ')
            r.recvline()
        r.recvuntil(b'> ')
        r.sendline(b'1')
        r.recvuntil(b': ')
        r.sendline(Fortress.b64encode(data).encode())
        r.recvuntil(b': ')
        enc = r.recvline().strip().decode()
        r.close()
        return Fortress.b64decode(enc)

    def getFaultedData(self, data: bytes, state_location: int, xor_bit_location: int):
        assert(0 <= state_location and state_location < 8)
        assert(0 <= xor_bit_location and xor_bit_location < 128)

        r = self.getConnection()
        if self.num_skip_round:
            r.recvuntil(b'> ')
            r.sendline(b'1')
            r.recvuntil(b': ')
            r.sendline(Fortress.b64encode(b'\x00' * self.FORTRESS_BLOCK_SIZE).encode())
            r.recvuntil(b': ')
            r.recvline()

        r.recvuntil(b'> ')
        r.sendline(b'1')
        r.recvuntil(b': ')

        payload = b''
        payload += data
        payload += b'\x00' * ((len(data) % 3) + 1)
        payload += int.to_bytes(xor_bit_location, 1)

        r.sendline(Fortress.b64encode(payload, state_location | 0b1000).encode())
        r.recvuntil(b': ')
        enc = r.recvline().strip().decode()
        r.close()
        return Fortress.b64decode(enc)[:len(data)]
    
    def getCandidates(self, diffs: list, coef_funcs: list, epsilon: int):
        candidates = set()
        for diff_index in range(len(diffs)):
            for candidate in range(256):
                diff = Fortress.SBOX[candidate] ^ Fortress.SBOX[candidate ^ epsilon]
                if coef_funcs[diff_index](diff) == diffs[diff_index]:
                    candidates.add(candidate)
        return candidates

    def getCoefs(self, diffs: list):
        coefs = [None] * 4
        mul1_indices = []
        for i in range(len(diffs)):
            for j in range(i + 1, len(diffs)):
                if diffs[i] == diffs[j]:
                    coefs[i] = Fortress.mul1
                    coefs[j] = Fortress.mul1
                    mul1_indices.append(i)
                    mul1_indices.append(j)
                    break
            if len(mul1_indices) == 2:
                break
        other_indices = [i for i in range(4) if i not in mul1_indices]
        for i in other_indices:
            if Fortress.mul2(diffs[mul1_indices[0]]) == diffs[i]:
                coefs[i] = Fortress.mul2
            elif Fortress.mul3(diffs[mul1_indices[0]]) == diffs[i]:
                coefs[i] = Fortress.mul3
        return coefs

    def recoverState(self, fault_state, diff_locations):
        state = bytearray(16)
        for byte_location in range(16):
            diff_location = diff_locations[byte_location]
            candidates = set(range(256))

            faulted = self.getFaultedData(self.test_plain, fault_state, 8 * byte_location)
            xored = xor(self.normal_enc, faulted)
            diffs = [xored[i] for i in range(diff_location, diff_location + 4)]
            coefs = self.getCoefs(diffs)
            epsilon = 1 << 0
            candidates &= self.getCandidates(diffs, coefs, epsilon)

            faulted = self.getFaultedData(self.test_plain, fault_state, 8 * byte_location + 1)
            xored = xor(self.normal_enc, faulted)
            diffs = [xored[i] for i in range(diff_location, diff_location + 4)]
            coefs = self.getCoefs(diffs)
            epsilon = 1 << 1
            candidates &= self.getCandidates(diffs, coefs, epsilon)

            state[byte_location] = next(iter(candidates))
        
        return bytes(state)

    def recoverState1(self) -> bytes:
        diff_locations = [
            0, 12, 8, 4,
            4, 0, 12, 8,
            8, 4, 0, 12,
            12, 8, 4, 0
        ]
        return self.recoverState(1, diff_locations)

    def recoverState5(self, state1: bytes) -> bytes:
        state5 = xor(self.normal_enc[0:16], Fortress.aesencIns(state1))
        return state5

    def recoverState0XorState4(self) -> bytes:
        diff_locations = [
            16, 28, 24, 20,
            20, 16, 28, 24,
            24, 20, 16, 28,
            28, 24, 20, 16
        ]
        return self.recoverState(4, diff_locations)

    def recoverState2(self, state0XorState4) -> bytes:
        state2 = xor(self.normal_enc[16:32], Fortress.aesencIns(state0XorState4))
        return state2

    def recoverState3XorState7(self) -> bytes:
        diff_locations = [
            48, 60, 56, 52,
            52, 48, 60, 56,
            56, 52, 48, 60,
            60, 56, 52, 48
        ]
        return self.recoverState(3, diff_locations)

    def recoverState6(self, state3XorState7: bytes, state1: bytes):
        state6 = xor(xor(self.normal_enc[48:64], Fortress.aesencIns(state3XorState7)), state1)
        return state6

    def recoverState4(self):
        diff_locations = [
            32, 44, 40, 36,
            36, 32, 44, 40,
            40, 36, 32, 44,
            44, 40, 36, 32
        ]
        return self.recoverState(4, diff_locations)

    def recoverState0(self, state0XorState4, state4):
        state0 = xor(state0XorState4, state4)
        return state0

    def recoverState7(self):
        self.setNumSkipRound(1)
        nextState0XorState4 = self.recoverState0XorState4()
        nextState4 = self.recoverState4()
        nextState0 = self.recoverState0(nextState0XorState4, nextState4)

        self.setNumSkipRound(0)
        state7 = xor(nextState0, self.normal_enc[0:16])
        return state7

    def recoverState3(self, state3XorState7, state7):
        c0 = self.normal_enc[0:16]
        c1 = self.normal_enc[16:32]
        state = bytearray(16)
        state = xor(state, state3XorState7)
        state = xor(state, c0)
        state = xor(state, c1)
        state = xor(state, state7)
        return state

    def getEncryptedFlag(self) -> bytes:
        r = self.getConnection()
        r.recvuntil(b'> ')
        r.sendline(b'2')
        r.recvuntil(b': ')
        enc = r.recvline().strip().decode()
        r.close()
        return Fortress.b64decode(enc)

    def getPrevState(self, state: list, c0: bytes, c1: bytes) -> list:
        prev_state = [None] * 8
        prev_state[7] = xor(state[0], c0)
        prev_state[0] = Fortress.aesdecIns(xor(state[1], prev_state[7]))
        prev_state[3] = xor(state[4], c1)
        prev_state[4] = Fortress.aesdecIns(xor(state[5], prev_state[3]))
        prev_state[5] = Fortress.aesdecIns(xor(state[6], prev_state[4]))
        prev_state[6] = xor(state[7], prev_state[0])
        prev_state[1] = xor(state[2], prev_state[6])
        prev_state[2] = Fortress.aesdecIns(xor(state[3], prev_state[1]))
        return prev_state

    def getFlag(self, state: list) -> list:
        assert(len(state) == 8)

        enc_flag = self.getEncryptedFlag()

        c0 = enc_flag[0:16]
        c1 = enc_flag[16:32]

        prev_state = self.getPrevState(state, c0, c1)
        for i in range(len(prev_state)):
            print(f'prev_state{i}: {prev_state[i].hex()}')

        z0 = xor(Fortress.aesencIns(prev_state[1]), prev_state[5])
        z1 = xor(Fortress.aesencIns(xor(prev_state[0], prev_state[4])), prev_state[2])

        flag = b''
        flag += xor(c0, z0)
        flag += xor(c1, z1)
        return flag


    def exploit(self):
        state = [None] * 8
        state[1] = self.recoverState1()
        print(f'[+] Recovered state1: {state[1].hex()}')
        state[5] = self.recoverState5(state[1])
        print(f'[+] Recovered state5: {state[5].hex()}')
        state0XorState4 = self.recoverState0XorState4()
        print(f'[+] Recovered state0 ^ state4: {state0XorState4.hex()}')
        state[2] = self.recoverState2(state0XorState4)
        print(f'[+] Recovered state2: {state[2].hex()}')
        state3XorState7 = self.recoverState3XorState7()
        print(f'[+] Recovered state3 ^ state7: {state3XorState7.hex()}')
        state[6] = self.recoverState6(state3XorState7, state[1])
        print(f'[+] Recovered state6: {state[6].hex()}')
        state[4] = self.recoverState4()
        print(f'[+] Recovered state4: {state[4].hex()}')
        state[0] = self.recoverState0(state0XorState4, state[4])
        print(f'[+] Recovered state0: {state[0].hex()}')
        state[7] = self.recoverState7()
        print(f'[+] Recovered state7: {state[7].hex()}')
        state[3] = self.recoverState3(state3XorState7, state[7])

        for i in range(len(state)):
            print(f'[+] state{i}: {state[i].hex()}')

        flag = self.getFlag(state)
        print(f'[+] Flag: {flag.decode()}')


def main():
    args = parse_args()
    fortress = Fortress(args.host, args.port, args.binary)
    fortress.exploit()


if __name__ == '__main__':
    main()
