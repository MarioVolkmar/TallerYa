// Capturas comparativas del visor con cámaras fijas (skill moto-3d-realista). Pegar en /garaje/<pk>/vista-3d/?modelo3d=glb.
//   await capturarVersion("v3")          → guarda en localStorage las 4 vistas de lo que está montado ahora
//   (cambiar el GLB: copiar el otro archivo encima, subir ?v= en glb.js y recargar; volver a pegar este archivo)
//   await panelVersiones("v3", "v4")      → arma la hoja 800×450 (una fila por versión) y la muestra a pantalla completa
//                                            para tomar UNA captura (la imagen queda en tool-results: copiarla al informe)
// Mismos colores para todas: gris medio (deja ver facetas) y negro de fábrica, sin accesorios.
window.VISTAS_VISOR = {
  frontal: [[3.4, 0.75, 0.0], [0, 0.55, 0]], lateral: [[0, 0.62, 3.9], [0, 0.55, 0]],
  trasera: [[-3.4, 0.8, 0.0], [0, 0.5, 0]], "3/4": [[2.0, 0.95, 2.6], [0, 0.5, 0]],
};
window.capturarVersion = async function (clave, color = "#6b7785") {
  const T = await import("three"); const v = window.__visor, r = v._moto.raiz;
  window.TallerYa3D.aplicar({ color, color_secundario: "#1c2022", estilo: { accesorios: [] } });
  await new Promise((s) => setTimeout(s, 400));
  // (con el panel oculto el lienzo mide 0×0 y es transparente: tamaño fijo y fondo claro)
  v._ren.setPixelRatio(1); v._ren.setSize(900, 600, false); v._cam.aspect = 1.5; v._cam.updateProjectionMatrix();
  v._esc.background = new T.Color(0xe6e9eb);
  const caps = {};
  for (const [n, [pos, obj]] of Object.entries(window.VISTAS_VISOR)) {
    r.position.set(0, 0, 0); r.rotation.set(0, 0, 0); r.updateMatrixWorld(true); // (la vitrina anima la moto)
    v._ctl.target.set(...obj); v._cam.position.set(...pos); v._ctl.update();
    v._ren.shadowMap.needsUpdate = true; v._ren.render(v._esc, v._cam);
    caps[n] = v._ren.domElement.toDataURL("image/jpeg", 0.85);
  }
  localStorage.setItem("cap_" + clave, JSON.stringify(caps));
  return r.userData.glb;
};
window.panelVersiones = async function (...claves) {
  const carga = (s) => new Promise((ok) => { const i = new Image(); i.onload = () => ok(i); i.src = s; });
  const cv = document.createElement("canvas"); cv.width = 800; cv.height = 450; const c = cv.getContext("2d");
  c.fillStyle = "#fff"; c.fillRect(0, 0, 800, 450);
  const nombres = Object.keys(window.VISTAS_VISOR), H = (450 - 20) / claves.length, W = 800 / nombres.length;
  c.font = "bold 13px Arial"; c.fillStyle = "#111";
  nombres.forEach((n, j) => c.fillText(n, j * W + 6, 14));
  for (const [i, k] of claves.entries()) {
    const caps = JSON.parse(localStorage.getItem("cap_" + k));
    for (const [j, n] of nombres.entries()) {
      const im = await carga(caps[n]);
      // (recorte central: la moto ocupa el medio del lienzo de 900×600)
      const sx = 150, sy = 60, sw = 600, sh = 480, e = Math.min((W - 4) / sw, (H - 4) / sh);
      c.drawImage(im, sx, sy, sw, sh, j * W + (W - sw * e) / 2, 20 + i * H + (H - sh * e) / 2, sw * e, sh * e);
    }
    c.fillText(k, 4, 20 + i * H + 14);
  }
  let d = document.getElementById("ov");
  if (!d) { d = document.createElement("div"); d.id = "ov"; d.style = "position:fixed;inset:0;z-index:99999;background:#fff"; document.body.appendChild(d); }
  d.innerHTML = ""; const i = new Image(); i.src = cv.toDataURL("image/jpeg", 0.92);
  i.style = "position:fixed;left:0;top:0;width:100vw;height:100vh"; d.appendChild(i);
  return "listo";
};
