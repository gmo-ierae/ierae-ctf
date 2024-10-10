FROM ubuntu:22.04

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get upgrade -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install ruby curl -y && \
    curl -L https://github.com/Charo-IT/pwnlib/raw/master/pwnlib.rb > /usr/lib/ruby/3.0.0/pwnlib.rb && \
    apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

ENV CHALL_HOST localhost
ENV CHALL_PORT 51914

ADD exploit.rb /exploit.rb

CMD ["ruby", "/exploit.rb", "r"]
