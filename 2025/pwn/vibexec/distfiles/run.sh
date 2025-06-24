#!/bin/sh
qemu-system-x86_64 \
  -m 128M \
  -kernel ./bzImage \
  -initrd ./rootfs.cpio.gz \
  -append "console=ttyS0 quiet root=/dev/sda rw oops=panic panic=1 panic_on_warn=1 kaslr pti=on" \
  -drive file=flag,if=virtio,format=raw \
  -monitor /dev/null \
  -nographic \
  -cpu kvm64,+smep,+smap \
  -no-reboot \
  -snapshot
