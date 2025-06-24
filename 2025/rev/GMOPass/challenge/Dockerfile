FROM --platform=linux/amd64 ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y clang --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

FROM pwn.red/jail
COPY --from=0 / /srv
COPY ./run ./GMOPass.so /srv/app/

RUN chmod 555 /srv/app/run && chmod 444 /srv/app/GMOPass.so
ENV JAIL_MEM=32M JAIL_TIME=15 JAIL_PORT=12450 JAIL_TMP_SIZE=4096 JAIL_CPU=1000 JAIL_POW=30000
EXPOSE 12450
