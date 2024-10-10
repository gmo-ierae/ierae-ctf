FROM ubuntu:24.04

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing
RUN head -c 1024 /dev/urandom | sha512sum | head -c 96 > key.txt

FROM pwn.red/jail
COPY --from=0 / /srv
RUN mkdir /srv/app
COPY ./fortress /srv/app/run
COPY ./flag.txt /srv/app/flag.txt
RUN mv /srv/key.txt /srv/app/key.txt

ENV JAIL_MEM=20M JAIL_TIME=300 JAIL_PORT=20001
EXPOSE 20001
