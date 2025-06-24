FROM ubuntu:24.04@sha256:72297848456d5d37d1262630108ab308d3e9ec7ed1c3286a32fe09856619a782

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing

FROM pwn.red/jail
COPY --from=0 / /srv
RUN mkdir /srv/app
COPY ./chal /srv/app/run
COPY ./flag.txt /srv/app/

RUN chmod 555 /srv/app/run
RUN chmod 444 /srv/app/flag.txt

WORKDIR /srv/app
RUN mv flag.txt flag-$(md5sum flag.txt | awk '{print $1}').txt

ENV JAIL_PIDS=6 JAIL_MEM=600M JAIL_TIME=300 JAIL_PORT=33337
EXPOSE 33337
