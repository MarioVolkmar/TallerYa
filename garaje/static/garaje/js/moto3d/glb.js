// Carga un GLB de carrocería "realista" (skill moto-3d-realista) y lo monta sobre la moto procedural.
// Piloto: solo se activa con ?modelo3d=glb en la dirección (o localStorage "moto3d_glb" = "1") y solo para las
// líneas que tienen GLB. Si algo falla, la moto procedural queda tal cual (respaldo).
// El GLB lo escribe .claude/skills/moto-3d-realista/scripts/glb.py: nodos "material.parte", posiciones int16 y
// normales int8 (KHR_mesh_quantization) y extras {pieza, padre, rin, rol} que dicen dónde va cada malla.
import * as THREE from "three";

// (?v= cambia con cada versión del GLB: así el navegador no se queda con el anterior en caché)
const MODELOS = { nmax: "../../modelos/nmax155.glb?v=19" };
// Variante ?modelo3d=tripo: malla base generada con IA, aligerada y partida en piezas con nombre (mismo formato)
const MODELOS_TRIPO = { nmax: "../../modelos/nmax155_tripo.glb?v=3" };

export function glbDeLinea(linea) {
  const pedido = new URLSearchParams(location.search).get("modelo3d");
  let activo = pedido === "glb" || pedido === "tripo";
  try { activo ||= localStorage.getItem("moto3d_glb") === "1"; } catch { /* sin almacenamiento */ }
  if (!activo) return null;
  const modelos = pedido === "tripo" ? MODELOS_TRIPO : MODELOS;
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
  return g.nodes.map((n) => {
    const pr = g.meshes[n.mesh].primitives[0];
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", atributo(pr.attributes.POSITION));
    geo.setAttribute("normal", atributo(pr.attributes.NORMAL));
    geo.setIndex(atributo(pr.indices));
    geo.computeBoundingSphere();
    return { nombre: n.name, material: n.name.split(".")[0], geo, t: n.translation || [0, 0, 0], s: n.scale || [1, 1, 1], extras: n.extras || {} };
  });
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

// Monta el GLB en moto (lo que devuelve construirMoto). Devuelve true si quedó puesto.
export async function montarGlb(moto, url) {
  const nodos = await leerGlb(url);
  const M = moto.M;
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
  M.vidrio_oscuro ??= new THREE.MeshPhysicalMaterial({ color: 0x1b2226, transparent: true, opacity: 0.55, roughness: 0.03, clearcoat: 1, depthWrite: false });
  M.dorado ??= new THREE.MeshStandardMaterial({ color: 0xc9a23a, roughness: 0.3, metalness: 0.85 });
  M.titanio ??= new THREE.MeshStandardMaterial({ color: 0x4b4845, roughness: 0.55, metalness: 0.35 });
  const visores = [];
  let visorFijo = false;
  for (const n of nodos) {
    const mat = M[n.material] || M.oscuro;
    const malla = new THREE.Mesh(n.geo, mat);
    malla.name = n.nombre;
    malla.position.fromArray(n.t);
    malla.scale.fromArray(n.s);
    malla.castShadow = malla.receiveShadow = true;
    malla.userData.glb = true; // (así unirEstaticas no la fusiona con otras y conserva su nombre "material.parte")
    let destino = moto.raiz;
    const ex = n.extras;
    if (ex.pieza && moto.piezas[ex.pieza]) {
      const g = moto.piezas[ex.pieza];
      destino = g.userData.pivoteRueda || g;
      // (extras.eje [x, y]: centro real de la rueda del GLB; el pivote se lleva ahí para que gire sin cabecear)
      if (ex.eje && destino !== g && !vaciados.has(destino)) { destino.position.x = ex.eje[0]; destino.position.y = ex.eje[1]; }
      vaciar(destino, true);
      if (ex.rin) malla.userData.rin = moto.rinFabrica;
      if (ex.aro) malla.userData.aro = true; // (aro aparte: queda con cualquier estilo de rin y Personalizar le cambia el color)
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
    if (ex.manubrio && manubrioProc) ajustes.push(() => alManubrio(moto, manubrioProc, ex.manubrio,
      [...Object.entries(moto.espejos || {}).filter(([k]) => k !== "fabrica").map(([, g]) => g), moto.accesorios?.cubremanos]));
    for (const a of ex.acomodar || []) ajustes.push(() => acomodar(moto, a));
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
  for (const f of ajustes) f();
  // Piezas de mantenimiento que el GLB no trae (batería, bujía, filtro, aceite, radiador…): en la moto real van tapadas
  // por la carrocería; las procedurales asomaban o repetían el motor del GLB. Quedan internas: solo en Rayos X.
  for (const g of Object.values(moto.piezas)) {
    if (vaciados.has(g) || vaciados.has(g.userData.pivoteRueda)) continue;
    g.traverse((o) => { if (o.isMesh && !o.userData.glb) { o.userData.interno = true; o.visible = false; } });
  }
  moto.raiz.userData.glb = url;
  return true;
}
