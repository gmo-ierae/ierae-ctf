FROM ubuntu:22.04@sha256:340d9b015b194dc6e2a13938944e0d016e57b9679963fdeb9ce021daac430221

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing

FROM pwn.red/jail
COPY --from=0 / /srv
RUN mkdir /srv/app
COPY ./chal /srv/app/run
COPY ./flag.txt /srv/app/

ENV JAIL_MEM=20M JAIL_TIME=300 JAIL_PORT=33334
EXPOSE 33334
