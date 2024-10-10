FROM python:3.12-alpine@sha256:7130f75b1bb16c7c5d802782131b4024fe3d7a87ce7d936e8948c2d2e0180bc4 as app

FROM pwn.red/jail@sha256:ee52ad5fd6cfed7fd8ea30b09792a6656045dd015f9bef4edbbfa2c6e672c28c
COPY --from=app / /srv
COPY challenge.py /srv/app/run
ENV JAIL_MEM=20M JAIL_TIME=300 JAIL_PORT=55555
EXPOSE 55555
