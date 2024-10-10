FROM python:3.9-slim@sha256:0079b018ed406019db5398f7a24749a498052dba4916cefb58f98d56fede839f

ARG APP_ADMIN_USERNAME
ARG APP_ADMIN_PASSWORD
ENV APP_ADMIN_USERNAME=${APP_ADMIN_USERNAME}
ENV APP_ADMIN_PASSWORD=${APP_ADMIN_PASSWORD}

WORKDIR /app

COPY ./app /app
RUN pip install --no-cache-dir -r requirements.txt && flask seeds

CMD ["gunicorn", "--workers", "8", "--worker-class", "gevent", "--bind", "0.0.0.0:5000", "app:app"]
