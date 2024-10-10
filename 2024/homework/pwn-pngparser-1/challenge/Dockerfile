FROM ubuntu:22.04

RUN set -x && \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y xinetd && \
    useradd user && \
    apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

COPY --chown=root:user chall /chall
COPY --chown=root:user run.sh /run.sh
COPY --chown=root:user flag1.txt /flag1.txt
COPY --chown=root:user flag2.txt /flag2.txt
COPY --chown=root:root chall.conf /etc/xinetd.d/chall.conf

RUN chmod 550 /chall /run.sh && \
    chmod 440 /flag1.txt /flag2.txt

USER user
EXPOSE 51914

CMD ["xinetd", "-dontfork", "-f", "/etc/xinetd.d/chall.conf"]