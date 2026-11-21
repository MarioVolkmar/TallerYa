// Pegar en la consola de http://localhost:8767/garaje/38/vista-3d/ (proxy.py). Define:
// __cap(nombre, az, el, {fov, ids, W, H, dist}) -> guarda caps/<nombre>.png
// Fondo transparente, sin piso, sombra, pata ni accesorios. az 0 = lado derecho (+z), el en grados.
// ids: true = pasada de ID: cada malla "clase.pieza" con su color plano de window.idsMapa (emisivo, sin luces ni tone mapping).
window.__cap = async (nombre, az = 0, el = 2, o = {}) => {
  const v = window.__visor, ren = v._ren, esc = v._esc, cam = v._cam, M = v._moto;
  const { fov = 14, ids = false, W = 1200, H = 800, dist = 12, mapa = window.idsMapa || {} } = o;
  const ocultos = [], mats = [], luces = [];
  const ocultar = (x) => { if (x && x.visible) { x.visible = false; ocultos.push(x); } };
  for (const c of esc.children) if (c !== M.raiz && (c.isMesh || c.isLineSegments)) ocultar(c);
  ocultar(M.pata); for (const g of Object.values(M.accesorios || {})) ocultar(g);
  // caja de la moto (Box3 sacado de un boundingBox)
  let caja = null;
  M.raiz.updateMatrixWorld(true);
  M.raiz.traverse((x) => {
    if (!x.isMesh || !x.visible || !x.name.includes(".")) return;
    const g = x.geometry; if (!g.boundingBox) g.computeBoundingBox();
    const b = g.boundingBox.clone().applyMatrix4(x.matrixWorld);
    caja = caja ? caja.union(b) : b;
  });
  const prev = { tm: ren.toneMapping, pr: ren.getPixelRatio(), w: ren.domElement.width, h: ren.domElement.height, bg: esc.background, env: esc.environment,
    fov: cam.fov, asp: cam.aspect, pos: cam.position.clone(), q: cam.quaternion.clone(), ca: ren.getClearAlpha() };
  if (ids) {
    ren.toneMapping = 0; esc.environment = null;
    esc.traverse((x) => { if (x.isLight) { luces.push([x, x.intensity]); x.intensity = 0; } });
    // las pinturas se dibujan con mallas unidas (grupoMoto) y su original lleva material invisible: se usa el original
    M.raiz.traverse((x) => { if (x.isMesh && (x.userData.grupoMoto || x.userData.calca)) ocultar(x); });
    M.raiz.traverse((x) => {
      if (!x.isMesh || !x.visible || Array.isArray(x.material)) return;
      if (x.material.type === "MeshBasicMaterial") {
        const c = mapa[x.name] || [0, 0, 0], m = x.material.clone();
        m.map = null; m.alphaMap = null; m.visible = true; m.transparent = false; m.opacity = 1; m.vertexColors = false;
        m.color.setRGB(c[0] / 255, c[1] / 255, c[2] / 255); m.needsUpdate = true;
        mats.push([x, x.material]); x.material = m; return;
      }
      const c = mapa[x.name] || [0, 0, 0], m = x.material.clone();
      for (const k of ["map", "emissiveMap", "envMap", "normalMap", "roughnessMap", "metalnessMap", "aoMap", "lightMap", "alphaMap"]) if (k in m) m[k] = null;
      if (m.color) m.color.setRGB(0, 0, 0);
      if (m.emissive) { m.emissive.setRGB(c[0] / 255, c[1] / 255, c[2] / 255); m.emissiveIntensity = 1; }
      m.visible = true; m.transparent = false; m.opacity = 1; if ("metalness" in m) { m.metalness = 0; m.roughness = 1; }
      if ("vertexColors" in m) m.vertexColors = false;
      m.needsUpdate = true; mats.push([x, x.material]); x.material = m;
    });
  }
  esc.background = null; ren.setClearAlpha(0); ren.setPixelRatio(1); ren.setSize(W, H, false);
  const cen = caja.getCenter(cam.position.clone());
  const a = az * Math.PI / 180, e = el * Math.PI / 180;
  cam.fov = fov; cam.aspect = W / H; cam.updateProjectionMatrix();
  cam.position.set(cen.x + dist * Math.cos(e) * Math.sin(a), cen.y + dist * Math.sin(e), cen.z + dist * Math.cos(e) * Math.cos(a));
  cam.lookAt(cen); cam.updateMatrixWorld();
  ren.render(esc, cam);
  const url = ren.domElement.toDataURL("image/png");
  for (const [x, m] of mats) { x.material.dispose(); x.material = m; }
  for (const [x, i] of luces) x.intensity = i;
  for (const x of ocultos) x.visible = true;
  ren.toneMapping = prev.tm; esc.background = prev.bg; esc.environment = prev.env; ren.setClearAlpha(prev.ca); ren.setPixelRatio(prev.pr);
  if (prev.w) ren.setSize(prev.w / prev.pr, prev.h / prev.pr, false);
  cam.fov = prev.fov; cam.aspect = prev.asp; cam.position.copy(prev.pos); cam.quaternion.copy(prev.q); cam.updateProjectionMatrix();
  await fetch("/__guardar/" + nombre + ".png", { method: "POST", body: url });
  return [nombre, url.length];
};
