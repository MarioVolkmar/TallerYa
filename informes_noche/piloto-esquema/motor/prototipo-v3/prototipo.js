/* Prototipo UX v3 (revisora UX, 16-nov-2026): envuelve el motor esquema.js SIN cambiarlo.
   Ideas «va» de propuesta-ux-v3.md:
   1 buscar por lo que notas · 2 resumen de una línea en la ficha y en la hoja · 3 «¿Varado?» en la cabecera
   4 Talleres del servicio y enlace al diagnóstico · 5 latido de la pieza elegida y avisos para lector de pantalla
   6 teclado (Esc, ← →) y foco visible.
   Se carga DESPUÉS de esquema.js y ANTES del script que llama a Esquema.iniciar. Configurable con window.P3_CFG. */
(() => {
  const CFG = Object.assign({ servicio: "frenos", emergencias: "/emergencias/", diagnostico: "/diagnostico/",
    talleres: (s) => `/talleres/servicio/${s}/` }, window.P3_CFG || {});
  let D = null; const K_DE_NOMBRE = {};
  const limpia = (s) => String(s || "").replace(/\[\[([^|\]]+)\|([^\]]+)\]\]/g, "$2").replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
  const norm = (s) => limpia(s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const QUIEN = { facil: "Lo puedes hacer tú", media: "Mejor en el taller", taller: "Mejor en el taller" };
  const $ = (s, r = document) => r.querySelector(s);
  // Palabras de calle → raíces que usan las fichas (sin tildes). Genérico: sirve para frenos, CVT, motor, eléctrico.
  const SINONIMOS = [
    [/^bland|^esponj|^suav|^floj|^hund/, ["hund", "esponj", "suav", "blanda", "floj", "llega al puno", "hasta el puno"]],
    [/^gote|^fug|^bot|^manch|^rieg|^escurr/, ["gote", "gota", "fuga", "mancha", "humed", "escurr", "pierde"]],
    [/^chill|^chirr|^rechin|^ruid|^suen|^pit/, ["chill", "chirr", "ruido", "suena", "rechin", "pito"]],
    [/^dur|^ties|^pesad/, ["dura", "ties", "pesad", "cuesta"]],
    [/^frena|^freno/, ["frena", "freno"]],
    [/^vibr|^temb/, ["vibr", "tiembl", "golpe"]],
    [/^calient|^calor|^quem|^olor/, ["calient", "calor", "quem", "olor", "humo"]],
    [/^luz|^bombill|^stop/, ["luz", "stop", "bombill", "enciende"]],
  ];

  // Los datos de la lámina: se toman al pasar por Esquema.iniciar
  if (window.Esquema && Esquema.iniciar) {
    const orig = Esquema.iniciar;
    Esquema.iniciar = function (d, ...r) {
      D = d; Object.entries(d.fichas || {}).forEach(([k, F]) => { if (F && F.nombre) K_DE_NOMBRE[F.nombre.trim()] = k; });
      const out = orig.call(this, d, ...r); setTimeout(montar, 0); return out;
    };
  }

  // 2. Resumen de una línea: «Se cambia · Mejor en el taller · Cada 2 años»
  function cadaCuanto(F) {
    const t = limpia(F.cuando);
    const m = t.match(/cada\s+(?:\d[\d.]*\s*(?:años?|meses|km|kilómetros|horas)|(?:año|mes|servicio|cambio de aceite)\b)/i)
      || t.match(/\b(?:a los|cada)\s+[\d.]+\s*km\b/i);
    if (!m) return "";
    const s = m[0].replace(/kilómetros/i, "km"); return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function resumenHTML(k) {
    const F = D && D.fichas && D.fichas[k]; if (!F || F.ctx) return "";
    const p = [];
    if (F.decision) p.push(`<b class="${F.decision === "repara" ? "p3-rep" : "p3-cam"}">${F.decision === "repara" ? "Se repara" : "Se cambia"}</b>`);
    if (QUIEN[F.dif]) p.push(esc(QUIEN[F.dif]));
    const c = cadaCuanto(F); if (c) p.push(esc(c));
    return p.length ? `<p class="p3-resumen">${p.join('<span class="p3-pt" aria-hidden="true"> · </span>')}</p>` : "";
  }
  function kDeFicha() {
    const h = $("#ficha .esq-cab h3, #ficha h3"); return h ? K_DE_NOMBRE[h.textContent.trim()] : null;
  }
  function parchear() {
    // resumen en la ficha
    const cab = $("#ficha .esq-cab");
    if (cab && !$("#ficha .p3-resumen")) { const k = kDeFicha(); const r = k && resumenHTML(k); if (r) cab.insertAdjacentHTML("afterend", r); }
    // resumen en la hoja inferior (si el motor la tiene)
    const t = $("#h2T"), box = t && t.parentElement;
    if (box) {
      const k = K_DE_NOMBRE[t.textContent.trim()], viejo = box.querySelector(".p3-resumen");
      if (viejo && viejo.dataset.k !== k) viejo.remove();
      if (k && !box.querySelector(".p3-resumen")) { const r = resumenHTML(k); if (r) { box.insertAdjacentHTML("beforeend", r); box.lastElementChild.dataset.k = k; } }
    }
    // 4. «Talleres» lleva a los talleres del servicio
    document.querySelectorAll('a[href="#talleres"]').forEach((a) => { a.href = CFG.talleres(CFG.servicio); a.dataset.p3 = "1"; });
    // 1. el buscador anuncia que también entiende síntomas
    document.querySelectorAll(".esq-v2-q").forEach((q) => { if (!q.dataset.p3) { q.dataset.p3 = "1"; q.placeholder = "Pieza o lo que notas: gotea, blanda…"; q.setAttribute("aria-label", "Buscar una pieza o lo que notas"); } });
  }

  // 1. Buscar por lo que notas: se suma a los resultados del motor (que busca por nombre)
  // (el motor registra su búsqueda después que este archivo y reescribe los resultados: se corre en la tarea siguiente)
  document.addEventListener("input", (e) => { const q = e.target.closest && e.target.closest(".esq-v2-q"); if (q) setTimeout(() => buscarSintomas(q), 0); });
  function buscarSintomas(q) {
    if (!D) return;
    const res = q.closest(".esq-v2-buscar") && q.closest(".esq-v2-buscar").parentElement.querySelector(".esq-v2-res"); if (!res) return;
    // cada palabra se busca con sus sinónimos de calle (el mismo diccionario para todas las láminas)
    const pal = norm(q.value).split(/\s+/).filter((w) => w.length >= 3).map((w) => {
      for (const [re, alt] of SINONIMOS) if (re.test(w)) return [w, ...alt];
      return [w.length > 5 ? w.slice(0, w.length - 1) : w];
    });
    res.querySelectorAll(".p3-sint, .p3-diag").forEach((x) => x.closest("li, p") ? x.closest("li, p").remove() : x.remove());
    if (!pal.length) return;
    const ya = new Set([...res.querySelectorAll("[data-k]")].map((b) => b.dataset.k)), filas = [];
    // primero las piezas principales de los grupos, después la tornillería
    const principales = new Set(((D.v2 && D.v2.grupos) || []).flatMap((g) => g.piezas || []));
    for (const [k, F] of Object.entries(D.fichas || {})) {
      if (!F || F.ctx || ya.has(k)) continue;
      const frase = (F.sintomas || []).find((s) => { const n = norm(s); return pal.every((alts) => alts.some((w) => n.includes(w))); });
      if (frase) filas.push({ p: principales.has(k) ? 0 : 1, h: `<li><button type="button" class="esq-v2-item p3-sint" data-k="${esc(k)}"><span class="esq-v2-num">${esc(k)}</span>${esc(F.nombre)}<span class="p3-frase">${esc(limpia(frase))}</span></button></li>` });
    }
    filas.sort((a, b) => a.p - b.p);
    if (filas.length) {
      const vacio = res.querySelector(".esq-vacia"); if (vacio) vacio.remove();
      let ul = res.querySelector("ul"); if (!ul) { res.insertAdjacentHTML("afterbegin", "<ul></ul>"); ul = res.querySelector("ul"); }
      ul.insertAdjacentHTML("beforeend", filas.slice(0, 8).map((f) => f.h).join("")); res.hidden = false;
    }
    if (!res.querySelector("[data-k]")) res.insertAdjacentHTML("beforeend", `<p class="p3-diag">¿No sabes qué pieza es? <a href="${CFG.diagnostico}">Prueba el diagnóstico ›</a></p>`);
  }

  // 5. Avisos para lector de pantalla
  let vivo;
  function decir(t) { if (!vivo) return; vivo.textContent = ""; setTimeout(() => { vivo.textContent = t; }, 30); }

  function montar() {
    // 3. «¿Varado?» en la cabecera
    const cab = $(".esq-cabeza");
    if (cab && !$(".p3-varado")) cab.insertAdjacentHTML("beforeend", `<a class="p3-varado" href="${CFG.emergencias}" aria-label="¿Varado? Talleres y grúas cerca">¿Varado?<span class="p3-largo">&nbsp;Talleres y grúas cerca</span>&nbsp;<span aria-hidden="true">›</span></a>`);
    vivo = document.createElement("div"); vivo.className = "p3-vivo"; vivo.setAttribute("aria-live", "polite"); document.body.appendChild(vivo);
    parchear();
    new MutationObserver(() => parchear()).observe(document.body, { childList: true, subtree: true, characterData: true });
    // avisos: al entrar a un grupo y al elegir una pieza
    const tit = $("#v2Titulo");
    if (tit) new MutationObserver(() => {
      const n = document.querySelectorAll("#lamina .esq-pz.esq-engr").length;
      if ($("#v2Volver") && !$("#v2Volver").hidden) decir(`${tit.textContent}: ${n} piezas. Toca una para ver su ficha.`);
    }).observe(tit, { childList: true, characterData: true, subtree: true });
    const fi = $("#ficha");
    if (fi) new MutationObserver(() => { const k = kDeFicha(); if (k) decir(`${D.fichas[k].nombre}. ${limpia(resumenHTML(k))}`); }).observe(fi, { childList: true });
  }

  // 6. Teclado: Esc vuelve a la vista general; ← → recorren piezas
  document.addEventListener("keydown", (e) => {
    const t = e.target; if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
    if (e.key === "Escape") { const v = $("#v2Volver"); if (v && !v.hidden) { v.click(); e.preventDefault(); } return; }
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      const fl = [...document.querySelectorAll("#ficha .esq-v2-flecha")]; const b = e.key === "ArrowLeft" ? fl[0] : fl[fl.length - 1];
      if (b && !b.disabled && b.dataset.k) { b.click(); e.preventDefault(); setTimeout(() => { const h = $("#ficha h3"); if (h) h.focus({ preventScroll: true }); }, 50); }
    }
  });
})();
