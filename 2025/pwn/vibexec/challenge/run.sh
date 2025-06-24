#!/bin/sh
## Proof-of-Work
echo 'Install hashcash on Ubuntu with `sudo apt install hashcash`. For other distros, see http://www.hashcash.org/.\n'
LENGTH=10
STRENGTH=27
challenge=`dd bs=32 count=1 if=/dev/urandom 2>/dev/null | base64 | tr +/ _. | cut -c -$LENGTH`
echo hashcash -mb$STRENGTH $challenge

echo "hashcash token: "
read token
if [ `expr "$token" : "^[a-zA-Z0-9\_\+\.\:\/]\{52\}$"` -eq 52 ]; then
   if hashcash -cdb$STRENGTH -f /tmp/hashcash.sdb -r $challenge $token 2> /dev/null; then
       echo "[+] Correct"
   else
       echo "[-] Wrong"
       exit
   fi
else
   echo "[-] Invalid token"
   exit
fi
## End Proof-of-Work
qemu-system-x86_64 \
  -m 128M \
  -kernel ./bzImage \
  -initrd ./rootfs.cpio.gz \
  -append "console=ttyS0 quiet root=/dev/sda rw oops=panic panic=1 panic_on_warn=1 kaslr pti=on" \
  -drive file=flag,if=virtio,format=raw,readonly=on \
  -monitor /dev/null \
  -nographic \
  -cpu kvm64,+smep,+smap \
  -no-reboot \
  -snapshot
