import gdb
import os
import random
import time
from pathlib import Path
from struct import pack, unpack

NS_PER_INST     = 2 ** 10
JITTER          = 0

VIC_BASE        = 0x10140000
VIC_INTENABLE   = 0x10

UART_BREAKPOINT = {"chal1": 0x10088, "chal2": 0x10048}

TIMER0_BASE     = 0x101e2000
TIMER2_BASE     = 0x101e3000
TIMER_LOAD      = 0x00
TIMER_VALUE     = 0x04
TIMER_CONTROL   = 0x08
TIMER_INTCLR    = 0x0c

IRQ_TIMER2      = 5

LOG_FILE        = f"{os.environ['LOG_DIR']}/skip.log"
FLAG_FILE       = "/flag.txt"

HINT_IP         = int(os.environ["HINT_IP"])

target_running  = False
timer_offset    = 0

def log(message):
    if target_running:
        line = f"[{get_clock_ns():012d}] {message}\n"
    else:
        line = f"[************] {message}\n"

    print(line, end="")
    with open(LOG_FILE, "a") as f:
        f.write(line)
        f.flush()

def get_clock_ns():
    value = unpack('<I', gdb.inferiors()[0].read_memory(TIMER0_BASE + TIMER_VALUE, 4))[0]
    value += timer_offset
    return (0xFFFFFFFF - value) * NS_PER_INST

def clock_setup():
    store_in_machine(TIMER0_BASE + TIMER_LOAD, 0xFFFFFFFF)
    store_in_machine(TIMER0_BASE + TIMER_CONTROL, 0b1000_0010)

class TriggerBreakpoint(gdb.Breakpoint):
    def __init__(self, pattern, count):
        bp = next(addr for name, addr in UART_BREAKPOINT.items() if name in os.environ["CHALLENGE_FILE"])
        super().__init__(f"*{bp:#010x}", internal=True)
        self.silent = True
        self._pattern = pattern
        self._count = count

    def stop(self):
        inst = gdb.selected_frame().architecture().disassemble(gdb.selected_frame().pc() - 4, gdb.selected_frame().pc() - 4)[0]['asm']
        if inst.split()[0] != 'str':
            return False
        src_reg = inst.split()[1].split(',')[0]

        ch = int(gdb.selected_frame().read_register(src_reg))
        log(f"ch = {ch:#04x}")
        
        if ch == self._pattern:
            self._count -= 1
        return self._count == 0
    
class TimerBreakpoint(gdb.Breakpoint):
    def __init__(self, offset):
        super().__init__("*0x18", internal=True)
        self.silent = True

        # Enable timer interrupt
        gdb.execute("set $cpsr &= ~0x80")
        store_in_machine(VIC_BASE + VIC_INTENABLE, 1 << IRQ_TIMER2)

        # Set up timer interrupt handler
        # This handler skips one instruction
        # ldr sp, =0x07f00000
        # stmfd   sp!, {lr}
        # ldmfd   sp!, {pc}^
        gdb.inferiors()[0].write_memory(0x18, b"\x04\xd0\x9f\xe5\x00\x40\x2d\xe9\x00\x80\xfd\xe8\x00\x00\xf0\x07")
        
        # Set up timer
        store_in_machine(TIMER2_BASE + TIMER_LOAD, offset // NS_PER_INST)
        store_in_machine(TIMER2_BASE + TIMER_CONTROL, 0b1010_0011)

    def stop(self):
        lr = int(gdb.selected_frame().read_register("lr"))
        if HINT_IP:
            log(f"Skipping an instruction at {lr - 0x04:#010x}......")
        else:
            log(f"Skipping an instruction......")
        return True

    def delete(self):
        store_in_machine(TIMER2_BASE + TIMER_INTCLR, 1)  # Clear the timer interrupt
        return super().delete()

def store_in_machine(address, value):
    # Evacuate all registers and current instruction
    regs = {
        r.name: int(gdb.selected_frame().read_register(r.name))
        for r in gdb.selected_frame().architecture().registers()
    }
    inst = gdb.inferiors()[0].read_memory(gdb.selected_frame().pc(), 4)
    
    # Execute "STR R1, [R0]"
    gdb.execute(f"set $r0 = {address:#010x}")
    gdb.execute(f"set $r1 = {value:#010x}")
    gdb.inferiors()[0].write_memory(gdb.selected_frame().pc(), b"\x00\x10\x80\xe5")
    gdb.execute("stepi")

    global timer_offset
    timer_offset += 1

    # Restore registers and instruction
    for reg, val in regs.items():
        gdb.execute(f"set ${reg} = {val:#010x}")
    gdb.inferiors()[0].write_memory(gdb.selected_frame().pc(), inst)

def flag_setup():
    flag = Path(FLAG_FILE)
    if flag.exists():
        log(f"Loading flag into memory address 0x20000......")
        gdb.inferiors()[0].write_memory(0x20000, flag.read_bytes())
    else:
        log(f"Warning: Flag file not found.")

def get_gdb_socket():
    gdb_socket = Path(os.environ['GDB_SOCKET'])
    while not gdb_socket.exists():
        time.sleep(0.1)
    time.sleep(0.3)

    return gdb_socket.absolute()

def main():
    gdb_socket = get_gdb_socket()

    log("Log format: [(Machine time in ns)] (message)")

    gdb.set_parameter("architecture", "arm")
    gdb.execute(f"target remote {gdb_socket}")

    pattern = int(gdb.convenience_variable("pattern"))
    count = int(gdb.convenience_variable("count"))
    offset = int(gdb.convenience_variable("offset"))
    log(f"pattern = {pattern:#04x}")
    log(f"count = {count}")
    log(f"offset = {offset} ns")

    clock_setup()
    flag_setup()

    log("Setting a trigger......")
    trigger = TriggerBreakpoint(pattern, count)

    log("Running the target......")
    global target_running
    target_running = True
    gdb.execute("continue")
    log("Trigger fired!")
    trigger.delete()

    TriggerBreakpoint(None, None)

    log("Resuming the target and waiting for the offset time......")
    timer = TimerBreakpoint(max(0, offset + random.randint(-1 * JITTER, 1 * JITTER)))
    gdb.execute("continue")
    timer.delete()

    log("Resuming the target......")
    gdb.execute("continue")
    log("Completed.")

if __name__ == '__main__':
    main()
