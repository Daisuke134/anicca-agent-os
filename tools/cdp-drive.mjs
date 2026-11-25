// Minimal CDP driver (Node >= 22, global WebSocket). Runs on the Mac via SSH.
// Adds a 20s timeout per CDP call and forces process exit so a wedged
// renderer can never hang the caller.
import fs from "node:fs";
setTimeout(() => { console.log("HARD-EXIT-30s"); process.exit(2); }, 30000);
const BASE = "http://127.0.0.1:9222";
async function jget(p) { const r = await fetch(BASE + p); return r.json(); }
async function list() { return jget("/json/list"); }
async function newTab(url) {
  const r = await fetch(BASE + "/json/new?" + new URLSearchParams({ url }), { method: "PUT" });
  return r.json();
}
class Sess {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.id = 0;
    this.pending = new Map();
    this.ready = new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = (e) => rej(new Error("WS-ERROR " + (e.message || "connect failed")));
      setTimeout(() => rej(new Error("WS-CONNECT-TIMEOUT")), 15000);
    });
    this.ws.onmessage = (m) => {
      const d = JSON.parse(m.data);
      if (d.id && this.pending.has(d.id)) {
        const { res, rej, timer } = this.pending.get(d.id);
        clearTimeout(timer);
        this.pending.delete(d.id);
        d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result);
      }
    };
    this.ws.onclose = () => {
      for (const [id, { rej, timer }] of this.pending) {
        clearTimeout(timer);
        this.pending.delete(id);
        rej(new Error("WS-CLOSED"));
      }
    };
  }
  async send(method, params = {}) {
    await this.ready;
    const id = ++this.id;
    return new Promise((res, rej) => {
      const timer = setTimeout(() => {
        if (this.pending.has(id)) { this.pending.delete(id); rej(new Error("CDP-TIMEOUT " + method)); }
      }, 20000);
      this.pending.set(id, { res, rej, timer });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
  async eval(expr, awaitPromise = false) {
    const r = await this.send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise });
    if (r.exceptionDetails) throw new Error("JS EX: " + JSON.stringify(r.exceptionDetails).slice(0, 500));
    return r.result ? r.result.value : undefined;
  }
  close() { try { this.ws.close(); } catch {} }
}
async function attachByUrlMatch(substr) {
  const ts = await list();
  const t = ts.find((x) => x.type === "page" && x.url.includes(substr));
  if (!t) throw new Error("no page matching " + substr);
  const s = new Sess(t.webSocketDebuggerUrl);
  await s.ready;
  return { s, t };
}
const cmd = process.argv[2];
try {
  if (cmd === "list") { console.log(JSON.stringify(await list(), null, 1)); }
  else if (cmd === "new") { console.log(JSON.stringify(await newTab(process.argv[3] || "about:blank"))); }
  else if (cmd === "close") {
    const ts = await list();
    const t = ts.find((x) => x.type === "page" && x.url.includes(process.argv[3]));
    if (!t) throw new Error("no page matching " + process.argv[3]);
    const r = await fetch(BASE + "/json/close/" + t.id);
    console.log("close " + t.id + " -> " + r.status);
  }
  else if (cmd === "eval") {
    const { s } = await attachByUrlMatch(process.argv[3]);
    try { const v = await s.eval(process.argv[4]); console.log(typeof v === "string" ? v : JSON.stringify(v)); }
    finally { s.close(); }
  }
  else if (cmd === "shot") {
    const { s } = await attachByUrlMatch(process.argv[3]);
    try {
      await s.send("Page.enable");
      const r = await s.send("Page.captureScreenshot", { format: "jpeg", quality: 80 });
      fs.writeFileSync(process.argv[4], Buffer.from(r.data, "base64"));
      console.log("saved " + process.argv[4]);
    } finally { s.close(); }
  }
  else if (cmd === "raw") {
    const { s } = await attachByUrlMatch(process.argv[3]);
    try { const r = await s.send(process.argv[4], JSON.parse(process.argv[5] || "{}")); console.log(JSON.stringify(r).slice(0, 2000)); }
    finally { s.close(); }
  }
  else { console.log("usage: list|new <url>|close <urlmatch>|eval <urlmatch> <js>|shot <urlmatch> <file>|raw <urlmatch> <method> <json>"); }
} catch (e) {
  console.log("ERR: " + (e.message || e));
  process.exitCode = 1;
}
setTimeout(() => process.exit(process.exitCode || 0), 500);
