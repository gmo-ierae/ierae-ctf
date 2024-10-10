FROM sagemath/sagemath:10.4

RUN sudo apt update && sudo apt install -y socat hashcash

USER sage
WORKDIR /app

COPY --chmod=755 run.sh .
COPY --chmod=755 chall.sage .
COPY flag.py .

CMD ["socat", "TCP-LISTEN:17285,fork,reuseaddr", "EXEC:'timeout --kill-after=120 180 /app/run.sh',pty,ctty"]
EXPOSE 17285
