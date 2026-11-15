// Utilidades de geometría: subdivisión, unión de vértices y de mallas, contornos.
import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";

// Contorno convexo de dos círculos (para el recorrido de la cadena).
export function cascoCirculos(circulos) {
  const puntos = [];
  for (const [cx, cy, r] of circulos) {
    for (let i = 0; i < 40; i++) {
      const a = (i / 40) * Math.PI * 2;
      puntos.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
  }
  puntos.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cruz = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const inferior = [];
  for (const p of puntos) {
    while (inferior.length >= 2 && cruz(inferior.at(-2), inferior.at(-1), p) <= 0) inferior.pop();
    inferior.push(p);
  }
  const superior = [];
  for (const p of puntos.slice().reverse()) {
    while (superior.length >= 2 && cruz(superior.at(-2), superior.at(-1), p) <= 0) superior.pop();
    superior.push(p);
  }
  return inferior.slice(0, -1).concat(superior.slice(0, -1));
}

// Subdivisión adaptativa: solo se parten las aristas más largas que `maximo` (las de las tapas grandes); las caras
// ya densas quedan igual. Como la decisión es por arista (compartida entre vecinos), no quedan grietas ni "T".
export function subdividir(geo, maximo, vueltas = 4) {
  const pos = Array.from(geo.attributes.position.array);
  let idx = Array.from(geo.index.array);
  const largo = (a, b) => Math.hypot(pos[a * 3] - pos[b * 3], pos[a * 3 + 1] - pos[b * 3 + 1], pos[a * 3 + 2] - pos[b * 3 + 2]);
  for (let v = 0; v < vueltas; v++) {
    const medios = new Map();
    const clave = (a, b) => (a < b ? a * 4194304 + b : b * 4194304 + a);
    let partidas = 0;
    for (let i = 0; i < idx.length; i += 3) {
      for (const [a, b] of [[idx[i], idx[i + 1]], [idx[i + 1], idx[i + 2]], [idx[i + 2], idx[i]]]) {
        const k = clave(a, b);
        if (!medios.has(k) && largo(a, b) > maximo) {
          medios.set(k, pos.length / 3);
          pos.push((pos[a * 3] + pos[b * 3]) / 2, (pos[a * 3 + 1] + pos[b * 3 + 1]) / 2, (pos[a * 3 + 2] + pos[b * 3 + 2]) / 2);
          partidas++;
        }
      }
    }
    if (!partidas) break;
    const nuevo = [];
    for (let i = 0; i < idx.length; i += 3) {
      const t = [idx[i], idx[i + 1], idx[i + 2]];
      const m = [medios.get(clave(t[0], t[1])), medios.get(clave(t[1], t[2])), medios.get(clave(t[2], t[0]))];
      const n = m.filter((x) => x !== undefined).length;
      if (n === 0) { nuevo.push(...t); continue; }
      if (n === 3) { nuevo.push(t[0], m[0], m[2], m[0], t[1], m[1], m[2], m[1], t[2], m[0], m[1], m[2]); continue; }
      // Girar para que la (primera) arista partida sea la de t[0]→t[1]
      let r = 0;
      if (n === 1) r = m.findIndex((x) => x !== undefined);
      else r = m[0] === undefined ? 1 : m[1] === undefined ? 2 : 0; // con dos partidas: la que sigue a la no partida
      const a = t[r], b = t[(r + 1) % 3], c = t[(r + 2) % 3];
      const mab = m[r], mbc = m[(r + 1) % 3];
      if (n === 1) nuevo.push(a, mab, c, mab, b, c);
      else nuevo.push(mab, b, mbc, a, mab, mbc, a, mbc, c);
    }
    idx = nuevo;
  }
  const salida = new THREE.BufferGeometry();
  salida.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  salida.setIndex(idx);
  return salida;
}

// Une los vértices repetidos de una geometría sin índice que solo tiene posiciones (como mergeVertices de three,
// pero bastante más rápido: clave numérica por vértice en vez de recorrer todos los atributos como texto).
export function unirVertices(geo) {
  const pos = geo.attributes.position.array;
  const n = pos.length / 3;
  const mapa = new Map();
  const indices = new Uint32Array(n);
  const unicos = [];
  for (let i = 0; i < n; i++) {
    const x = Math.round(pos[i * 3] * 1e5), y = Math.round(pos[i * 3 + 1] * 1e5), z = Math.round(pos[i * 3 + 2] * 1e5);
    const clave = x * 73856093 ^ y * 19349663 ^ z * 83492791;
    let lista = mapa.get(clave), idx = -1;
    if (lista) for (const j of lista) if (unicos[j * 3] === x && unicos[j * 3 + 1] === y && unicos[j * 3 + 2] === z) { idx = j; break; }
    if (idx < 0) {
      idx = unicos.length / 3;
      unicos.push(x, y, z);
      if (lista) lista.push(idx); else mapa.set(clave, [idx]);
    }
    indices[i] = idx;
  }
  const salida = new THREE.BufferGeometry();
  salida.setAttribute("position", new THREE.Float32BufferAttribute(Float32Array.from(unicos, (v) => v / 1e5), 3));
  salida.setIndex(new THREE.BufferAttribute(indices, 1));
  return salida;
}

// Une las mallas sueltas de un grupo que comparten material en una sola (ver "Rendimiento" en construirMoto).
export function unirDecorado(grupo) {
  const porMaterial = new Map();
  for (const m of [...grupo.children]) {
    if (!m.isMesh || m.isInstancedMesh || m.children.length || Object.keys(m.userData).length) continue;
    if (!porMaterial.has(m.material)) porMaterial.set(m.material, []);
    porMaterial.get(m.material).push(m);
  }
  for (const [material, lista] of porMaterial) {
    if (lista.length < 2) continue; // (desde dos: cada par unido es una llamada de dibujo menos)
    const geos = lista.map((m) => {
      m.updateMatrix();
      const g = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
      for (const k of Object.keys(g.attributes)) if (k !== "position" && k !== "normal") g.deleteAttribute(k);
      if (!g.attributes.normal) g.computeVertexNormals();
      g.applyMatrix4(m.matrix);
      return g;
    });
    const unida = mergeGeometries(geos);
    geos.forEach((g) => g.dispose());
    if (!unida) continue;
    for (const m of lista) { grupo.remove(m); m.geometry.dispose(); }
    const malla = new THREE.Mesh(unida, material);
    malla.castShadow = true;
    grupo.add(malla);
  }
}

// Une las mallas fijas que comparten material, cada una dentro de su "ancla": la raíz, cada pieza del despiece
// (así en Estado y Rayos X se sigue tocando y pintando pieza por pieza), cada variante o accesorio que se prende y
// apaga, y lo que se mueve en la animación (el pivote de cada rueda, el gato). Baja las llamadas de dibujo a menos
// de la mitad. Quedan sueltas las mallas con datos propios (internas, bordes, zonas de calcas…) y las instanciadas.
// Con piezaComoAncla = false (portada: ahí no hay modos Estado ni Rayos X) se une a través de las piezas.
// (materiales que el visor guarda por malla para los modos: no impiden unir; se vuelven a crear al cambiar de modo)
const MATERIALES_DE_MODO = ["original", "matEstado", "matRayos"];
export function unirEstaticas(raiz, movibles = [], piezaComoAncla = true) {
  const esAncla = new Set(movibles);
  const neutras = piezaComoAncla ? ["original"] : ["original", "pieza"];
  const anclaDe = (o) => {
    let p = o.parent;
    while (p && p !== raiz && !esAncla.has(p) && !Object.keys(p.userData).some((k) => !neutras.includes(k))) p = p.parent;
    return p || raiz;
  };
  const libre = (m) => m.isMesh && !m.isInstancedMesh && !m.isSkinnedMesh && !m.children.length && m.geometry.attributes.position
    && !Array.isArray(m.material) && !Object.keys(m.userData).some((k) => !MATERIALES_DE_MODO.includes(k));
  raiz.updateMatrixWorld(true);
  const grupos = new Map();
  raiz.traverse((m) => {
    if (!libre(m)) return;
    const ancla = anclaDe(m);
    const clave = ancla.uuid + "|" + m.material.uuid + "|" + m.visible + "|" + m.castShadow + "|" + m.receiveShadow;
    if (!grupos.has(clave)) grupos.set(clave, { ancla, lista: [] });
    grupos.get(clave).lista.push(m);
  });
  let unidas = 0;
  const inversa = new THREE.Matrix4(), rel = new THREE.Matrix4();
  for (const { ancla, lista } of grupos.values()) {
    if (lista.length < 2) continue;
    const material = lista[0].material;
    // Atributos comunes a todas (si el material usa textura, todas deben tener uv)
    const comunes = ["position", "normal", "uv"].filter((k) => lista.every((m) => m.geometry.attributes[k]));
    if (material.map && !comunes.includes("uv")) continue;
    inversa.copy(ancla.matrixWorld).invert();
    const geos = lista.map((m) => {
      const g = new THREE.BufferGeometry();
      for (const k of comunes) g.setAttribute(k, m.geometry.attributes[k].clone());
      const n = g.attributes.position.count;
      g.setIndex(m.geometry.index ? m.geometry.index.clone() : [...Array(n).keys()]);
      if (!g.attributes.normal) g.computeVertexNormals();
      g.applyMatrix4(rel.multiplyMatrices(inversa, m.matrixWorld));
      return g;
    });
    const unida = mergeGeometries(geos);
    geos.forEach((g) => g.dispose());
    if (!unida) continue;
    const malla = new THREE.Mesh(unida, material);
    Object.assign(malla, { castShadow: lista[0].castShadow, receiveShadow: lista[0].receiveShadow, visible: lista[0].visible });
    if (lista[0].userData.original) malla.userData.original = lista[0].userData.original;
    for (const m of lista) m.removeFromParent();
    ancla.add(malla);
    unidas += lista.length - 1;
  }
  return unidas;
}
