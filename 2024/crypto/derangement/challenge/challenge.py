#!/usr/bin/env python

from os import getenv
import random
import string
import sys

FLAG = getenv("FLAG", "TEST{TEST_FLAG}")

LENGTH = 15
CHAR_SET = string.ascii_letters + string.digits + string.punctuation

def generate_magic_word(length=LENGTH, char_set=CHAR_SET):
    return ''.join(random.sample(char_set, length))

def is_derangement(perm, original):
    return all(p != o for p, o in zip(perm, original))

def output_derangement(magic_word):
    while True:
        deranged = ''.join(random.sample(magic_word, len(magic_word)))
        if is_derangement(deranged, magic_word):
            print('hint:', deranged)
            break

def guess_random(magic_word, flag):
    print('Oops, I spilled the beans! What is the magic word?')
    if input('> ') == magic_word:
        print('Congrats!\n', flag)
        return True
    print('Nope')
    return False

def main():
    magic_word = generate_magic_word()
    banner = """
/********************************************************\\
|                                                        |
|   Abracadabra, let's perfectly rearrange everything!   |
|                                                        |
\\********************************************************/
"""
    print(banner)
    connection_count = 0

    while connection_count < 300:
        print('type 1 to show hint')
        print('type 2 to submit the magic word')
        try:
            connection_count += 1
            user_input = int(input('> '))

            if user_input == 1:
                output_derangement(magic_word)
            elif user_input == 2:
                if guess_random(magic_word, FLAG):
                    break
                sys.exit()
            else:
                print('bye!')
                sys.exit()
        except:
            sys.exit(-1)
    
    print('Connection limit reached. Exiting...')

if __name__ == "__main__":
    main()
