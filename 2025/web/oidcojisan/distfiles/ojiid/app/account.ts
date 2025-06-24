import crypto from "crypto";

import db from "./db.js";

// Type definitions for account data
export interface AccountData {
	id: string;
	email: string;
	password: string;
}

export interface Claims {
	sub: string;
	email?: string;
}

function findById(id: string) {
	for (const account of db.accounts.values()) {
		if (account.id === id) {
			return account;
		}
	}
	return null;
}
function calcPasswordHash(password: string) {
	return crypto.createHash("sha256").update(password, "utf-8").digest("hex");
}

export async function getClaims(
	id: string,
	_scope: string,
): Promise<Claims | null> {
	const account = findById(id);

	if (!account) {
		return null;
	}

	const claims: Claims = {
		sub: id,
		email: account.email,
	};

	return claims;
}

export async function authenticate(
	email: string,
	password: string,
): Promise<string | null> {
	const account = db.accounts.get(email);

	if (!account) {
		return null;
	}
	if (account.password !== calcPasswordHash(password)) {
		return null;
	}

	return account.id;
}

export async function createAccount(
	email: string,
	password: string,
): Promise<string | null> {
	if (db.accounts.has(email)) {
		return null;
	}

	const id = crypto.randomUUID();

	db.accounts.set(email, {
		id,
		email,
		password: calcPasswordHash(password),
	});

	return id;
}
