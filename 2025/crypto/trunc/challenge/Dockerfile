FROM sagemath/sagemath:10.6@sha256:19995db6194f4a4bab18ce9a88556fd15b9ed5e916b4504fefe618a7796ddbdb

USER sage
WORKDIR /app

COPY chal.sage ./chal.sage
COPY flag.txt  ./flag.txt

CMD ["sage", "chal.sage"]
