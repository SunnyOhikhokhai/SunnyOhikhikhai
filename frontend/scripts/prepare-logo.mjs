// Turns the official NIMPA logo (white background) into the transparent web
// assets the site uses. Run with: node scripts/prepare-logo.mjs [source image]
// then `npm run icons` to rebuild favicons, app icons and the share image.
import { mkdir } from "node:fs/promises";
import sharp from "sharp";

const SRC = process.argv[2] ?? "brand-source/nimpa-logo-original.webp";
// Regions of the 1536×1024 source artwork.
const EMBLEM = { left: 430, top: 27, width: 690, height: 531 };

/** Make the white background transparent, keeping soft anti-aliased edges. */
async function whiteToAlpha(input) {
  const { data, info } = await sharp(input).removeAlpha().raw().toBuffer({ resolveWithObject: true });
  const out = Buffer.alloc(info.width * info.height * 4);
  for (let p = 0, q = 0; p < data.length; p += 3, q += 4) {
    const r = data[p], g = data[p + 1], b = data[p + 2];
    const light = Math.min(r, g, b);
    // Fully opaque below 205, fully transparent above 248, smooth in between.
    const a = Math.max(0, Math.min(1, (248 - light) / 43));
    const un = (c) => (a > 0 ? Math.max(0, Math.min(255, Math.round((c - (1 - a) * 255) / a))) : 0);
    out[q] = un(r);
    out[q + 1] = un(g);
    out[q + 2] = un(b);
    out[q + 3] = Math.round(a * 255);
  }
  return sharp(out, { raw: { width: info.width, height: info.height, channels: 4 } }).png();
}

await mkdir("public/brand", { recursive: true });

const full = await (await whiteToAlpha(SRC)).toBuffer();
await sharp(full).trim({ threshold: 1 }).extend({ top: 24, bottom: 24, left: 24, right: 24, background: { r: 0, g: 0, b: 0, alpha: 0 } })
  .png({ compressionLevel: 9, palette: true, quality: 95 }).toFile("public/brand/nimpa-logo.png");

const emblem = await (await whiteToAlpha(await sharp(SRC).extract(EMBLEM).toBuffer())).toBuffer();
const trimmed = await sharp(emblem).trim({ threshold: 1 }).toBuffer({ resolveWithObject: true });
const side = Math.max(trimmed.info.width, trimmed.info.height);
// sharp resizes before extending within one pipeline, so square it first.
const square = await sharp(trimmed.data)
  .extend({
    top: Math.floor((side - trimmed.info.height) / 2),
    bottom: Math.ceil((side - trimmed.info.height) / 2),
    left: Math.floor((side - trimmed.info.width) / 2),
    right: Math.ceil((side - trimmed.info.width) / 2),
    background: { r: 0, g: 0, b: 0, alpha: 0 },
  })
  .png()
  .toBuffer();
await sharp(square).resize(512, 512).png({ compressionLevel: 9, palette: true, quality: 95 }).toFile("public/brand/nimpa-mark.png");

console.log("Wrote public/brand/nimpa-logo.png and public/brand/nimpa-mark.png");
