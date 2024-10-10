# docker build -t luz_da_lua:latest .
# debug
## docker run -it -v "$(pwd)":/mnt --rm luz_da_lua:latest
# compile
## docker run -v "$(pwd)":/mnt --rm luz_da_lua:latest bash -c "/task/lua-5.4.7/src/luac -o /mnt/LuzDaLua.luac /mnt/LuzDaLua.lua"
# test
## docker run -it -v "$(pwd)":/mnt --rm luz_da_lua:latest bash -c "/task/lua-5.4.7/src/lua /mnt/LuzDaLua.luac" < flag.txt

FROM ubuntu:24.04
RUN apt update && apt upgrade

RUN mkdir -p /task
WORKDIR /task

RUN apt install -y wget make build-essential
RUN wget https://www.lua.org/ftp/lua-5.4.7.tar.gz
RUN tar -xf lua-5.4.7.tar.gz
RUN cd /task/lua-5.4.7 && make
