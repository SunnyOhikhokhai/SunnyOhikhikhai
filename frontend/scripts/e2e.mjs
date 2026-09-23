// End-to-end smoke test of the main member and admin flows in a real browser.
//   BASE=http://localhost:5173 npm run e2e
// Requires the API running with NIPAM_DEV_EXPOSE_OTP=true and demo seed data.
import { existsSync, readdirSync, mkdirSync } from "node:fs";
import { chromium } from "playwright-core";

const BASE = process.env.BASE ?? "http://localhost:5173";
const SHOTS = process.env.SHOTS ?? "e2e-screens";
const ADMIN = { email: process.env.ADMIN_EMAIL ?? "admin@nipam.local", password: process.env.ADMIN_PASSWORD ?? "ChangeMe!Admin2026" };
mkdirSync(SHOTS, { recursive: true });

function browserPath() {
  if (process.env.CHROMIUM_PATH) return process.env.CHROMIUM_PATH;
  const root = "/opt/pw-browsers";
  if (existsSync(root)) {
    const dir = readdirSync(root).find((d) => /^chromium-\d+/.test(d));
    if (dir) return `${root}/${dir}/chrome-linux/chrome`;
  }
  return undefined;
}

const browser = await chromium.launch({ executablePath: browserPath(), args: ["--no-sandbox"] });
const errors = [];
let step = 0;
async function newPage(width = 390) {
  const ctx = await browser.newContext({ viewport: { width, height: 844 } });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));
  page.on("console", (m) => m.type() === "error" && !/status of 4\d\d/.test(m.text()) && errors.push(`console: ${m.text()}`));
  await page.addInitScript(() => localStorage.setItem("nipam-cookie-notice", "1"));
  return page;
}
async function check(name, fn, page) {
  step++;
  try {
    await fn();
    console.log(`✓ ${step}. ${name}`);
    if (page) await page.screenshot({ path: `${SHOTS}/${String(step).padStart(2, "0")}-${name.replace(/\W+/g, "-").toLowerCase()}.png` });
  } catch (e) {
    console.error(`✗ ${step}. ${name}\n   ${e.message.split("\n")[0]}`);
    if (page) await page.screenshot({ path: `${SHOTS}/FAILED-${step}.png`, fullPage: true });
    await browser.close();
    process.exit(1);
  }
}
const devCode = async (page) => (await page.locator("code").last().innerText()).trim();

// ---------------------------------------------------------------- member flow
const email = `e2e-${Date.now()}@example.com`;
const phoneTail = String(Date.now()).slice(-7);
const m = await newPage(390);

await check("Home renders on mobile", async () => {
  await m.goto(BASE);
  await m.getByRole("heading", { level: 1, name: /NIPAM/ }).waitFor();
  await m.getByRole("button", { name: "Open menu" }).click();
  await m.getByRole("dialog").getByRole("link", { name: "Join NIPAM" }).click();
}, m);

await check("Registration step 1 — personal information", async () => {
  await m.getByLabel("Full name").fill("Chidinma E2E Test");
  await m.getByLabel("Email address").fill(email);
  await m.getByLabel(/Phone number/).fill(`0809${phoneTail}`);
  await m.getByLabel("Password", { exact: true }).fill("E2eStrongPass1");
  await m.getByLabel("Confirm password").fill("E2eStrongPass1");
  await m.getByRole("button", { name: "Continue" }).click();
  await m.getByText("Which FCT Area Council do you reside in?").waitFor();
}, m);

await check("Registration step 2 — Area Council", async () => {
  await m.getByText("Kuje", { exact: true }).click();
  await m.getByRole("checkbox").click();
  await m.getByRole("button", { name: "Create account" }).click();
  await m.getByText("Email verification").waitFor();
}, m);

await check("Registration step 3 — verification (email + phone OTP)", async () => {
  const code = (await m.locator("code").first().innerText()).trim();
  await m.getByLabel("Enter the 6-digit code").fill(code);
  await m.getByRole("button", { name: "Verify email" }).click();
  await m.getByText("Email verified").first().waitFor();
  const sms = m.getByLabel("Enter the code sent by SMS");
  if (await sms.count()) {
    await sms.fill(await devCode(m));
    await m.getByRole("button", { name: "Verify phone" }).click();
    await m.getByText("Phone number verified").first().waitFor();
  }
  await m.getByRole("button", { name: "Continue" }).click();
}, m);

await check("Registration step 4 — consent → dashboard", async () => {
  await m.getByText("Event notifications", { exact: true }).first().waitFor();
  await m.getByRole("checkbox").first().click();
  await m.getByRole("button", { name: /Finish/ }).click();
  await m.getByRole("heading", { name: /Welcome, Chidinma/ }).waitFor();
  await m.getByText("Kuje Area Council").first().waitFor();
}, m);

await check("Logout and log back in", async () => {
  await m.getByRole("button", { name: "Account menu" }).click();
  await m.getByRole("menuitem", { name: "Log out" }).click();
  await m.goto(`${BASE}/login`);
  await m.getByLabel("Email or phone number").fill(email);
  await m.getByLabel("Password", { exact: true }).fill("E2eStrongPass1");
  await m.getByRole("button", { name: "Log in" }).click();
  await m.getByRole("heading", { name: /Welcome, Chidinma/ }).waitFor();
}, m);

await check("Area Council page tabs", async () => {
  await m.goto(`${BASE}/area-councils/kuje`);
  await m.getByRole("heading", { name: "Kuje Area Council" }).waitFor();
  await m.getByRole("tab", { name: /Projects\/Records/ }).click();
  await m.getByText("[Sample] Community Health Centre Record").waitFor();
}, m);

await check("Our Record — filter, list view and detail", async () => {
  await m.goto(`${BASE}/our-record`);
  await m.getByRole("button", { name: /Filters/ }).click();
  await m.locator('select[aria-label="Category"]:visible').selectOption("roads");
  await m.getByText("1 record").waitFor();
  await m.getByRole("button", { name: "list view" }).click();
  await m.getByRole("link", { name: /Rural Road Access/ }).click();
  await m.getByRole("heading", { name: "Sources & references" }).waitFor();
  await m.getByText("[SOURCE TO BE ADDED]").waitFor();
}, m);

await check("News list and article", async () => {
  await m.goto(`${BASE}/news`);
  await m.getByRole("link", { name: "Welcome to the NIPAM community platform" }).first().click();
  await m.getByText("Published by").waitFor();
}, m);

let eventUrl;
await check("Events — register for an event", async () => {
  await m.goto(`${BASE}/events`);
  await m.getByRole("link", { name: /Community Town Hall/ }).click();
  await m.getByRole("button", { name: "Register" }).click();
  await m.getByText("You're registered").first().waitFor();
  eventUrl = m.url();
}, m);

await check("Events — calendar view", async () => {
  await m.goto(`${BASE}/events?view=calendar`);
  await m.getByRole("grid").waitFor();
}, m);

let threadUrl;
await check("Community — start a discussion and comment", async () => {
  await m.goto(`${BASE}/community`);
  await m.getByRole("button", { name: "Start a discussion" }).click();
  await m.getByLabel("Title").fill("Improving street lighting in Kuje");
  await m.getByLabel("Your post").fill("How can residents best work together to report and follow up on street lighting issues?");
  await m.getByRole("button", { name: "Post discussion" }).click();
  await m.getByRole("heading", { name: "Improving street lighting in Kuje" }).waitFor();
  threadUrl = m.url();
  await m.getByLabel("Write a comment").fill("Starting with a list of affected streets would help.");
  await m.getByRole("button", { name: "Post comment" }).click();
  await m.getByText("Starting with a list of affected streets").waitFor();
  await m.getByRole("button", { name: "Like" }).first().click();
}, m);

await check("Notifications centre", async () => {
  await m.goto(`${BASE}/notifications`);
  await m.getByText(/You're registered/).first().waitFor();
  await m.getByRole("button", { name: "Mark all as read" }).click();
  await m.getByText("0 unread").waitFor();
}, m);

await check("Settings — notification preferences", async () => {
  await m.goto(`${BASE}/settings?tab=notifications`);
  await m.getByText("Communication preferences").waitFor();
}, m);

await check("Global search", async () => {
  await m.goto(`${BASE}/search?q=kuje`);
  await m.getByRole("heading", { name: /Area Councils/ }).waitFor();
}, m);

// A second member reports the discussion so the admin can moderate it.
const r = await newPage(1280);
await check("Second member reports the discussion", async () => {
  await r.goto(`${BASE}/login`);
  await r.getByLabel("Email or phone number").fill("member@nipam.local");
  await r.getByLabel("Password", { exact: true }).fill("Member!Demo2026");
  await r.getByRole("button", { name: "Log in" }).click();
  await r.getByRole("heading", { name: /Welcome, Demo/ }).waitFor();
  await r.goto(threadUrl);
  await r.getByRole("button", { name: "Report" }).first().click();
  await r.getByText("Spam", { exact: true }).click();
  await r.getByRole("button", { name: "Submit report" }).click();
  await r.getByText(/moderator will review/).waitFor();
}, r);

await check("Member logout", async () => {
  await m.getByRole("button", { name: "Account menu" }).click();
  await m.getByRole("menuitem", { name: "Log out" }).click();
  await m.getByText("logged out securely").waitFor();
}, m);

// ----------------------------------------------------------------- admin flow
const a = await newPage(1440);
await check("Admin login → overview", async () => {
  await a.goto(`${BASE}/login`);
  await a.getByLabel("Email or phone number").fill(ADMIN.email);
  await a.getByLabel("Password", { exact: true }).fill(ADMIN.password);
  await a.getByRole("button", { name: "Log in" }).click();
  await a.getByRole("heading", { name: /Welcome, NIPAM/ }).waitFor();
  await a.getByText("Membership growth").waitFor();
}, a);

await check("Admin — members search and detail", async () => {
  await a.getByRole("link", { name: "Members" }).click();
  await a.getByPlaceholder("Name, email or phone").fill("Chidinma");
  await a.getByRole("button", { name: "View" }).first().click();
  await a.getByText("Communication preferences").waitFor();
  await a.keyboard.press("Escape");
}, a);

await check("Admin — create, source and publish a record", async () => {
  await a.getByRole("link", { name: "Our Record" }).click();
  await a.getByRole("link", { name: "New record" }).click();
  await a.getByLabel("Project / action title").fill("E2E test record");
  await a.getByLabel("Short description").fill("Created by the end-to-end test.");
  await a.getByRole("button", { name: "Add source" }).click();
  await a.getByLabel("Source title").fill("Test gazette");
  await a.locator("#r-ver").selectOption("verified");
  await a.getByRole("button", { name: "Save" }).click();
  await a.getByRole("button", { name: "Publish" }).click();
  await a.getByText("Record published").waitFor();
}, a);

await check("Admin — draft and publish news", async () => {
  await a.getByRole("link", { name: "News" }).click();
  await a.getByRole("link", { name: "New article" }).click();
  await a.getByLabel("Title").fill("E2E Kuje update");
  await a.locator("#n-council").selectOption("kuje");
  await a.getByRole("button", { name: "Save draft" }).click();
  await a.getByRole("button", { name: "Publish" }).click();
  await a.getByText(/Published/).first().waitFor();
}, a);

await check("Admin — create and publish an event", async () => {
  await a.getByRole("link", { name: "Events" }).click();
  await a.getByRole("link", { name: "New event" }).click();
  await a.getByLabel("Event title").fill("E2E Forum");
  await a.getByLabel("Starts (WAT)").fill("2030-05-01T10:00");
  await a.getByLabel("Location").fill("Kuje");
  await a.getByRole("button", { name: "Save" }).click();
  await a.getByRole("button", { name: "Publish" }).click();
  await a.getByText(/members notified/).waitFor();
}, a);

await check("Admin — moderation: resolve the report", async () => {
  await a.getByRole("link", { name: "Moderation" }).click();
  await a.getByText("Improving street lighting in Kuje").first().waitFor();
  await a.getByRole("button", { name: "Dismiss" }).first().click();
  await a.getByText("Report resolved").waitFor();
}, a);

await check("Admin — analytics", async () => {
  await a.getByRole("link", { name: "Analytics" }).click();
  await a.getByText("Content engagement").waitFor();
  await a.getByText("Popular records").waitFor();
}, a);

await check("Admin — audit log", async () => {
  await a.getByRole("link", { name: "Audit log" }).click();
  await a.getByText("record.published").first().waitFor();
}, a);

await browser.close();
if (errors.length) {
  console.error("\nBrowser errors:\n" + [...new Set(errors)].join("\n"));
  process.exit(1);
}
console.log(`\nAll ${step} end-to-end checks passed. Screenshots in ${SHOTS}/`);
