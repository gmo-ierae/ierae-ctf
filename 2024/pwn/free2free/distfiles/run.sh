qemu-system-x86_64 \
  -kernel ./bzImage \
  -initrd ./rootfs.cpio.gz \
  -nographic \
  -monitor /dev/null \
  -cpu kvm64,+smep,+smap \
  -net nic,model=virtio \
  -net user \
  -append "console=ttyS0 kaslr oops=panic panic=1 quiet cgroup_disable=memory" \
  -no-reboot \
  -m 256M \
  2>&1
