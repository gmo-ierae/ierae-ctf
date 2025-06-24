import {
  Form,
  isRouteErrorResponse,
  Link,
  Links,
  Meta,
  Outlet,
  redirect,
  Scripts,
  ScrollRestoration,
  useLoaderData,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";
import { getUser } from "./utils/auth";
import { langDB } from "./utils/db";
import { useTranslation } from "./utils/translate";

export const links: Route.LinksFunction = () => [
	{ rel: "preconnect", href: "https://fonts.googleapis.com" },
	{
		rel: "preconnect",
		href: "https://fonts.gstatic.com",
		crossOrigin: "anonymous",
	},
	{
		rel: "stylesheet",
		href: "https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap",
	},
];

export function meta({}: Route.MetaArgs) {
	return [
		{ title: "Ojimemo👴" },
		{ name: "description", content: "Ojisan memo app" },
	];
};

export async function loader({ params, request }: Route.LoaderArgs) {
	let lang = params.lang;
	const user = await getUser(request);

	if (user && user.sub) {
		if (lang === undefined) {
			// use saved language preferences
			const newLang = langDB.get(user.sub) || "en";
			const path = new URL(request.url).pathname;
			return redirect(`/${newLang}${path}`);
		}
	} else {
		if (lang === undefined) {
			lang = "en";
		}
	}

	return { lang, user };
};

export function Layout({ children }: { children: React.ReactNode }) {
	const t = useTranslation();
	const { lang, user } = useLoaderData<typeof loader>();
	const langPrefix = lang ? `/${lang}` : "";

	return (
		<html lang="en">
			<head>
				<meta charSet="utf-8" />
				<meta name="viewport" content="width=device-width, initial-scale=1" />
				<Meta />
				<Links />
			</head>
			<body>
				<header className="bg-white dark:bg-gray-800 shadow">
					<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
						<div className="flex justify-between items-center">
							<h1 className="text-2xl font-bold text-gray-800 dark:text-gray-100">
								{t("ojimemo")}
							</h1>
							<div className="flex gap-4 items-center">
								<Form method="post" action="/locale">
									<select
										name="lang"
										value={lang || "en"}
										onChange={(e) => e.target.form?.submit()}
										className="bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded px-2 py-1"
									>
										<option value="en">English</option>
										<option value="ja">日本語</option>
									</select>
								</Form>
								{user ? (
									<>
										<span className="text-gray-600 dark:text-gray-300">
											{user.email}
										</span>
										<Link
											to={`${langPrefix}/logout`}
											className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
										>
											{t("logout")}
										</Link>
									</>
								) : (
									<Link
										to={`${langPrefix}/login`}
										className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
									>
										{t("login")}
									</Link>
								)}
							</div>
						</div>
					</div>
				</header>
				<main className="min-h-screen">{children}</main>
				<ScrollRestoration />
				<Scripts />
			</body>
		</html>
	);
}

export default function App() {
	return <Outlet />;
}
