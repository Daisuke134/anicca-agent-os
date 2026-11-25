#!/usr/bin/env node
/* anicca-ops へ files/screenshot-consistency-gate-2026-11-17.md を Contents API で push し、
 * origin から読み戻してバイト一致を検証する。 */
const fs = require("fs");
const { execFileSync } = require("child_process");

const REPO = "Daisuke134/anicca-ops";
const PATH_IN_REPO = "files/screenshot-consistency-gate-2026-11-17.md";
const LOCAL = process.env.HOME + "/workspace/anicca-ops/files/screenshot-consistency-gate-2026-11-17.md";

const localBuf = fs.readFileSync(LOCAL);

function ghApi(args, input) {
  return execFileSync("gh", ["api", ...args], {
    input: input || undefined,
    maxBuffer: 64 * 1024 * 1024,
  });
}

// 既存ファイルの sha を取得 (無ければ null)
let sha = null;
try {
  const cur = JSON.parse(ghApi([`repos/${REPO}/contents/${PATH_IN_REPO}`, "--jq", "{sha: .sha}"]).toString());
  sha = cur.sha;
  console.log("existing sha:", sha);
} catch (e) {
  console.log("no existing file on origin (create)");
}

const body = {
  message: "gate: App Store screenshot cross-locale consistency gate spec + measured results 2026-11-17",
  content: localBuf.toString("base64"),
};
if (sha) body.sha = sha;
const res = JSON.parse(
  ghApi([`repos/${REPO}/contents/${PATH_IN_REPO}`, "-X", "PUT", "--input", "-"],
        Buffer.from(JSON.stringify(body))).toString());
console.log("pushed commit:", res.commit.sha);

// 読み戻し検証
const back = JSON.parse(ghApi([`repos/${REPO}/contents/${PATH_IN_REPO}`]).toString());
const backBuf = Buffer.from(back.content, "base64");
console.log("origin bytes:", backBuf.length, "local bytes:", localBuf.length);
console.log(backBuf.equals(localBuf) ? "READBACK: byte-identical" : "READBACK: MISMATCH");
