import puppeteer from "puppeteer";

const FLAG = process.env.FLAG ?? console.log("No flag") ?? process.exit(1);

const APP_HOST = "web";
const APP_PORT = "3000";
export const APP_URL = `http://${APP_HOST}:${APP_PORT}`;

// Flag format
if (!/^IERAE{[a-z]+}$/.test(FLAG) || FLAG.length > 20) {
  console.log("Bad flag");
  process.exit(1);
}

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
    // Create a flag note
    const page1 = await context.newPage();
    await page1.goto(APP_URL, { timeout: 3000 });
    await page1.waitForSelector("#show-form");
    await page1.click("#show-form");
    await sleep(0.5 * 1000);
    await page1.waitForSelector("#new-title");
    await page1.type("#new-title", "Secret Note");
    await page1.waitForSelector("#new-body");
    await page1.type("#new-body", FLAG);
    await page1.waitForSelector("#new-style");
    await page1.type("#new-style", "body { background-image: linear-gradient(to left, violet, indigo, blue, green, yellow, orange, red); }");
    await page1.waitForSelector("#new-button");
    await page1.click("#new-button");
    await sleep(1 * 1000);
    await page1.close();
    await sleep(1 * 1000);

    // Visit the given URL
    const page2 = await context.newPage();
    await page2.goto(url, { timeout: 3000 });
    await sleep(100 * 1000);
    await page2.close();
  } catch (e) {
    console.error(e);
  }

  await context.close();
  await browser.close();

  console.log(`end: ${url}`);
};
