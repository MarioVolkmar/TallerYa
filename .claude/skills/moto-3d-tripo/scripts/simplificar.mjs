// Simplifica la malla soldada cuidando normales y color (asi los bordes pintura/plastico quedan como aristas)
import fs from "node:fs";
import { MeshoptSimplifier as S } from "meshoptimizer";
const [d, objetivo, pesoN = "0.6", pesoC = "1.5"] = process.argv.slice(2);
const f32 = (n) => { const b = fs.readFileSync(`${d}/${n}`); return new Float32Array(b.buffer, b.byteOffset, b.length / 4); };
const pos = f32("w_pos.bin"), nor = f32("w_nor.bin"), col = f32("w_col.bin");
const bi = fs.readFileSync(`${d}/w_idx.bin`); const idx = new Uint32Array(bi.buffer, bi.byteOffset, bi.length / 4);
const nv = pos.length / 3;
const atr = new Float32Array(nv * 6);
for (let i = 0; i < nv; i++) { atr.set(nor.subarray(i * 3, i * 3 + 3), i * 6); atr.set(col.subarray(i * 3, i * 3 + 3), i * 6 + 3); }
await S.ready;
const pn = +pesoN, pc = +pesoC;
const t0 = Date.now();
let res;
try { res = S.simplifyWithAttributes(idx, pos, 3, atr, 6, [pn, pn, pn, pc, pc, pc], null, objetivo * 3, 1.0, ["Prune"]); }
catch (e) { console.log("sin Prune:", e.message); res = S.simplifyWithAttributes(idx, pos, 3, atr, 6, [pn, pn, pn, pc, pc, pc], null, objetivo * 3, 1.0, []); }
const [out, error] = res;
// compactar vertices
const mapa = new Int32Array(nv).fill(-1); let n = 0;
for (const i of out) if (mapa[i] < 0) mapa[i] = n++;
const P = new Float32Array(n * 3), N = new Float32Array(n * 3), C = new Float32Array(n * 3);
for (let i = 0; i < nv; i++) { const j = mapa[i]; if (j < 0) continue; for (let k = 0; k < 3; k++) { P[j*3+k] = pos[i*3+k]; N[j*3+k] = nor[i*3+k]; C[j*3+k] = col[i*3+k]; } }
const I = Uint32Array.from(out, (i) => mapa[i]);
const g = (n, a) => fs.writeFileSync(`${d}/${n}`, Buffer.from(a.buffer, a.byteOffset, a.byteLength));
g("s_pos.bin", P); g("s_nor.bin", N); g("s_col.bin", C); g("s_idx.bin", I);
console.log(`triangulos ${idx.length / 3} -> ${I.length / 3}, vertices ${n}, error ${error.toFixed(5)}, ${(Date.now() - t0) / 1000}s`);
