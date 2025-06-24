FROM python:3.13.2-alpine@sha256:323a717dc4a010fee21e3f1aac738ee10bb485de4e7593ce242b36ee48d6b352 as app

FROM pwn.red/jail
COPY --from=app / /srv

RUN mkdir /srv/app

COPY chal.py /srv/app/run
COPY ./flag.txt /srv/app/

RUN chmod 555 /srv/app/run
RUN chmod 444 /srv/app/flag.txt

ENV JAIL_MEM=20M JAIL_TIME=300 JAIL_PORT=12343
EXPOSE 12343
