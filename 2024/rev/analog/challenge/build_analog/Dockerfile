FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        make \
        rsync

RUN mkdir /work
COPY Makefile analog.c flag /work/

WORKDIR /work
RUN make \
    && ./analog < flag > flag.encoded \
    && rm Makefile analog.c flag
