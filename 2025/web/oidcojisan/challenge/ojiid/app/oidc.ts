import crypto from "crypto";
import * as jose from "jose";
import jwt from "jsonwebtoken";

import { getClaims } from "./account.js";
import { CLIENTS, type Client, ISSUER, TTLS } from "./config.js";
import db from "./db.js";

export interface AuthRequest {
	client_id: string;
	redirect_uri: string;
	state?: string;
	scope: string;
	response_type: string;
	nonce?: string;
}

export function generateToken() {
	// Generate a secure random token
	return crypto.randomBytes(32).toString("hex");
}

// Generate RSA key pair for JWT signing
export async function generateKeys() {
	const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
		modulusLength: 2048, // Required for RS256
		publicKeyEncoding: {
			type: "spki",
			format: "pem",
		},
		privateKeyEncoding: {
			type: "pkcs8",
			format: "pem",
		},
	});

	// Convert the keys to JWK format
	const privateJwk = await jose.importPKCS8(privateKey, "RS256", {
		extractable: true
	});
	const privateJwkExport = await jose.exportJWK(privateJwk);
	const privateJwkObj = {
		...privateJwkExport,
		kid: "ojiid-key",
		use: "sig",
		alg: "RS256",
	};

	return {
		keys: [privateJwkObj],
		publicKey,
		privateKey,
	};
}

// Helper functions
export function validateClient(clientId: string, clientSecret: string) {
	const client = CLIENTS.find((c) => c.clientId === clientId);
	if (!client) return false;
	if (client.clientSecret !== clientSecret) return false;
	return client;
}

export function validateRedirectUri(client: Client, checkUrl: string) {
	const redirectUrl = new URL(checkUrl);
	if (redirectUrl.origin !== client.redirectHost) {
		return false;
	}

	// Allow /callback, /en/callback and /ja/callback
	if (!/^\/([a-z]+\/)?callback$/.test(redirectUrl.pathname)) {
		return false;
	}

	return redirectUrl.href;
}

export async function generateIdToken(
	privateKey: string,
	sub: string,
	clientId: string,
	nonce?: string,
	scope?: string,
): Promise<string> {
	const claims = await getClaims(sub, scope || "openid");
	if (!claims) {
		throw new Error("User not found");
	}

	const payload = {
		...claims,
		nonce,
		iss: ISSUER,
		aud: clientId,
		exp: Math.floor(Date.now() / 1000) + TTLS.idToken,
		iat: Math.floor(Date.now() / 1000),
	};

	const token = jwt.sign(payload, privateKey, {
		algorithm: "RS256",
		keyid: "ojiid-key",
	});

	return token;
}

export function generateCallbackUrl(
	accountId: string,
	authRequest: AuthRequest,
) {
	// Generate authorization code
	const code = generateToken();

	// Store the authorization code with associated data
	db.authorizationCodes.set(code, {
		accountId,
		clientId: authRequest.client_id,
		redirectUri: authRequest.redirect_uri,
		scope: authRequest.scope,
		nonce: authRequest.nonce,
		expiresAt: Date.now() + TTLS.authorizationCode * 1000,
	});

	// Redirect back to client with authorization code
	const params = new URLSearchParams({
		code,
		...(authRequest.state && { state: authRequest.state }),
	});
	const redirectUrl = `${authRequest.redirect_uri}?${params}`;
	return redirectUrl;
}
