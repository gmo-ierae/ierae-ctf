#!/bin/bash

chroot /srv sudo -u ctf bash -c "cd /home/ctf; python3 -u ./chal.py"
