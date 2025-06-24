import crypto from "crypto";

// Define types for OIDC client configuration
export interface Client {
	clientId: string;
	clientSecret: string;
	redirectHost: string;
	responseTypes: string[];
	grantTypes: string[];
	scope: string;
}

export const PORT = process.env.PORT || 36001;

export const ISSUER =
	process.env.ISSUER || `http://ojiid.127-0-0-1.nip.io:${PORT}`;

// Generate a secure cookie key
export const COOKIE_KEY = crypto.randomBytes(32).toString("hex");

const CLIENT_HOST =
	process.env.CLIENT_HOST || "http://ojimemo.127-0-0-1.nip.io:36000";
export const CLIENTS: Client[] = [
	{
		clientId: "ojimemo",
		clientSecret: "ojimemo-secret",
		redirectHost: CLIENT_HOST,
		responseTypes: ["code"],
		grantTypes: ["authorization_code"],
		scope: "openid email profile",
	},
];

// Configuration
export const TTLS = {
	authorizationCode: 600, // 10 minutes
	accessToken: 3600, // 1 hour
	idToken: 3600, // 1 hour
	refreshToken: 1209600, // 14 days
};
