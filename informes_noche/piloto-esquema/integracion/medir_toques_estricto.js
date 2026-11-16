// Prueba estricta de toques (revisora UX). Cada número visible tiene que recibir su toque en el centro
// y a ±9 px en 4 direcciones, y el elemento tocado tiene que ser ESE número (.bola), no la pieza ni otro control.
// Recorre armado y despiece, Normal y Transparente, y desplaza el dibujo a la vista antes de medir.
// Uso: await (await fetch("integracion/medir_toques_estricto.js")).text() → eval, o pegar en la consola.
(async () => {
  const S = (ms) => new Promise((r) => setTimeout(r, ms));
  // Con el panel oculto, rAF y transiciones se pausan: se reemplazan solo para medir
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
  const st = document.createElement("style"); st.textContent = "*{transition:none!important;animation:none!important}"; document.head.append(st);
  const vis = (e) => { for (let x = e; x && x.tagName !== "svg"; x = x.parentElement) { const c = getComputedStyle(x); if (+c.opacity < 0.1 || c.display === "none" || c.visibility === "hidden") return false; } return true; };
  const boton = (id, texto) => document.getElementById(id) || [...document.querySelectorAll("button")].find((b) => b.textContent.trim() === texto);
  async function medir() {
    document.getElementById("lamina").scrollIntoView({ block: "center" }); await S(400);
    let n = 0, centro = 0, roces = [], fallas = [], rmin = 1e9;
    for (const b of document.querySelectorAll("#lamina .bola")) {
      const r = b.getBoundingClientRect(); if (!r.width || !vis(b)) continue; n++;
      const t = b.querySelector(".toque"); if (t) rmin = Math.min(rmin, t.getBoundingClientRect().width / 2);
      const cx = r.left + r.width / 2, cy = r.top + r.height / 2, num = b.closest(".pz").dataset.n;
      const de = (x, y) => { const e = document.elementFromPoint(x, y); return e ? (e.closest(".bola") === b ? "ok" : (e.closest(".bola") ? "bola" + e.closest(".pz").dataset.n : e.tagName)) : "fuera"; };
      const c = de(cx, cy); if (c === "ok") centro++; else fallas.push(num + "→" + c);
      for (const [dx, dy] of [[9, 0], [-9, 0], [0, 9], [0, -9]]) { const h = de(cx + dx, cy + dy); if (h.startsWith("bola") || h === "BUTTON") roces.push(num + "(" + dx + "," + dy + ")→" + h); }
    }
    return { centro: centro + "/" + n, fallas, roces, radioMin: Math.round(rmin * 10) / 10 };
  }
  const res = { ancho: innerWidth + "x" + innerHeight, scrollW: document.documentElement.scrollWidth };
  const N = boton("vNormal", "Normal"), T = boton("vTrans", "Transparente");
  res.armN = await medir(); T.click(); await S(500); res.armT = await medir();
  for (let i = 0; i < 16; i++) { document.getElementById("bAdel").click(); await S(60); } await S(800);
  res.desT = await medir(); N.click(); await S(500); res.desN = await medir();
  for (let i = 0; i < 16; i++) { document.getElementById("bAtras").click(); await S(40); } await S(600);
  st.remove();
  return JSON.stringify(res);
})();
