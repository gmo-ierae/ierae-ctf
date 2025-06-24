import puppeteer from "puppeteer";
import crypto from "crypto";

const FLAG = process.env.FLAG ?? console.log("No FLAG") ?? process.exit(1);
export const APP_URL = process.env.APP_URL ?? console.log("No APP_URL") ?? process.exit(1);

// Flag format
if (!/^IERAE{\w+}$/.test(FLAG)) {
  console.log("Bad flag");
  process.exit(1);
}

const sleep = async (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const visit = async (url) => {
  console.log(`start: ${url}`);

  const RANDOM_USERNAME = crypto.randomBytes(16).toString('hex');
  const RANDOM_PASSWORD = crypto.randomBytes(16).toString('hex');
  console.log(`username: ${RANDOM_USERNAME}`);
  console.log(`password: ${RANDOM_PASSWORD}`);

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
    const page1 = await context.newPage();
    await page1.goto(APP_URL, { timeout: 3_000 });
    
    // Click login button
    await page1.waitForSelector("#login");
    await page1.click("#login");

    // Create user
    await page1.waitForSelector("#email");
    await page1.type("#email", `${RANDOM_USERNAME}@bot.test`);
    await page1.waitForSelector("#password");
    await page1.type("#password", RANDOM_PASSWORD);
    await page1.waitForSelector("#login");
    await page1.click("#login");

    // Input FLAG into memo and submit
    await page1.waitForSelector("#memo");
    await page1.type("#memo", FLAG);
    await page1.waitForSelector("#save-memo");
    await page1.click("#save-memo");

    await sleep(1_000);
    await page1.close();

    const page2 = await context.newPage();
    await page2.goto(url, { timeout: 5_000 });
    await sleep(5_000);
    await page2.close();
  } catch (e) {
    console.error(e);
  }

  await context.close();
  await browser.close();

  console.log(`end: ${url}`);
};
