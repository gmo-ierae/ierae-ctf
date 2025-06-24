from pwn import context, asm, disasm
import random
import sys
import claripy
import capstone
import cle
import os

Cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)

context(os="linux", arch="amd64")

# IERAE{AQ4A8f-CYIJ1gneQ_IxekeOQlA}
# FLAG = list(b"IERAE{AQ4A8f-CYIJ1gneQ_IxekeOQlA")
FLAG = [claripy.BVS(f"flag_{i}", 8) for i in range(32)]
assert len(FLAG) == 32

ORIGINAL_FLAG = FLAG[:]

BUFFER_LEN = 64

random.seed(1145141919)

def bytes_to_c_arr(data, lowercase=True):
    return ', '.join(format(b, '#04x' if lowercase else '#04X') for b in data)

def encode_jmp(number):
    buf = bytearray()
    buf.append((number & 0x7f) | 0x80)
    number >>= 7
    while number:
        buf.insert(0, number & 0x7f)
        number >>= 7
    return buf

class Context:
    def __init__(self, validate=False, main_size=3141):
        assert main_size % 16 != 0
        self.code = [] # (end, jump)
        self.tags = {}
        self.data = [None] * main_size
        self.solver = claripy.Solver()
        for i in range(32):
            self.solver.add(ORIGINAL_FLAG[i] == b'IERAE{AQ4A8f-CYIJ1gneQ_IxekeOQlA}'[i])
        self.validate_solver = None
        self.code_off = None
        if validate:
            self.loader = cle.Loader("actual", auto_load_libs=False)
            self.code_off = validate
            self.validate_solver = claripy.Solver()
            for i in range(6):
                self.validate_solver.add(ORIGINAL_FLAG[i] == b'IERAE{AQ4A8f-CYIJ1gneQ_IxekeOQlA}'[i])
        elif os.path.exists("./a.out"):
            self.loader = cle.Loader("./a.out", auto_load_libs=False)
            self.code_off = self.loader.main_object.get_symbol("main_inner").rebased_addr

    def evaluate(self, expr):
        if isinstance(expr, int):
            return expr
        results = self.solver.eval(expr, 2)
        assert len(results) == 1
        if self.validate_solver is not None:
            self.validate_solver.add(expr == results[0])
        return results[0]

    def store_code(self, data, off, /, re=None, reserve=False, align=1):
        possible = []

        if re is None:
            re = len(self.data)

        for i in range(0, re):
            if (off + i < len(self.data)) != (off + i + len(data) <= len(self.data)):
                continue

            addr = (off + i) % len(self.data)

            if ((self.code_off or 0) + addr) % align != 0:
                continue

            # if addr + 7 >= len(self.data):
            #     continue

            cnt = 0
            for j in range(len(data)):
                if reserve:
                    if self.data[addr + j] is not None:
                        break
                elif self.data[addr + j] is None:
                    cnt += 1
                elif self.data[addr + j] != data[j]:
                    break
            else:
                possible.append((cnt, addr))
        
        assert possible, ("no possible place to store code", data, self.data)
        
        possible.sort()
        filtered = [i for s, i in possible if s == possible[0][0]]
        selected = random.choice(filtered)
        self.data[selected:selected+len(data)] = data

        if isinstance(data, bytes):
            print(disasm(data, vma=selected))
        else:
            print(hex(selected), data, sep='\t')

        return selected

    def add_line(self, line, **kwargs):
        if isinstance(line, str):
            line = asm(line)

        if isinstance(line, (bytes, list)):
            if not self.code:
                self.data[:len(line)] = line
                off = 0
            else:
                fixed = kwargs.pop("fixed", None)
                last_end, last_jump = self.code[-1]
                if last_jump is None:
                    # must store behind
                    assert all(i is None for i in self.data[last_end:last_end+len(line)])
                    assert fixed is None
                    off = last_end
                    self.data[last_end:last_end+len(line)] = line
                elif last_jump == ():
                    # find two before
                    last_last_end = self.code[-2][0]
                    off = self.store_code(line, last_last_end, **kwargs) if fixed is None else fixed
                    extra = 0
                    if not kwargs:
                        extra = len(self.data) * random.randint(0, 600)
                    print((off - last_last_end) % len(self.data) + extra)
                    self.code[-1] = (last_end, (off - last_last_end) % len(self.data) + extra)
                else:
                    assert last_jump is ..., self.code
                    off = self.store_code(line, last_end, **kwargs) if fixed is None else fixed
                    extra = 0
                    if not kwargs:
                        extra = len(self.data) * random.randint(0, 600)
                    print((off - last_end) % len(self.data) + extra)
                    self.code[-1] = (last_end, (off - last_end) % len(self.data) + extra)
            self.code.append((off + len(line), ...))
            return off

        print(line)
        return line.resolve(self, **kwargs)
    
    def export_offsets(self):
        offsets = bytearray()
        for _, o in self.code:
            if o is not None:
                offsets.extend(encode_jmp(o))
        return offsets

    def get_prev_rbx(self):
        rbx = 0
        for _, o in self.code[:-1]:
            if o is not None:
                rbx += len(encode_jmp(o))
        return rbx

    def rbx_reserve(self, size, **kwargs):
        assert 'reserve' not in kwargs
        off = self.add_line([None] * size, reserve=True, **kwargs)
        rbx = self.get_prev_rbx()
        return rbx, off

class LeaMov:
    def __init__(self, reg, cst):
        assert reg.startswith("e") and reg != "ebx"
        self.reg = reg
        self.cst = cst

    def resolve(self, ctx: Context):
        rbx, loc = ctx.rbx_reserve(6)
        c = asm(f"lea {self.reg}, [rbx + {ctx.evaluate(self.cst) - rbx}]")
        assert len(c) <= 6
        ctx.data[loc:loc+len(c)] = c
        assert ctx.code[-1][1] is ...
        ctx.code[-1] = (ctx.code[-1][0] - 6 + len(c), ...)
    
    def __repr__(self):
        return f"<lea> mov {self.reg}, {self.cst}"

class IfNotThen:
    def __init__(self, reg, false="ret"):
        self.reg = reg
        self.false = false

    def resolve(self, ctx: Context):
        ctx.add_line(f"add bl, {self.reg}")

        rbx = ctx.get_prev_rbx()
        assert rbx & 0xff != 0xff
        assert (rbx + 1) & 0xff != 0xff
        assert (rbx + 2) & 0xff != 0xff

        pos = len(ctx.code)
        ctx.add_line(self.false, re=128)
        assert len(ctx.code) - pos == 1

        end, of = ctx.code[pos]
        assert of is ...
        ctx.code[pos] = (end, ())

    def __repr__(self):
        return f"<if not> {self.reg} -> {repr(self.false)}"

class Ref:
    def __init__(self, tag):
        self.tag = tag
    
    def resolve(self, ctx: Context):
        assert self.tag not in ctx.tags
        rbx, loc = ctx.rbx_reserve(5)
        for i in range(5):
            ctx.data[loc + i] = self.tag
        ctx.tags[self.tag] = len(ctx.code) - 1, loc, rbx

class JmpBack:
    def __init__(self, tag):
        self.tag = tag

    def resolve(self, ctx: Context, **kwargs):
        pos, prev_loc, prev_rbx = ctx.tags.pop(self.tag)

        rbx, loc = ctx.rbx_reserve(6, **kwargs)
        c = asm(f"sub ebx, {rbx - prev_rbx}")
        assert len(c) <= 6
        ctx.data[loc:loc+len(c)] = c
        assert ctx.code[-1][1] is ...
        ctx.code[-1] = (ctx.code[-1][0] - 6 + len(c), ...)

        jmp_tgt = (ctx.code[pos][0] + ctx.code[pos][1]) % len(ctx.data) # this is the start of the loop
        off = ctx.code[-1][0] # the current rip

        diff = (jmp_tgt - off) % len(ctx.data)

        # the amount of jump of the jmp instruction
        # should satisfy prev_loc + len(jmp) + jmp_amount + diff == jmp_tgt
        # -> prev_loc + len(jmp) + jmp_amount + jmp_tgt - off == jmp_tgt
        # -> jmp_amount == off - prev_loc - len(jmp)

        jmp_amount = off - prev_loc - 2
        if 127 >= jmp_amount >= -128:
            ctx.data[prev_loc] = 0xeb
            ctx.data[prev_loc + 1] = jmp_amount & 0xff
            for i in range(2, 5):
                assert ctx.data[prev_loc + i] == self.tag
                ctx.data[prev_loc + i] = None
            prev_off = ctx.code[pos][1]
            while len(encode_jmp(prev_off)) > len(encode_jmp(diff)):
                diff += len(ctx.data)
            assert len(encode_jmp(prev_off)) == len(encode_jmp(diff)), (prev_off, diff)
            ctx.code[pos] = (prev_loc + 2, diff)
        else:
            jmp_amount -= 3
            ctx.data[prev_loc] = 0xe9
            ctx.data[prev_loc + 1:prev_loc + 5] = jmp_amount.to_bytes(4, "little", signed=True)
            prev_off = ctx.code[pos][1]
            while len(encode_jmp(prev_off)) > len(encode_jmp(diff)):
                diff += len(ctx.data)
            assert len(encode_jmp(prev_off)) == len(encode_jmp(diff)), (prev_off, diff)
            ctx.code[pos] = (prev_loc + 5, diff)

class Syscall:
    RESERVE = 6

    def resolve(self, ctx: Context):
        ctx.add_line([*asm("syscall")] + [None] * self.RESERVE, reserve=True)
        ctx.code[-1] = (ctx.code[-1][0] - self.RESERVE, None)

class Data:
    cache = {}

    def __init__(self, line: str, data: bytes, align=1):
        assert len(data) % align == 0
        assert '[rip]' in line
        self.line = line
        self.data = data
        self.align = align
        self.data_loc = None

    def pre_resolve(self, ctx: Context):
        assert self.data_loc is None
        
        for d in self.data:
            if not isinstance(d, int):
                break
        else:
            self.data_loc = ctx.store_code(self.data, 0, align=self.align)
            return
        
        self.data_loc = random.randint(0x10000, 0x50000) + 32
        if ctx.code_off is not None:
            act_data = ctx.loader.memory.load(ctx.code_off + self.data_loc, len(self.data))
            print(act_data.hex())
        else:
            act_data = [0] * len(self.data)
        for i, d in enumerate(self.data):
            ctx.solver.add(d == claripy.BVV(act_data[i], 8))
            if ctx.validate_solver is not None:
                ctx.validate_solver.add(d == claripy.BVV(act_data[i], 8))

    def resolve(self, ctx: Context):
        assert self.data_loc is not None
        is_concrete = all(isinstance(d, int) for d in self.data)
        if is_concrete and (self.line, bytes(self.data)) in Data.cache:
            loc, size = Data.cache[self.line, bytes(self.data)]
            ctx.add_line([None] * size, fixed=loc)
            return

        c = asm(self.line.replace("[rip]", "[rip + 0x23456BAD]"))
        loc = ctx.add_line(c, reserve=True)
        diff = self.data_loc - loc - len(c)
        ctx.data[loc:loc+len(c)] = c.replace(b'\xad\x6b\x45\x23', diff.to_bytes(4, "little", signed=True))

        if is_concrete:
            Data.cache[self.line, bytes(self.data)] = (loc, len(c))
    
    def __repr__(self):
        return self.line.replace("[rip]", "<data>")


PROL = [
    "xor ebx, ebx",
    f"lea rsi, [rsp - {BUFFER_LEN}]", # rsi points to the buffer
]

OUTPUT_INIT = [
    LeaMov("eax", 952658),
    "imul rax, 37196155", # rax: "flag: "
    "mov qword ptr [rsi], rax", # store "flag: "
    LeaMov("eax", 1), # syscall number for sys_write
    "mov edi, eax", # file descriptor 1 (stdout)
    LeaMov("edx", 6), # length of the string
    Syscall(), # invoke the syscall
]

INPUT_INIT = [
    LeaMov("edx", BUFFER_LEN), # buffer size
    "xor eax, eax", # clear eax
    "dec edi", # clear edi
    Syscall(), # invoke the syscall
]

CHECK_LEN = [
    LeaMov("ecx", 32), # length of the flag - 1
    f"cmp al, cl", # check if the input length is greater than 32
    "seta al", # set al to 1 if greater than
    IfNotThen("al"), # if not greater than, jump to error
]

SUCCESS = [
    LeaMov("eax", 424373749),
    "imul rax, 1775171831", # rax: "correct\n"
    "mov qword ptr [rsi], rax", # store "correct\n"
    LeaMov("eax", 1), # syscall number for sys_write
    "mov edi, eax", # file descriptor 1 (stdout)
    LeaMov("edx", 8), # length of the string
    Syscall(), # invoke the syscall
    "pop rax",
    "ret"
]

# 1, 2, 4, 8, 16, 32 bytes
# 

def method_sum_all_32():
    result = sum(FLAG) & 0xFF

    return ([
        "vextracti32x4   xmm0, ymm7, 0x1",
        "vpaddb  xmm0, xmm0, xmm7",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_shift_32(value):
    values = [claripy.Extract(i + 7, i, value) for i in range(len(FLAG))]
    result = sum(c * d for c, d in zip(FLAG, values)) & 0xFF
    pro = [
        "xor dl, dl",
        "xor ecx, ecx",
        Data("mov rdi, qword ptr [rip]", [claripy.Extract(i * 8 + 7, i * 8, value) for i in range(8)]),
        "vmovups ymmword ptr [rsi], ymm7"
    ]
    loop = [
        Ref("loop"),
        "mov al, dil",
        "shr rdi, 1",
        "mul byte ptr [rsi + rcx]",
        "add dl, al",
        LeaMov("eax", 32),
        "inc ecx",
        "cmp cl, al",
        "sete al",
        IfNotThen("al", JmpBack("loop")),
    ]
    epi = [
        LeaMov("eax", result),
        f"cmp dl, al",
        "sete al",
        IfNotThen("al"),
    ]
    return pro + loop + epi

def method_increment_32():
    result = sum(FLAG[i] * (i + 1) for i in range(32)) & 0xFF

    pro = [
        "xor dl, dl",
        "xor ecx, ecx",
        "vmovups ymmword ptr [rsi], ymm7",
    ]
    loop = [
        Ref("loop"),
        "mov al, byte ptr [rsi + rcx]",
        "inc ecx",
        "mul cl",
        "add dl, al",
        LeaMov("eax", 32),
        "cmp cl, al",
        "sete al",
        IfNotThen("al", JmpBack("loop")),
    ]
    epi = [
        LeaMov("eax", result),
        f"cmp dl, al",
        "sete al",
        IfNotThen("al"),
    ]
    return pro + loop + epi


def method_avx512_clang_32(values):
    assert len(values) == 32
    result = sum(c * d for c, d in zip(FLAG, values)) & 0xFF

    return ([
        Data("vpmovzxbw  zmm0, ymmword ptr [rip]", values),
        "vpmovzxbw       zmm1, ymm7",
        "vpmullw zmm0, zmm0, zmm1",
        "vpmovwb ymm0, zmm0",
        "vextracti128    xmm1, ymm0, 1",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_gcc_32(values):
    assert len(values) == 32
    result = sum(c * d for c, d in zip(FLAG, values)) & 0xFF

    return ([
        Data("vpmovzxbw  zmm0, YMMWORD PTR [rip]", values),
        "vpmovzxbw       zmm1, ymm7",
        "vpmullw zmm1, zmm1, zmm0",
        "vpmovwb ymm1, zmm1",
        "vextracti32x4   xmm0, ymm1, 0x1",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)


def method_avx512_clang_16_off_0(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF

    return ([
        Data("vpmovzxbw       ymm0, xmmword ptr [rip]", values),
        "vpmovzxbw       ymm1, xmm7",
        "vpmullw ymm0, ymm0, ymm1",
        "vpmovwb xmm0, ymm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_gcc_16_off_0(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF

    return ([
        Data("vpmovzxbw       ymm0, XMMWORD PTR [rip]", values),
        "vpmovzxbw       ymm1, xmm7",
        "vpmullw ymm0, ymm0, ymm1",
        "vpmovwb xmm0, ymm0",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_clang_16_off_4(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[4:][:16], values)) & 0xFF

    return ([
        Data("vpmovzxbw       ymm0, xmmword ptr [rip]", values),
        "vextracti128    xmm1, ymm7, 1",
        f"vpalignr        xmm1, xmm1, xmm7, 4",
        "vpmovzxbw       ymm1, xmm1",
        "vpmullw ymm0, ymm0, ymm1",
        "vpmovwb xmm0, ymm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_clang_16_off_12(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[12:][:16], values)) & 0xFF

    return ([
        Data("vpmovzxbw       ymm0, xmmword ptr [rip]", values),
        "vextracti128    xmm1, ymm7, 1",
        f"vpalignr        xmm1, xmm1, xmm7, 12",
        "vpmovzxbw       ymm1, xmm1",
        "vpmullw ymm0, ymm0, ymm1",
        "vpmovwb xmm0, ymm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_clang_16_off_8(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[8:][:16], values)) & 0xFF

    return ([
        "vpermq  ymm0, ymm7, 233",
        Data("vpmovzxbw       ymm1, xmmword ptr [rip]", values),
        "vpmovzxbw       ymm0, xmm0",
        "vpmullw ymm0, ymm1, ymm0",
        "vpmovwb xmm0, ymm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_clang_16_off_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[16:][:16], values)) & 0xFF

    return ([
        "vextracti128    xmm0, ymm7, 1",
        Data("vpmovzxbw       ymm1, xmmword ptr [rip]", values),
        "vpmovzxbw       ymm0, xmm0",
        "vpmullw ymm0, ymm1, ymm0",
        "vpmovwb xmm0, ymm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_gcc_16_off_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[16:][:16], values)) & 0xFF

    return ([
        Data("vpmovzxbw       ymm0, XMMWORD PTR [rip]", values),
        "vextracti32x4   xmm1, ymm7, 0x1",
        "vpmovzxbw       ymm1, xmm1",
        "vpmullw ymm0, ymm0, ymm1",
        "vpmovwb xmm0, ymm0",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)


def method_avx512_clang_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, qword ptr [rip]", values),
        "vpmovzxbw       xmm1, xmm7",
        "vpmullw xmm0, xmm0, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_gcc_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpmovzxbw       xmm1, xmm7",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_clang_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF

    return ([
        "vpunpckhbw      xmm0, xmm7, xmm7",
        Data("vpmovzxbw       xmm1, qword ptr [rip]", values),
        "vpmullw xmm0, xmm1, xmm0",
        "vpmovwb xmm0, xmm0",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_gcc_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_clang_8_off_16(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[16:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, qword ptr [rip]", values),
        "vextracti128    xmm1, ymm7, 1",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx512_gcc_8_off_16(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[16:][:8], values)) & 0xFF

    return ([
        "vextracti64x2   xmm1, ymm7, 1",
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_clang_8_off_24(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[24:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, qword ptr [rip]", values),
        "vpermq  ymm1, ymm7, 255",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)


def method_avx512_gcc_8_off_24(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[24:][:8], values)) & 0xFF

    return ([
        "valignq ymm1, ymm7, ymm7, 3",
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_0(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpmovzxbw       xmm1, xmm7",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_4(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[4:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 4",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_8(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[8:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_12(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[12:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 12",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_16(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[16:][:4], values)) & 0xFF

    return ([
        "vextracti32x4   xmm1, ymm7, 1",
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_20(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[20:][:4], values)) & 0xFF

    return ([
        "valignd ymm1, ymm7, ymm7, 5",
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_24(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[24:][:4], values)) & 0xFF

    return ([
        "valignd ymm1, ymm7, ymm7, 6",
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx512_gcc_4_off_28(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[28:][:4], values)) & 0xFF

    return ([
        "valignd ymm1, ymm7, ymm7, 7",
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpmovwb xmm0, xmm0",
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_32(values):
    assert len(values) == 32
    result = sum(c * d for c, d in zip(FLAG, values)) & 0xFF
    return ([
        Data("vmovdqu ymm0, ymmword ptr [rip]", values),
        Data("vpbroadcastw    ymm1, word ptr [rip]", [255, 0]),
        "vpand   ymm2, ymm7, ymm1",
        "vpmaddubsw      ymm2, ymm0, ymm2",
        "vpand   ymm2, ymm2, ymm1",
        "vpandn  ymm1, ymm1, ymm7",
        "vpmaddubsw      ymm0, ymm0, ymm1",
        "vpsllw  ymm0, ymm0, 8",
        "vpor    ymm0, ymm2, ymm0",
        "vextracti128    xmm1, ymm0, 1",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_32(values):
    assert len(values) == 32
    result = sum(c * d for c, d in zip(FLAG, values)) & 0xFF
    return ([
        Data("vmovdqu ymm1, YMMWORD PTR [rip]", values),
        "vpunpcklbw      ymm2, ymm7, ymm7",
        "vpunpckhbw      ymm0, ymm7, ymm7",
        "vpunpcklbw      ymm3, ymm1, ymm1",
        "vpunpckhbw      ymm1, ymm1, ymm1",
        "vpmullw ymm2, ymm2, ymm3",
        "vpmullw ymm0, ymm0, ymm1",
        Data("vpshufb ymm1, ymm2, YMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14, 8, 9, 10, 11, 12, 13, 14, 15, 0, 2, 4, 6, 8, 10, 12, 14, 8, 9, 10, 11, 12, 13, 14, 15]),
        Data("vpshufb ymm0, ymm0, YMMWORD PTR [rip]", [0, 1, 2, 3, 4, 5, 6, 7, 0, 2, 4, 6, 8, 10, 12, 14, 0, 1, 2, 3, 4, 5, 6, 7, 0, 2, 4, 6, 8, 10, 12, 14]),
        "vpblendd        ymm0, ymm0, ymm1, 51",
        "vextracti128    xmm1, ymm0, 0x1",
        "vpaddb  xmm0, xmm1, xmm0",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_16_off_0(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF

    return ([
        Data("vpmovzxbw       ymm0, xmmword ptr [rip]", values),
        "vpmovzxbw       ymm1, xmm7",
        "vpmullw ymm0, ymm0, ymm1",
        Data("vpand   ymm0, ymm0, ymmword ptr [rip]", [255, 0] * 16),
        "vextracti128    xmm1, ymm0, 1",
        "vpackuswb       xmm0, xmm0, xmm1",
        "vpackuswb       xmm1, xmm1, xmm1",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_16_off_0(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF

    return ([
        Data("vmovdqu xmm2, XMMWORD PTR [rip]", values),
        "vpunpcklbw      xmm0, xmm7, xmm7",
        "vpunpckhbw      xmm1, xmm7, xmm7",
        "vpunpcklbw      xmm3, xmm2, xmm2",
        "vpunpckhbw      xmm2, xmm2, xmm2",
        "vpmullw xmm1, xmm1, xmm2",
        "vpmullw xmm0, xmm0, xmm3",
        "vpcmpeqd        xmm2, xmm2, xmm2",
        "vpsrlw  xmm2, xmm2, 8",
        "vpand   xmm0, xmm2, xmm0",
        "vpand   xmm2, xmm2, xmm1",
        "vpackuswb       xmm0, xmm0, xmm2",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_16_off_8(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[8:][:16], values)) & 0xFF

    return ([
        "vpermq  ymm0, ymm7, 233",
        Data("vpmovzxbw       ymm1, xmmword ptr [rip]", values),
        "vpmovzxbw       ymm0, xmm0",
        "vpmullw ymm0, ymm1, ymm0",
        Data("vpand   ymm0, ymm0, ymmword ptr [rip]", [255, 0] * 16),
        "vextracti128    xmm1, ymm0, 1",
        "vpackuswb       xmm0, xmm0, xmm1",
        "vpackuswb       xmm1, xmm1, xmm1",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_clang_16_off_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[16:][:16], values)) & 0xFF

    return ([
        "vextracti128    xmm0, ymm7, 1",
        Data("vpmovzxbw       ymm1, xmmword ptr [rip]", values),
        "vpmovzxbw       ymm0, xmm0",
        "vpmullw ymm0, ymm1, ymm0",
        Data("vpand   ymm0, ymm0, ymmword ptr [rip]", [255, 0] * 16),
        "vextracti128    xmm1, ymm0, 1",
        "vpackuswb       xmm0, xmm0, xmm1",
        "vpackuswb       xmm1, xmm1, xmm1",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_16_off_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[16:][:16], values)) & 0xFF

    return ([
        Data("vmovdqu xmm2, XMMWORD PTR [rip]", values),
        "vextracti128    xmm1, ymm7, 0x1",
        "vpunpcklbw      xmm0, xmm1, xmm1",
        "vpunpckhbw      xmm1, xmm1, xmm1",
        "vpunpcklbw      xmm3, xmm2, xmm2",
        "vpunpckhbw      xmm2, xmm2, xmm2",
        "vpmullw xmm0, xmm0, xmm3",
        "vpmullw xmm1, xmm1, xmm2",
        "vpcmpeqd        xmm2, xmm2, xmm2",
        "vpsrlw  xmm2, xmm2, 8",
        "vpand   xmm0, xmm2, xmm0",
        "vpand   xmm2, xmm2, xmm1",
        "vpackuswb       xmm0, xmm0, xmm2",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, qword ptr [rip]", values),
        "vpmovzxbw       xmm1, xmm7",
        "vpmullw xmm0, xmm0, xmm1",
        Data("vpshufb xmm0, xmm0, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8),
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpmovzxbw       xmm1, xmm7",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, qword ptr [rip]", values),
        "vpunpckhbw      xmm1, xmm7, xmm7",
        "vpmullw xmm0, xmm0, xmm1",
        Data("vpshufb xmm0, xmm0, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8),
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_8_off_16(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[16:][:8], values)) & 0xFF

    return ([
        "vextracti128    xmm0, ymm7, 1",
        Data("vpmovzxbw       xmm1, qword ptr [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm1, xmm0",
        Data("vpshufb xmm0, xmm0, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8),
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_8_off_16(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[16:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vextracti128    xmm1, ymm7, 0x1",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_clang_8_off_24(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[24:][:8], values)) & 0xFF

    return ([
        "vpermq  ymm0, ymm7, 255",
        Data("vpmovzxbw       xmm1, qword ptr [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm1, xmm0",
        Data("vpshufb xmm0, xmm0, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8),
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx2_gcc_8_off_24(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[24:][:8], values)) & 0xFF

    return ([
        "vextracti128    xmm1, ymm7, 0x1",
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm1, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_0(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpmovzxbw       xmm1, xmm7",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_4(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[4:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 4",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_8(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[8:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_12(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[12:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm7, 12",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_16(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[16:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextracti128    xmm1, ymm7, 0x1",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_20(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[20:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextracti128    xmm1, ymm7, 0x1",
        "vpsrldq xmm1, xmm1, 4",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_24(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[24:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextracti128    xmm1, ymm7, 0x1",
        "vpsrldq xmm1, xmm1, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx2_gcc_4_off_28(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[28:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextracti128    xmm1, ymm7, 0x1",
        "vpsrldq xmm1, xmm1, 12",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_clang_16_off_0(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF

    return ([
        Data("vmovdqu xmm0, xmmword ptr [rip]", values),
        Data("vbroadcastss    xmm1, dword ptr [rip]", [255, 0, 255, 0]),
        "vpand   xmm2, xmm7, xmm1",
        "vpmaddubsw      xmm2, xmm0, xmm2",
        "vpand   xmm2, xmm2, xmm1",
        "vpandn  xmm1, xmm1, xmm7",
        "vpmaddubsw      xmm0, xmm0, xmm1",
        "vpsllw  xmm0, xmm0, 8",
        "vpor    xmm0, xmm2, xmm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

# def method_avx_gcc_16_off_0(values): same as method_avx2_gcc_16_off_0

def method_avx_clang_16_off_8(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[8:][:16], values)) & 0xFF

    return ([
        "vextractf128    xmm0, ymm7, 1",
        "vpalignr        xmm0, xmm0, xmm7, 8",
        Data("vmovdqu xmm1, xmmword ptr [rip]", values),
        Data("vbroadcastss    xmm2, dword ptr [rip]", [255, 0, 255, 0]),
        "vpand   xmm3, xmm0, xmm2",
        "vpmaddubsw      xmm3, xmm1, xmm3",
        "vpand   xmm3, xmm3, xmm2",
        "vpandn  xmm0, xmm2, xmm0",
        "vpmaddubsw      xmm0, xmm1, xmm0",
        "vpsllw  xmm0, xmm0, 8",
        "vpor    xmm0, xmm3, xmm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx_clang_16_off_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[16:][:16], values)) & 0xFF

    return ([
        "vextractf128    xmm0, ymm7, 1",
        Data("vmovdqu xmm1, xmmword ptr [rip]", values),
        Data("vbroadcastss    xmm2, dword ptr [rip]", [255, 0, 255, 0]),
        "vpand   xmm3, xmm0, xmm2",
        "vpmaddubsw      xmm3, xmm1, xmm3",
        "vpand   xmm3, xmm3, xmm2",
        "vpandn  xmm0, xmm2, xmm0",
        "vpmaddubsw      xmm0, xmm1, xmm0",
        "vpsllw  xmm0, xmm0, 8",
        "vpor    xmm0, xmm3, xmm0",
        "vpshufd xmm1, xmm0, 238",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx_gcc_16_off_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[16:][:16], values)) & 0xFF

    return ([
        Data("vmovdqu xmm2, XMMWORD PTR [rip]", values),
        "vextractf128    xmm1, ymm7, 0x1",
        "vpunpcklbw      xmm0, xmm1, xmm1",
        "vpunpckhbw      xmm1, xmm1, xmm1",
        "vpunpcklbw      xmm3, xmm2, xmm2",
        "vpunpckhbw      xmm2, xmm2, xmm2",
        "vpmullw xmm0, xmm0, xmm3",
        "vpmullw xmm1, xmm1, xmm2",
        "vpcmpeqd        xmm2, xmm2, xmm2",
        "vpsrlw  xmm2, xmm2, 8",
        "vpand   xmm0, xmm2, xmm0",
        "vpand   xmm2, xmm2, xmm1",
        "vpackuswb       xmm0, xmm0, xmm2",
        "vpsrldq xmm1, xmm0, 8",
        "vpaddb  xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_clang_8_off_16(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[16:][:8], values)) & 0xFF

    return ([
        "vextractf128    xmm0, ymm7, 1",
        Data("vpmovzxbw       xmm1, qword ptr [rip]", values),
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm1, xmm0",
        Data("vpshufb xmm0, xmm0, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8),
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx_gcc_8_off_16(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[16:][:8], values)) & 0xFF

    return ([
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vextractf128    xmm1, ymm7, 0x1",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_clang_8_off_24(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[24:][:8], values)) & 0xFF

    return ([
        "vextractf128    xmm0, ymm7, 1",
        Data("vpmovzxbw       xmm1, qword ptr [rip]", values),
        "vpunpckhbw      xmm0, xmm0, xmm0",
        "vpmullw xmm0, xmm1, xmm0",
        Data("vpshufb xmm0, xmm0, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8),
        "vpxor   xmm1, xmm1, xmm1",
        "vpsadbw xmm0, xmm0, xmm1",
        "vmovd   %s, xmm0",
    ], result)

def method_avx_gcc_8_off_24(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[24:][:8], values)) & 0xFF

    return ([
        "vextractf128    xmm1, ymm7, 0x1",
        Data("vpmovzxbw       xmm0, QWORD PTR [rip]", values),
        "vpsrldq xmm1, xmm1, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_gcc_4_off_16(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[16:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextractf128    xmm1, ymm7, 0x1",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_gcc_4_off_20(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[20:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextractf128    xmm1, ymm7, 0x1",
        "vpsrldq xmm1, xmm1, 4",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_gcc_4_off_24(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[24:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextractf128    xmm1, ymm7, 0x1",
        "vpsrldq xmm1, xmm1, 8",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_avx_gcc_4_off_28(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[28:][:4], values)) & 0xFF

    return ([
        Data("vmovd   xmm0, DWORD PTR [rip]", values),
        "vextractf128    xmm1, ymm7, 0x1",
        "vpsrldq xmm1, xmm1, 12",
        "vpmovzxbw       xmm1, xmm1",
        "vpmovzxbw       xmm0, xmm0",
        "vpmullw xmm0, xmm0, xmm1",
        "vpxor   xmm1, xmm1, xmm1",
        Data("vpshufb xmm0, xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2),
        "vinsertps       xmm0, xmm0, xmm0, 0xe",
        "vpsadbw xmm0, xmm0, xmm1",
        "vpextrb %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF
    return ([
        Data("movdqu  xmm0, xmmword ptr [rip]", values),
        Data("pmovzxbw        xmm1, qword ptr [rip]", [255] * 8),
        "movdqa  xmm2, xmm7",
        "pand    xmm2, xmm1",
        "movdqa  xmm3, xmm0",
        "pmaddubsw       xmm3, xmm2",
        "pand    xmm3, xmm1",
        "pandn   xmm1, xmm7",
        "pmaddubsw       xmm0, xmm1",
        "psllw   xmm0, 8",
        "por     xmm0, xmm3",
        "pshufd  xmm1, xmm0, 238",
        "paddb   xmm1, xmm0",
        "pxor    xmm0, xmm0",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse4_2_gcc_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF
    return ([
        Data("movdqu  xmm1, XMMWORD PTR [rip]", values),
        "movdqa  xmm0, xmm7",
        "movdqa  xmm2, xmm7",
        "punpcklbw       xmm0, xmm7",
        "punpckhbw       xmm2, xmm7",
        "movdqa  xmm3, xmm1",
        "punpcklbw       xmm3, xmm1",
        "punpckhbw       xmm1, xmm1",
        "pmullw  xmm2, xmm1",
        "pmullw  xmm0, xmm3",
        "pcmpeqd xmm1, xmm1",
        "psrlw   xmm1, 8",
        "pand    xmm0, xmm1",
        "pand    xmm1, xmm2",
        "packuswb        xmm0, xmm1",
        "movdqa  xmm1, xmm0",
        "psrldq  xmm1, 8",
        "paddb   xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF
    return ([
        Data("pmovzxbw        xmm0, qword ptr [rip]", values),
        "pmovzxbw        xmm1, xmm7",
        "pmullw  xmm1, xmm0",
        Data("pshufb  xmm1, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8, align=16),
        "pxor    xmm0, xmm0",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse4_2_gcc_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF
    return ([
        Data("pmovzxbw        xmm0, QWORD PTR [rip]", values),
        "movdqa  xmm1, xmm7",
        "pmovzxbw        xmm1, xmm1",
        "pmullw  xmm0, xmm1",
        "pxor    xmm1, xmm1",
        Data("pshufb  xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2, align=16),
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_8_off_4(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[4:][:8], values)) & 0xFF
    return ([
        "movdqa  xmm0, xmm7",
        Data("pshufb  xmm0, xmmword ptr [rip]", [4, 1, 5, 1, 6, 1, 7, 1, 8, 1, 9, 1, 10, 1, 11, 1], align=16),
        Data("pmovzxbw        xmm1, qword ptr [rip]", values),
        "pmullw  xmm1, xmm0",
        Data("pshufb  xmm1, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8, align=16),
        "pxor    xmm0, xmm0",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse4_2_clang_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF
    return ([
        "movdqa  xmm0, xmm7",
        Data("pmovzxbw        xmm1, qword ptr [rip]", values),
        "punpckhbw       xmm0, xmm0",
        "pmullw  xmm1, xmm0",
        Data("pshufb  xmm1, xmmword ptr [rip]", [0, 2, 4, 6, 8, 10, 12, 14] + [1] * 8, align=16),
        "pxor    xmm0, xmm0",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse4_2_gcc_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF
    return ([
        Data("pmovzxbw        xmm0, QWORD PTR [rip]", values),
        "movhlps xmm1, xmm7",
        "pmovzxbw        xmm1, xmm1",
        "pmullw  xmm0, xmm1",
        "pxor    xmm1, xmm1",
        Data("pshufb  xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2, align=16),
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_4_off_0(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "pmovzxbw        xmm1, xmm7",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pshufb  xmm0, xmmword ptr [rip]", [0, 2, 4, 6] + [128] * 12, align=16),
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse4_2_gcc_4_off_0(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, DWORD PTR [rip]", values),
        "movdqa  xmm1, xmm7",
        "pmovzxbw        xmm1, xmm1",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        "pxor    xmm1, xmm1",
        Data("pshufb  xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2, align=16),
        "insertps        xmm0, xmm0, 0xe",
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_4_off_4(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[4:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "pmovzxbw        xmm1, xmm7",
        "pshufd  xmm1, xmm1, 238",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pshufb  xmm0, xmmword ptr [rip]", [0, 2, 4, 6] + [128] * 12, align=16),
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse4_2_gcc_4_off_4(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[4:][:4], values)) & 0xFF
    return ([
        "pextrd  edi, xmm7, 1",
        "movd    xmm1, edi",
        Data("movd    xmm0, DWORD PTR [rip]", values),
        "pmovzxbw        xmm1, xmm1",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        "pxor    xmm1, xmm1",
        Data("pshufb  xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2, align=16),
        "insertps        xmm0, xmm0, 0xe",
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_4_off_8(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[8:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpckhbw       xmm1, xmm1",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pshufb  xmm0, xmmword ptr [rip]", [0, 2, 4, 6] + [128] * 12, align=16),
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse4_2_gcc_4_off_8(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[8:][:4], values)) & 0xFF
    return ([
        "pextrd  edi, xmm7, 2",
        "movd    xmm1, edi",
        Data("movd    xmm0, DWORD PTR [rip]", values),
        "pmovzxbw        xmm1, xmm1",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        "pxor    xmm1, xmm1",
        Data("pshufb  xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2, align=16),
        "insertps        xmm0, xmm0, 0xe",
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse4_2_clang_4_off_12(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[12:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpckhbw       xmm1, xmm1",
        "pshufd  xmm1, xmm1, 238",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pshufb  xmm0, xmmword ptr [rip]", [0, 2, 4, 6] + [128] * 12, align=16),
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse4_2_gcc_4_off_12(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[12:][:4], values)) & 0xFF
    return ([
        "pextrd  edi, xmm7, 3",
        "movd    xmm1, edi",
        Data("movd    xmm0, DWORD PTR [rip]", values),
        "pmovzxbw        xmm1, xmm1",
        "pmovzxbw        xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        "pxor    xmm1, xmm1",
        Data("pshufb  xmm0, XMMWORD PTR [rip]", [0, 2, 4, 6, 8, 10, 12, 14] * 2, align=16),
        "insertps        xmm0, xmm0, 0xe",
        "psadbw  xmm0, xmm1",
        "pextrb  %s, xmm0, 0",
    ], result)

def method_sse2_clang_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF
    return ([
        Data("movdqu  xmm0, xmmword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpckhbw       xmm1, xmm1",
        "movdqa  xmm2, xmm0",
        "punpckhbw       xmm2, xmm2",
        "pmullw  xmm2, xmm1",
        Data("movdqu  xmm1, xmmword ptr [rip]", [255, 0] * 8),
        "pand    xmm2, xmm1",
        "movdqa  xmm3, xmm7",
        "punpcklbw       xmm3, xmm3",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm3",
        "pand    xmm0, xmm1",
        "packuswb        xmm0, xmm2",
        "packuswb        xmm2, xmm2",
        "paddb   xmm2, xmm0",
        "pxor    xmm0, xmm0",
        "psadbw  xmm0, xmm2",
        "movd    %s, xmm0",
    ], result)

def method_sse2_gcc_16(values):
    assert len(values) == 16
    result = sum(c * d for c, d in zip(FLAG[:16], values)) & 0xFF
    return ([
        Data("movdqu  xmm1, XMMWORD PTR [rip]", values),
        "movdqa  xmm0, xmm7",
        "movdqa  xmm2, xmm7",
        "punpcklbw       xmm0, xmm7",
        "punpckhbw       xmm2, xmm7",
        "movdqa  xmm3, xmm1",
        "punpcklbw       xmm3, xmm1",
        "punpckhbw       xmm1, xmm1",
        "pmullw  xmm2, xmm1",
        "pmullw  xmm0, xmm3",
        "pcmpeqd xmm1, xmm1",
        "psrlw   xmm1, 8",
        "pand    xmm0, xmm1",
        "pand    xmm1, xmm2",
        "packuswb        xmm0, xmm1",
        "movdqa  xmm1, xmm0",
        "psrldq  xmm1, 8",
        "paddb   xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_clang_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF
    return ([
        Data("movq    xmm0, qword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpcklbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse2_gcc_8_off_0(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[:8], values)) & 0xFF
    return ([
        Data("movq    xmm1, QWORD PTR [rip]", values),
        "movdqa  xmm0, xmm7",
        "punpcklbw       xmm0, xmm0",
        "punpcklbw       xmm1, xmm1",
        "pmullw  xmm1, xmm0",
        "pcmpeqd xmm0, xmm0",
        "psrlw   xmm0, 8",
        "pand    xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "packuswb        xmm0, xmm0",
        "movdqa  xmm2, xmm0",
        "psadbw  xmm2, xmm1",
        "movd    %s, xmm2",
    ], result)

def method_sse2_clang_8_off_4(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[4:][:8], values)) & 0xFF
    return ([
        Data("movq    xmm0, qword ptr [rip]", values),
        "pshufd  xmm1, xmm7, 249",
        "punpcklbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse2_clang_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF
    return ([
        Data("movq    xmm0, qword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpckhbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "psadbw  xmm1, xmm0",
        "movd    %s, xmm1",
    ], result)

def method_sse2_gcc_8_off_8(values):
    assert len(values) == 8
    result = sum(c * d for c, d in zip(FLAG[8:][:8], values)) & 0xFF
    return ([
        Data("movq    xmm1, QWORD PTR [rip]", values),
        "movhlps xmm0, xmm7",
        "punpcklbw       xmm0, xmm0",
        "punpcklbw       xmm1, xmm1",
        "pmullw  xmm1, xmm0",
        "pcmpeqd xmm0, xmm0",
        "psrlw   xmm0, 8",
        "pand    xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "packuswb        xmm0, xmm0",
        "movdqa  xmm2, xmm0",
        "psadbw  xmm2, xmm1",
        "movd    %s, xmm2",
    ], result)

def method_sse2_clang_4_off_0(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpcklbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "punpckldq       xmm0, xmm1",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_gcc_4_off_0(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[:4], values)) & 0xFF
    return ([
        Data("movd    xmm1, DWORD PTR [rip]", values),
        "movdqa  xmm0, xmm7",
        "punpcklbw       xmm0, xmm0",
        "punpcklbw       xmm1, xmm1",
        "pmullw  xmm1, xmm0",
        "pcmpeqd xmm0, xmm0",
        "psrlw   xmm0, 8",
        "pand    xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "packuswb        xmm0, xmm0",
        "movd    edi, xmm0",
        "movd    xmm0, edi",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_clang_4_off_4(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[4:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "pshufd  xmm1, xmm7, 249",
        "punpcklbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "punpckldq       xmm0, xmm1",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_gcc_4_off_4(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[4:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm1, DWORD PTR [rip]", values),
        "pshufd  xmm0, xmm7, 85",
        "punpcklbw       xmm0, xmm0",
        "punpcklbw       xmm1, xmm1",
        "pmullw  xmm1, xmm0",
        "pcmpeqd xmm0, xmm0",
        "psrlw   xmm0, 8",
        "pand    xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "packuswb        xmm0, xmm0",
        "movd    edi, xmm0",
        "movd    xmm0, edi",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_clang_4_off_8(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[8:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "movdqa  xmm1, xmm7",
        "punpckhbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "punpckldq       xmm0, xmm1",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_gcc_4_off_8(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[8:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm1, DWORD PTR [rip]", values),
        "movdqa  xmm0, xmm7",
        "punpckhdq       xmm0, xmm7",
        "punpcklbw       xmm0, xmm0",
        "punpcklbw       xmm1, xmm1",
        "pmullw  xmm1, xmm0",
        "pcmpeqd xmm0, xmm0",
        "psrlw   xmm0, 8",
        "pand    xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "packuswb        xmm0, xmm0",
        "movd    edi, xmm0",
        "movd    xmm0, edi",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_clang_4_off_12(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[12:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm0, dword ptr [rip]", values),
        "pshufd  xmm1, xmm7, 249",
        "punpckhbw       xmm1, xmm1",
        "punpcklbw       xmm0, xmm0",
        "pmullw  xmm0, xmm1",
        Data("pand    xmm0, xmmword ptr [rip]", [255, 0] * 8, align=16),
        "packuswb        xmm0, xmm0",
        "pxor    xmm1, xmm1",
        "punpckldq       xmm0, xmm1",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_sse2_gcc_4_off_12(values):
    assert len(values) == 4
    result = sum(c * d for c, d in zip(FLAG[12:][:4], values)) & 0xFF
    return ([
        Data("movd    xmm1, DWORD PTR [rip]", values),
        "pshufd  xmm0, xmm7, 255",
        "punpcklbw       xmm0, xmm0",
        "punpcklbw       xmm1, xmm1",
        "pmullw  xmm1, xmm0",
        "pcmpeqd xmm0, xmm0",
        "psrlw   xmm0, 8",
        "pand    xmm0, xmm1",
        "pxor    xmm1, xmm1",
        "packuswb        xmm0, xmm0",
        "movd    edi, xmm0",
        "movd    xmm0, edi",
        "psadbw  xmm0, xmm1",
        "movd    %s, xmm0",
    ], result)

def method_shuffle(masks):
    coll = set()
    for m in masks:
        coll.add(m & 0b11111)
    assert len(coll) == 32

    old_flag = FLAG[:]
    for i in range(32):
        pos = masks[i] & 0b11111
        FLAG[i] = old_flag[pos]

    if random.getrandbits(1):
        old_mask = masks[:]
        for i in range(32):
            pos = old_mask[i] & 0b11111
            masks[i] = old_mask[pos]

        return [
            "vmovdqa64 ymm5, ymm7",
            "vpermb ymm7, ymm6, ymm5",
            "vmovdqa64 ymm5, ymm6",
            "vpermb ymm6, ymm5, ymm5",
        ]
    else:
        return [
            "vmovdqa64 ymm5, ymm7",
            "vpermb ymm7, ymm6, ymm5",
        ]

def method_check_IERAE():
    return [
        "vpextrb eax, xmm7, 4",
        "vpextrb ecx, xmm7, 5",
        "vmovd   edx, xmm7",
        "cmp     al, 69",
        "sete    al",
        "xor     cl, 123",
        "vextracti32x4   xmm0, zmm7, 2",
        "vmovd   edi, xmm0",
        "xor     dil, 125",
        "cmp     edx, 1095910729",
        "sete    dl",
        "and     dl, al",
        "or      dil, cl",
        "sete    al",
        "and     al, dl",
        IfNotThen("al"),
    ]

def assemble(code):
    if len(sys.argv) > 1:
        ctx = Context(validate=int(sys.argv[1], 16))
    else:
        ctx = Context()

    datas = sorted((d for d in code if isinstance(d, Data)), key=lambda x: len(x.data), reverse=True)
    for data in datas:
        data.pre_resolve(ctx)

    for line in code:
        print('----------')
        print(line)
        print('----------')
        ctx.add_line(line)
    assert ctx.code[-1][1] is ...
    ctx.code[-1] = (ctx.code[-1][0], None)

    # remove all none from back of ctx.data
    # while ctx.data and ctx.data[-1] is None:
    #     ctx.data.pop()

    # validate
    if ctx.validate_solver is not None:
        sols = ctx.validate_solver.batch_eval(ORIGINAL_FLAG, 2)
        assert len(sols) == 1
        print(bytes(sols[0]), file=sys.stderr)
        return

    for i in range(len(ctx.data)):
        if ctx.data[i] is None:
            ctx.data[i] = random.getrandbits(8)
            # ctx.data[i] = 0xF1

    rbx = 0
    print(ctx.code, file=sys.stderr)
    print(bytes(ctx.data).hex(), file=sys.stderr)

    with open("offsets.arr", "wt") as f:
        print(bytes_to_c_arr(ctx.export_offsets()), file=f)

    with open("main.arr", "wt") as f:
        print(bytes_to_c_arr(ctx.data), file=f)

def combine(*args):
    assert len(args) > 0

    dest = [
        ('eax', 'al'),
        ('ecx', 'cl'),
        ('edx', 'dl'),
    ]
    result_reg, calc_reg, imm_reg = random.sample(dest, 3)
    _, final = random.choice(dest)

    if len(args) == 1:
        code, result = args[0]
        code[-1] %= calc_reg[0]
    else:
        code = [
            f'xor {calc_reg[0]}, {calc_reg[0]}',
        ]
        result = claripy.BVV(0, 8)
        for c, re in args:
            c[-1] %= imm_reg[0]
            code.extend(c)
            code.append(f"add {calc_reg[1]}, {imm_reg[1]}")
            result += re

    index = random.randint(0, len(code))
    code.insert(index, LeaMov(result_reg[0], result))
    return code + [
        f"cmp {result_reg[1]}, {calc_reg[1]}",
        f"sete {final}",
        IfNotThen(final),
    ]

def main():
    mask = []
    for i in range(32):
        mask.append(i | (random.randint(0b001, 0b111) << 5))
    random.shuffle(mask)

    xord_flag = []
    for i in range(32):
        a = 0
        while a.bit_length() < 4 or a in xord_flag:
            a = random.getrandbits(8)
        xord_flag.append(a)
    xor_body = [
        "vmovups zmm7, zmmword ptr [rsi]",
        *method_check_IERAE(),
        Data("vxorps ymm7, ymm7, ymmword ptr [rip]", xord_flag),
    ]
    for i in range(32):
        FLAG[i] ^= xord_flag[i]
    

    body = [
        *xor_body,

        # 1
        *combine(method_sum_all_32()),
        Data("vmovups ymm6, ymmword ptr [rip]", mask[:]),
    ]

    methods = []
    for m, obj in globals().items():
        if m.startswith("method_"):
            if '_gcc_' not in m and '_clang_' not in m:
                print('ignore', m, file=sys.stderr)
                continue
            try:
                index = m.index('_gcc_')
                index += 5
            except ValueError:
                index = m.index('_clang_')
                index += 7
            
            off = m[index:]
            if '_off_' in off:
                l, off = off.split('_off_')
                if off != 'x':
                    off = int(off)
            else:
                l = off
                off = 0
            l = int(l)

            methods.append((obj, l))
            # bmask = 0
            # for i in range(l):
            #     bmask |= (1 << (off + i))
            # methods.append((bmask, obj))

    copied = methods[:]
    for i in range(25):
        body.extend(method_shuffle(mask))

        match i:
            case 20:
                body.extend(method_increment_32())
            case 10:
                body.extend(method_shift_32(claripy.BVS("method_shift_32", 64)))
            case _:
                combines = []
                for j in range(4):
                    if not copied:
                        copied = methods[:]
                    idx = random.randint(0, len(copied) - 1)
                    m, l = copied.pop(idx)
                    combines.append(m([claripy.BVS(f"method_{i}_{j}_{k}", 8) for k in range(l)]))
                body.extend(combine(*combines))

    assemble(PROL + OUTPUT_INIT + INPUT_INIT + CHECK_LEN + body + SUCCESS)

if __name__ == "__main__":
    main()
