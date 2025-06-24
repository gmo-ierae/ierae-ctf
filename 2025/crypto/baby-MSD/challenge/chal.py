#!/usr/bin/env python3

from sys import exit
from random import randint

def stage():
  digit_counts = [0 for i in range(10)]

  for i in range(2000):
    secret = randint(10 ** 60, 10 ** 100)
    M = int(input("Enter mod: "))
    if M < 10 ** 30:
      print("Too small!")
      exit(1)

    msd = str(secret % M)[0]
    digit_counts[int(msd)] += 1

  choice = int(input("Which number (1~9) appeared the most? : "))
  for i in range(10):
    if digit_counts[choice] < digit_counts[i]:
      print("Failed :(")
      exit(1)

  print("OK")

def main():
  for i in range(100):
    print("==== Stage {} ====\n".format(i+1))
    stage()

  print("You did it!")
  with open("flag.txt", "r") as f:
    print(f.read())

if __name__ == '__main__':
  main()
