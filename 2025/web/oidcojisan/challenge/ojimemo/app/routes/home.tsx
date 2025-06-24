import { Form, Link, redirect, useLoaderData, useRouteLoaderData } from "react-router";
import type { Route } from "./+types/home";
import type { Info } from "../+types/root";
import { getUser } from "../utils/auth";
import { memoDB } from "../utils/db";
import { useTranslation } from "../utils/translate";

export async function loader({ request }: Route.LoaderArgs) {
	const user = await getUser(request);
	if (user && user.sub) {
		// Retrieve the memo for the user
		const memo = memoDB.get(user.sub);
		return { memo };
	}

	return {};
};

export async function action({ request }: Route.ActionArgs) {
	const user = await getUser(request);
	if (!user || !user.sub) {
		return null;
	}

	const formData = await request.formData();
	const memo = formData.get("memo");
	memoDB.set(user.sub, memo?.toString() || "");

	return redirect("/");
};

export default function Index() {
	const { user } = useRouteLoaderData<Info["loaderData"]>("root") || {};
	const { memo } = useLoaderData<typeof loader>();
	const t = useTranslation();

	return (
		<div className="flex h-screen items-center justify-center">
			<div className="flex flex-col items-center gap-8">
				<header className="flex flex-col items-center gap-4">
					<img src="/logo.png" alt="OJIMEMO Logo" className="w-32 h-32 mb-4" />
				</header>
				{user ? (
					<Form method="post" className="w-full max-w-md">
						<div className="flex flex-col gap-4">
							<textarea
								id="memo"
								name="memo"
								defaultValue={memo}
								className="w-full p-2 border rounded-md"
								placeholder={t("memo.placeholder")}
								rows={4}
							/>
							<button
								id="save-memo"
								type="submit"
								className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
							>
								{t("save")}
							</button>
						</div>
					</Form>
				) : (
					<div className="text-center">
						<p className="text-gray-600 dark:text-gray-300 mb-4">
							{t("memo.login.warning")}
						</p>
						<Link
							to="/login"
							id="login"
							className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
						>
							{t("memo.login")}
						</Link>
					</div>
				)}
			</div>
		</div>
	);
}
