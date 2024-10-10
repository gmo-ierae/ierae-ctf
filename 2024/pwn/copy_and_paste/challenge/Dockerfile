FROM ubuntu:23.10@sha256:fd7fe639db24c4e005643921beea92bc449aac4f4d40d60cd9ad9ab6456aec01

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing
COPY ./flag.txt /
RUN mv /flag.txt /flag-$(md5sum flag.txt | awk '{print $1}').txt

FROM pwn.red/jail
COPY --from=0 / /srv
RUN mkdir /srv/app
COPY ./chal /srv/app/run
RUN mv /srv/flag*txt /srv/app/
