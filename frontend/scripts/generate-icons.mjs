// Generates PWA/app icons, favicons, splash screens and the Open Graph image
// from the official NIMPA logo (public/brand/nimpa-mark.png and nimpa-logo.png,
// produced by scripts/prepare-logo.mjs). Run with: npm run icons
import { mkdir, writeFile } from "node:fs/promises";
import sharp from "sharp";

const MARK = "public/brand/nimpa-mark.png";
const LOGO = "public/brand/nimpa-logo.png";
const WHITE = { r: 255, g: 255, b: 255, alpha: 1 };
await mkdir("public/icons", { recursive: true });

/** The emblem centred on a square canvas, `scale` of the side, on `background`. */
async function icon(size, scale, background = { r: 0, g: 0, b: 0, alpha: 0 }) {
  const inner = await sharp(MARK).resize(Math.round(size * scale)).toBuffer();
  return sharp({ create: { width: size, height: size, channels: 4, background } }).composite([{ input: inner, gravity: "center" }]).png();
}

await (await icon(32, 1)).toFile("public/icons/favicon-32.png");
await (await icon(48, 1)).toFile("public/favicon.png");
for (const size of [192, 512]) await (await icon(size, 0.92, WHITE)).toFile(`public/icons/icon-${size}.png`);
await (await icon(180, 0.86, WHITE)).flatten({ background: "#FFFFFF" }).toFile("public/apple-touch-icon.png");
// Maskable icon: emblem inside the central safe zone.
await (await icon(512, 0.7, WHITE)).toFile("public/icons/maskable-512.png");

// iOS splash screens: full logo centred on white.
for (const [w, h] of [[1170, 2532], [1290, 2796], [750, 1334], [1668, 2388]]) {
  const logo = await sharp(LOGO).resize({ width: Math.round(w * 0.7) }).toBuffer();
  await sharp({ create: { width: w, height: h, channels: 4, background: WHITE } })
    .composite([{ input: logo, gravity: "center" }])
    .png()
    .toFile(`public/icons/splash-${w}x${h}.png`);
}

// Open Graph image (1200x630): full logo on white with a green base line.
const logo = await sharp(LOGO).resize({ height: 560 }).toBuffer({ resolveWithObject: true });
await sharp({ create: { width: 1200, height: 630, channels: 4, background: WHITE } })
  .composite([
    { input: logo.data, top: 24, left: Math.round((1200 - logo.info.width) / 2) },
    { input: { create: { width: 1200, height: 16, channels: 4, background: "#079447" } }, top: 614, left: 0 },
  ])
  .flatten({ background: "#FFFFFF" })
  .png()
  .toFile("public/og-image.png");

await writeFile("public/icons/.generated", new Date().toISOString());
console.log("Icons generated.");
