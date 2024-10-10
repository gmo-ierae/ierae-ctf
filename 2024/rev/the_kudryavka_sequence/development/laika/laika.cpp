#include <windows.h>
#include <bcrypt.h>
#include <stdio.h>
#include <intrin.h>
#include "resource.h"

#pragma comment(lib, "bcrypt.lib")

#define AES_KEY_SIZE 32  // 256 bits
#define AES_BLOCK_SIZE 16  // 128 bits (CBC block size)
#define NT_SUCCESS(Status) (((NTSTATUS)(Status)) >= 0)
#define STATUS_UNSUCCESSFUL ((NTSTATUS)0xC0000001)

void AES_Encrypt(
	PBYTE pbKey,
	DWORD cbKey,
	PBYTE pbIV,
	DWORD cbIV,
	PBYTE pbData,
	DWORD cbData,
	PBYTE* ppbEncryptedData,
	DWORD* pcbEncryptedData
) {
	BCRYPT_ALG_HANDLE hAlgorithm = NULL;
	BCRYPT_KEY_HANDLE hKey = NULL;
	NTSTATUS status = STATUS_UNSUCCESSFUL;
	DWORD cbCipherText = 0;
	DWORD cbResult = 0;
	PBYTE pbCipherText = NULL;

	status = BCryptOpenAlgorithmProvider(
		&hAlgorithm,
		BCRYPT_AES_ALGORITHM,
		NULL,
		0
	);
	if (!NT_SUCCESS(status)) {
		fprintf(stderr, "Error: BCryptOpenAlgorithmProvider\n");
		exit(1);
	}

	status = BCryptSetProperty(
		hAlgorithm,
		BCRYPT_CHAINING_MODE,
		(PBYTE)BCRYPT_CHAIN_MODE_CBC,
		sizeof(BCRYPT_CHAIN_MODE_CBC),
		0
	);
	if (!NT_SUCCESS(status)) {
		fprintf(stderr, "Error: BCryptSetProperty\n");
		exit(1);
	}

	status = BCryptGenerateSymmetricKey(
		hAlgorithm,
		&hKey,
		NULL,
		0,
		pbKey,
		cbKey,
		0
	);
	if (!NT_SUCCESS(status)) {
		fprintf(stderr, "Error: BCryptGenerateSymmetricKey\n");
		exit(1);
	}

	status = BCryptEncrypt(
		hKey,
		pbData,
		cbData,
		NULL,
		pbIV,
		cbIV,
		NULL,
		0,
		&cbCipherText,
		BCRYPT_BLOCK_PADDING
	);
	if (!NT_SUCCESS(status)) {
		fprintf(stderr, "Error: BCryptEncrypt (get size)\n");
		exit(1);
	}

	pbCipherText = (PBYTE)HeapAlloc(GetProcessHeap(), 0, cbCipherText);
	if (pbCipherText == NULL) {
		fprintf(stderr, "Error: HeapAlloc\n");
		exit(1);
	}

	status = BCryptEncrypt(
		hKey,
		pbData,
		cbData,
		NULL,
		pbIV,
		cbIV,
		pbCipherText,
		cbCipherText,
		&cbResult,
		BCRYPT_BLOCK_PADDING
	);
	if (!NT_SUCCESS(status)) {
		fprintf(stderr, "Error: BCryptEncrypt\n");
		exit(1);
	}

	*ppbEncryptedData = pbCipherText;
	*pcbEncryptedData = cbResult;

	if (hKey) {
		BCryptDestroyKey(hKey);
	}
	if (hAlgorithm) {
		BCryptCloseAlgorithmProvider(hAlgorithm, 0);
	}
}

void readFlagFile(BYTE** pFileData, DWORD* pFileSize) {
	HANDLE hFile = CreateFile(L"flag.png", GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
	if (hFile == INVALID_HANDLE_VALUE) {
		fprintf(stderr, "Error: CreateFile\n");
		exit(1);
	}

	DWORD dwFileSize = GetFileSize(hFile, NULL);
	if (dwFileSize == INVALID_FILE_SIZE) {
		fprintf(stderr, "Error: GetFileSize\n");
		CloseHandle(hFile);
		exit(1);
	}

	PBYTE fileData = (PBYTE)HeapAlloc(GetProcessHeap(), 0, dwFileSize);
	if (fileData == NULL) {
		fprintf(stderr, "Error: HeapAlloc\n");
		CloseHandle(hFile);
		exit(1);
	}
	DWORD dwBytesRead;
	if (!ReadFile(hFile, fileData, dwFileSize, &dwBytesRead, NULL)) {
		fprintf(stderr, "Error: ReadFile\n");
		CloseHandle(hFile);
		exit(1);
	}

	CloseHandle(hFile);

	*pFileData = fileData;
	*pFileSize = dwFileSize;
}

DWORD randRange(DWORD min, DWORD max) {
	DWORD randValue = rand();
	randValue *= rand();
	randValue *= rand();
	return min + randValue / (MAXDWORD32 / (max - min + 1) + 1);
}

void shuffleEncryptedData(BYTE* data, DWORD size) {
	for (DWORD i = 0; i < size; i++) {
		DWORD j = randRange(0, size - 1);
		BYTE temp = data[i];
		data[i] = data[j];
		data[j] = temp;
	}
}

void erazeFlagFile() {
	HANDLE hFile = CreateFile(L"flag.png", GENERIC_WRITE, 0, NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
	if (hFile == INVALID_HANDLE_VALUE) {
		fprintf(stderr, "Error: CreateFile\n");
		exit(1);
	}

	DWORD dwFileSize = GetFileSize(hFile, NULL);
	if (dwFileSize == INVALID_FILE_SIZE) {
		fprintf(stderr, "Error: GetFileSize\n");
		CloseHandle(hFile);
		exit(1);
	}

	BYTE* buffer = (BYTE*)HeapAlloc(GetProcessHeap(), 0, dwFileSize);
	if (buffer == NULL) {
		fprintf(stderr, "Error: HeapAlloc\n");
		CloseHandle(hFile);
		exit(1);
	}
	memset(buffer, 0, dwFileSize);

	DWORD dwBytesWritten;
	if (!WriteFile(hFile, buffer, dwFileSize, &dwBytesWritten, NULL)) {
		fprintf(stderr, "Error: WriteFile\n");
		CloseHandle(hFile);
		HeapFree(GetProcessHeap(), 0, buffer);
		exit(1);
	}

	CloseHandle(hFile);
	HeapFree(GetProcessHeap(), 0, buffer);

	DeleteFile(L"flag.png");
}

void dropStatement() {
	HRSRC hRes = FindResource(NULL, MAKEINTRESOURCE(IDB_IMAGE1), L"PNG");
	if (hRes == NULL) {
		fprintf(stderr, "Error: FindResource\n");
		exit(1);
	}

	HGLOBAL hResData = LoadResource(NULL, hRes);
	if (hResData == NULL) {
		fprintf(stderr, "Error: LoadResource\n");
		exit(1);
	}

	DWORD dwSize = SizeofResource(NULL, hRes);
	if (dwSize == 0) {
		fprintf(stderr, "Error: SizeofResource\n");
		exit(1);
	}

	LPVOID pResData = LockResource(hResData);
	if (pResData == NULL) {
		fprintf(stderr, "Error: LockResource\n");
		exit(1);
	}

	HANDLE hFile = CreateFile(L"statement.png", GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
	if (hFile == INVALID_HANDLE_VALUE) {
		fprintf(stderr, "Error: CreateFile\n");
		exit(1);
	}

	DWORD dwWritten;
	BOOL bResult = WriteFile(hFile, pResData, dwSize, &dwWritten, NULL);
	CloseHandle(hFile);
}

int main() {
	BYTE key[AES_KEY_SIZE] = { 0x00 };
	BYTE iv[AES_BLOCK_SIZE] = { 0x00 };

	PBYTE fileData = NULL;
	DWORD dwBytesRead = 0;
	readFlagFile(&fileData, &dwBytesRead);

#ifdef _DEBUG
	printf("File data:\n");
	for (DWORD i = 0; i < 0x200; i++) {
		printf("%02x ", fileData[i]);
	}
	printf("\n");
#else
	erazeFlagFile();
#endif

	dropStatement();

	SYSTEMTIME st;
	GetLocalTime(&st);
	unsigned int seed = 1;
	seed = seed * 131243 + st.wYear;
	seed = seed * 131243 + st.wMonth;
	seed = seed * 131243 + st.wDayOfWeek;
	seed = seed * 131243 + st.wDay;
	seed = seed * 131243 + st.wHour;
	seed = seed * 131243 + st.wMinute;
	seed = seed * 131243 + st.wSecond;
	seed = seed * 131243 + st.wMilliseconds;
	srand(seed);

	for (DWORD i = 0; i < sizeof(key); i++) {
		key[i] = rand() % 256;
	}

	for (DWORD i = 0; i < sizeof(iv); i++) {
		iv[i] = rand() % 256;
	}

#ifdef _DEBUG
	printf("Key: ");
	for (DWORD i = 0; i < sizeof(key); i++) {
		printf("%02x ", key[i]);
	}
	printf("\n");

	printf("IV: ");
	for (DWORD i = 0; i < sizeof(iv); i++) {
		printf("%02x ", iv[i]);
	}
	printf("\n");
#endif

	PBYTE encryptedData = NULL;
	DWORD encryptedDataSize = 0;
	AES_Encrypt(
		key,
		sizeof(key),
		iv,
		sizeof(iv),
		fileData,
		dwBytesRead,
		&encryptedData,
		&encryptedDataSize
	);

	shuffleEncryptedData(encryptedData, encryptedDataSize);

#ifdef _DEBUG
	printf("Encrypted data:\n");
	for (DWORD i = 0; i < 0x200; i++) {
		printf("%02x ", encryptedData[i]);
	}
	printf("\n");
#endif

	HANDLE hEncryptedFile = CreateFile(L"flag.png.laika", GENERIC_WRITE, 0, NULL, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
	if (hEncryptedFile == INVALID_HANDLE_VALUE) {
		fprintf(stderr, "Error: CreateFile\n");
		exit(1);
	}

	DWORD dwBytesWritten;
	if (!WriteFile(hEncryptedFile, encryptedData, encryptedDataSize, &dwBytesWritten, NULL)) {
		fprintf(stderr, "Error: WriteFile\n");
		CloseHandle(hEncryptedFile);
		exit(1);
	}

	CloseHandle(hEncryptedFile);

	if (encryptedData) {
		HeapFree(GetProcessHeap(), 0, encryptedData);
	}
	if (fileData) {
		HeapFree(GetProcessHeap(), 0, fileData);
	}

	return 0;
}
