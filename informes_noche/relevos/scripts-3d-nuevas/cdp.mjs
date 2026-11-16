// Chrome sin ventana con la sesión local; ejecuta una expresión JS en vista-3d (con el arnés cargado) y guarda
// la hoja (__hoja) como JPG si existe. Uso: node cdp.mjs salida.jpg "expresión que devuelve una promesa"
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
const DIR = path.dirname(new URL(import.meta.url).pathname).replace(/^\/(\w:)/, "$1");
const [salida, expr] = process.argv.slice(2);
const sesion = fs.readFileSync(path.join(DIR, "sesion.txt"), "utf8").trim();
const PUERTO = 9400 + Math.floor(Math.random() * 400);
const perfil = path.join(DIR, "chrome-perfil");
const chrome = spawn("C:/Program Files/Google/Chrome/Application/chrome.exe", [
  `--remote-debugging-port=${PUERTO}`, `--user-data-dir=${perfil}`, "--headless=new", "--window-size=1400,900",
  "--ignore-gpu-blocklist", "--enable-gpu", "--use-angle=d3d11", "--no-first-run", "about:blank"], { stdio: "ignore" });
const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
let ws;
for (let i = 0; i < 60 && !ws; i++) {
  await esperar(250);
  try { const l = await (await fetch(`http://127.0.0.1:${PUERTO}/json/list`)).json(); const p = l.find((x) => x.type === "page"); if (p) ws = p.webSocketDebuggerUrl; } catch {}
}
const sock = new WebSocket(ws);
await new Promise((r) => (sock.onopen = r));
let nid = 0; const pend = new Map();
sock.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); } };
const cdp = (method, params = {}) => new Promise((r) => { const id = ++nid; pend.set(id, r); sock.send(JSON.stringify({ id, method, params })); });
const evalua = async (e) => { const r = await cdp("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true }); return r.result?.result?.value ?? r.result?.exceptionDetails?.exception?.description; };
await cdp("Network.enable");
await cdp("Network.setCookie", { name: "sessionid", value: sesion, domain: "127.0.0.1", path: "/" });
await cdp("Page.enable");
await cdp("Page.navigate", { url: "http://127.0.0.1:8001/garaje/1/vista-3d/" + (process.env.Q || "") });
await esperar(4000);
await evalua(`(async()=>{for(const r of await navigator.serviceWorker.getRegistrations()) await r.unregister(); eval(await (await fetch("/media/_arnes3d.js",{cache:"no-store"})).text()); return 1})()`);
const res = await evalua(`(async()=>{ const v = await (${expr}); return typeof v === "string" ? v : JSON.stringify(v); })()`);
console.log(res);
if (salida && salida !== "-") {
  const url = await evalua(`document.getElementById("__hoja")?.toDataURL("image/jpeg",0.82)`);
  if (url) { fs.writeFileSync(salida, Buffer.from(url.split(",")[1], "base64")); console.log("hoja:", salida); }
}
sock.close(); chrome.kill();
process.exit(0);
