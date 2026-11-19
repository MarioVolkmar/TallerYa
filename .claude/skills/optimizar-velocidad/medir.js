// Medición de carga de una página de TallerYa. Pegar el archivo entero en javascript_tool (Browser pane) JUSTO después
// de navegar, en el mismo browser_batch: espera el load y hasta 20 s a que salgan el esquema y el 3D (si la página los tiene).
// La pestaña tiene que estar VISIBLE (tabs_context: «displayed»): oculta, Chrome frena rAF y el 3D da tiempos falsos.
// Devuelve un objeto corto (≈1 KB). Tiempos en segundos desde la navegación.
(async () => {
  const s = (ms) => (ms == null ? null : Math.round(ms) / 1000);
  const KB = (b) => Math.round(b / 1024);
  const t0 = performance.now();
  const esperar = (ms) => new Promise((r) => setTimeout(r, ms));
  const secEsquema = () => document.querySelector("#despiece:not(.diag-despiece-fuera)");
  const listoEsquema = (sec) => {
    if (!sec?.classList.contains("despiece-listo")) return false;
    const img = sec.querySelector("img");
    return !img || img.complete;
  };
  // 1) Esperar load, esquema y 3D (sondeo cada 50 ms, máx. 20 s). Se puede correr apenas empieza la navegación.
  let esquema = null, esquemaYa = false, hayEsquema = false, hayVisor = false;
  if (listoEsquema(secEsquema())) esquemaYa = true;
  for (let i = 0; i < 400; i++) {
    const sec = secEsquema();
    hayEsquema ||= !!sec; hayVisor ||= !!document.getElementById("visor");
    if (sec && !esquema && !esquemaYa && listoEsquema(sec)) esquema = performance.now();
    const listo3d = !hayVisor || window.__visor?.info?.()?.tiempos?.listo;
    if (document.readyState === "complete" && (!hayEsquema || esquema || esquemaYa) && listo3d) break;
    await esperar(50);
  }
  const esquemaSec = hayEsquema;
  // 2) LCP y tareas largas (entradas guardadas desde el inicio)
  const tomar = (type) => new Promise((r) => {
    const lista = [];
    try {
      const o = new PerformanceObserver((l) => lista.push(...l.getEntries()));
      o.observe({ type, buffered: true });
      setTimeout(() => { o.disconnect(); r(lista); }, 60);
    } catch { r(lista); }
  });
  const [lcpE, largas] = await Promise.all([tomar("largest-contentful-paint"), tomar("longtask")]);
  const lcp = lcpE.at(-1);
  // 3) Navegación y recursos
  const n = performance.getEntriesByType("navigation")[0] || {};
  const rec = performance.getEntriesByType("resource");
  const tipo = (u) => (u.match(/\.(js|mjs|css|json|svg|glb|png|jpe?g|webp|avif|woff2?)(\?|$)/i)?.[1] || (u.includes(".json") || u.includes("json") ? "json" : "otro")).toLowerCase().replace("mjs", "js").replace("jpeg", "jpg");
  const porTipo = {};
  for (const r of rec) {
    const t = tipo(r.name);
    porTipo[t] ??= { n: 0, kbRed: 0, kbReal: 0 };
    porTipo[t].n++; porTipo[t].kbRed += r.transferSize; porTipo[t].kbReal += r.decodedBodySize;
  }
  for (const t in porTipo) { porTipo[t].kbRed = KB(porTipo[t].kbRed); porTipo[t].kbReal = KB(porTipo[t].kbReal); }
  const corto = (u) => u.replace(location.origin, "").replace(/\?.*/, "").slice(-60);
  const grandes = rec.filter((r) => r.decodedBodySize > 100 * 1024 || r.duration > 800)
    .sort((a, b) => b.decodedBodySize - a.decodedBodySize).slice(0, 8)
    .map((r) => `${corto(r.name)} ${KB(r.decodedBodySize)}KB/${KB(r.transferSize)}KB red, ${s(r.startTime)}→${s(r.responseEnd)}s`);
  const v = window.__visor?.info?.();
  return {
    url: location.pathname, ancho: innerWidth, visible: document.visibilityState,
    aviso: document.visibilityState !== "visible" ? "PESTAÑA OCULTA: tiempos del 3D no válidos" : undefined,
    ttfb: s(n.responseStart), fcp: s(performance.getEntriesByName("first-contentful-paint")[0]?.startTime), dcl: s(n.domContentLoadedEventEnd), load: s(n.loadEventEnd),
    lcp: s(lcp?.startTime), lcpElem: lcp?.element ? (lcp.element.tagName + (lcp.element.id ? "#" + lcp.element.id : "")) : null,
    htmlKB: `${KB(n.decodedBodySize || 0)}/${KB(n.transferSize || 0)} red`,
    totalKB: `${KB(rec.reduce((a, r) => a + r.decodedBodySize, 0))}/${KB(rec.reduce((a, r) => a + r.transferSize, 0))} red`,
    porTipo, grandes,
    largas: { n: largas.length, maxS: s(Math.max(0, ...largas.map((l) => l.duration))), sumaS: s(largas.reduce((a, l) => a + l.duration, 0)) },
    esquema: esquemaSec ? (esquema ? s(esquema) : esquemaYa ? `≤${s(t0)} (ya estaba al medir)` : "no salió en 20 s") : undefined,
    tresD: hayVisor && !v ? "no arrancó en 20 s (¿espera a verse?)" : v ? { listo: s(v.tiempos?.listo), tiempos: v.tiempos, calidad: v.calidad, msArmado: v.msArmado, pedazoMasLargo: v.pedazoMasLargo, triangulos: v.triangulos, llamadas: v.llamadas } : undefined,
  };
})();
