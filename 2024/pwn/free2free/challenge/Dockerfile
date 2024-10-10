FROM ubuntu@sha256:075680e983398fda61b1ac59ad733ad81d18df4bc46411666bb8a03fb9ea0195

RUN apt-get update --fix-missing && apt-get -y upgrade && apt-get update --fix-missing
RUN apt-get install -y qemu qemu-system-x86 qemu-utils socat cpio gzip wget hashcash

RUN useradd -d /home/ctf -m -p ctf -s /bin/bash ctf
RUN ulimit -c 0

WORKDIR /home/ctf
COPY bzImage ./bzImage
COPY run.sh ./run.sh
COPY rootfs.cpio.gz ./rootfs.cpio.gz
RUN chmod +x *.sh
RUN chmod 664 ./rootfs.cpio.gz

USER ctf
CMD ["socat", "tcp-l:31622,reuseaddr,fork", "EXEC:./run.sh,pty,stderr"]
EXPOSE 31622
