import fastify from "fastify";
import crypto from "node:crypto";
import path from "node:path";

import db from "./db.js";

const app = fastify({});

app.register(await import('@fastify/static'), {
  root: path.join(import.meta.dirname, "public"),
})
app.register(await import("@fastify/formbody"));
app.register(await import("@fastify/cookie"));
app.register(await import("@fastify/session"), {
  secret: crypto.randomBytes(32).toString("base64"),
  cookie: { secure: false, httpOnly: false },
});

app.addHook("preHandler", (req, reply, next) => {
  const userId = req.session.get("userId") ??
    (() => {
      const user = db.createUser();
      req.session.set("userId", user.id);
      return user.id;
    })();

  req.user = db.getUser(userId);
  next();
});

app.get("/", (req, reply) => { reply.sendFile("index.html") });
app.get("/puzzle", (req, reply) => { reply.sendFile("puzzle.html") });

const schema = {
  body: {
    type: "object",
    properties: {
      title: { type: "string", maxLength: 100 },
      template: { type: "string", maxLength: 1000 },
      answers: { type: "string", minLength: 8, maxLength: 8 },
    },
    required: ["title", "template", "answers"],
  },
};

app.post("/create", { schema }, (req, reply) => {
  const title = req.body.title;
  const template = req.body.template.replaceAll("\r", "").replaceAll("\n", "");
  const answers = req.body.answers;

  const puzzle = db.createPuzzle(req.user, {
    title,
    template,
    answers,
  });

  return reply.redirect(`/puzzle?id=${puzzle.id}`);
});

app.get("/puzzles", (req, reply) => {
  reply.send(req.user.getPuzzles().map(({ id, title }) => ({ id, title })));
});

app.get("/puzzles/:id", (req, reply) => {
  const { id } = req.params;
  const puzzle = req.user.getPuzzles().find((puzzle) => puzzle.id === id);
  reply.send({ title: puzzle.title, template: puzzle.template, answers: puzzle.answers });
});

app.listen({ port: 3000, host: "0.0.0.0" });
