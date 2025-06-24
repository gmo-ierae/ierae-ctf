FROM ubuntu:24.04@sha256:72297848456d5d37d1262630108ab308d3e9ec7ed1c3286a32fe09856619a782

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing
RUN apt-get -y install python3 npm sudo curl
RUN npm install n -g
RUN n stable
RUN apt-get purge -y nodejs npm && apt-get autoremove -y
RUN groupadd -r ctf && useradd -r -g ctf ctf

COPY ./sudo-as-nobody /etc/sudoers.d/
RUN chmod 440 /etc/sudoers.d/sudo-as-nobody

WORKDIR /home/ctf
COPY ./flag.txt .
COPY ./chal.py .
RUN chmod 550 ./chal.py ./flag.txt
RUN chmod -R go-w .

# Disable write to /tmp
RUN chmod -R o-w /tmp /var/tmp
RUN chown -R root:ctf /home/ctf /tmp

# Use chroot to disable write to /dev
FROM ubuntu:24.04@sha256:72297848456d5d37d1262630108ab308d3e9ec7ed1c3286a32fe09856619a782

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing
RUN apt-get -y install socat
COPY --from=0 / /srv
COPY run.sh /

RUN chmod 550 /run.sh

CMD socat -t180 -T180 TCP-L:9319,reuseaddr,fork EXEC:"./run.sh"
