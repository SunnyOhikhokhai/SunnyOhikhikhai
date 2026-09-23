// Generates PWA/app icons, favicon PNGs, splash screens and the Open Graph
// image from the SVG brand mark. Run with: npm run icons
import { readFile, writeFile, mkdir } from "node:fs/promises";
import sharp from "sharp";

const mark = await readFile("public/brand/nipam-mark.svg");
const onDark = await readFile("public/brand/nipam-mark-on-dark.svg");
await mkdir("public/icons", { recursive: true });

const png = (svg, size) => sharp(svg, { density: 512 }).resize(size, size).png();

for (const size of [192, 512]) await png(mark, size).toFile(`public/icons/icon-${size}.png`);
await png(mark, 32).toFile("public/icons/favicon-32.png");
await png(mark, 180)
  .flatten({ background: "#063B66" })
  .toFile("public/apple-touch-icon.png");

// Maskable icon: full-bleed navy with the emblem inside the safe zone.
const maskable = await png(onDark, 340).toBuffer();
await sharp({ create: { width: 512, height: 512, channels: 4, background: "#063B66" } })
  .composite([{ input: maskable, gravity: "center" }])
  .png()
  .toFile("public/icons/maskable-512.png");

// iOS splash screens (navy with centred emblem).
for (const [w, h] of [[1170, 2532], [1290, 2796], [750, 1334], [1668, 2388]]) {
  const emblem = await png(onDark, Math.round(w * 0.34)).toBuffer();
  await sharp({ create: { width: w, height: h, channels: 4, background: "#063B66" } })
    .composite([{ input: emblem, gravity: "center" }])
    .png()
    .toFile(`public/icons/splash-${w}x${h}.png`);
}

// Open Graph image (1200x630).
const og = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#063B66"/><stop offset="1" stop-color="#04243F"/></linearGradient></defs>
  <rect width="1200" height="630" fill="url(#g)"/>
  <rect x="0" y="600" width="1200" height="30" fill="#079447"/>
  <text x="400" y="300" font-family="DejaVu Sans, Arial, sans-serif" font-size="120" font-weight="800" fill="#FFFFFF" letter-spacing="8">NIPAM</text>
  <text x="404" y="370" font-family="DejaVu Sans, Arial, sans-serif" font-size="30" fill="#CDEFDB">Non-Indigenes for Philip Aduda Movement</text>
  <text x="404" y="430" font-family="DejaVu Sans, Arial, sans-serif" font-size="24" fill="#D5D9DD">Community · Information · Participation — FCT, Nigeria</text>
</svg>`;
const emblem = await png(onDark, 260).toBuffer();
await sharp(Buffer.from(og))
  .composite([{ input: emblem, left: 90, top: 170 }])
  .png()
  .toFile("public/og-image.png");
await writeFile("public/icons/.generated", new Date().toISOString());
console.log("Icons generated.");
