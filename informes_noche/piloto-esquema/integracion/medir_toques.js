// Panel oculto: rAF y transiciones CSS se pausan; se reemplaza rAF y se apagan las transiciones solo para medir.
// Toques al centro y a ±9 px de cada número (armado/despiece, Normal/Transparente). Con el panel oculto, rAF se pausa: se reemplaza por setTimeout.
(async () => {
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
  const st = document.createElement("style"); st.textContent = "*{transition:none!important;animation:none!important}"; document.head.append(st);
  const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
  const contar = () => { let ok = 0, n = 0, roce = 0; document.querySelectorAll("#lamina .et").forEach((e) => { const b = e.querySelector(".bola") || e; const r = b.getBoundingClientRect(); if (!r.width || getComputedStyle(e).opacity === "0" || r.bottom > innerHeight || r.top < 0) return; n++; const cx = r.x + r.width / 2, cy = r.y + r.height / 2; const yo = e.closest(".pz"); const hit = document.elementFromPoint(cx, cy); if (hit && hit.closest(".pz") === yo) ok++; for (const [dx, dy] of [[9, 0], [-9, 0], [0, 9], [0, -9]]) { const h = document.elementFromPoint(cx + dx, cy + dy); const pz = h && h.closest(".pz"); if (pz && pz !== yo && pz.querySelector(".et") && getComputedStyle(pz.querySelector(".et")).opacity !== "0") roce++; } }); return ok + "/" + n + " roces±9:" + roce; };
  scrollTo(0, 0); await esperar(300);
  const res = { armadoN: contar() };
  document.getElementById("vTrans").click(); await esperar(900); res.armadoT = contar();
  document.getElementById("bTodo").click(); await esperar(26000); res.despieceT = contar();
  document.getElementById("vNormal").click(); await esperar(900); res.despieceN = contar();
  res.vb = document.getElementById("lamina").getAttribute("viewBox");
  res.scrollW = document.documentElement.scrollWidth + "/" + innerWidth;
  return JSON.stringify(res);
})();
