#!/usr/bin/env python

from os import getenv
import random
import secrets

FLAG = getenv("FLAG", "TEST{TEST_FLAG}")


def main():
    # Python uses the Mersenne Twister (MT19937) as the core generator.
    # Setup Random Number Generator
    rng = random.Random()
    rng.seed(secrets.randbits(32))

    secret = rng.getrandbits(32)

    print("Welcome!")
    print("Recover the initial output and input them to get the flag.")

    while True:
        print("--------------------")
        print("Menu")
        print("1. Get next 16 random data")
        print("2. Submit your answer")
        print("3. Quit")
        print("Enter your choice (1-3)")
        choice = input("> ").strip()

        if choice == "1":
            print("Here are your random data:")
            for _ in range(16):
                print(rng.getrandbits(32))
        elif choice == "2":
            print("Enter the secret decimal number")
            try:
                num = int(input("> ").strip())

                if num == secret:
                    print("Correct! Here is your flag:")
                    print(FLAG)
                else:
                    print("Incorrect number. Bye!")
                break
            except (ValueError, EOFError):
                print("Invalid input. Exiting.")
                break
        elif choice == "3":
            print("Bye!")
            break
        else:
            print("Invalid choice. Please enter 1, 2 or 3.")
            continue


if __name__ == "__main__":
    main()
