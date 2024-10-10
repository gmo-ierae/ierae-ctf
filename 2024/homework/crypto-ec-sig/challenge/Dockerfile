FROM openjdk:17.0.2

WORKDIR /crypto-ec-sig

RUN microdnf update && microdnf install socat

COPY Chall.java .
RUN javac Chall.java

EXPOSE 21449
CMD ["socat", "TCP-LISTEN:21449,reuseaddr,fork", "EXEC:'java -ea Chall'"]