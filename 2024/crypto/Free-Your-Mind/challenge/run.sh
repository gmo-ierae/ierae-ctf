#!/bin/sh

## Proof-of-Work
echo -e 'Install hashcash on Ubuntu with `sudo apt install hashcash`. For other distros, see http://www.hashcash.org/.\n'
LENGTH=16
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

/app/chall.sage
