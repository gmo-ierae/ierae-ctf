import type { AccountData } from "./account.js";

// Type definitions for stored data
export interface AuthCodeData {
	accountId: string;
	clientId: string;
	redirectUri: string;
	scope: string;
	nonce?: string;
	expiresAt: number;
}

export interface TokenData {
	accountId: string;
	clientId: string;
	scope: string;
	expiresAt: number;
}

// In-memory stores for authorization codes, tokens, and sessions
export const authorizationCodes = new Map<string, AuthCodeData>();
export const accounts = new Map<string, AccountData>();

export default {
	authorizationCodes,
	accounts,
};
