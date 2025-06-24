import { redirect } from "react-router";
import type { Route } from "./+types/locale";
import { langDB } from "../utils/db";
import { getUser } from "../utils/auth";

export async function action({ request }: Route.ActionArgs) {
	const user = await getUser(request);
	const formData = await request.formData();
	const lang = formData.get("lang");
	if (!lang) {
		return redirect("/");
	}

	if (user && user.sub) {
		// save language preference
		langDB.set(user.sub, lang.toString());
	}
	return redirect(`/${lang}`);
};

export default function Locale() {
	return null;
}
