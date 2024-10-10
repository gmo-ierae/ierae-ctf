FROM ruby:3.2-bookworm

WORKDIR /app

RUN apt update && apt install -y default-mysql-server
RUN mkdir -p /run/mysqld

COPY ./app/Gemfile ./app/Gemfile.lock /app/
RUN bundle install

COPY ./app /app

ENTRYPOINT ["./docker-entrypoint.sh"]
