// Main server file for the custom OIDC provider
import path from "node:path";
import bodyParser from "body-parser";
import express, { type Request, type Response } from "express";
import session from "express-session";

import { authenticate, createAccount } from "./account.js";
import { CLIENTS, COOKIE_KEY, ISSUER, PORT, TTLS } from "./config.js";
import db from "./db.js";
import {
	type AuthRequest,
	generateCallbackUrl,
	generateIdToken,
	generateKeys,
	generateToken,
	validateClient,
	validateRedirectUri,
} from "./oidc.js";

// Define types for session
declare module "express-session" {
	interface SessionData {
		accountId?: string;
		authRequest?: AuthRequest;
	}
}

// Create Express app
const app = express();

// Set up middleware
app.use(express.static(path.join(import.meta.dirname, "..", "public")));
app.use(bodyParser.urlencoded({ extended: false }));
app.use(
	session({
		secret: COOKIE_KEY,
		resave: true,
		saveUninitialized: true,
		cookie: {
			httpOnly: true,
			secure: false,
			sameSite: "lax",
			maxAge: 24 * 60 * 60 * 1000, // 24 hours
		},
	}),
);

// Set up views
app.set("views", path.join(import.meta.dirname, "..", "views"));
app.set("view engine", "ejs");

// JWKS keys will be set after server starts
let keys: Awaited<ReturnType<typeof generateKeys>> | null = null;

// Login endpoint
app.get("/login", async (req: Request, res: Response) => {
	const { client_id, redirect_uri, state, scope, response_type, nonce } =
		req.query as {
			client_id?: string;
			redirect_uri?: string;
			state?: string;
			scope?: string;
			response_type?: string;
			nonce?: string;
		};

	// Validate client
	if (!client_id) {
		res.status(400).json({
			error: "invalid_request",
			error_description: "Missing client_id parameter",
		});
		return;
	}

	const client = CLIENTS.find((c) => c.clientId === client_id);
	if (!client) {
		res
			.status(400)
			.json({ error: "invalid_client", error_description: "Client not found" });
		return;
	}

	// Validate redirect URI
	if (!redirect_uri) {
		res.status(400).json({
			error: "invalid_request",
			error_description: "Missing redirect_uri parameter",
		});
		return;
	}

	const redirectUrl = validateRedirectUri(client, redirect_uri);
	if (!redirectUrl) {
		res.status(400).json({
			error: "invalid_redirect_uri",
			error_description: "Invalid redirect URI",
		});
		return;
	}

	// Store the auth request parameters in the session
	req.session.authRequest = {
		client_id,
		redirect_uri: redirectUrl,
		state,
		scope: scope || "openid",
		response_type: response_type || "code",
		nonce,
	};

	// Check if user is already logged in
	if (req.session.accountId) {
		console.log(
			"User already logged in with accountId:",
			req.session.accountId,
		);

		// User is already logged in, generate authorization code and redirect
		const accountId = req.session.accountId;
		const authRequest = req.session.authRequest;

		if (!authRequest) {
			res.status(400).json({
				error: "invalid_request",
				error_description: "No authentication request found",
			});
			return;
		}
		req.session.authRequest = undefined;

		const redirectUrl = generateCallbackUrl(accountId, authRequest);
		res.redirect(redirectUrl);
		return;
	}

	// User is not logged in, show login page
	res.render("login");
});

// Login submission
app.post("/login", async (req, res) => {
	console.log("Login submission - Session before:", req.session);

	const { email, password } = req.body as { email: string; password: string };

	// Authenticate user
	let accountId = await authenticate(email, password);
	if (!accountId) {
		// Try register account if not found
		accountId = await createAccount(email, password);
	}

	if (!accountId) {
		res.render("login", {
			error: "Invalid email or password",
		});
		return;
	}

	// Save the accountId in the session
	req.session.accountId = accountId;

	// Get auth request from session
	const authRequest = req.session.authRequest;
	if (!authRequest) {
		res.render("login", {
			error: "No authentication request found",
		});
		return;
	}
	req.session.authRequest = undefined;

	// Force session save
	req.session.save((err) => {
		if (err) {
			console.error("Error saving session:", err);
		}
	});

	const redirectUrl = generateCallbackUrl(accountId, authRequest);
	res.redirect(redirectUrl);
});

// Authorization endpoint
app.get("/auth", (req: Request, res: Response) => {
	const { client_id, redirect_uri, state, scope, response_type, nonce } =
		req.query as {
			client_id?: string;
			redirect_uri?: string;
			state?: string;
			scope?: string;
			response_type?: string;
			nonce?: string;
		};

	// Validate required parameters
	if (!client_id || !redirect_uri || !response_type) {
		res.status(400).json({
			error: "invalid_request",
			error_description: "Missing required parameters",
		});
		return;
	}

	// Validate client
	const client = CLIENTS.find((c) => c.clientId === client_id);
	if (!client) {
		res
			.status(400)
			.json({ error: "invalid_client", error_description: "Client not found" });
		return;
	}

	// Validate redirect URI
	if (!validateRedirectUri(client, redirect_uri)) {
		res.status(400).json({
			error: "invalid_redirect_uri",
			error_description: "Invalid redirect URI",
		});
		return;
	}

	// Validate response type
	if (response_type !== "code") {
		res.status(400).json({
			error: "unsupported_response_type",
			error_description: "Only code response type is supported",
		});
		return;
	}

	// Redirect to login page
	const params = new URLSearchParams({
		client_id,
		redirect_uri,
		state: state || "",
		scope: scope || "openid",
		response_type,
		nonce: nonce || "",
	});
	res.redirect(`/login?${params.toString()}`);
});

// Token endpoint
app.post("/token", async (req: Request, res: Response) => {
	// Get client credentials from request body
	const clientId = req.body.client_id as string;
	const clientSecret = req.body.client_secret as string;

	if (!clientId || !clientSecret) {
		res.status(400).json({
			error: "invalid_request",
			error_description: "Missing client credentials",
		});
		return;
	}

	// Validate client
	const client = validateClient(clientId, clientSecret);
	if (!client) {
		res.status(401).json({
			error: "invalid_client",
			error_description: "Invalid client credentials",
		});
		return;
	}

	// Handle different grant types
	const grantType = req.body.grant_type as string;

	if (grantType === "authorization_code") {
		const code = req.body.code as string;

		// Validate code
		if (!code || !db.authorizationCodes.has(code)) {
			res.status(400).json({
				error: "invalid_grant",
				error_description: "Invalid authorization code",
			});
			return;
		}

		// Get code data
		const codeData = db.authorizationCodes.get(code);

		if (!codeData) {
			res.status(400).json({
				error: "invalid_grant",
				error_description: "Authorization code data not found",
			});
			return;
		}

		// Validate code expiration
		if (codeData.expiresAt < Date.now()) {
			db.authorizationCodes.delete(code);
			res.status(400).json({
				error: "invalid_grant",
				error_description: "Authorization code expired",
			});
			return;
		}

		// Validate client ID
		if (codeData.clientId !== clientId) {
			res.status(400).json({
				error: "invalid_grant",
				error_description: "Authorization code was not issued to this client",
			});
			return;
		}

		// Generate access token
		const accessToken = generateToken();

		// Generate ID token
		if (keys === null) {
			res.status(500).json({
				error: "server_error",
				error_description: "Server is not ready",
			});
			return;
		}
		const idToken = await generateIdToken(
			keys.privateKey,
			codeData.accountId,
			clientId,
			codeData.nonce,
			codeData.scope,
		);

		// Delete used authorization code
		db.authorizationCodes.delete(code);

		res.json({
			access_token: accessToken,
			token_type: "Bearer",
			expires_in: TTLS.accessToken,
			id_token: idToken,
		});
	} else {
		res.status(400).json({
			error: "unsupported_grant_type",
			error_description: "Unsupported grant type",
		});
		return;
	}
});

// JWKS endpoint
app.get("/jwks", (_req: Request, res: Response) => {
	// Return the public keys in JWKS format
	res.json({
		keys: keys?.keys.map((key) => {
			// Remove private key components for public JWKS
			// eslint-disable-next-line @typescript-eslint/no-unused-vars
			const { d, p, q, dp, dq, qi, ...publicKey } = key;
			return publicKey;
		}),
	});
});

// Start the server
async function startServer(): Promise<void> {
	try {
		// Generate keys
		keys = await generateKeys();

		// Start the server
		app.listen(PORT, () => {
			console.log(`OIDC Provider listening on port ${PORT}`);
			console.log(`OIDC Provider issuer: ${ISSUER}`);
		});
	} catch (error) {
		console.error("Failed to start server:", error);
		process.exit(1);
	}
}

// Start the server
startServer().catch((err) => {
	console.error("Fatal error during startup:", err);
	process.exit(1);
});
