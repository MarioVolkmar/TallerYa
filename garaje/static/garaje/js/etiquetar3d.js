// Etiquetado de las partes de un GLB de Tripo (solo staff). Cada parte se ilumina, se elige su pieza y su acabado
// (prellenados con sugerencias) y se guarda en garaje/etiquetas_3d/<modelo>.json, que alimenta el glosario.
// Sugerencias, en orden: etiqueta ya guardada → nombre de la parte → parte parecida del glosario (posición y forma
// dentro de la moto) → reglas de forma (llantas, luces, motor). Cada parte se pinta con el color de su acabado.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const yo = document.querySelector("script[data-glb]");
const D = JSON.parse(document.getElementById("et3d-datos").textContent);
const $ = (id) => document.getElementById(id);
const NOMBRE_PIEZA = Object.fromEntries(D.piezas), NOMBRE_ACABADO = Object.fromEntries(D.acabados);

// ---------- Lectura del GLB (cualquier GLB: flotante o cuantizado, con jerarquía; sin texturas) ----------
async function leerGlb(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`GLB ${r.status}`);
  const buf = await r.arrayBuffer(), dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x46546c67) throw new Error("no es GLB");
  const largo = dv.getUint32(12, true);
  const g = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, largo)));
  const base = 20 + largo + 8;
  const TIPOS = { 5120: Int8Array, 5121: Uint8Array, 5122: Int16Array, 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };
  const NC = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4 };
  const leer = (i) => {
    const a = g.accessors[i], bv = g.bufferViews[a.bufferView], T = TIPOS[a.componentType], c = NC[a.type];
    const paso = (bv.byteStride || T.BYTES_PER_ELEMENT * c) / T.BYTES_PER_ELEMENT;
    const arr = new T(buf, base + (bv.byteOffset || 0) + (a.byteOffset || 0), (a.count - 1) * paso + c);
    const esc = a.normalized ? { 5120: 127, 5121: 255, 5122: 32767, 5123: 65535 }[a.componentType] || 1 : 1;
    const out = c === 1 ? new Uint32Array(a.count) : new Float32Array(a.count * c);
    for (let k = 0; k < a.count; k++) for (let j = 0; j < c; j++) out[k * c + j] = c === 1 ? arr[k * paso] : Math.max(arr[k * paso + j] / esc, -1);
    return out;
  };
  const partes = [];
  const visitar = (i, padre) => {
    const n = g.nodes[i], m = new THREE.Matrix4();
    if (n.matrix) m.fromArray(n.matrix);
    else m.compose(new THREE.Vector3(...(n.translation || [0, 0, 0])), new THREE.Quaternion(...(n.rotation || [0, 0, 0, 1])), new THREE.Vector3(...(n.scale || [1, 1, 1])));
    m.premultiply(padre);
    if (n.mesh !== undefined) {
      const pos = [], idx = []; let o = 0;
      for (const pr of g.meshes[n.mesh].primitives) {
        if (pr.mode !== undefined && pr.mode !== 4) continue;
        const p = leer(pr.attributes.POSITION), cuenta = p.length / 3;
        pos.push(p);
        const ii = pr.indices !== undefined ? leer(pr.indices) : Uint32Array.from({ length: cuenta }, (_, k) => k);
        idx.push(ii.map((v) => v + o)); o += cuenta;
      }
      if (o) {
        const geo = new THREE.BufferGeometry();
        const todo = new Float32Array(o * 3); let k = 0; for (const p of pos) { todo.set(p, k); k += p.length; }
        const ind = new Uint32Array(idx.reduce((s, a) => s + a.length, 0)); k = 0; for (const a of idx) { ind.set(a, k); k += a.length; }
        geo.setAttribute("position", new THREE.BufferAttribute(todo, 3));
        geo.setIndex(new THREE.BufferAttribute(ind, 1));
        geo.applyMatrix4(m);
        geo.computeVertexNormals();
        partes.push({ nombre: n.name || g.meshes[n.mesh].name || `parte_${partes.length + 1}`, geo });
      }
    }
    for (const h of n.children || []) visitar(h, m);
  };
  const escena = g.scenes?.[g.scene || 0];
  for (const i of escena ? escena.nodes : g.nodes.map((_, i) => i)) visitar(i, new THREE.Matrix4());
  // (nombres repetidos: se numeran, la etiqueta se guarda por nombre)
  const vistos = {};
  for (const p of partes) { vistos[p.nombre] = (vistos[p.nombre] || 0) + 1; if (vistos[p.nombre] > 1) p.nombre += `#${vistos[p.nombre]}`; }
  return partes;
}

// ---------- Sugerencias ----------
// Por nombre: los GLB del visor nombran «material.pieza» (caucho.llanta_del, luz.faro_a…); los de Tripo, a veces, algo legible.
const REGLAS_NOMBRE = [
  [/llanta_?del|tire_?f|front_?tire/, "llanta_del", "caucho"], [/llanta_?tras|tire_?r|rear_?tire/, "llanta_tras", "caucho"],
  [/rin_?del/, "rin_del", "aluminio"], [/rin_?tras/, "rin_tras", "aluminio"], [/rayos_?del|aro_?del/, "rin_del", "cromo"], [/rayos_?tras|aro_?tras/, "rin_tras", "cromo"],
  [/disco/, "disco_del", "aluminio"], [/freno_?tras|tambor/, "freno_tras", "aluminio"],
  [/faro|headl/, "faro", "mica_faro"], [/stop|tail/, "stop", "mica_roja"], [/direccional|ambar|blinker|turn/, "direccional", "mica_ambar"],
  [/asiento|seat/, "asiento", "vinilo"], [/tanque|tank/, "tanque", "pintura"], [/espejo|mirror/, "espejo", "plastico_brillo"],
  [/manubrio|handle/, "manubrio", "plastico_mate"], [/horquilla_baja/, "horquilla", "aluminio"], [/horquilla|fork/, "horquilla", "cromo"],
  [/amortigu|shock/, "amortiguador", "aluminio"], [/protector_?escape/, "protector_escape", "plastico_brillo"], [/escape|exhaust|muffler/, "escape", "aluminio"],
  [/motor|engine|bloque/, "motor", "motor"], [/cvt/, "cvt", "motor"], [/chasis|frame/, "chasis", "chasis"], [/basculante|swing/, "basculante", "chasis"],
  [/guardacadena/, "guardacadena", "plastico_mate"], [/cadena|chain/, "cadena", "motor"], [/guardabarros_?del|fender_?f/, "guardabarros_del", "pintura"],
  [/guardabarros|fender/, "guardabarros_tras", "plastico_mate"], [/portaplaca|placa/, "portaplaca", "plastico_mate"], [/visor|parabrisas|windsc/, "visor", "mica_faro"],
  [/tablero|reloj|pantalla/, "tablero", "plastico_brillo"], [/colin/, "colin", "pintura"], [/tapa/, "tapa_lateral", "pintura"], [/carenado/, "carenado", "pintura"],
  [/frente|farola/, "frente", "pintura"], [/escudo/, "escudo", "pintura"], [/pisadera/, "pisadera", "plastico_mate"], [/bajos|quilla/, "bajos", "plastico_mate"], [/radiador/, "radiador", "aluminio"],
];
const ACABADO_MATERIAL = { pintura: "pintura", blanco: "pintura_secundaria", plastico: "plastico_mate", oscuro: "plastico_mate", negro_brillo: "plastico_brillo",
  cromo: "cromo", metal: "aluminio", rin: "aluminio", caucho: "caucho", asiento: "vinilo", luz: "mica_faro", vidrio: "mica_faro", vidrio_oscuro: "mica_faro",
  ambar: "mica_ambar", stop: "mica_roja", motor: "motor", chasis: "chasis", titanio: "aluminio" };

function porNombre(p) {
  const n = p.nombre.toLowerCase(), mat = n.split(".")[0];
  for (const [re, pieza, acabado] of REGLAS_NOMBRE) if (re.test(n)) return { pieza, acabado: ACABADO_MATERIAL[mat] && n.includes(".") ? ACABADO_MATERIAL[mat] : acabado, motivo: "por el nombre" };
  if (n.includes(".") && ACABADO_MATERIAL[mat]) return { pieza: "otra", acabado: ACABADO_MATERIAL[mat], motivo: "por el material del nombre" };
  return null;
}
function porGlosario(p) {
  let mejor = null, dmin = Infinity;
  for (const e of D.glosario.entradas || []) {
    if (e.modelo === D.modelo) continue;
    const d = Math.hypot(e.pos[0] - p.pos[0], (e.pos[1] - p.pos[1]) * 1.2, (e.pos[2] - p.pos[2]) * 0.6)
      + 0.25 * Math.hypot(...[0, 1, 2].map((k) => Math.log((e.tam[k] + 0.01) / (p.tam[k] + 0.01))));
    if (d < dmin) { dmin = d; mejor = e; }
  }
  return mejor && dmin < 0.32 ? { pieza: mejor.pieza, acabado: mejor.acabado, motivo: `parecida a «${mejor.parte}» de ${mejor.modelo}` } : null;
}
function porForma(p) {
  const [x, y] = p.pos, [l, h, a] = p.tam;
  const redonda = Math.abs(l - h) < 0.25 * Math.max(l, h) && a < 0.6 * l;
  if (redonda && l > 0.2 && y < 0.4) return { pieza: x > 0.5 ? "llanta_del" : "llanta_tras", acabado: "caucho", motivo: "redonda y grande abajo" };
  if (redonda && l > 0.08 && y < 0.4) return { pieza: x > 0.5 ? "disco_del" : "freno_tras", acabado: "aluminio", motivo: "redonda al centro de una rueda" };
  if (l < 0.05 && h < 0.05 && y > 0.45) return { pieza: x > 0.5 ? "faro" : "stop", acabado: x > 0.5 ? "mica_faro" : "mica_roja", motivo: "pequeña en un extremo alto" };
  if (y < 0.5 && x > 0.3 && x < 0.65 && l > 0.15) return { pieza: "motor", acabado: "motor", motivo: "grande al centro y abajo" };
  if (l * h * a < 1e-5) return { pieza: "basura", acabado: "oculta", motivo: "resto diminuto" };
  return { pieza: "otra", acabado: y > 0.45 ? "pintura" : "plastico_mate", motivo: "sin pista: revisar" };
}

// ---------- Pantalla fija (sin scroll de página) y pestañas del panel ----------
const app = document.querySelector(".et3d-app");
const ajustarAlto = () => app.style.setProperty("--et3d-alto", `${Math.max(360, innerHeight - app.getBoundingClientRect().top - 6)}px`);
ajustarAlto(); addEventListener("resize", ajustarAlto);
document.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll("[data-tab]").forEach((x) => { const on = x === b; x.setAttribute("aria-selected", String(on)); $(`et3d-t-${x.dataset.tab}`).hidden = !on; });
}));

// ---------- Escena ----------
const cont = $("et3d-visor");
const ren = new THREE.WebGLRenderer({ antialias: true });
ren.setPixelRatio(Math.min(devicePixelRatio, 2));
cont.prepend(ren.domElement);
const escena = new THREE.Scene();
escena.background = new THREE.Color(0xe9e6df);
escena.environment = new THREE.PMREMGenerator(ren).fromScene(new RoomEnvironment(), 0.04).texture;
const cam = new THREE.PerspectiveCamera(35, 1, 0.01, 50);
const ctl = new OrbitControls(cam, ren.domElement);
ctl.enableDamping = false; // sin inercia: la cámara se detiene apenas sueltas
const MAT = {
  pintura: { color: 0x2f6fd6, roughness: 0.35, clearcoat: 1 }, pintura_secundaria: { color: 0xe8e4da, roughness: 0.4, clearcoat: 0.6 },
  plastico_mate: { color: 0x2a2d2f, roughness: 0.9 }, plastico_brillo: { color: 0x0c0e0f, roughness: 0.2, clearcoat: 1 },
  cromo: { color: 0xe4e8ea, roughness: 0.08, metalness: 1 }, aluminio: { color: 0xb9bec1, roughness: 0.35, metalness: 0.75 },
  caucho: { color: 0x161616, roughness: 0.95 }, vinilo: { color: 0x4a3a30, roughness: 0.7 },
  mica_faro: { color: 0xcfe6f2, roughness: 0.05, transparent: true, opacity: 0.6 }, mica_ambar: { color: 0xff9a1f, roughness: 0.1 },
  mica_roja: { color: 0xd0262b, roughness: 0.1 }, motor: { color: 0x6b6f73, roughness: 0.5, metalness: 0.5 },
  chasis: { color: 0x3b3f42, roughness: 0.45, metalness: 0.4 }, oculta: { color: 0x999999, transparent: true, opacity: 0.12, depthWrite: false },
};
const materiales = Object.fromEntries(Object.entries(MAT).map(([k, v]) => [k, new THREE.MeshPhysicalMaterial(v)]));
const resaltado = new THREE.MeshPhysicalMaterial({ color: 0xf2611d, emissive: 0xf2611d, emissiveIntensity: 0.55, roughness: 0.4 });

let partes = [], actual = 0, sola = false, caja = new THREE.Box3();

function medir() {
  caja = new THREE.Box3();
  for (const p of partes) { p.geo.computeBoundingBox(); caja.union(p.geo.boundingBox); }
  const t = caja.getSize(new THREE.Vector3()), c = caja.getCenter(new THREE.Vector3());
  const largo = Math.max(t.x, t.z), ejeLargo = t.x >= t.z ? "x" : "z";
  for (const p of partes) {
    const b = p.geo.boundingBox, pc = b.getCenter(new THREE.Vector3()), pt = b.getSize(new THREE.Vector3());
    const L = ejeLargo === "x" ? [pc.x, pc.z, pt.x, pt.z, t.x, t.z] : [pc.z, pc.x, pt.z, pt.x, t.z, t.x];
    // pos: [0 atrás … 1 adelante, 0 piso … 1 arriba, 0 centro … 1 costado]; tam: medidas sobre el largo de la moto
    p.pos = [(L[0] - (ejeLargo === "x" ? caja.min.x : caja.min.z)) / L[4], (pc.y - caja.min.y) / t.y, Math.abs(L[1] - (ejeLargo === "x" ? c.z : c.x)) / (L[5] / 2 || 1)];
    p.tam = [L[2] / largo, pt.y / largo, L[3] / largo];
    p.volumen = pt.x * pt.y * pt.z;
  }
}

// ---------- Pintar encima: zonas de una parte (otro color u otra pieza) ----------
// p.grupo: Uint8Array por vértice (0 sin pintar, 1-4 zona); p.zt: texto de cada zona. Se guarda como rangos de vértices.
const MAX_ZONAS = 8;
const COL_ZONA = [0xbfbfbf, 0x19c3e6, 0xe619b4, 0xf2d21d, 0x3ec23e, 0xff7a00, 0x8a4dff, 0xe02020, 0x0a3d91];
const matZona = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.6 });
const dedos = new Set();
let herramienta = "pincel", lazo = [];
// «Proteger otras zonas» (activo por defecto): los pinceles solo escriben donde no hay pintura o ya es la misma zona; borrar y deshacer sí pueden
const libre = (p, i) => !$("et3d-proteger").checked || grupoAct === 0 || p.grupo[i] === 0 || p.grupo[i] === grupoAct;
// Pintando: un dedo pinta; dos dedos giran o arrastran la cámara, según el botón «Dos dedos» (solo táctil)
let arrastrar = false;
function aplicarControles() {
  const mov = arrastrar ? THREE.TOUCH.DOLLY_PAN : THREE.TOUCH.DOLLY_ROTATE;
  ctl.touches = pintando ? { ONE: null, TWO: mov } : { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
  // Mouse al pintar: izquierdo pinta, derecho gira, rueda apretada arrastra la cámara, rueda girando acerca
  ctl.mouseButtons = pintando ? { LEFT: null, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.ROTATE } : { LEFT: THREE.MOUSE.ROTATE, MIDDLE: THREE.MOUSE.PAN, RIGHT: THREE.MOUSE.PAN };
}
$("et3d-mover").addEventListener("click", (e) => {
  arrastrar = !arrastrar; e.target.setAttribute("aria-pressed", String(arrastrar));
  e.target.textContent = arrastrar ? "Dos dedos: arrastrar (táctil)" : "Dos dedos: girar (táctil)"; aplicarControles();
});
const claveZona = () => (grupoAct < 0 ? 0 : grupoAct); // «lo sin pintar» (-1) guarda su nombre en la zona 0
let pintando = false, grupoAct = 1, grosor = 0.03, trazo = false;
function prepararPintura(p) {
  actualizarEstado(p);
  const n = p.geo.attributes.position.count;
  if (!p.grupo || p.grupo.length !== n) p.grupo = new Uint8Array(n);
  if (!p.zt) p.zt = Array(MAX_ZONAS + 1).fill("");
  if (!p.geo.attributes.color) p.geo.setAttribute("color", new THREE.BufferAttribute(new Float32Array(n * 3), 3));
  for (let i = 0; i < n; i++) colorVertice(p, i);
  p.geo.attributes.color.needsUpdate = true;
}
// Estado de una parte para el progreso: hecha (confirmada, verde), con nombre o pintura sin confirmar (azul claro), pendiente (gris oscuro)
const COL_ESTADO = { ok: 0x4fae6a, nom: 0x6fa8dc, pend: 0x8d949c };
function actualizarEstado(p) {
  const antes = p.estado;
  p.estado = p.confirmada ? "ok" : p.nombrada || p.zt?.[0]?.trim() || (p.grupo && p.grupo.some((v) => v)) ? "nom" : "pend";
  return antes !== p.estado;
}
function colorVertice(p, i) { const g = p.grupo[i], c = new THREE.Color(g ? COL_ZONA[g] : COL_ESTADO[p.estado || "pend"]); p.geo.attributes.color.setXYZ(i, c.r, c.g, c.b); }
const radioMundo = () => grosor * Math.max(...caja.getSize(new THREE.Vector3()).toArray());
// Círculo que muestra el tamaño real del pincel (en pantalla) donde está el puntero; también al elegir el grosor
function circuloPincel(x, y, dist) {
  const el = $("et3d-pincel"), v = cont.getBoundingClientRect();
  const px = (radioMundo() * (v.height / 2)) / (Math.tan((cam.fov * Math.PI) / 360) * dist);
  el.hidden = false; el.style.width = el.style.height = `${Math.max(4, px * 2)}px`;
  el.style.left = `${x - v.left}px`; el.style.top = `${y - v.top}px`;
}
function mostrarCirculo(e) {
  if (!pintando || (herramienta !== "pincel" && herramienta !== "lapiz")) { $("et3d-pincel").hidden = true; return; }
  if (herramienta === "lapiz") { const el = $("et3d-pincel"), v = cont.getBoundingClientRect(); el.hidden = false; el.style.width = el.style.height = "8px"; el.style.left = `${e.clientX - v.left}px`; el.style.top = `${e.clientY - v.top}px`; return; }
  const r = ren.domElement.getBoundingClientRect(), p = partes[actual];
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), cam);
  const hit = p && ray.intersectObject(p.malla)[0];
  circuloPincel(e.clientX, e.clientY, hit ? hit.distance : cam.position.distanceTo(ctl.target));
}
function vistaPrevia() { // al cambiar el grosor: círculo en el centro del visor un momento
  const v = cont.getBoundingClientRect();
  circuloPincel(v.left + v.width / 2, v.top + v.height / 2, cam.position.distanceTo(ctl.target));
  clearTimeout(vistaPrevia.t); vistaPrevia.t = setTimeout(() => { $("et3d-pincel").hidden = true; }, 1400);
}
function rellenarLazo(p, pts) {
  if (pts.length < 3) return;
  const r = ren.domElement.getBoundingClientRect(), pos = p.geo.attributes.position, nor = p.geo.attributes.normal, v = new THREE.Vector3();
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of pts) { x0 = Math.min(x0, x); y0 = Math.min(y0, y); x1 = Math.max(x1, x); y1 = Math.max(y1, y); }
  cam.updateMatrixWorld();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i);
    const dx = cam.position.x - v.x, dy = cam.position.y - v.y, dz = cam.position.z - v.z;
    if (nor && nor.getX(i) * dx + nor.getY(i) * dy + nor.getZ(i) * dz <= 0) continue; // de espaldas a la cámara
    v.project(cam);
    if (v.z < -1 || v.z > 1) continue;
    const sx = ((v.x + 1) / 2) * r.width, sy = ((1 - v.y) / 2) * r.height;
    if (sx < x0 || sx > x1 || sy < y0 || sy > y1) continue;
    let dentro = false;
    for (let a = 0, b = pts.length - 1; a < pts.length; b = a++) {
      const [xa, ya] = pts[a], [xb, yb] = pts[b];
      if ((ya > sy) !== (yb > sy) && sx < ((xb - xa) * (sy - ya)) / (yb - ya) + xa) dentro = !dentro;
    }
    if (dentro && libre(p, i)) { p.grupo[i] = grupoAct; colorVertice(p, i); }
  }
  p.geo.attributes.color.needsUpdate = true;
}
// Lápiz fino: línea delgada continua (interpola entre los puntos del dedo) que pinta el vértice más cercano de cada punto
let lapizAnt = null;
function lapizEn(e) {
  const p = partes[actual], r = ren.domElement.getBoundingClientRect(), pos = p.geo.attributes.position, tam = 0.005 * Math.max(...caja.getSize(new THREE.Vector3()).toArray());
  const act = [e.clientX, e.clientY], ant = lapizAnt || act, n = Math.max(1, Math.ceil(Math.hypot(act[0] - ant[0], act[1] - ant[1]) / 3));
  for (let k = 1; k <= n; k++) {
    const x = ant[0] + ((act[0] - ant[0]) * k) / n, y = ant[1] + ((act[1] - ant[1]) * k) / n;
    ray.setFromCamera(new THREE.Vector2(((x - r.left) / r.width) * 2 - 1, -((y - r.top) / r.height) * 2 + 1), cam);
    const hit = ray.intersectObject(p.malla)[0]; if (!hit) continue;
    const f = hit.face; let mejor = f.a, dm = Infinity;
    for (const i of [f.a, f.b, f.c]) { const d = hit.point.distanceToSquared(new THREE.Vector3().fromBufferAttribute(pos, i)); if (d < dm) { dm = d; mejor = i; } if (d < tam * tam && libre(p, i)) { p.grupo[i] = grupoAct; colorVertice(p, i); } }
    if (libre(p, mejor)) { p.grupo[mejor] = grupoAct; colorVertice(p, mejor); }
  }
  lapizAnt = act; p.geo.attributes.color.needsUpdate = true;
}
// Rellenar: desde el vértice tocado, se riega por la malla sobre lo que tenga el mismo valor y frena en el borde pintado
function vecinos(p) {
  if (p.vec) return p.vec;
  const n = p.geo.attributes.position.count, ind = p.geo.index.array, ady = Array.from({ length: n }, () => []);
  for (let t = 0; t < ind.length; t += 3) for (let k = 0; k < 3; k++) { const a = ind[t + k], b = ind[t + ((k + 1) % 3)]; ady[a].push(b); ady[b].push(a); }
  return (p.vec = ady);
}
function rellenarEn(e) {
  const p = partes[actual], r = ren.domElement.getBoundingClientRect(), pos = p.geo.attributes.position;
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), cam);
  const hit = ray.intersectObject(p.malla)[0]; if (!hit) return;
  let ini = hit.face.a, dm = Infinity;
  for (const i of [hit.face.a, hit.face.b, hit.face.c]) { const d = hit.point.distanceToSquared(new THREE.Vector3().fromBufferAttribute(pos, i)); if (d < dm) { dm = d; ini = i; } }
  const valor = p.grupo[ini]; if (valor === grupoAct || !libre(p, ini)) return;
  const ady = vecinos(p), pila = [ini]; p.grupo[ini] = grupoAct;
  while (pila.length) { const v = pila.pop(); for (const w of ady[v]) if (p.grupo[w] === valor) { p.grupo[w] = grupoAct; pila.push(w); } }
  recolorear(p);
}
// Al pasar el mouse sobre una parte: su nombre y, si tiene zonas, qué es la zona bajo el puntero
let tipPend = null;
function textoTip(p, hit) {
  const nom = p.texto || p.nombre, f = hit.face, pos = p.geo.attributes.position;
  let linea = "";
  if (p.grupo) {
    let mejor = f.a, dm = Infinity;
    for (const i of [f.a, f.b, f.c]) { const d = hit.point.distanceToSquared(new THREE.Vector3().fromBufferAttribute(pos, i)); if (d < dm) { dm = d; mejor = i; } }
    const g = p.grupo[mejor];
    if (g) linea = `Zona ${g}: ${p.zt?.[g] || "sin nombre"}`;
    else if (p.zt?.[0]?.trim()) linea = `Sin pintar: ${p.zt[0]}`;
    else if (hayPintura(p)) linea = "Sin pintar";
  }
  return [nom, linea];
}
function mostrarTip(e) {
  const yaHay = !!tipPend; tipPend = e; if (yaHay) return; // un solo cálculo por cuadro
  requestAnimationFrame(() => {
    const ev = tipPend; tipPend = null; const el = $("et3d-tip");
    if (!ev || trazo || pintando) { el.hidden = true; return; } // el texto flotante solo sale fuera del modo pintar
    const r = ren.domElement.getBoundingClientRect();
    ray.setFromCamera(new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1), cam);
    const hit = ray.intersectObjects(partes.map((q) => q.malla).filter((m) => m.visible))[0];
    if (!hit) { el.hidden = true; return; }
    const p = partes.find((q) => q.malla === hit.object), [a, b] = textoTip(p, hit);
    el.textContent = ""; el.append(Object.assign(document.createElement("b"), { textContent: a }));
    if (b) el.append(document.createElement("br"), document.createTextNode(b));
    el.hidden = false; el.style.left = `${Math.min(ev.clientX - r.left + 14, r.width - 170)}px`; el.style.top = `${Math.max(4, ev.clientY - r.top - 8)}px`;
  });
}
ren.domElement.addEventListener("pointermove", (e) => { if (!trazo) mostrarTip({ clientX: e.clientX, clientY: e.clientY }); });
ren.domElement.addEventListener("pointerleave", () => { $("et3d-tip").hidden = true; });

function dibujarLazo() { $("et3d-lazo").firstElementChild.setAttribute("points", lazo.map((q) => q.join(",")).join(" ")); }

function pintarEn(p, punto, normal) {
  const pos = p.geo.attributes.position, nor = p.geo.attributes.normal, r = radioMundo(), r2 = r * r;
  for (let i = 0; i < pos.count; i++) {
    const dx = pos.getX(i) - punto.x, dy = pos.getY(i) - punto.y, dz = pos.getZ(i) - punto.z;
    if (dx * dx + dy * dy + dz * dz > r2) continue;
    if (nor && nor.getX(i) * normal.x + nor.getY(i) * normal.y + nor.getZ(i) * normal.z < 0.1) continue; // no la cara de atrás
    if (!libre(p, i)) continue;
    p.grupo[i] = grupoAct; colorVertice(p, i);
  }
  p.geo.attributes.color.needsUpdate = true;
}
// Deshacer / rehacer por parte: copia del pintado antes de cada trazo (máx. 40)
function guardarPaso(p) { (p.deshacer ||= []).push(p.grupo.slice()); if (p.deshacer.length > 40) p.deshacer.shift(); p.rehacer = []; }
function recolorear(p) { for (let i = 0; i < p.grupo.length; i++) colorVertice(p, i); p.geo.attributes.color.needsUpdate = true; }
function cambiarPaso(p, de, a) {
  if (!de?.length) return;
  a.push(p.grupo.slice()); p.grupo.set(de.pop()); recolorear(p); zonaUI();
}
function botonesHistorial() { const p = partes[actual]; $("et3d-deshacer").disabled = !p?.deshacer?.length; $("et3d-rehacer").disabled = !p?.rehacer?.length; }
// Puntos de guardado: foto de todo lo pintado (todas las partes) en este aparato, para volver si algo sale mal
const CLAVE_PUNTOS = `et3d-puntos-${D.modelo}`;
const leerPuntos = () => { try { return JSON.parse(localStorage.getItem(CLAVE_PUNTOS) || "[]"); } catch { return []; } };
function escribirPuntos(l) { try { localStorage.setItem(CLAVE_PUNTOS, JSON.stringify(l)); return true; } catch { return false; } }
function pintarPuntos(sel) {
  const l = leerPuntos(), s = $("et3d-puntos");
  s.innerHTML = l.length ? "" : "<option value=''>Aún no hay puntos</option>";
  l.forEach((pt, i) => { const o = document.createElement("option"); o.value = i; o.textContent = `${pt.nombre} · ${pt.partes.length} partes`; s.append(o); });
  if (sel !== undefined) s.value = sel;
  $("et3d-punto-volver").disabled = $("et3d-punto-borrar").disabled = !l.length;
}
$("et3d-punto-nuevo").addEventListener("click", () => {
  const l = leerPuntos(), h = new Date();
  // v2: además del pintado, qué partes están confirmadas o con nombre, con su texto, pieza y acabado
  const guardables = partes.filter((p) => p.confirmada || p.nombrada || (p.grupo && (p.grupo.some((v) => v) || p.zt?.[0]?.trim())));
  const partesPunto = guardables.map((p) => ({ parte: p.nombre, zonas: zonasDe(p), confirmada: !!p.confirmada, nombrada: !!p.nombrada, texto: p.texto || "", pieza: p.pieza, acabado: p.acabado }));
  l.push({ v: 2, nombre: `${h.getHours()}:${String(h.getMinutes()).padStart(2, "0")}`, partes: partesPunto });
  while (l.length > 12) l.shift();
  $("et3d-estado").textContent = escribirPuntos(l) ? "Punto guardado." : "No se pudo guardar el punto (almacenamiento lleno).";
  pintarPuntos(l.length - 1);
});
$("et3d-punto-volver").addEventListener("click", () => {
  const pt = leerPuntos()[+$("et3d-puntos").value]; if (!pt) return;
  for (const p of partes) {
    if (!p.grupo) continue;
    const resto = p.zt?.[0] || ""; // el nombre de «lo sin pintar» no se pierde al volver a un punto viejo
    guardarPaso(p); p.grupo.fill(0); p.zt = Array(MAX_ZONAS + 1).fill(""); p.zt[0] = resto;
  }
  if (pt.v === 2) for (const p of partes) { p.confirmada = false; p.nombrada = false; } // el punto manda: lo que no está en él vuelve a pendiente
  for (const z of pt.partes) { const p = partes.find((x) => x.nombre === z.parte); if (p) {
    if (pt.v === 2) { p.confirmada = !!z.confirmada; p.nombrada = !!z.nombrada; if (z.texto) { p.texto = z.texto; p.editado = true; } if (NOMBRE_PIEZA[z.pieza]) p.pieza = z.pieza; if (NOMBRE_ACABADO[z.acabado]) p.acabado = z.acabado; }
    else if (z.zonas?.length) p.nombrada = true; if (!p.grupo) prepararPintura(p); else if (!p.deshacer?.length) guardarPaso(p); const resto = p.zt[0]; desdeRangos(p, z.zonas); if (!p.zt[0]) p.zt[0] = resto; } }
  $("et3d-estado").textContent = `Pintado vuelto al punto de las ${pt.nombre}. Si no te gusta, usa Deshacer.`;
  // todo se refresca: colores de cada vértice (también de las partes que se vaciaron), deducciones viejas, panel, progreso, tooltip
  for (const p of partes) { actualizarEstado(p); if (p.grupo) { recolorear(p); p.zdeduc = {}; } }
  $("et3d-zona-texto").value = partes[actual]?.zt?.[claveZona()] || "";
  $("et3d-tip").hidden = true; mostrar(false); pintar(); zonaUI();
  if (pt.v !== 2) $("et3d-estado").textContent += " (Punto antiguo: solo trae el pintado; lo confirmado no se toca. Los nuevos guardan todo.)";
});
$("et3d-punto-borrar").addEventListener("click", () => {
  const l = leerPuntos(); l.splice(+$("et3d-puntos").value, 1); escribirPuntos(l); pintarPuntos();
});
function rangos(grupo, g) {
  const out = []; let ini = -1;
  for (let i = 0; i <= grupo.length; i++) {
    if (i < grupo.length && grupo[i] === g) { if (ini < 0) ini = i; } else if (ini >= 0) { out.push([ini, i - 1]); ini = -1; }
  }
  return out;
}
function desdeRangos(p, zonas) {
  prepararPintura(p);
  p.nombrada = p.nombrada || (zonas || []).length > 0; actualizarEstado(p);
  for (const z of zonas || []) { for (const [a, b] of z.vertices || []) for (let i = a; i <= b && i < p.grupo.length; i++) p.grupo[i] = z.grupo; p.zt[z.grupo] = z.texto || ""; }
  for (let i = 0; i < p.grupo.length; i++) colorVertice(p, i);
  p.geo.attributes.color.needsUpdate = true;
}
function zonasDe(p) {
  if (!p.grupo) return [];
  const out = [];
  for (let g = 1; g <= MAX_ZONAS; g++) { const r = rangos(p.grupo, g); if (r.length) out.push({ grupo: g, texto: p.zt?.[g] || "", vertices: r }); }
  // «Lo sin pintar» (grupo 0): solo se guarda su nombre; lo que no tiene zona es el resto
  if (p.zt?.[0]?.trim()) out.unshift({ grupo: 0, texto: p.zt[0], vertices: [] });
  return out;
}

function vista(tipo) {
  const c = caja.getCenter(new THREE.Vector3()), r = caja.getSize(new THREE.Vector3()).length() * 1.15 * Math.max(1, 1.5 / cam.aspect);
  const dir = { lado: [0.25, 0.25, 1], frente: [1, 0.3, 0.25], atras: [-1, 0.3, 0.25] }[tipo];
  ctl.target.copy(c);
  cam.position.copy(c).add(new THREE.Vector3(...dir).normalize().multiplyScalar(r));
  ctl.update();
}

// Progreso: hecha (confirmada) en verde, pendiente en gris, la actual en naranja; lo pintado por zonas se ve con los colores de sus zonas
const matOk = new THREE.MeshPhysicalMaterial({ color: 0x4fae6a, roughness: 0.6 });
const matPend = new THREE.MeshPhysicalMaterial({ color: 0x8d949c, roughness: 0.85 });
const matNom = new THREE.MeshPhysicalMaterial({ color: 0x6fa8dc, roughness: 0.6 });
let verProgreso = true, sinResaltar = false; // sinResaltar: se tocó el vacío; la parte sigue en el panel pero ya no se ve marcada
const hayPintura = (p) => !!p.grupo && p.grupo.some((v) => v);
function materialDe(p, i) {
  if (i === actual && (!sinResaltar || pintando)) return pintando && p.grupo ? matZona : resaltado;
  if (!verProgreso) return materiales[p.acabado];
  actualizarEstado(p);
  if (hayPintura(p)) return matZona;
  return p.estado === "ok" ? matOk : p.estado === "nom" ? matNom : matPend;
}
function pintar() {
  partes.forEach((p, i) => {
    p.malla.material = materialDe(p, i);
    p.malla.visible = !sola || i === actual;
  });
}

const sinTildes = (t) => t.toLowerCase().split(" (")[0];
function textoDe(p) {
  if (p.pieza === "basura") return "";
  if (p.pieza === "otra") return sinTildes(NOMBRE_ACABADO[p.acabado] || ""); // sin pieza conocida: solo el material o color
  return `${sinTildes(NOMBRE_PIEZA[p.pieza] || "")}, ${sinTildes(NOMBRE_ACABADO[p.acabado] || "")}`;
}

function mostrar(enfocar = true) {
  if (enfocar) sinResaltar = false;
  const p = partes[actual];
  if (!p) return;
  $("et3d-parte").textContent = `${actual + 1}. ${p.nombre}`;
  $("et3d-motivo").textContent = p.confirmada ? "Confirmada" : `Sugerencia: ${p.motivo}`;
  if (document.activeElement !== campo) campo.value = p.texto ?? "";
  $("et3d-deduccion").textContent = p.por_revisar ? "Por revisar: no entendí esto" : `Pieza: ${NOMBRE_PIEZA[p.pieza]} · ${NOMBRE_ACABADO[p.acabado]}`;
  $("et3d-pieza").value = p.pieza;
  for (const b of document.querySelectorAll(".et3d-acabado")) b.setAttribute("aria-checked", String(b.dataset.acabado === p.acabado));
  const n = partes.filter((x) => x.confirmada).length;
  $("et3d-num").textContent = n; $("et3d-total").textContent = partes.length;
  partes.forEach(actualizarEstado);
  const nom = partes.filter((x) => x.estado === "nom").length;
  $("et3d-nom").textContent = nom ? ` · ${nom} con nombre sin confirmar` : "";
  $("et3d-barra").style.width = `${(100 * n) / (partes.length || 1)}%`;
  pintar(); zonaUI();
  if (enfocar) { campo.value = p.texto ?? ""; campo.focus({ preventScroll: true }); campo.select(); }
}

$("et3d-deshacer").addEventListener("click", () => { const p = partes[actual]; cambiarPaso(p, p.deshacer, (p.rehacer ||= [])); });
$("et3d-rehacer").addEventListener("click", () => { const p = partes[actual]; cambiarPaso(p, p.rehacer, (p.deshacer ||= [])); });

// Ctrl+Z deshace y Ctrl+Y (o Ctrl+Mayús+Z) rehace el pintado; en los campos de texto queda el deshacer normal del texto
document.addEventListener("keydown", (e) => {
  if (!pintando || !(e.ctrlKey || e.metaKey) || e.altKey) return;
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName)) return;
  const k = e.key.toLowerCase();
  if (k === "z" && !e.shiftKey) { e.preventDefault(); $("et3d-deshacer").click(); }
  else if (k === "y" || (k === "z" && e.shiftKey)) { e.preventDefault(); $("et3d-rehacer").click(); }
});

function zonaUI() {
  botonesHistorial();
  const p = partes[actual];
  const k = claveZona();
  $("et3d-zona-t").textContent = grupoAct < 0 ? "¿Qué es todo lo que quedó sin pintar?" : grupoAct ? `¿Qué es la zona ${grupoAct}?` : "Borrando: pasa el dedo sobre lo pintado";
  $("et3d-zona-texto").hidden = !grupoAct;
  if (p && grupoAct && document.activeElement !== $("et3d-zona-texto")) $("et3d-zona-texto").value = p.zt?.[k] || "";
  const d = p?.zdeduc?.[k];
  $("et3d-zona-deduccion").textContent = !grupoAct || !p?.zt?.[k] ? "" : d ? (d.por_revisar ? "Por revisar: no entendí esto" : `Pieza: ${NOMBRE_PIEZA[d.pieza]} · ${NOMBRE_ACABADO[d.acabado]}`) : "Se deduce al guardar";
  const n = p ? zonasDe(p).length : 0;
  $("et3d-pintar").textContent = pintando ? "✓ Terminar de pintar" : n ? `Pintar encima (${n} zonas)` : "Pintar encima";
}

$("et3d-progreso").addEventListener("click", (e) => {
  verProgreso = !verProgreso; e.currentTarget.setAttribute("aria-pressed", String(verProgreso));
  $("et3d-leyenda").hidden = !verProgreso; pintar();
});
$("et3d-pintar").addEventListener("click", () => {
  pintando = !pintando; $("et3d-tip").hidden = true;
  if (!pintando) document.querySelector('[data-tab="nombre"]').click(); // al terminar de pintar se vuelve a «Nombre»
  $("et3d-pintar").setAttribute("aria-pressed", String(pintando));
  $("et3d-pintura-op").hidden = !pintando;
  aplicarControles();
  ren.domElement.style.touchAction = pintando ? "none" : "";
  if (pintando) { prepararPintura(partes[actual]); if (!sola) $("et3d-sola").click(); } // solo esta parte a la vista: lo de dentro no se podría pintar
  pintar(); zonaUI();
});
document.querySelectorAll(".et3d-grupo").forEach((b) => b.addEventListener("click", () => {
  grupoAct = +b.dataset.grupo;
  document.querySelectorAll(".et3d-grupo").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
  zonaUI();
}));
document.querySelectorAll("[data-herr]").forEach((b) => b.addEventListener("click", () => {
  herramienta = b.dataset.herr;
  document.querySelectorAll("[data-herr]").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
  $("et3d-pincel").hidden = true;
}));
document.querySelectorAll("[data-grosor]").forEach((b) => b.addEventListener("click", () => {
  grosor = +b.dataset.grosor; vistaPrevia();
  document.querySelectorAll("[data-grosor]").forEach((x) => x.setAttribute("aria-checked", String(x === b)));
}));
$("et3d-limpiar-zonas").addEventListener("click", () => {
  const p = partes[actual]; if (!p?.grupo) return;
  guardarPaso(p); p.grupo.fill(0); p.zt = Array(MAX_ZONAS + 1).fill(""); p.zdeduc = {}; prepararPintura(p); zonaUI();
});
$("et3d-zona-texto").addEventListener("input", (e) => { const p = partes[actual]; if (!p.zt) prepararPintura(p); p.zt[claveZona()] = e.target.value; if (actualizarEstado(p)) recolorear(p); });
$("et3d-zona-texto").addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); e.target.blur(); } });
function pincel(e) {
  const p = partes[actual], r = ren.domElement.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), cam);
  const hit = ray.intersectObject(p.malla)[0];
  if (hit) pintarEn(p, hit.point, hit.face.normal);
}

async function guardar(silencioso) {
  const cuerpo = { partes: partes.map((p) => ({ parte: p.nombre, pieza: p.pieza, acabado: p.acabado, pos: p.pos, tam: p.tam, confirmada: !!p.confirmada, texto: p.texto || "", editado: !!p.editado, zonas: zonasDe(p) })) };
  const csrf = document.cookie.match(/csrftoken=([^;]+)/)?.[1] || "";
  try {
    const r = await fetch(yo.dataset.guardar, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrf }, body: JSON.stringify(cuerpo) });
    const j = await r.json();
    if (!j.ok) throw new Error(j.error);
    // lo deducido por el servidor se aplica a las partes y se repinta
    for (const d of j.partes_deducidas || []) {
      const p = partes.find((x) => x.nombre === d.parte);
      if (p) { Object.assign(p, { pieza: d.pieza, acabado: d.acabado, por_revisar: d.por_revisar, editado: false }); p.zdeduc = Object.fromEntries((d.zonas || []).map((z) => [z.grupo, z])); }
    }
    pintar(); mostrar(false);
    $("et3d-estado").textContent = silencioso ? "Guardado automático." : `Guardado: ${j.partes} partes. El glosario ya tiene ${j.glosario}.`;
  } catch (e) { $("et3d-estado").textContent = `No se pudo guardar: ${e.message}`; }
}

// El campo de texto libre manda: al avanzar, el servidor deduce pieza y acabado. Las listas son opcionales.
const campo = $("et3d-texto");
campo.addEventListener("input", () => { const p = partes[actual]; p.texto = campo.value; p.editado = true; p.nombrada = true; if (actualizarEstado(p) && p.grupo) recolorear(p); pintar(); });
campo.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); $("et3d-confirmar").click(); } });
$("et3d-pieza").addEventListener("change", (e) => { partes[actual].pieza = e.target.value; partes[actual].editado = false; partes[actual].texto = textoDe(partes[actual]); mostrar(false); });
$("et3d-acabado").addEventListener("click", (e) => {
  const b = e.target.closest("[data-acabado]"); if (!b) return;
  partes[actual].acabado = b.dataset.acabado; partes[actual].editado = false; partes[actual].texto = textoDe(partes[actual]); mostrar(false);
});
$("et3d-confirmar").addEventListener("click", () => {
  partes[actual].texto = campo.value; if (campo.value !== textoDe(partes[actual])) partes[actual].editado = true;
  partes[actual].confirmada = true; actualizarEstado(partes[actual]); if (partes[actual].grupo) recolorear(partes[actual]);
  const n = partes.filter((x) => x.confirmada).length;
  if (n % 10 === 0) guardar(true);
  const sig = partes.findIndex((x, i) => i > actual && !x.confirmada);
  actual = sig >= 0 ? sig : Math.min(actual + 1, partes.length - 1);
  if (n === partes.length) guardar(false);
  mostrar();
});
$("et3d-anterior").addEventListener("click", () => { actual = Math.max(0, actual - 1); mostrar(); });
$("et3d-guardar").addEventListener("click", () => guardar(false));
$("et3d-sola").addEventListener("click", (e) => { sola = !sola; e.target.setAttribute("aria-pressed", String(sola)); pintar(); });
for (const b of document.querySelectorAll("[data-vista]")) b.addEventListener("click", () => vista(b.dataset.vista));

// Tocar una parte en el 3D la elige (si no se arrastró)
const ray = new THREE.Raycaster(), inicio = new THREE.Vector2();
ren.domElement.addEventListener("pointerdown", (e) => {
  inicio.set(e.clientX, e.clientY);
  if (pintando) {
    dedos.add(e.pointerId);
    if (dedos.size > 1 || (e.pointerType === "mouse" && e.button !== 0) || grupoAct < 0) { trazo = false; return; } // dos dedos: mover el modelo, no pintar
    trazo = true; guardarPaso(partes[actual]); ren.domElement.setPointerCapture(e.pointerId);
    if (herramienta === "lazo") { const r = ren.domElement.getBoundingClientRect(); lazo = [[e.clientX - r.left, e.clientY - r.top]]; dibujarLazo(); }
    else if (herramienta === "lapiz") { lapizAnt = null; lapizEn(e); }
    else if (herramienta === "relleno") rellenarEn(e);
    else pincel(e);
  }
});
ren.domElement.addEventListener("pointermove", (e) => {
  if (!pintando) return;
  // solo pinta con el botón izquierdo (o el dedo) apretado; con el derecho (girar/arrastrar) o sin botón se corta el trazo
  if (trazo && ((e.buttons & 2) || !(e.buttons & 1))) { trazo = false; lazo = []; dibujarLazo(); }
  if (trazo && herramienta === "lazo") { const r = ren.domElement.getBoundingClientRect(); lazo.push([e.clientX - r.left, e.clientY - r.top]); dibujarLazo(); }
  else if (trazo && herramienta === "lapiz") lapizEn(e);
  else if (trazo && herramienta === "pincel") pincel(e);
  mostrarCirculo(e);
});
ren.domElement.addEventListener("pointerleave", () => { $("et3d-pincel").hidden = true; });
ren.domElement.addEventListener("pointercancel", (e) => { dedos.delete(e.pointerId); trazo = false; lazo = []; dibujarLazo(); });
ren.domElement.addEventListener("contextmenu", (e) => { if (pintando) e.preventDefault(); });
ren.domElement.addEventListener("pointerup", (e) => {
  if (pintando) {
    dedos.delete(e.pointerId);
    if (trazo && herramienta === "lazo") { rellenarLazo(partes[actual], lazo); lazo = []; dibujarLazo(); }
    if (trazo) { // un trazo que no cambió nada no cuenta como paso
      const p = partes[actual], ant = p.deshacer?.at(-1);
      if (ant && ant.every((v, i) => v === p.grupo[i])) p.deshacer.pop();
    }
    trazo = false; if (actualizarEstado(partes[actual])) recolorear(partes[actual]); zonaUI(); return;
  }
  if (inicio.distanceTo(new THREE.Vector2(e.clientX, e.clientY)) > 6) return;
  const r = ren.domElement.getBoundingClientRect();
  ray.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), cam);
  const hit = ray.intersectObjects(partes.map((p) => p.malla).filter((m) => m.visible))[0];
  if (hit) { actual = partes.findIndex((p) => p.malla === hit.object); sinResaltar = false; mostrar(); }
  else { sinResaltar = true; $("et3d-motivo").textContent = "Ninguna parte marcada (toca una para elegirla)"; pintar(); }
});

function tamano() {
  const w = cont.clientWidth, h = cont.clientHeight;
  ren.setSize(w, h, false); cam.aspect = w / h; cam.updateProjectionMatrix();
}
new ResizeObserver(tamano).observe(cont);
ren.setAnimationLoop(() => { ctl.update(); ren.render(escena, cam); });

pintarPuntos();
try {
  partes = await leerGlb(yo.dataset.glb);
  medir();
  const guardadas = Object.fromEntries((D.etiquetas.partes || []).map((p) => [p.parte, p]));
  for (const p of partes) {
    const g = guardadas[p.nombre];
    const s = g ? { pieza: g.pieza, acabado: g.acabado, motivo: "ya etiquetada" } : porNombre(p) || porGlosario(p) || porForma(p);
    Object.assign(p, s, { confirmada: !!g?.confirmada, texto: g?.texto, por_revisar: !!g?.por_revisar });
    if (g) { const sug = porNombre(p) || porGlosario(p) || porForma(p); p.nombrada = !!(g.zonas?.length) || ((g.texto || "").trim() !== "" && g.texto !== textoDe(sug)); }
    if (!NOMBRE_PIEZA[p.pieza]) p.pieza = "otra";
    if (!NOMBRE_ACABADO[p.acabado]) p.acabado = "plastico_mate";
    if (p.texto === undefined) p.texto = textoDe(p);
    if (g?.zonas?.length) { desdeRangos(p, g.zonas); p.zdeduc = Object.fromEntries(g.zonas.map((z) => [z.grupo, z])); }
  }
  // De la más grande a la más pequeña: lo que más se ve primero
  partes.sort((a, b) => b.volumen - a.volumen);
  for (const p of partes) { p.malla = new THREE.Mesh(p.geo, materiales[p.acabado]); escena.add(p.malla); }
  escena.add(new THREE.HemisphereLight(0xffffff, 0x8a8478, 1.2));
  const sol = new THREE.DirectionalLight(0xffffff, 1.4); sol.position.set(2, 4, 3); escena.add(sol);
  actual = Math.max(0, partes.findIndex((p) => !p.confirmada));
  $("et3d-cargando").remove();
  tamano(); vista("lado"); mostrar();
  window.__et3d = { partes, vista, ren, escena, cam };
} catch (e) {
  console.error(e); const c = $("et3d-cargando"); if (c) c.textContent = `No se pudo cargar el modelo: ${e.message}`; else $("et3d-estado").textContent = `Error: ${e.message}`;
}
