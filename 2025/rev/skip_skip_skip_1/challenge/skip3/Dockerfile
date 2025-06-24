FROM ubuntu:24.04

# Patching QEMU to fix a bug
# https://gitlab.com/qemu-project/qemu/-/issues/2830
WORKDIR /root
COPY qemu-system-arm_8.2.2+ds-0ubuntu1.7_amd64.deb .
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install -y ./qemu-system-arm_*.deb

# Preparing for the challenges
WORKDIR /
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        gcc-arm-none-eabi \
        make \
        gdb-multiarch \
        expect \
        socat

COPY chal1 /chal1
RUN make -C /chal1 \
    && arm-none-eabi-objdump -d /chal1/kernel.elf > /chal1/kernel.asm

COPY chal2 /chal2
RUN make -C /chal2 \
    && arm-none-eabi-objdump -d /chal2/kernel.elf > /chal2/kernel.asm

COPY --chmod=755 service.sh challenge.py qemu.exp skip.py ./
ARG FLAG
RUN echo -n "$FLAG" > /flag.txt
RUN mkdir /log