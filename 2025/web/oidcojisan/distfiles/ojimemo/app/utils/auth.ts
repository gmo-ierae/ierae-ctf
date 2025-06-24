import * as jose from "jose";
import { createCookieSessionStorage } from "react-router";
import {
	OIDC_CLIENT,
	OIDC_HOST,
	APP_HOST,
} from "./config";
import crypto from "crypto";

// Create a session storage
export const sessionStorage = createCookieSessionStorage({
	cookie: {
		name: "ojimemo_session",
		httpOnly: true,
		path: "/",
		sameSite: "lax",
		secrets: [ crypto.randomBytes(16).toString('hex') ],
		secure: process.env.NODE_ENV === "production",
	},
});

/**
 * Exchange an authorization code for an ID token
 * @param code The authorization code from the OIDC provider
 * @returns The verified ID token payload or null if the exchange fails
 */
export async function exchangeCodeForIdToken(code: string, lang: string | undefined): Promise<jose.JWTPayload | null> {
	try {
		// Prepare token request
		const tokenEndpoint = `${OIDC_HOST}/token`;
		// Use the same redirect URI as in the login route
		const langPrefix = lang ? `/${lang}` : "";
		const redirectUri = `${APP_HOST}${langPrefix}/callback`;
		
		const tokenRequest = new URLSearchParams();
		tokenRequest.append("grant_type", "authorization_code");
		tokenRequest.append("client_id", OIDC_CLIENT);
		tokenRequest.append("client_secret", "ojimemo-secret");
		tokenRequest.append("code", code);
		tokenRequest.append("redirect_uri", redirectUri);
		
		// Exchange code for tokens
		const response = await fetch(tokenEndpoint, {
			method: "POST",
			headers: {
				"Content-Type": "application/x-www-form-urlencoded",
			},
			body: tokenRequest,
		});
		
		if (!response.ok) {
			const reason = await response.text();
			throw new Error(`Token request failed: ${response.status} ${response.statusText} ${reason}`);
		}
		
		const tokens = await response.json();
		const idToken = tokens.id_token;
		
		if (!idToken) {
			console.error("No ID token received in the token response");
			return null;
		}
		
		// Verify the ID token
		const JWKS = jose.createRemoteJWKSet(
			new URL(
				`/jwks`,
				OIDC_HOST,
			),
		);

		const { payload } = await jose.jwtVerify(idToken, JWKS, {
			issuer: OIDC_HOST,
			audience: OIDC_CLIENT,
		});
		
		// Only return the sub claim from the payload
		if (!payload.sub) {
			console.error("No sub claim in ID token payload");
			return null;
		}
		
		return payload
	} catch (e) {
		console.error("Error exchanging code for token or verifying token:", e);
		return null;
	}
}

/**
 * Get user information from the session
 * @param request The incoming request
 * @returns The user information or null if not authenticated
 */
export async function getUser(request: Request) {
	const session = await sessionStorage.getSession(request.headers.get("Cookie"));
	const sub: string = session.get("sub");
	
	if (!sub) {
		return null;
	}
	
	// Return a payload-like object with the sub claim
	// This maintains compatibility with the existing code
	return {
		sub,
		email: session.get("email") as string,
	};
}
