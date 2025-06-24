#!/usr/bin/env python3
import hashlib
import random
import shutil
import string
import subprocess
import sys
import time
import os
import tempfile

STDIN_FILE      = f"{os.environ['LOG_DIR']}/target_input.txt"
STDOUT_FILE     = f"{os.environ['LOG_DIR']}/target_output.txt"
SKIP_LOG_FILE   = f"{os.environ['LOG_DIR']}/skip.log"

BANNER = """===== skip skip skip =====
In this challenge, we simulate Fault Injection attack against hardware within an emulation environment.
You can skip a single instruction at a specified timing in a program running on QEMU.

The timing for skipping an instruction is specified using characters output by the program as a temporal trigger point.
This timing is configured using three parameters: Character, Count, and Offset.
Character: A single character that determines when the trigger activates
Count: The number of times the specified character must appear in the output before the trigger fires
Offset: The delay (in nanoseconds) between the trigger firing and the instruction skip

For example, with parameters Character = 0x41, Count = 2, and Offset = 100000, one instruction will be skipped 100,000 nanoseconds after the program outputs the character "A" for the second time.

You can give arbitrary input to the program.

Notes:
* Character output from the program occurs when a STR instruction is executed to address 0x101f1000
* In the QEMU environment, approximately one instruction executes every 1024ns
* The QEMU environment is deterministic: using the same parameters will always fire the trigger at the same timing and skip the same
instruction
=========================="""

RUN_CMD = ["./qemu.exp"]
GDB_CMD = [
    "gdb-multiarch",
    "-batch",
    "-ex", "set $pattern = {pattern}",
    "-ex", "set $count = {count}",
    "-ex", "set $offset = {offset}",
    "-x", "skip.py"
]

POW_DIFFICULTY  = int(os.environ["POW_DIFFICULTY"])
TIMEOUT         = int(os.environ["TIMEOUT"])

def challenge_pow(difficulty):
    if difficulty == -1:
        print("Skipping proof of work challenge.", file=sys.stderr)
        return True

    prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    
    print(f"Find a string X such that SHA256({prefix} + X) starts with {difficulty} zeros")
    print(f"Enter X: ")
    solution = input().strip()

    h = hashlib.sha256((prefix + solution).encode()).hexdigest()
    if h.startswith('0' * difficulty):
        print("Correct.")
        return True
    else:
        print("Incorrect.")
        return False

def get_gdb_command():
    try:
        print("Enter trigger character (0x00 <= x <= 0xff):")
        pattern = int(input().strip(), 0)
        if not (0x00 <= pattern <= 0xff):
            print("Error: Out of range.")
            sys.exit(1)

        print("Enter trigger count (1 <= x):")
        count = int(input().strip(), 0)
        if not (1 <= count):
            print("Error: Out of range.")
            sys.exit(1)

        print("Enter offset time in ns (0 <= x):")
        offset = int(input().strip(), 0)
        if not (0 <= offset):
            print("Error: Out of range.")
            sys.exit(1)
    except ValueError:
        print("Error: Not an integer.")
        sys.exit(1)

    cmd = [
        c.format(**locals())
        for c in GDB_CMD
    ]
    return cmd

def get_input():
    try:
        print("Enter input (hex):")
        input_data = bytes.fromhex(input().strip())
    except ValueError:
        print("Error: Input must be hex-encoded.")
        sys.exit(1)

    if len(input_data) > 32:
        print("Error: Input too long (max 32 bytes).")
        sys.exit(1)
    return input_data

def main():
    print(f"Case number: {os.environ['CASE_NUMBER']}")

    if not challenge_pow(POW_DIFFICULTY):
        sys.exit(1)
    print()

    print(BANNER)
    print()

    gdb_socket = tempfile.mktemp()
    os.environ["GDB_SOCKET"] = gdb_socket

    gdb_cmd = get_gdb_command()
    input_data = get_input()
    with open(STDIN_FILE, "wb") as f:
        f.write(input_data)
    print()

    print("Running the application......")

    try:
        run_proc = subprocess.Popen(RUN_CMD, stdout=sys.stderr, stderr=sys.stderr)
        gdb_proc = subprocess.Popen(gdb_cmd, stdout=sys.stderr, stderr=sys.stderr)
        
        start_time = time.time()
        while time.time() - start_time < TIMEOUT:
            if run_proc.poll() is not None and gdb_proc.poll() is not None:
                print("Processes completed.", file=sys.stderr)
                break
            time.sleep(0.1)
        else: 
            print("Timeout.")
            print("Timeout reached. Killing the processes...", file=sys.stderr)
    finally:
        if run_proc.poll() is None:
            run_proc.kill()
        if gdb_proc.poll() is None:
            gdb_proc.kill()

    print("Completed.")
    print()

    with open(STDOUT_FILE, "rb") as f:
        print("Output:")
        print(f.read())
        print()

    with open(SKIP_LOG_FILE, "r") as f:
        print("Observation log:")
        print(f.read())

if __name__ == "__main__":
    try:
        main()
    finally:
        shutil.rmtree(os.environ['LOG_DIR'])
