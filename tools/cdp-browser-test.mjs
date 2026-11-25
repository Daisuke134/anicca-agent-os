// Browser-level flattened CDP session test (runs on Mac via SSH).
const BASE = "http://127.0.0.1:9222";
setTimeout(() => { console.log("HARD-EXIT"); process.exit(2); }, 25000);
const version = await (await fetch(BASE + "/json/version")).json();
const ws = new WebSocket(version.webSocketDebuggerUrl);
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { const { res, rej, timer } = pending.get(d.id); clearTimeout(timer); pending.delete(d.id); d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result); }
  else if (d.method === "Target.attachedToTarget") { console.log("ATTACHED", d.params.sessionId); }
  else if (d.method) { /* ignore events */ }
};
const send = (method, params = {}, sessionId) => new Promise((res, rej) => { const i = ++id;
  const timer = setTimeout(() => { if (pending.has(i)) { pending.delete(i); rej(new Error("TIMEOUT " + method)); } }, 15000);
  pending.set(i, { res, rej, timer });
  ws.send(JSON.stringify({ id: i, method, params, sessionId })); });
await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
console.log("BROWSER-WS-OPEN");
const targets = await send("Target.getTargets");
const page = targets.targetInfos.find((t) => t.type === "page" && t.url.includes("example.com"));
console.log("PAGE-TARGET:", page ? page.targetId + " " + page.url : "none");
if (!page) { console.log("NO-PAGE"); process.exit(1); }
const { sessionId } = await send("Target.attachToTarget", { targetId: page.targetId, flatten: true });
console.log("SESSION:", sessionId);
const r = await send("Runtime.evaluate", { expression: "document.title + '|' + document.readyState", returnByValue: true }, sessionId);
console.log("EVAL-RESULT:", JSON.stringify(r.result && r.result.value));
process.exit(0);
