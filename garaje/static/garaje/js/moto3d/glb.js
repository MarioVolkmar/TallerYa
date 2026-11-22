// Carga un GLB de carrocería "realista" (skill moto-3d-realista) y lo monta sobre la moto procedural.
// Las líneas con modelo realista (MODELOS_TRIPO) lo cargan por defecto; el piloto anterior, con ?modelo3d=glb. Si algo falla, la moto procedural queda tal cual (respaldo).
// El GLB lo escribe .claude/skills/moto-3d-realista/scripts/glb.py: nodos "material.parte", posiciones int16 y
// normales int8 (KHR_mesh_quantization) y extras {pieza, padre, rin, rol} que dicen dónde va cada malla.
import * as THREE from "three";

// (?v= cambia con cada versión del GLB: así el navegador no se queda con el anterior en caché)
const MODELOS = { nmax: "../../modelos/nmax155.glb?v=19" };
// Modelo realista por defecto de cada línea: malla base generada con IA, aligerada y partida en piezas con nombre
// (skill moto-3d-tripo; mismo formato que el piloto)
const MODELOS_TRIPO = { nmax: "../../modelos/nmax155_tripo.glb?v=24", nkd: "../../modelos/nkd125_tripo.glb?v=11", "boxer[ _-]*ct[ _-]*100": "../../modelos/boxer100_tripo.glb?v=4", "xtz[ _-]*150": "../../modelos/xtz150_tripo.glb?v=8", "xtz[ _-]*125": "../../modelos/xtz125_tripo.glb?v=5", "mt[ _-]*0?3(?!\d)": "../../modelos/mt03_tripo.glb?v=16", aerox: "../../modelos/aerox155_tripo5.glb?v=10", "xr[ _-]*190": "../../modelos/xr190l_tripo4.glb?v=8", "eco[ _-]*deluxe": "../../modelos/ecodeluxe100_tripo.glb?v=6", "fz[ _-]*25": "../../modelos/fz25_tripo.glb?v=1" };

const ACCESORIOS_GLB = ["baul", "led"];

export function glbDeLinea(linea) {
  // Por defecto, el modelo realista de la línea (si lo tiene). ?modelo3d=procedural deja la moto genérica y
  // ?modelo3d=glb (o localStorage "moto3d_glb" = "1") carga el piloto anterior.
  const pedido = new URLSearchParams(location.search).get("modelo3d");
  if (pedido === "procedural") return null;
  let piloto = pedido === "glb";
  try { piloto ||= !pedido && localStorage.getItem("moto3d_glb") === "1"; } catch { /* sin almacenamiento */ }
  const modelos = piloto ? MODELOS : MODELOS_TRIPO;
  const clave = Object.keys(modelos).find((k) => new RegExp(k, "i").test(linea || ""));
  return clave ? new URL(modelos[clave], import.meta.url).href : null;
}

async function leerGlb(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`GLB ${r.status}`);
  const buf = await r.arrayBuffer();
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x46546c67) throw new Error("no es GLB");
  const largoJson = dv.getUint32(12, true);
  const g = JSON.parse(new TextDecoder().decode(new Uint8Array(buf, 20, largoJson)));
  const base = 20 + largoJson + 8;
  const TIPOS = { 5120: Int8Array, 5121: Uint8Array, 5122: Int16Array, 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };
  const COMP = { SCALAR: 1, VEC3: 3 };
  const atributo = (i) => {
    const a = g.accessors[i], bv = g.bufferViews[a.bufferView], T = TIPOS[a.componentType];
    const stride = (bv.byteStride || T.BYTES_PER_ELEMENT * COMP[a.type]) / T.BYTES_PER_ELEMENT;
    const arr = new T(buf, base + (bv.byteOffset || 0), a.count * stride);
    if (a.type === "SCALAR") return new THREE.BufferAttribute(arr, 1);
    // Se descuantiza a Float32 sin entrelazar: el visor une mallas y proyecta calcas leyendo .array directamente
    // (con int16 entrelazado salía geometría basura). El archivo sigue cuantizado: solo pesa más en memoria.
    const c = COMP[a.type], escala = a.normalized ? (T === Int16Array ? 32767 : T === Int8Array ? 127 : 1) : 1;
    const out = new Float32Array(a.count * c);
    for (let i = 0; i < a.count; i++) for (let j = 0; j < c; j++) out[i * c + j] = Math.max(arr[i * stride + j] / escala, -1);
    return new THREE.BufferAttribute(out, c);
  };
  const nodos = g.nodes.map((n) => {
    const pr = g.meshes[n.mesh].primitives[0];
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", atributo(pr.attributes.POSITION));
    geo.setAttribute("normal", atributo(pr.attributes.NORMAL));
    geo.setIndex(atributo(pr.indices));
    geo.computeBoundingSphere();
    return { nombre: n.name, material: n.name.split(".")[0], geo, t: n.translation || [0, 0, 0], s: n.scale || [1, 1, 1], extras: n.extras || {} };
  });
  // (extras de la escena, p. ej. {modelo_completo: true})
  nodos.escena = g.scenes?.[g.scene || 0]?.extras || {};
  return nodos;
}

// Lleva la placa procedural (con su lámina del número) al portaplaca del GLB: centro c en coordenadas de la moto,
// inclinación incl (rad, negativa = arriba hacia adelante) y tamaño tam = [ancho, alto] en metros.
function ponerPlacaEn(moto, { c, incl, tam }) {
  const placa = moto.placa;
  moto.raiz.updateMatrixWorld(true);
  const p = moto.raiz.localToWorld(new THREE.Vector3(...c));
  placa.parent.worldToLocal(p);
  placa.position.copy(p);
  placa.rotation.set(0, 0, incl);
  // (la caja de la placa procedural mide 0,006 × 0,084 × 0,204 m: se escala al tamaño pedido)
  const g = placa.geometry.parameters || { height: 0.084, depth: 0.204 };
  placa.scale.set(1, tam[1] / g.height, tam[0] / g.depth);
}

// Caja de las mallas procedurales de un grupo en coordenadas de la moto (sin las del GLB; cuenta también las ocultas)
function cajaProcedural(moto, g) {
  moto.raiz.updateMatrixWorld(true);
  const inv = new THREE.Matrix4().copy(moto.raiz.matrixWorld).invert(), caja = new THREE.Box3();
  g.traverse((o) => {
    if (!o.isMesh || o.userData.glb) return;
    if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
    caja.union(o.geometry.boundingBox.clone().applyMatrix4(new THREE.Matrix4().multiplyMatrices(inv, o.matrixWorld)));
  });
  return caja;
}

// Corre un objeto d metros (coordenadas de la moto) aunque cuelgue de un padre movido
function correr(moto, o, d) {
  moto.raiz.updateMatrixWorld(true);
  const a = moto.raiz.localToWorld(new THREE.Vector3()), b = moto.raiz.localToWorld(d.clone());
  o.parent.worldToLocal(a); o.parent.worldToLocal(b);
  o.position.add(b.sub(a));
}

// Lo procedural que se conserva (espejos de otros estilos, accesorios) quedó armado para el manubrio, el frente y la
// cola genéricos: se lleva a los del GLB. Así no quedan espejos ni cubremanos flotando ni un baúl colgando de la cola.
// - Manubrio: el nodo del GLB con extras.manubrio {x, y, extremo} (centro del puño y punta del manubrio). El de la
//   procedural sale de sus espejos de fábrica (construir.js: base del tallo en (H.x-0,04, H.y+alto, ±(ancho-0,06)),
//   tallo de radio 0,0065 que sube y carcasa hasta 0,154 m más afuera de la base).
// - extras.acomodar [{grupo: "accesorios.baul", ref: "abajo"|"arriba"|"abajo_frente", a: [x|null, y|null, z|null]}]:
//   lleva ese punto de la caja del grupo al punto a (null = ese eje no se mueve).
function manubrioProcedural(moto) {
  const f = moto.espejos?.fabrica;
  if (!f) return null;
  const c = cajaProcedural(moto, f);
  if (c.isEmpty()) return null;
  return { x: c.max.x - 0.0065 - 0.01, y: c.min.y + 0.0065, extremo: c.max.z - 0.154 + 0.06 };
}
function alManubrio(moto, proc, glb, grupos) {
  const d = new THREE.Vector3(glb.x - proc.x, glb.y - proc.y, 0), dz = glb.extremo - proc.extremo;
  for (const g of grupos) {
    if (!g) continue;
    correr(moto, g, d);
    // (cada lado se abre o se cierra por su cuenta: el manubrio del GLB no tiene el mismo ancho)
    // (una malla con los dos lados juntos se estira a lo ancho desde el centro)
    for (const o of g.children) {
      const c = cajaProcedural(moto, o);
      if (c.isEmpty()) continue;
      if (c.min.z < -0.05 && c.max.z > 0.05) o.scale.z *= glb.extremo / proc.extremo;
      else correr(moto, o, new THREE.Vector3(0, 0, Math.sign(c.getCenter(new THREE.Vector3()).z) * dz));
    }
  }
}
function acomodar(moto, { grupo, ref, a }) {
  const g = grupo.split(".").reduce((o, k) => o?.[k], moto);
  if (!g) return;
  const c = cajaProcedural(moto, g);
  if (c.isEmpty()) return;
  const m = c.getCenter(new THREE.Vector3());
  const p = { abajo: [m.x, c.min.y, m.z], arriba: [m.x, c.max.y, m.z], abajo_frente: [c.max.x, c.min.y, m.z] }[ref] || m.toArray();
  correr(moto, g, new THREE.Vector3(...[0, 1, 2].map((i) => (a[i] ?? p[i]) - p[i])));
}

// Lámpara de un nodo del GLB (extras.lampara {tipo: "faro" | "stop" | "direccional"}): centro de la cara del lente, hacia
// dónde mira y su tamaño, en coordenadas de la moto. De ahí nacen el haz, los halos y el parpadeo al encender.
function lamparaDe(n, datos) {
  const p = n.geo.attributes.position, idx = n.geo.index.array, a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  const centro = new THREE.Vector3(), normal = new THREE.Vector3(), nt = new THREE.Vector3(), caja = new THREE.Box3();
  const punto = (v, i) => v.fromBufferAttribute(p, i).multiply(new THREE.Vector3(...n.s)).add(new THREE.Vector3(...n.t));
  let area = 0;
  for (let i = 0; i < idx.length; i += 3) {
    punto(a, idx[i]); punto(b, idx[i + 1]); punto(c, idx[i + 2]);
    nt.crossVectors(b.clone().sub(a), c.clone().sub(a));
    const ar = nt.length() / 2;
    centro.addScaledVector(a.clone().add(b).add(c), ar / 3);
    normal.add(nt);
    area += ar;
    caja.expandByPoint(a).expandByPoint(b).expandByPoint(c);
  }
  const pos = centro.divideScalar(area || 1), dir = normal.normalize();
  const lado = datos.tipo === "direccional" ? (pos.x > 0 ? "d" : "t") + (pos.z > 0 ? "i" : "d") : pos.z > 0.02 ? "i" : pos.z < -0.02 ? "d" : "c";
  // (cono: false = luz de posición: halo al encender, pero el haz al piso sale de los otros faros)
  return { tipo: datos.tipo, lado, pos, dir, ancho: caja.max.z - caja.min.z, alto: caja.max.y - caja.min.y, area, ...(datos.cono === false && { cono: false }) };
}

// Pantalla del tablero (extras.pantalla {c, n, tam}): un plano sobre el velocímetro con el dibujo de una pantalla
// digital. Usa M.pantalla, que el visor ya atenúa con la moto apagada y enciende con "Encender".
// El lienzo lleva dos dibujos, uno encima del otro: arriba el tablero con velocidad (el de la NMAX) y abajo un
// tacómetro. redonda: reloj redondo de diámetro tam[0] (motos de calle, dos relojes); dibujo "tacometro" usa el de abajo.
function texturaTablero() {
  const lienzo = document.createElement("canvas");
  lienzo.width = 512; lienzo.height = 660;
  const g = lienzo.getContext("2d");
  g.fillStyle = "#04090a"; g.fillRect(0, 0, 512, 330);
  g.strokeStyle = "#1d3a3a"; g.lineWidth = 6; g.strokeRect(8, 8, 496, 314);
  // Barra de revoluciones: sube en arco de izquierda a derecha; en mínimo van prendidos los primeros segmentos
  for (let i = 0; i < 22; i++) {
    const alto = 26 + i * 2.6;
    g.fillStyle = i < 5 ? "#e9fffb" : i > 17 ? "#3a1512" : "#17302f";
    g.fillRect(34 + i * 20.4, 104 - alto, 14, alto);
  }
  g.fillStyle = "#7fb8b2"; g.font = "bold 20px sans-serif"; g.textAlign = "left";
  g.fillText("x1000 r/min", 34, 132);
  // Velocidad
  g.fillStyle = "#f2fffd"; g.textAlign = "right"; g.font = "bold 150px sans-serif";
  g.fillText("0", 330, 290);
  g.font = "bold 30px sans-serif"; g.textAlign = "left";
  g.fillText("km/h", 344, 288);
  // Gasolina (izquierda) y datos (derecha)
  g.font = "bold 22px sans-serif"; g.fillStyle = "#7fb8b2";
  g.fillText("F", 36, 176); g.fillText("E", 36, 300);
  for (let i = 0; i < 6; i++) { g.fillStyle = i < 2 ? "#17302f" : "#e9fffb"; g.fillRect(62, 160 + i * 23.5, 44, 17); }
  g.fillStyle = "#e9fffb"; g.textAlign = "right"; g.font = "bold 30px sans-serif";
  g.fillText("ECO", 484, 176);
  g.fillStyle = "#7fb8b2"; g.font = "bold 22px sans-serif";
  g.fillText("ODO", 484, 214);
  // Tacómetro (mitad de abajo): arco de 0 a 10 mil vueltas con la zona roja al final, rayas encendidas en mínimo y el cambio
  g.fillStyle = "#04090a"; g.fillRect(0, 330, 512, 330);
  const cx = 256, cy = 512;
  for (let i = 0; i <= 40; i++) {
    const a = Math.PI * (1.15 - 1.3 * i / 40), largo = i % 4 === 0 ? 26 : 14;
    g.strokeStyle = i < 6 ? "#e9fffb" : i > 32 ? "#c0392b" : "#2a5553"; g.lineWidth = i % 4 === 0 ? 7 : 4;
    g.beginPath(); g.moveTo(cx + Math.cos(a) * 128, cy - Math.sin(a) * 128); g.lineTo(cx + Math.cos(a) * (128 - largo), cy - Math.sin(a) * (128 - largo)); g.stroke();
  }
  g.fillStyle = "#7fb8b2"; g.font = "bold 20px sans-serif"; g.textAlign = "center";
  for (let k = 0; k <= 10; k += 2) { const a = Math.PI * (1.15 - 1.3 * k / 10); g.fillText(String(k), cx + Math.cos(a) * 84, cy - Math.sin(a) * 84 + 7); }
  g.fillText("x1000 r/min", cx, cy + 62);
  g.fillStyle = "#f2fffd"; g.font = "bold 78px sans-serif"; g.fillText("N", cx, cy + 30);
  const tex = new THREE.CanvasTexture(lienzo);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}
function ponerPantalla(moto, { c, n, tam, redonda, dibujo }) {
  const mat = moto.M.pantalla;
  const tex = mat.userData.soloEncendida ? mat.emissiveMap : texturaTablero();
  // (el dibujo solo va en la luz que emite: con la moto apagada la pantalla queda negra, como una de verdad)
  mat.emissiveMap = tex;
  mat.color.set(0x030607); mat.emissive.set(0xbff5ee);
  mat.userData.soloEncendida = true;
  mat.needsUpdate = true;
  const N = new THREE.Vector3(...n).normalize();
  const U = new THREE.Vector3(1, 0, 0).addScaledVector(N, -N.x).normalize(); // (arriba de la pantalla = hacia adelante)
  const R = new THREE.Vector3().crossVectors(U, N);
  const geo = redonda ? new THREE.CircleGeometry(tam[0] / 2, 40) : new THREE.PlaneGeometry(tam[0], tam[1]);
  // (cada pantalla toma su mitad del lienzo; la redonda, el cuadrado del centro de esa mitad)
  const uv = geo.attributes.uv, abajo = dibujo === "tacometro" ? 0 : 0.5;
  // (u al revés: la raíz de la moto va espejada en z y sin esto los números se leerían en espejo)
  for (let i = 0; i < uv.count; i++) uv.setXY(i, redonda ? 0.178 + (1 - uv.getX(i)) * 0.644 : 1 - uv.getX(i), abajo + uv.getY(i) * 0.5);
  const malla = new THREE.Mesh(geo, mat);
  malla.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(R, U, N));
  malla.position.set(...c);
  malla.name = "pantalla.tablero";
  malla.userData.glb = true;
  moto.raiz.add(malla);
}

// Labrado de las llantas del GLB (no traen UV): se envuelve alrededor del eje (u = ángulo, v = ancho) un relieve con
// un surco central y surcos inclinados a los lados; los costados quedan lisos. Solo relieve: no cambia el color.
function texturaLabrado() {
  const l = document.createElement("canvas");
  l.width = l.height = 128;
  const g = l.getContext("2d");
  g.fillStyle = "#8c8c8c"; g.fillRect(0, 0, 128, 128);
  g.strokeStyle = "#1c1c1c"; g.lineCap = "round";
  // (20-nov-2026: sin el canal corrido en el centro, que se veía como una raya fea; ranuras en V alternadas, como el
  // labrado de calle: cada lado sale del hombro hacia el centro sin cruzarlo, corrido media ranura del otro lado)
  g.lineWidth = 6;
  for (const x0 of [0, 64]) {
    g.beginPath(); g.moveTo(x0 + 4, 14); g.lineTo(x0 + 30, 56); g.stroke();
    g.beginPath(); g.moveTo(x0 + 36, 114); g.lineTo(x0 + 62, 72); g.stroke();
  }
  g.lineWidth = 4;
  for (const x0 of [0, 64]) { g.beginPath(); g.moveTo(x0 + 26, 60); g.lineTo(x0 + 40, 68); g.stroke(); }
  const tex = new THREE.CanvasTexture(l);
  tex.wrapS = THREE.RepeatWrapping;
  tex.anisotropy = 4;
  return tex;
}
function labrarLlanta(n) {
  const geo = n.geo.toNonIndexed(), p = geo.attributes.position, uv = new Float32Array(p.count * 2);
  const [ex, ey] = n.extras.eje, s = n.s[0], [tx, ty, tz] = n.t;
  let ancho = 1e-6;
  for (let i = 0; i < p.count; i++) ancho = Math.max(ancho, Math.abs(p.getZ(i) * s + tz));
  for (let i = 0; i < p.count; i += 3) {
    let a0 = 0;
    for (let k = 0; k < 3; k++) {
      let a = Math.atan2(p.getY(i + k) * s + ty - ey, p.getX(i + k) * s + tx - ex);
      // (los tres vértices de una cara del mismo lado del corte del ángulo: si no, una franja sale estirada)
      if (k === 0) a0 = a; else if (a - a0 > Math.PI) a -= 2 * Math.PI; else if (a0 - a > Math.PI) a += 2 * Math.PI;
      uv[(i + k) * 2] = a / (2 * Math.PI) * 30;
      uv[(i + k) * 2 + 1] = 0.5 + 0.5 * (p.getZ(i + k) * s + tz) / ancho;
    }
  }
  geo.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  n.geo = geo;
}

// Llanta del GLB rehecha como sólido de revolución (19-nov-2026). La de Tripo no es una rueda completa: donde toca el
// guardabarros, la horquilla o el basculante, el corte deja caras en el cuerpo fijo, y al girar se veía el hueco dando
// vueltas (y el pedazo quieto). Se mide su perfil (radio exterior por franjas de ancho, el 98 % para no fiarse de
// sueltos; radio interior en el asiento del aro) y se tornea alrededor del eje, 3 mm más grande para tapar esos pedazos.
// UV como labrarLlanta (u = ángulo × 30, v = ancho). Si la medida no cuadra, se deja la malla de Tripo labrada.
function tornearLlanta(n) {
  const p = n.geo.attributes.position, [ex, ey] = n.extras.eje, s = n.s[0], [tx, ty, tz] = n.t;
  const r = new Float32Array(p.count), z = new Float32Array(p.count);
  let z0 = Infinity, z1 = -Infinity;
  for (let i = 0; i < p.count; i++) {
    r[i] = Math.hypot(p.getX(i) * s + tx - ex, p.getY(i) * s + ty - ey);
    z[i] = p.getZ(i) * s + tz;
    z0 = Math.min(z0, z[i]); z1 = Math.max(z1, z[i]);
  }
  const cuantil = (a, q) => { const o = Float32Array.from(a).sort(); return o[Math.min(o.length - 1, Math.floor(q * o.length))]; };
  const rIn = cuantil(r, 0.03), FR = 14, holgura = 0.003, franjas = [];
  for (let k = 0; k < FR; k++) {
    const a = z0 + (z1 - z0) * k / FR, b = z0 + (z1 - z0) * (k + 1) / FR, en = [];
    for (let i = 0; i < p.count; i++) if (z[i] >= a && z[i] <= b) en.push(r[i]);
    franjas.push(en.length > 8 ? cuantil(en, 0.98) : null);
  }
  const rMax = Math.max(...franjas.filter((x) => x !== null));
  if (!(rMax > rIn + 0.02) || franjas.filter((x) => x !== null).length < FR * 0.6) return false;
  // Perfil (radio, z): del talón de un lado, por el costado y la banda, al talón del otro; franjas vacías interpoladas
  let lleno = franjas.map((x, k) => x ?? (franjas[k - 1] ?? franjas[k + 1] ?? rMax));
  // (extras.torno "redondo": corona lisa y simétrica entre el radio mayor y el de los hombros; la malla medida de algunas
  // motos da dos lomos con un canal en el medio, que de atrás se veía como dos llantas)
  if (n.extras.torno === "redondo") {
    const re = Math.min(rMax - 0.012, (lleno[0] + lleno[FR - 1]) / 2);
    lleno = lleno.map((_, k) => { const u = (k + 0.5) / FR * 2 - 1; return re + (rMax - re) * Math.sqrt(Math.max(0, 1 - u ** 4)); });
  }
  const zc = (z0 + z1) / 2, mitad = (z1 - z0) / 2 + holgura;
  // (costados abombados: tres puntos entre el talón y la primera franja, que salen hasta el ancho completo a media
  // altura; antes era un cono recto y de lado la llanta se veía rara)
  const banda = lleno.map((x, k) => new THREE.Vector2(Math.max(rIn + 0.004, x + holgura), zc - mitad + (2 * mitad) * (k + 0.5) / FR));
  const costado = (signo, borde) => [0.3, 0.55, 0.8].map((t) => new THREE.Vector2(rIn + (borde.x - rIn) * t,
    zc + signo * mitad * (0.92 + 0.1 * Math.sin(Math.PI * t))));
  const pts = [new THREE.Vector2(rIn, zc - mitad * 0.92), ...costado(-1, banda[0]), ...banda,
    ...costado(1, banda[FR - 1]).reverse(), new THREE.Vector2(rIn, zc + mitad * 0.92)];
  const geo = new THREE.LatheGeometry(pts, 72);
  // Labrado solo en la banda de rodadura: el costado toma la franja lisa del lienzo (antes las rayas se estiraban por
  // todo el costado). v por punto del perfil: liso hasta el 75 % de la altura, rayas en la banda.
  {
    const uvp = geo.attributes.uv, alto = rMax - rIn, enBanda = pts.map((q) => q.x > rIn + 0.75 * alto);
    const i0 = enBanda.indexOf(true), i1 = enBanda.lastIndexOf(true);
    const vs = pts.map((q, j) => (j < i0 ? 0.04 : j > i1 ? 0.96 : 0.12 + 0.76 * (j - i0) / Math.max(1, i1 - i0)));
    for (let i = 0; i < uvp.count; i++) uvp.setY(i, vs[i % pts.length]);
  }
  // (el torno gira alrededor de y: se acuesta sobre z, se lleva al eje y se pasa a las coordenadas del nodo)
  geo.rotateX(Math.PI / 2); // (la y del perfil pasa a ser la z de la moto)
  geo.translate(ex - tx, ey - ty, -tz).scale(1 / s, 1 / s, 1 / s);
  const uv = geo.attributes.uv;
  for (let i = 0; i < uv.count; i++) uv.setX(i, uv.getX(i) * 30);
  geo.computeVertexNormals();
  n.geo = geo;
  return true;
}

// Monta el GLB en moto (lo que devuelve construirMoto). Devuelve true si quedó puesto.
export async function montarGlb(moto, url) {
  const nodos = await leerGlb(url);
  const M = moto.M;
  // Modo «modelo completo» (extras.modelo_completo en la escena, 21-nov-2026): el GLB se muestra tal cual. El visor solo
  // gira las ruedas, enciende las luces del GLB, pinta según Personalizar y aplica Rayos X (y pone la placa): sin pata, espejos,
  // escape, farola ni accesorios genéricos, y sin tornear, labrar ni reemplazar llantas. Los GLB sin la marca siguen igual.
  const completo = !!nodos.escena.modelo_completo;
  const manubrioProc = manubrioProcedural(moto); // (antes de que el GLB vacíe los espejos de fábrica)
  const ajustes = [];
  // Lo que se conserva de la moto procedural: piezas de mantenimiento, accesorios, espejos, placa, pata y escape
  // (Personalizar y el plan de mantenimiento los usan). Lo demás (la carrocería genérica) se oculta.
  const protegidos = new Set([...Object.values(moto.piezas), ...Object.values(moto.accesorios || {}),
    ...Object.values(moto.espejos || {}), moto.placa, moto.pata, moto.escapeFabrica].filter(Boolean));
  const protegido = (o) => { for (let p = o; p && p !== moto.raiz; p = p.parent) if (protegidos.has(p)) return true; return false; };
  // (con userData.oculto: el cambio de modo de moto3d.js pone visible = !oculto en todas las mallas; sin esto la
  // carrocería procedural volvía a dibujarse encima del GLB)
  const ocultar = (o) => { o.visible = false; o.userData.oculto = true; };
  moto.raiz.traverse((o) => { if (o.isMesh && !o.userData.calca && !protegido(o)) ocultar(o); });
  // Destinos que el GLB reemplaza: se ocultan sus mallas originales una sola vez
  const vaciados = new Set();
  const vaciar = (destino, conRin) => {
    if (vaciados.has(destino)) return;
    vaciados.add(destino);
    destino.traverse((o) => {
      if (o === destino) return;
      // (el rin procedural de fábrica se renombra para que "Personalizar" ya no lo vuelva a mostrar)
      if (conRin && o.userData.rin) { o.userData.rin = "~" + o.userData.rin; o.visible = false; }
      else if (o.isMesh) ocultar(o);
    });
    if (destino.isMesh) destino.geometry.setDrawRange(0, 0);
  };
  // Acabados propios del GLB (no los toca Personalizar): plástico negro mate texturizado, negro de piano y mica ahumada
  M.plastico ??= new THREE.MeshStandardMaterial({ color: 0x1f2224, roughness: 0.9, metalness: 0 });
  M.negro_brillo ??= new THREE.MeshPhysicalMaterial({ color: 0x0c0e0f, roughness: 0.22, metalness: 0.1, clearcoat: 1, clearcoatRoughness: 0.05 });
  M.vidrio_oscuro ??= new THREE.MeshPhysicalMaterial({ color: 0x1b2226, transparent: true, opacity: 0.86, roughness: 0.03, clearcoat: 1, depthWrite: false });
  M.dorado ??= new THREE.MeshStandardMaterial({ color: 0xc9a23a, roughness: 0.3, metalness: 0.85 });
  M.faro ??= new THREE.MeshPhysicalMaterial({ color: 0x3a4146, roughness: 0.12, metalness: 0.9, clearcoat: 1, clearcoatRoughness: 0.03 });
  M.disco ??= new THREE.MeshStandardMaterial({ color: 0xb9bec1, roughness: 0.34, metalness: 0.6 });
  // Reflector del faro (modelo completo, 21-nov-2026): apagado se ve como la parábola cromada detrás de la mica clara;
  // al encender brilla como la luz baja (moto3d.js le sube el emisivo junto con la tira LED de M.luz)
  M.luz_reflector ??= new THREE.MeshPhysicalMaterial({ color: 0xe1e5e8, roughness: 0.2, metalness: 0.7, clearcoat: 1, clearcoatRoughness: 0.04,
    emissive: 0xfff3d6, emissiveIntensity: 0 });
  // Direccional de mica transparente con bombillo ámbar (va dentro de la unidad del stop): apagada se ve clara y solo
  // se pone ámbar cuando parpadea (userData.direccional la suma al saludo de «Encender»)
  M.mica_dir ??= new THREE.MeshPhysicalMaterial({ color: 0xe3e7e9, roughness: 0.1, metalness: 0.15, clearcoat: 1, clearcoatRoughness: 0.03,
    emissive: 0xff9a1f, emissiveIntensity: 0, userData: { direccional: true } });
  // Reflector ámbar (no alumbra ni parpadea)
  M.reflector ??= new THREE.MeshPhysicalMaterial({ color: 0xff9226, roughness: 0.25, metalness: 0.1, clearcoat: 0.8 });
  M.titanio ??= new THREE.MeshStandardMaterial({ color: 0x4b4845, roughness: 0.55, metalness: 0.35 });
  M.blanco ??= new THREE.MeshPhysicalMaterial({ color: 0xb5bbca, roughness: 0.45, metalness: 0, clearcoat: 0.4 }); // (plástico blanco de fábrica: tapas laterales de la XR 190L)
  const visores = [];
  let visorFijo = false;
  const lamparas = [];
  for (const n of nodos) {
    let mat = M[n.material] || M.oscuro;
    // (extras.tono / acabado / emisivo: color base propio de una pieza sin tocar el material que comparten las otras
    // motos; solo en piezas que Personalizar no recolorea)
    if (n.material === "chasis" && n.extras.tono) {
      // (chasis con tono de fábrica: pasa a ser el «chasis a la vista», que Personalizar deja de serie o cambia al color elegido)
      M.chasisVisto ??= M.chasis.clone();
      M.chasisVisto.color.set(n.extras.tono); M.chasisVisto.userData.fabrica = M.chasisVisto.color.getHex();
      if (n.extras.acabado) Object.assign(M.chasisVisto, n.extras.acabado);
      mat = M.chasisVisto;
    } else if (n.extras.tono || n.extras.emisivo) {
      mat = mat.clone();
      if (n.extras.tono) mat.color.set(n.extras.tono);
      if (n.extras.emisivo && mat.emissive) mat.emissive.set(n.extras.emisivo);
      if (n.extras.acabado) Object.assign(mat, n.extras.acabado);
      // (plástico blanco con tono de fábrica: sigue al color secundario de Personalizar; con el de serie conserva su tono)
      if (n.material === "blanco" && n.extras.tono) { mat.userData.fabrica = mat.color.getHex(); (M.secundarios ??= []).push(mat); }
    }
    // (extras.rueda "del" | "tras", 21-nov-2026: rueda de Tripo que gira tal cual, sin llanta torneada ni labrado. El nodo
    // lleva su traslación en el centro del eje, que hace de pivote; llanta, rin y disco o corona llevan la misma marca.
    // Los GLB viejos, sin la marca, siguen con el torneado de abajo.)
    if (!completo && n.material === "caucho" && n.extras.eje && !n.extras.rueda && /llanta/.test(n.nombre)) {
      M.caucho_labrado ??= Object.assign(M.caucho.clone(), { bumpMap: texturaLabrado(), bumpScale: 2.2 });
      if (!tornearLlanta(n)) labrarLlanta(n);
      mat = M.caucho_labrado;
    }
    // (extras.luz: factor de brillo de una pieza pintada que en la foto queda a la sombra, p. ej. el colín bajo el asiento;
    // copia en cada cuadro el color y el acabado del material compartido, así Personalizar la sigue pintando)
    // (extras.acabado sin tono: el material propio de la pieza, p. ej. plástico inyectado en vez de pintura metalizada,
    // con el color que Personalizar le dé al material compartido)
    const base = mat, acab = !n.extras.tono && !n.extras.emisivo && n.extras.acabado, luz = n.extras.luz || (acab ? 1 : 0);
    if (luz) mat = Object.assign(base.clone(), acab || {});
    const malla = new THREE.Mesh(n.geo, mat);
    if (luz) malla.onBeforeRender = () => {
      mat.color.copy(base.color).multiplyScalar(luz);
      for (const k of ["roughness", "metalness", "clearcoat", "clearcoatRoughness", "side"]) if (k in base && !(acab && k in acab)) mat[k] = base[k];
    };
    malla.name = n.nombre;
    malla.position.fromArray(n.t);
    malla.scale.fromArray(n.s);
    malla.castShadow = malla.receiveShadow = true;
    malla.userData.glb = true; // (así unirEstaticas no la fusiona con otras y conserva su nombre "material.parte")
    // (extras.interno: pieza que va tapada por la carrocería, como la batería o el radiador; solo se ve en Rayos X)
    if (n.extras.interno) { malla.userData.interno = true; malla.visible = false; malla.castShadow = false; }
    let destino = moto.raiz;
    const ex = n.extras;
    const piezaDe = ex.rueda ? "llanta_" + ex.rueda : ex.pieza;
    if (piezaDe && moto.piezas[piezaDe]) {
      const g = moto.piezas[piezaDe];
      destino = g.userData.pivoteRueda || g;
      // (extras.eje [x, y]: centro real de la rueda del GLB; el pivote se lleva ahí para que gire sin cabecear.
      // Con extras.rueda el centro es la traslación del nodo.)
      const eje = ex.rueda ? n.t : ex.eje;
      if (eje && destino !== g && !vaciados.has(destino)) { destino.position.x = eje[0]; destino.position.y = eje[1]; }
      vaciar(destino, true);
      if (ex.rin) malla.userData.rin = moto.rinFabrica;
      if (ex.aro) malla.userData.aro = true;
      if (completo && (ex.rin || ex.aro)) malla.userData.glbMat = malla.material; // (para volver al rin de fábrica) // (aro aparte: queda con cualquier estilo de rin y Personalizar le cambia el color)
      // (las ruedas giran sobre un pivote en su centro: la malla del GLB está en coordenadas de la moto)
      if (destino !== g) { destino.updateMatrixWorld(true); moto.raiz.updateMatrixWorld(true); }
    } else if (ex.padre) {
      // (si la procedural no trae escape de fábrica, el del GLB hace sus veces: Personalizar lo oculta al poner el deportivo)
      if (ex.padre === "escapeFabrica" && !moto.escapeFabrica) {
        moto.escapeFabrica = new THREE.Group();
        moto.escapeFabrica.name = "escape_glb";
        moto.raiz.add(moto.escapeFabrica);
        vaciados.add(moto.escapeFabrica);
      }
      const obj = ex.padre.split(".").reduce((o, k) => o?.[k], moto);
      if (obj) { destino = obj; vaciar(obj, false); }
    }
    if (ex.rol === "visor") visores.push(malla);
    // ("visor_fijo": también reemplaza al visor genérico, pero no se esconde al poner el parabrisas accesorio,
    // porque en ese GLB el visor cierra la carrocería y sin él quedaría un hueco)
    if (ex.rol === "visor_fijo") visorFijo = true;
    if (ex.placa && moto.placa) ponerPlacaEn(moto, ex.placa);
    if (ex.lampara) lamparas.push(lamparaDe(n, ex.lampara));
    // (extras.zonas: panel pintado donde se pegan calcas, las propias y las de fábrica, igual que en la moto genérica)
    if (ex.zonas) { malla.userData.zonas = ex.zonas; moto.raiz.userData.glbZonas = true; }
    // (extras.doble: pieza que Tripo dejó como lámina abierta, p. ej. llanta o guardabarros: por dentro se veía hueca)
    if (ex.doble) malla.material.side = THREE.DoubleSide;
    // (modelo completo: las caras de Tripo vienen abiertas o con la normal al revés; con una sola cara la llanta trasera
    // se veía con huecos. Se dibujan las dos caras: no cambia la geometría)
    if (completo) malla.material.side = THREE.DoubleSide;
    // (extras.calcas_fabrica: las calcas de fábrica de este modelo, ya ubicadas sobre él con "en: [x, y]")
    if (ex.calcas_fabrica) moto.raiz.userData.calcasFabrica = ex.calcas_fabrica;
    if (!completo) for (const p of [].concat(ex.pantalla || [])) ponerPantalla(moto, p);
    // (extras.sin ["accesorios.parabrisas", "espejos.puntas"…]: opciones de Personalizar que este modelo no ofrece,
    // porque la pieza genérica desentona con él. Se quitan de la moto: el visor y el cajón ya no las ven.)
    for (const ruta of ex.sin || []) {
      const [grupo, clave] = ruta.split(".");
      const g = moto[grupo]?.[clave];
      if (!g || (grupo === "espejos" && clave === "fabrica")) continue;
      g.visible = false;
      g.traverse((o) => { if (o.isMesh) ocultar(o); });
      delete moto[grupo][clave];
    }
    if (ex.manubrio && manubrioProc && !completo) ajustes.push(() => alManubrio(moto, manubrioProc, ex.manubrio,
      [...Object.entries(moto.espejos || {}).filter(([k]) => k !== "fabrica").map(([, g]) => g), moto.accesorios?.cubremanos]));
    if (!completo) for (const a of ex.acomodar || []) ajustes.push(() => acomodar(moto, a));
    // La malla está en coordenadas de la raíz: si el destino es un grupo movido, se compensa su transformación
    if (destino !== moto.raiz) {
      moto.raiz.updateMatrixWorld(true);
      const inv = new THREE.Matrix4().copy(moto.raiz.matrixWorld).invert().multiply(destino.matrixWorld).invert();
      malla.applyMatrix4(inv);
    }
    destino.add(malla);
  }
  if ((visores.length || visorFijo) && moto.visoresFabrica) {
    for (const v of moto.visoresFabrica) { v.visible = false; v.userData.oculto = true; }
    moto.visoresFabrica.length = 0;
    moto.visoresFabrica.push(...visores);
  }
  // Con modelo realista, Personalizar → Accesorios ofrece solo baúl y luz LED, en todas las motos (decisión del usuario,
  // 19-nov-2026): parabrisas, cubremanos, exploradoras, sliders, escape deportivo y protector genéricos desentonan.
  if (completo) quitarGenericas(moto, ocultar, vaciar, lamparas);
  for (const clave of Object.keys(moto.accesorios || {})) {
    if (ACCESORIOS_GLB.includes(clave) && !completo) continue;
    const g = moto.accesorios[clave];
    g.visible = false;
    g.traverse((o) => { if (o.isMesh) ocultar(o); });
    delete moto.accesorios[clave];
  }
  if (moto.anclas?.lamparas) moto.anclas.lamparas = moto.anclas.lamparas.filter((l) => !l.accesorio || ACCESORIOS_GLB.includes(l.accesorio));
  for (const f of ajustes) f();
  // Las lámparas del GLB reemplazan a las de la moto genérica del mismo tipo (que ya no se ven)
  if (lamparas.length && moto.anclas && !completo) {
    const tipos = new Set(lamparas.map((l) => l.tipo));
    moto.anclas.lamparas = [...(moto.anclas.lamparas || []).filter((l) => !tipos.has(l.tipo)), ...lamparas];
  }
  // Piezas de mantenimiento que el GLB no trae (batería, bujía, filtro, aceite, radiador…): en la moto real van tapadas
  // por la carrocería; las procedurales asomaban o repetían el motor del GLB. Quedan internas: solo en Rayos X.
  for (const g of Object.values(moto.piezas)) {
    if (vaciados.has(g) || vaciados.has(g.userData.pivoteRueda)) continue;
    g.traverse((o) => { if (o.isMesh && !o.userData.glb) { o.userData.interno = true; o.visible = false; } });
  }
  moto.raiz.userData.glb = url;
  moto.raiz.userData.modeloCompleto = completo;
  // (modelo completo: Personalizar ofrece calcas solo si el GLB trae las suyas, extras.calcas de la escena; ver la skill)
  moto.raiz.userData.calcasModelo = completo && !!nodos.escena.calcas;
  return true;
}

// Modelo completo: fuera todo lo procedural que se veía encima del GLB. Lo que el GLB no reemplazó (espejos de fábrica,
// escape, visor) se vacía; los otros estilos de espejos y los accesorios salen de la moto (Personalizar ya no los ofrece);
// la pata se oculta y las luces son solo las del GLB. La placa sí se pone (excepción permitida por el usuario, 21-nov-2026).
// La geometría del GLB no se agrega, reemplaza, recorta ni tornea.
function quitarGenericas(moto, ocultar, vaciar, lamparas) {
  const fuera = (g) => { if (!g) return; g.visible = false; g.userData.oculto = true; g.traverse((o) => { if (o.isMesh) ocultar(o); }); };
  for (const [clave, g] of Object.entries(moto.espejos || {})) {
    if (clave === "fabrica") vaciar(g, false);
    else { fuera(g); delete moto.espejos[clave]; }
  }
  if (moto.escapeFabrica) vaciar(moto.escapeFabrica, false);
  fuera(moto.pata);
  if (moto.visoresFabrica) {
    for (const v of moto.visoresFabrica) if (!v.userData.glb) fuera(v);
    moto.visoresFabrica.splice(0, moto.visoresFabrica.length, ...moto.visoresFabrica.filter((v) => v.userData.glb));
  }
  if (moto.anclas) moto.anclas.lamparas = [...lamparas];
}
