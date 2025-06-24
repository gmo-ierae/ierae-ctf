FROM ubuntu:24.04@sha256:b59d21599a2b151e23eea5f6602f4af4d7d31c4e236d22bf0b62b86d2e386b8f

RUN apt-get update --fix-missing && apt-get -y upgrade && apt-get update --fix-missing
RUN apt-get install -y qemu-system-x86 socat cpio gzip wget hashcash

RUN useradd -d /home/ctf -m -p ctf -s /bin/bash ctf
RUN ulimit -c 0

WORKDIR /home/ctf
COPY bzImage ./bzImage
COPY run.sh ./run.sh
COPY flag ./flag
COPY rootfs.cpio.gz ./rootfs.cpio.gz
RUN chmod +x run.sh && chmod 664 ./rootfs.cpio.gz

USER ctf
CMD ["socat", "tcp-l:31662,reuseaddr,fork", "EXEC:./run.sh,pty,stderr"]
EXPOSE 31662
