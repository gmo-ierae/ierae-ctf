import type { Route } from "./+types/callback";
import { exchangeCodeForIdToken, sessionStorage } from "../utils/auth";
import { redirect } from "react-router";

export async function loader({ request, params }: Route.LoaderArgs) {
	// Get the authorization code from URL query parameters
	const url = new URL(request.url);
	const code = url.searchParams.get("code");
	
	if (!code) {
		console.error("No authorization code found in URL");
		return redirect("/");
	}
	
	// Exchange the code for an ID token and verify it
	console.log("Exchanging code for ID token...");
	const result = await exchangeCodeForIdToken(code, params.lang);
	
	if (result && result.sub) {
		// If successful, create a session with the user's sub
		console.log("Successfully obtained and verified ID token");
		
		// Create a new session
		const session = await sessionStorage.getSession();
		session.set("sub", result.sub);
		session.set("email", result.email);
	
		// Commit the session and redirect to home page
		return redirect("/", {
			headers: {
				"Set-Cookie": await sessionStorage.commitSession(session, {
					secure: false
				}),
			},
		});
	} else {
		// If the exchange failed, redirect to home page without setting a session
		console.error("Failed to exchange code for ID token");
		return redirect("/");
	}
};

export default function Callback() {
	return null;
}
