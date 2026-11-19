// Control de duplicados y piezas sobrantes con el GLB montado (skill moto-3d-realista).
// Uso: en /garaje/<pk>/vista-3d/?modelo3d=glb, pegar este archivo en la consola (o en javascript_tool) y luego
//   await inventario()            → { ok, categorias, duplicados, flotantes, sueltas, repetidos }
//   await inventario({ estilo })  → primero aplica ese estilo de Personalizar (accesorios, espejos, rin…)
// Cuenta solo lo que se dibuja: cadena de padres visible, sin calcas ni las mallas fusionadas del visor (grupoMoto
// junta copias de mallas visibles; las originales siguen contando aquí aunque tengan el material invisible).
// - duplicados: malla procedural (que no sea accesorio ni espejo) y malla del GLB que ocupan casi la misma caja (≥ 50 % de la menor y tamaños
//   parecidos): la misma pieza dibujada dos veces (el manubrio doble de la otra estrategia).
// - flotantes: grupo procedural conservado (accesorio, espejos, placa, pata) a más de 3 cm de todo vértice del GLB.
// - sueltas: malla procedural visible que no es de ningún grupo conservado: la carrocería genérica no se ocultó.
// - repetidos: el mismo nombre de nodo del GLB más de una vez.
// - categorias: cuántas fuentes (glb / procedural) dibujan cada parte; ok solo si cada una tiene una sola fuente.
window.inventario = async function ({ estilo = null, holgura = 0.03 } = {}) {
  const T = await import("three");
  const v = window.__visor, m = v._moto;
  if (estilo) { window.TallerYa3D.aplicar({ estilo }); await new Promise((r) => setTimeout(r, 300)); }
  m.raiz.updateMatrixWorld(true);
  const grupos = new Map();
  const marcar = (g, n) => g && grupos.set(g, n);
  for (const [k, g] of Object.entries(m.piezas)) marcar(g, "pieza:" + k);
  for (const [k, g] of Object.entries(m.accesorios || {})) marcar(g, "accesorio:" + k);
  for (const [k, g] of Object.entries(m.espejos || {})) marcar(g, "espejos:" + k);
  marcar(m.placa, "placa"); marcar(m.pata, "pata"); marcar(m.escapeFabrica, "escape");
  const grupoDe = (o) => { for (let p = o; p && p !== m.raiz; p = p.parent) if (grupos.has(p)) return grupos.get(p); return null; };
  const seDibuja = (o) => { for (let p = o; p; p = p.parent) if (!p.visible) return false; const d = o.geometry?.drawRange; return !(d && d.count === 0); };
  const glb = [], proc = [];
  m.raiz.traverse((o) => {
    if (!o.isMesh || o.userData.calca || o.userData.grupoMoto || !seDibuja(o)) return;
    const caja = new T.Box3().setFromObject(o);
    let rin = null; for (let q = o; q && q !== m.raiz && !rin; q = q.parent) if (q.userData.rin && !String(q.userData.rin).startsWith("~")) rin = q.userData.rin;
    (o.userData.glb ? glb : proc).push({ o, caja, nombre: o.name, grupo: grupoDe(o), rin });
  });
  const vol = (b) => { const s = b.getSize(new T.Vector3()); return Math.max(s.x, 1e-3) * Math.max(s.y, 1e-3) * Math.max(s.z, 1e-3); };
  const r3 = (x) => +x.toFixed(3);
  const centro = (b) => b.getCenter(new T.Vector3()).toArray().map(r3);
  const duplicados = [], flotantes = [], sueltas = [];
  const puntos = [], w = new T.Vector3();
  for (const g of glb) {
    const pos = g.o.geometry.attributes.position;
    for (let i = 0; i < pos.count; i += 2) { w.fromBufferAttribute(pos, i).applyMatrix4(g.o.matrixWorld); puntos.push(w.x, w.y, w.z); }
  }
  const conservados = new Map(); // grupo → caja de lo que se dibuja de él
  for (const p of proc) {
    if (p.rin) continue; // (rin de otro estilo armado por Personalizar sobre el aro del GLB: se cuenta en categorías)
    if (p.grupo && /^(accesorio|espejos|placa|pata)/.test(p.grupo)) {
      if (!conservados.has(p.grupo)) conservados.set(p.grupo, new T.Box3());
      conservados.get(p.grupo).union(p.caja);
      continue; // (accesorios y espejos van montados sobre piezas del GLB: se controlan como flotantes, no como duplicados)
    }
    for (const g of glb) {
      const i = p.caja.clone().intersect(g.caja);
      if (i.isEmpty()) continue;
      const a = vol(p.caja), b = vol(g.caja);
      if (vol(i) / Math.min(a, b) > 0.5 && Math.max(a, b) / Math.min(a, b) < 5)
        duplicados.push({ procedural: p.grupo || "suelta", glb: g.nombre, centro: centro(p.caja) });
    }
    if (!p.grupo) sueltas.push({ centro: centro(p.caja), material: p.o.material?.name || p.o.material?.color?.getHexString?.() });
  }
  // Flotantes, por grupo entero (un espejo redondo tiene la cabeza lejos del manubrio, pero el tallo lo toca): distancia
  // de la caja del grupo al vértice del GLB más cercano (con cajas del GLB, un espejo suelto junto al frente pasaba)
  for (const [grupo, caja] of conservados) {
    let gap = Infinity;
    for (let i = 0; i < puntos.length; i += 3) { w.set(puntos[i], puntos[i + 1], puntos[i + 2]); gap = Math.min(gap, caja.distanceToPoint(w)); if (gap === 0) break; }
    if (gap > holgura) flotantes.push({ procedural: grupo, separacion_m: r3(gap), centro: centro(caja) });
  }
  const cuenta = {};
  for (const g of glb) cuenta[g.nombre] = (cuenta[g.nombre] || 0) + 1;
  const repetidos = Object.entries(cuenta).filter(([, n]) => n > 1).map(([k]) => k);
  // Categorías: palabras del nombre del nodo GLB y grupo de la malla procedural
  const CAT = { manubrio: /manubrio|puno/, espejos: /espejo/, faros: /faro|luces_dia|posicion/, direccionales: /direccional/,
    placa: /^placa$/, escape: /escape/, rines: /rin_/, aros: /aro_/, frenos: /disco|caliper|freno/, suspension: /barras|botellas|amortiguador|vastago|suspension/,
    reposapies: /estribo|alfombra/, stop: /stop/, pata: /^pata$|caballete/ };
  const categorias = {};
  for (const [cat, re] of Object.entries(CAT)) {
    const deGlb = glb.filter((g) => re.test(g.nombre.split(".").pop())).map((g) => g.nombre);
    const deProc = proc.filter((p) => (p.grupo && re.test(p.grupo)) || (cat === "rines" && p.rin)).map((p) => (cat === "rines" && p.rin ? "rin:" + p.rin : p.grupo));
    categorias[cat] = { glb: [...new Set(deGlb)], procedural: [...new Set(deProc)] };
  }
  // (pata lateral procedural + caballete central del GLB son dos piezas reales distintas)
  const dobles = Object.entries(categorias).filter(([c, x]) => c !== "pata" && x.glb.length && x.procedural.length).map(([c]) => c);
  const faltan = Object.entries(categorias).filter(([, x]) => !x.glb.length && !x.procedural.length).map(([c]) => c);
  return { ok: !duplicados.length && !flotantes.length && !sueltas.length && !repetidos.length && !dobles.length,
    mallas: { glb: glb.length, procedural: proc.length }, dobles, faltan, duplicados, flotantes, sueltas, repetidos, categorias };
};
