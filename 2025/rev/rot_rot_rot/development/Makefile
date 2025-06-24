CC = gcc
CFLAGS = -Wall -Wextra -std=c11
TARGET = rot_rot_rot
SRC = main.c
OBJ = $(SRC:.c=.o)

.PHONY: all clean release

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^
	strip $@

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJ) $(TARGET) flag.enc decrypt decrypt.o

release: $(TARGET) flag.txt
	./$(TARGET) flag.txt flag.enc
