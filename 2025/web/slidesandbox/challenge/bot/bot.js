import puppeteer from "puppeteer";

const APP_HOST = "web";
const APP_PORT = "3000";
export const APP_URL = `http://${APP_HOST}:${APP_PORT}`;

const FLAG = process.env.FLAG ?? console.log("No flag") ?? process.exit(1);

const sleep = async (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export const visit = async (url) => {
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
    console.log("Create a flag puzzle");
    const page1 = await context.newPage();
    await page1.goto(APP_URL, { timeout: 3000 });

    await page1.$eval("#new-title", (element, value) => element.value = value, FLAG);
    await page1.$eval("#new-template", element => element.value = `<style>
  body{
    background: linear-gradient( 135deg, #81FFEF 10%, #F067B4 100%);
  }
  h1{
    color: white;
    margin: 0;
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translateY(-50%) translateX(-50%);
    -webkit-transform: translateY(-50%) translateX(-50%);
  }
</style>
<body><h1>{{v}}</h1></body>`,
    );
    await page1.$eval("#new-answers", element => element.value = "slide!!!");

    await page1.waitForSelector("#new-button");
    await page1.click("#new-button");
    await sleep(1 * 1000);
    await page1.close();
    await sleep(1 * 1000);

    console.log(`start: ${url}`);
    const page2 = await context.newPage();
    await page2.goto(url, { timeout: 3000 });
    await sleep(5 * 1000);
    await page2.close();
    console.log(`end: ${url}`);
  } catch (e) {
    console.error(e);
  }

  await context.close();
  await browser.close();
};
