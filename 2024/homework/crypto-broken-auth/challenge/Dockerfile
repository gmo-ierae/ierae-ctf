FROM ubuntu:latest

RUN apt-get update && apt-get install -y openssh-server sudo
RUN mkdir /run/sshd

RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
RUN sed -i 's/Banner.+$//' /etc/ssh/sshd_config

COPY --chown=root:root print_flag /bin/print_flag

RUN useradd -m flag

COPY --chown=flag:flag authorized_keys /home/flag/.ssh/authorized_keys

RUN chmod 0600 /home/flag/.ssh/authorized_keys && chmod 777 /bin/print_flag && touch /home/flag/.hushlogin

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
