// Densidad de números en el despiece completo (motor esq-): distancia mínima entre centros en px de pantalla,
// pares a menos de 24 px, diámetro del disco visible y tamaño del número. Pegar o eval; deja la lámina armada.
(async () => {
  const S = (ms) => new Promise((r) => setTimeout(r, ms));
  window.requestAnimationFrame = (cb) => setTimeout(() => cb(performance.now()), 16);
  const st = document.createElement("style"); st.textContent = "*{transition:none!important;animation:none!important}"; document.head.append(st);
  for (let i = 0; i < 24; i++) { document.getElementById("bAdel").click(); await S(60); } await S(800);
  const vis = (e) => { for (let x = e; x && x.tagName !== "svg"; x = x.parentElement) { const c = getComputedStyle(x); if (+c.opacity < 0.1 || c.display === "none") return false; } return true; };
  const pts = [...document.querySelectorAll("#lamina .esq-bola")].filter(vis).map((b) => { const r = b.querySelector(".esq-disco").getBoundingClientRect(); return { n: b.closest(".esq-pz").dataset.n, x: r.left + r.width / 2, y: r.top + r.height / 2, d: r.width, f: b.querySelector("text").getBoundingClientRect().height }; });
  const pares = []; let dmin = 1e9;
  for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) { const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y); dmin = Math.min(dmin, d); if (d < 24) pares.push(pts[i].n + "-" + pts[j].n + ":" + d.toFixed(1)); }
  const lam = document.getElementById("lamina").getBoundingClientRect();
  const fuera = pts.filter((p) => p.x < lam.left || p.x > lam.right || p.y < lam.top || p.y > lam.bottom).map((p) => p.n);
  for (let i = 0; i < 24; i++) { document.getElementById("bAtras").click(); await S(40); } await S(600); st.remove();
  return JSON.stringify({ ancho: innerWidth, numeros: pts.length, distMin: +dmin.toFixed(1), paresMenos24: pares, discoMin: +Math.min(...pts.map((p) => p.d)).toFixed(1), letraMin: +Math.min(...pts.map((p) => p.f)).toFixed(1), fueraDelLienzo: fuera, lienzo: Math.round(lam.width) + "x" + Math.round(lam.height) });
})();
