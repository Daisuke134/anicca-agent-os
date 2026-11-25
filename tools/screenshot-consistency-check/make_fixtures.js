#!/usr/bin/env node
/* 合成フィクスチャ生成 (Node 版): 判定器の PASS/FAIL ロジック検証用。
 * 使い方: node make_fixtures.js <outdir>
 *   pass_a/, pass_b/ : 同一構造 (グリフ100px, バンド300px) → 合わせると PASS のはず
 *   fail_c/          : グリフ120px, バンド280px → FAIL のはず
 */
const fs = require("fs");
const path = require("path");
const zlib = require("zlib");

const BG = [114, 198, 239];
const INK = [17, 17, 17];
const W = 200, H = 600;

const crcTable = [];
for (let n = 0; n < 256; n++) {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  crcTable[n] = c >>> 0;
}
function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = crcTable[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}
function chunk(type, payload) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(payload.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), payload]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([len, body, crc]);
}
function writePng(file, img) {
  const stride = W * 3;
  const raw = Buffer.alloc(H * (stride + 1));
  for (let y = 0; y < H; y++) {
    raw[y * (stride + 1)] = 0;
    img.copy(raw, y * (stride + 1) + 1, y * stride, (y + 1) * stride);
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(W, 0);
  ihdr.writeUInt32BE(H, 4);
  ihdr[8] = 8; ihdr[9] = 2; // bit depth 8, color type 2 (RGB)
  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk("IHDR", ihdr),
    chunk("IDAT", zlib.deflateSync(raw)),
    chunk("IEND", Buffer.alloc(0)),
  ]);
  fs.writeFileSync(file, png);
}
function makeImage(glyphH, bandH) {
  const img = Buffer.alloc(W * H * 3);
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const i = (y * W + x) * 3;
      if (y >= bandH) {
        img[i] = (x * 7 + y) % 256; img[i + 1] = (x + y * 3) % 256; img[i + 2] = (x * 5 + y * 11) % 256;
      } else if ((y >= 50 && y < 50 + glyphH) || (y >= 190 && y < 190 + glyphH)) {
        const c = x >= 40 && x < 160 ? INK : BG;
        img[i] = c[0]; img[i + 1] = c[1]; img[i + 2] = c[2];
      } else {
        img[i] = BG[0]; img[i + 1] = BG[1]; img[i + 2] = BG[2];
      }
    }
  }
  return img;
}
const out = process.argv[2];
for (const [name, glyph, band] of [["pass_a", 100, 300], ["pass_b", 100, 300], ["fail_c", 120, 330]]) {
  const dir = path.join(out, name);
  fs.mkdirSync(dir, { recursive: true });
  const img = makeImage(glyph, band);
  for (const i of [1, 2]) writePng(path.join(dir, `shot_0${i}.png`), img);
  console.log(`${name}: glyph=${glyph} band=${band} -> ${dir}`);
}
