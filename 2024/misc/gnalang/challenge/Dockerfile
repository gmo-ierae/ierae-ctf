FROM ubuntu:23.10@sha256:fd7fe639db24c4e005643921beea92bc449aac4f4d40d60cd9ad9ab6456aec01

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing
RUN apt-get -y install python3 npm sudo curl
RUN npm install n -g
RUN n stable
RUN apt-get purge -y nodejs npm && apt-get autoremove -y
RUN groupadd -r ctf && useradd -r -g ctf ctf

COPY ./sudo-as-nobody /etc/sudoers.d/

WORKDIR /home/ctf
COPY ./flag.txt .
COPY ./chal.py .
RUN chmod 550 ./chal.py ./flag.txt
RUN chmod -R go-w .

# Disable write to /tmp
RUN chmod -R o-w /tmp /var/tmp
RUN chown -R root:ctf /home/ctf /tmp

# Use chroot to disable write to /dev
FROM ubuntu:23.10@sha256:fd7fe639db24c4e005643921beea92bc449aac4f4d40d60cd9ad9ab6456aec01

RUN apt-get -y update --fix-missing
RUN apt-get -y upgrade
RUN apt-get -y update --fix-missing
RUN apt-get -y install socat
COPY --from=0 / /srv
COPY run.sh /

CMD socat TCP-L:9319,reuseaddr,fork EXEC:"./run.sh"
