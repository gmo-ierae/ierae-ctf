import { redirect } from "react-router";
import type { Route } from "./+types/logout";
import { sessionStorage } from "../utils/auth";

export async function loader({ request }: Route.LoaderArgs) {
	// Get the current session
	const session = await sessionStorage.getSession(request.headers.get("Cookie"));
	
	// Destroy the session and redirect to home page
	return redirect("/", {
		headers: {
			"Set-Cookie": await sessionStorage.destroySession(session, {
				secure: false
			}),
		},
	});
};

export default function Logout() {
	return null;
}
