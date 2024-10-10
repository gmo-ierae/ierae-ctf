import crypto from "node:crypto";

class Note {
  #locals;

  constructor(title, body, style) {
    const id = crypto.randomBytes(16).toString("hex");
    this.#locals = {
      id,
      title,
      body,
      style,
    }
  }
  get id() {
    return this.#locals.id;
  }
  get title() {
    return this.#locals.title;
  }
  get body() {
    return this.#locals.body;
  }
  get style() {
    return this.#locals.style;
  }
}

class User {
  #locals;

  constructor() {
    const id = crypto.randomBytes(16).toString("hex");
    const notes = [];
    this.#locals = {
      id,
      notes,
    };
  }
  get id() {
    return this.#locals.id;
  }
  createNote(note) {
    this.#locals.notes.push(note);
  }
  getNotes() {
    return this.#locals.notes;
  }
}

class Db {
  #users;
  #notes;

  constructor() {
    // (userId: number) -> User
    this.#users = new Map();
    this.#notes = new Map();
  }
  createUser() {
    const user = new User();
    this.#users.set(user.id, user);
    return user;
  }
  getUser(id) {
    return this.#users.get(id);
  }
  createNote(user, { title, body, style }) {
    const note = new Note(title, body, style);
    user.createNote(note);
    this.#notes.set(note.id, note);
    return note;
  }
  getNote(id) {
    return this.#notes.get(id);
  }
}

export default new Db();
