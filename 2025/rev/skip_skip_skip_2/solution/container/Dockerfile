FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3 python3-pip python3-dev git libssl-dev libffi8

RUN python3 -m pip install --upgrade --break-system-packages pwntools

COPY --chmod=755 solve.py .
