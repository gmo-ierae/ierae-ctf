FROM python:3.13-slim@sha256:a658ec9b0f7df10fd2bd6f8f3a05a248f2580f105d08b89eaa359b9d4ddf0588

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN pip install --no-cache-dir pycryptodome
RUN apt-get -y install socat

COPY server.py .
COPY flag.txt .

CMD ["socat", "tcp-l:12349,reuseaddr,fork", "EXEC:'python server.py'"]
