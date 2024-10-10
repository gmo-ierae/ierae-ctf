from struct import pack

class LabelResolver:
    def __init__(self, payload):
        self.payload = payload
        self.name2addr = {}
        self.wait_list = {}

    def add_inst(self, inst):
        self.payload += inst

    def cur_addr(self):
        return len(self.payload)

    def label(self, name):
        addr = self.cur_addr()
        self.name2addr[name] = addr

        if name in self.wait_list:
            for pos, callback, len_tmp_inst in self.wait_list[name]:
                real_inst = callback(addr, pos + len_tmp_inst)
                assert len(real_inst) == len_tmp_inst

                for i in range(len_tmp_inst):
                    self.payload[pos + i] = real_inst[i]

            del self.wait_list[name]

    def label_addr(self, name):
        return self.name2addr[name]

    def resolve_label(self, name, callback):
        if name in self.name2addr:
            addr = self.label_addr(name)
            tmp_inst = callback(0, 0)
            nxt_ip = self.cur_addr() + len(tmp_inst)
            real_inst = callback(addr, nxt_ip)
            assert len(tmp_inst) == len(real_inst)
            self.add_inst(real_inst)
        else:
            if not name in self.wait_list:
                self.wait_list[name] = []

            tmp_inst = callback(0, 0)
            self.wait_list[name].append((self.cur_addr(), callback, len(tmp_inst)))
            self.add_inst(tmp_inst)

    def get_payload(self):
        assert not self.wait_list
        return self.payload


def _pad_in_7(bs):
    ret = []
    n = len(bs)
    reved_bs = bs[::-1]
    for i in range(0, n, 7):
        does_continue = i + 7 < n
        ret.append(int("01"[does_continue] + reved_bs[i : i + 7][::-1], 2))
    return ret


def uleb(val):
    assert 0 <= val < 2**128
    bs = bin(val)[2:]
    return _pad_in_7(bs)


def DW_CFA_val_expression(reg_idx, block):
    assert 0 <= reg_idx <= 48
    return [0x16, reg_idx] + uleb(len(block)) + block


def DW_OP_const1u(val):
    assert 0 <= val < 2**8
    return [0x8] + list(pack("<B", val))

def DW_OP_const2u(val):
    assert 0 <= val < 2**16
    return [0xA] + list(pack("<H", val))

def DW_OP_const4u(val):
    assert 0 <= val < 2**32
    return [0xC] + list(pack("<I", val))

def DW_OP_const8u(val):
    assert 0 <= val < 2**64
    return [0xE] + list(pack("<Q", val))

def DW_OP_deref():
    return [0x6]


def DW_OP_deref_size(size):
    assert 1 <= size <= 8
    return [0x94] + [size]


def DW_OP_dup():
    return [0x12]


def DW_OP_drop():
    return [0x13]


def DW_OP_over():
    return [0x14]


def DW_OP_swap():
    return [0x16]


def DW_OP_rot():
    return [0x17]


def DW_OP_minus():
    return [0x1C]


def DW_OP_div():
    return [0x1B]


def DW_OP_mod():
    return [0x1D]


def DW_OP_mul():
    return [0x1E]


def DW_OP_shl():
    return [0x24]


# DW_OP_reg0, ..., DW_OP_reg31 と
# DW_OP_regx を使い分ける汎用関数
def DW_OP_reg(reg_idx):
    assert 0 <= reg_idx <= 48
    if reg_idx < 32:
        return [0x50 + reg_idx]
    return [0x90] + uleb(reg_idx)


def DW_OP_plus():
    return [0x22]


def DW_OP_eq():
    return [0x29]


def DW_OP_ne():
    return [0x2E]


def DW_OP_bra(offset):
    return [0x28] + list(pack("<h", offset))


def DW_OP_skip(offset):
    return [0x2F] + list(pack("<h", offset))

def print_cfi_escape(payload):
    print(".cfi_escape " + ", ".join(str(i) for i in payload))

resolver = LabelResolver([])
resolver.add_inst(DW_OP_drop())

resolver.add_inst(DW_OP_const4u(0x40a855)) # pop rdi
resolver.add_inst(DW_OP_const4u(0x5a0bca)) # /bin/sh
resolver.add_inst(DW_OP_const4u(0x4111a0)) # pop rsi
resolver.add_inst(DW_OP_const1u(0)) # 0
resolver.add_inst(DW_OP_const4u(0x405960)) # execlp

resolver.add_inst(DW_OP_reg(7))
resolver.add_inst(DW_OP_const2u(0x950))
resolver.add_inst(DW_OP_minus())

print_cfi_escape(DW_CFA_val_expression(7, resolver.get_payload()))

PASSWORD_HASH = 0xfeedface # 0xdeadbeeffeedface

resolver = LabelResolver([])
resolver.add_inst(DW_OP_drop())

resolver.add_inst(DW_OP_reg(7))
resolver.add_inst(DW_OP_const2u(0x378))
resolver.add_inst(DW_OP_plus())
resolver.add_inst(DW_OP_deref())
resolver.add_inst(DW_OP_const1u(1))

resolver.label("LOOP_START")
resolver.add_inst(DW_OP_over())
resolver.add_inst(DW_OP_deref_size(1))

# cmp *ptr, '\0'; jnz out_of_loop
resolver.add_inst(DW_OP_dup())
resolver.add_inst(DW_OP_const1u(ord("\0")))
resolver.add_inst(DW_OP_eq())
resolver.resolve_label("OUT_OF_LOOP", lambda addr, nxt_ip: DW_OP_bra(addr - nxt_ip))

# mul_start:
resolver.add_inst(DW_OP_mul())
resolver.add_inst(DW_OP_swap())
resolver.add_inst(DW_OP_const1u(1))
resolver.add_inst(DW_OP_plus())
resolver.add_inst(DW_OP_swap())
resolver.resolve_label("LOOP_START", lambda addr, nxt_ip: DW_OP_skip(addr - nxt_ip))

resolver.label("OUT_OF_LOOP")
resolver.add_inst(DW_OP_drop())
resolver.add_inst(DW_OP_const8u(2 ** 32))
resolver.add_inst(DW_OP_mod())
resolver.add_inst(DW_OP_const4u(PASSWORD_HASH))
resolver.add_inst(DW_OP_ne())
resolver.resolve_label("FAIL", lambda addr, nxt_ip: DW_OP_bra(addr - nxt_ip))

# succ:
resolver.add_inst(DW_OP_drop())
resolver.add_inst(DW_OP_const4u(0x40a855)) # pop rdi
resolver.add_inst(DW_OP_const4u(0x5a0bca)) # /bin/sh

resolver.add_inst(DW_OP_const4u(0x4111a0)) # pop rsi
resolver.add_inst(DW_OP_const1u(0)) # 0

resolver.add_inst(DW_OP_const4u(0x405960)) # execlp
resolver.resolve_label("FINALLY", lambda addr, nxt_ip: DW_OP_skip(addr - nxt_ip))

# fail:
resolver.label("FAIL")
resolver.add_inst(DW_OP_drop())

for c in "Idiot\n":
  resolver.add_inst(DW_OP_const4u(0x40a855)) # pop rdi
  resolver.add_inst(DW_OP_const1u(ord(c)))
  resolver.add_inst(DW_OP_const4u(0x4111a0)) # pop rsi
  resolver.add_inst(DW_OP_const4u(0x5FA880)) # STDOUT
  resolver.add_inst(DW_OP_const4u(0x4EACB0)) # putc
resolver.add_inst(DW_OP_const4u(0x4DA930)) # exit

resolver.label("FINALLY")
resolver.add_inst(DW_OP_reg(7))
resolver.add_inst(DW_OP_const2u(0x930))
resolver.add_inst(DW_OP_minus())

print_cfi_escape(DW_CFA_val_expression(7, resolver.get_payload()))
