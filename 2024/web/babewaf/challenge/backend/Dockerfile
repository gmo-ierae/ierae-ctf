FROM denoland/deno

EXPOSE 3000
WORKDIR /app

USER deno
COPY . .
RUN deno cache main.ts
CMD deno task start