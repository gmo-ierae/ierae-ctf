# Cross-compiler toolchain
CROSS_COMPILE = arm-none-eabi-
CC = $(CROSS_COMPILE)gcc
AS = $(CROSS_COMPILE)as
LD = $(CROSS_COMPILE)ld
OBJCOPY = $(CROSS_COMPILE)objcopy

# Compiler flags
CFLAGS = -mcpu=arm926ej-s -nostdlib -nostartfiles -ffreestanding -O2 -Wall
ASFLAGS = -mcpu=arm926ej-s
LDFLAGS = -T linker.ld

# Source files
SRC_C = src/main.c src/uart.c src/rc4.c
SRC_S = src/startup.s
OBJ = $(SRC_C:.c=.o) $(SRC_S:.s=.o)

# Target
TARGET = kernel.elf
BINARY = kernel.bin

all: $(BINARY)

$(BINARY): $(TARGET)
	$(OBJCOPY) -O binary $< $@

$(TARGET): $(OBJ)
	$(LD) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

%.o: %.s
	$(AS) $(ASFLAGS) -o $@ $<

clean:
	rm -f $(OBJ) $(TARGET) $(BINARY)

.PHONY: all clean
