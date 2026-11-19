// Segunda pasada: cada pieza se simplifica con su propio presupuesto (las llantas y la mecánica oscura aguantan mucho
// más recorte que la pintura), con el borde bloqueado para que las piezas vecinas sigan casando sin rendijas.
import fs from "node:fs";
import { MeshoptSimplifier as S } from "meshoptimizer";
const d = process.argv[2];
const f32 = (n) => { const b = fs.readFileSync(`${d}/${n}`); return new Float32Array(b.buffer, b.byteOffset, b.length / 4); };
const pos = f32("c_pos.bin"), nor = f32("c_nor.bin"), col = f32("c_col.bin");
const bi = fs.readFileSync(`${d}/c_idx.bin`); const idx = new Uint32Array(bi.buffer, bi.byteOffset, bi.length / 4);
const bl = fs.readFileSync(`${d}/c_lab.bin`); const lab = new Int32Array(bl.buffer, bl.byteOffset, bl.length / 4);
const partes = JSON.parse(fs.readFileSync(`${d}/c_partes.json`, "utf8")).partes.map((p) => p.nombre);
let RAZON = [[/llanta/, 0.11], [/rin\./, 0.4], [/stop|faro|luz|ambar|mica|dorado|luna|reflector|posapies/, 1], [/visor|asiento/, 0.4], [/pintura|titanio/, 0.45],
  [/plastico\.(escudo|bajo)/, 0.27], [/./, 0.27]];
// (la ficha de la moto puede traer sus propias razones: ciclo.py las deja en razon.json)
if (fs.existsSync(`${d}/razon.json`)) RAZON = JSON.parse(fs.readFileSync(`${d}/razon.json`, "utf8")).map(([re, r]) => [new RegExp(re), r]);
await S.ready;
const nv = pos.length / 3;
const salidaIdx = [], salidaLab = [];
let antes = 0, despues = 0;
for (let k = 0; k < partes.length; k++) {
  const caras = [];
  for (let f = 0; f < lab.length; f++) if (lab[f] === k) caras.push(idx[f * 3], idx[f * 3 + 1], idx[f * 3 + 2]);
  if (!caras.length) continue;
  const razon = (RAZON.find(([re]) => re.test(partes[k])) || [0, 1])[1];
  let out = Uint32Array.from(caras);
  if (razon < 1 && caras.length > 600) {
    const objetivo = Math.floor(caras.length / 3 * razon) * 3;
    [out] = S.simplifyWithAttributes(out, pos, 3, nor, 3, [0.5, 0.5, 0.5], null, objetivo, 0.02, ["LockBorder"]);
  }
  antes += caras.length / 3; despues += out.length / 3;
  for (let i = 0; i < out.length; i += 3) { salidaIdx.push(out[i], out[i + 1], out[i + 2]); salidaLab.push(k); }
  console.log(partes[k].padEnd(32), String(caras.length / 3).padStart(6), "->", out.length / 3);
}
const mapa = new Int32Array(nv).fill(-1); let n = 0;
for (const i of salidaIdx) if (mapa[i] < 0) mapa[i] = n++;
const P = new Float32Array(n * 3), N = new Float32Array(n * 3), C = new Float32Array(n * 3);
for (let i = 0; i < nv; i++) { const j = mapa[i]; if (j < 0) continue; for (let c = 0; c < 3; c++) { P[j*3+c] = pos[i*3+c]; N[j*3+c] = nor[i*3+c]; C[j*3+c] = col[i*3+c]; } }
const g = (nombre, a) => fs.writeFileSync(`${d}/${nombre}`, Buffer.from(a.buffer, a.byteOffset, a.byteLength));
g("p_pos.bin", P); g("p_nor.bin", N); g("p_col.bin", C); g("p_idx.bin", Uint32Array.from(salidaIdx, (i) => mapa[i])); g("p_lab.bin", Int32Array.from(salidaLab));
console.log("total", antes, "->", despues, "vertices", n);
