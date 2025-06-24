import crypto from "node:crypto";

class Puzzle {
  #locals;

  constructor(title, template, answers) {
    const id = crypto.randomBytes(16).toString("hex");
    this.#locals = {
      id,
      title,
      template,
      answers,
    }
  }
  get id() {
    return this.#locals.id;
  }
  get title() {
    return this.#locals.title;
  }
  get template() {
    return this.#locals.template;
  }
  get answers() {
    return this.#locals.answers;
  }
}

class User {
  #locals;

  constructor() {
    const id = crypto.randomBytes(16).toString("hex");
    const puzzles = [];
    this.#locals = {
      id,
      puzzles,
    };
  }
  get id() {
    return this.#locals.id;
  }
  createPuzzle(puzzle) {
    this.#locals.puzzles.push(puzzle);
  }
  getPuzzles() {
    return this.#locals.puzzles;
  }
}

class Db {
  #users;
  #puzzles;

  constructor() {
    // (userId: number) -> User
    this.#users = new Map();
    this.#puzzles = new Map();
  }
  createUser() {
    const user = new User();
    this.#users.set(user.id, user);
    return user;
  }
  getUser(id) {
    return this.#users.get(id);
  }
  createPuzzle(user, { title, template, answers }) {
    const puzzle = new Puzzle(title, template, answers);
    user.createPuzzle(puzzle);
    this.#puzzles.set(puzzle.id, puzzle);
    return puzzle;
  }
  getPuzzle(id) {
    return this.#puzzles.get(id);
  }
}

export default new Db();