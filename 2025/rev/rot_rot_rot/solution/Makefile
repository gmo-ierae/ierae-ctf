CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -O3
TARGET = decrypt
SRC = decrypt.c
OBJ = $(SRC:.c=.o)

.PHONY: all clean decrypt

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJ) $(TARGET) decrypt decrypt.o
