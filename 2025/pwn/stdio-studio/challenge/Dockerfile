FROM ubuntu:24.04@sha256:72297848456d5d37d1262630108ab308d3e9ec7ed1c3286a32fe09856619a782
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing

RUN apt-get -y install xinetd
RUN groupadd -r pwn && useradd -r -g pwn pwn

RUN echo '#!/bin/sh\n\
/etc/init.d/xinetd start\n\
sleep infinity\n\
' > /start.sh

RUN rm /etc/xinetd.d/*

RUN echo 'service pwn\n\
{\n\
  type = UNLISTED\n\
  disable = no\n\
  socket_type = stream\n\
  protocol = tcp\n\
  wait = no\n\
  user = pwn\n\
  bind = 0.0.0.0\n\
  port = 33335\n\
  flags = REUSE\n\
  server = /home/pwn/chal\n\
  per_source = 5\n\
  rlimit_cpu = 20\n\
  rlimit_as = 32M\n\
  log_type = FILE /var/log/chal.log\n\
}' > /etc/xinetd.d/pwn

RUN chmod 550 /start.sh

RUN chmod 444 /etc/xinetd.d/pwn
RUN chmod 1733 /tmp /var/tmp /dev/shm

ADD flag.txt /flag.txt
RUN chmod 444 /flag.txt

WORKDIR /home/pwn
ADD chal .
RUN chmod 550 chal

RUN chown -R root:pwn /home/pwn

# NOTE: It may take a while until xinetd fully launches (~ 3mins).
CMD ["/start.sh"]
