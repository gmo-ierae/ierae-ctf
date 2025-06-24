import { redirect } from "react-router";
import type { Route } from "./+types/login";
import {
	OIDC_HOST,
	OIDC_CLIENT,
	APP_HOST,
} from "../utils/config";
import crypto from "crypto";

export async function loader({ params }: Route.LoaderArgs) {
	const authUrl = `${OIDC_HOST}/auth`;
	const langPrefix = params.lang ? `/${params.lang}` : "";
	const redirectUri = `${APP_HOST}${langPrefix}/callback`;

	const authParams = new URLSearchParams({
		client_id: OIDC_CLIENT,
		redirect_uri: redirectUri,
		response_type: "code",
		scope: "openid email profile",
		nonce: crypto.randomBytes(16).toString("hex"),
	});

	return redirect(`${authUrl}?${authParams.toString()}`);
}

export default function Login() {
	return null;
}
