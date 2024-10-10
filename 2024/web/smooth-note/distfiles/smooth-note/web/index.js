import fastify from "fastify";
import ejs from "ejs";
import crypto from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

import db from "./db.js";

const PORT = 3000;
const app = fastify({});

app.register(await import('@fastify/static'), {
  root: path.join(path.dirname(fileURLToPath(import.meta.url)), 'public'),
  prefix: '/public/',
})
app.register(await import("@fastify/view"), {
  engine: { ejs },
  root: "./views",
});
app.register(await import("@fastify/formbody"));
app.register(await import("@fastify/cookie"));
app.register(await import("@fastify/session"), {
  secret: crypto.randomBytes(32).toString("base64"),
  cookie: { secure: false },
});

app.addHook("onRequest", (req, reply, next) => {
  reply.header(
    "Content-Security-Policy",
    `default-src 'none'; style-src 'self' 'unsafe-inline'; img-src *`
  );
  next();
});

app.addHook("preHandler", (req, reply, next) => {
  const userId =
    req.session.get("userId") ??
    (() => {
      const user = db.createUser();
      req.session.set("userId", user.id);
      return user.id;
    })();

  req.user = db.getUser(userId);
  next();
});

app.post("/create", (req, reply) => {
  const title = String(req.body.title);
  const body = String(req.body.body);
  const style = String(req.body.style);
  if (title.length > 100 || body.length > 1000 || style.length > 1000) {
    return reply.code(400).send("Too long parameters");
  }

  const note = db.createNote(req.user, {
    title, body, style
  });

  return reply.redirect(`/note/${note.id}`);
});

app.get("/note/:id", (req, reply) => {
  const { id } = req.params;
  const note = req.user.getNotes().find(note => note.id === id);
  reply.view("note.ejs", { note });
});

app.get("/", (req, reply) => {
  const search = String(req.query.search || '');
  if (search.length > 100) {
    return reply.code(400).send("Too long parameters");
  }

  const notes = req.user.getNotes().filter(note => {
    if (search) {
      return note.body.includes(search);
    }
    return true;
  });

  reply.view("index.ejs", { notes });
});

app.listen({ port: PORT, host: "0.0.0.0" });
