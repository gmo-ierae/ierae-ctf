FROM php:8.4.8-fpm-bullseye@sha256:c1067f8ce60c6fdfcfa252efd64613719f1093b5c4aa057b04e0da86aa1a09c5

RUN pecl install apcu \
    && docker-php-ext-enable apcu

COPY ./src /var/www

EXPOSE 9000
