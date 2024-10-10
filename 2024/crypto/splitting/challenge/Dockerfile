FROM sagemath/sagemath:10.4@sha256:8d657a42f33a407b8dbc9a3cb5818cb6b4df8aacc7b291ba675132ee55d4db73

RUN sudo apt update && sudo apt install -y socat

USER sage
WORKDIR /app

COPY --chmod=755 challenge.sage .
COPY requirements.txt .
RUN sage -pip install -r requirements.txt

CMD ["socat", "TCP-LISTEN:11119,fork,reuseaddr", "EXEC:'/app/challenge.sage',pty,ctty"]
EXPOSE 11119
