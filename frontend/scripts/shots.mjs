// Screenshots + horizontal-overflow check for the content pages (dev helper).
import { chromium } from "playwright-core";
const BASE = process.env.BASE ?? "http://localhost:5173";
const OUT = process.env.OUT ?? "/tmp/claude-shots";
const pages = (process.env.PAGES ?? "/,/philip-aduda,/our-record,/our-record/bwari-01-global-suite-road-sabon-gari,/legislation,/legislation/fct-water-board-bill,/elections,/news,/news/who-is-senator-philip-tanimu-aduda").split(",");
const widths = (process.env.WIDTHS ?? "390,1280").split(",").map(Number);
const browser = await chromium.launch({ executablePath: process.env.CHROME ?? "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
for (const w of widths) {
  const ctx = await browser.newContext({ viewport: { width: w, height: 900 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  for (const p of pages) {
    await page.goto(BASE + p, { waitUntil: "networkidle" });
    await page.waitForTimeout(400);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    const name = `${w}-${p.replace(/\W+/g, "_") || "home"}.png`;
    await page.screenshot({ path: `${OUT}/${name}`, fullPage: true });
    console.log(w, p, overflow > 0 ? `OVERFLOW ${overflow}px` : "ok");
  }
  if (errors.length) console.log("errors:", errors.slice(0, 5));
  await ctx.close();
}
await browser.close();
