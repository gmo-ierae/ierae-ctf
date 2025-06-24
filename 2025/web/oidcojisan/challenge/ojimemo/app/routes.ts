import { type RouteConfig, index, prefix, route } from "@react-router/dev/routes";

export default [
  ...prefix(":lang?", [
    index("./routes/home.tsx"),
    route("callback", "./routes/callback.tsx"),
    route("locale", "./routes/locale.tsx"),
    route("login", "./routes/login.tsx"),
    route("logout", "./routes/logout.tsx"),
  ]),
] satisfies RouteConfig;
