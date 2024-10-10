import puppeteer from "puppeteer";

const APP_ADMIN_USERNAME = process.env.APP_ADMIN_USERNAME ?? console.log("No env") ?? process.exit(1);
const APP_ADMIN_PASSWORD = process.env.APP_ADMIN_PASSWORD ?? console.log("No env") ?? process.exit(1);

const APP_HOST = "web";
const APP_PORT = "5000";
const TIMEOUT_SECONDS = 50;
export const APP_URL = `http://${APP_HOST}:${APP_PORT}`;

const sleep = async (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const visit = async (url) => {
  console.log(`start: ${url}`);

  const browser = await puppeteer.launch({
    headless: "new",
    executablePath: "/usr/bin/chromium",
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      '--js-flags="--noexpose_wasm"',
    ],
  });

  const context = await browser.createBrowserContext();

  try {
    // Login with admin user
    const page = await context.newPage();
    await page.goto(`${APP_URL}/login`, { timeout: 3000 });
    await page.waitForSelector("#username");
    await page.type("#username", APP_ADMIN_USERNAME);
    await page.waitForSelector("#password");
    await page.type("#password", APP_ADMIN_PASSWORD);
    await page.click("button[type=submit]");
    await sleep(1 * 1000);

    await page.goto(url, { timeout: 3000 });
    await sleep(TIMEOUT_SECONDS * 1000);
    await page.close();
  } catch (e) {
    console.error(e);
  }

  await context.close();
  await browser.close();

  console.log(`end: ${url}`);
};
