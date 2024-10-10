const express = require("express");
const { createProxyMiddleware } = require("http-proxy-middleware");

const app = express();
const BACKEND = process.env.BACKEND;

app.use((req, res, next) => {
  if (req.url.indexOf("%") !== -1) {
    res.send("no hack :)");
  }
  if (req.url.indexOf("flag") !== -1) {
    res.send("🚩");
  }
  next();
});

app.get(
  "*",
  createProxyMiddleware({
    target: BACKEND,
  }),
);

app.listen(3000);
