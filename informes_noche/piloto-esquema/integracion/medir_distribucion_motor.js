// Distribución para la rúbrica v2; sirve para el integrado y para las láminas del motor (.esq-escenario).
(() => {
  window.scrollTo(0, 0);
  const vw = innerWidth, vh = innerHeight;
  const q = (s) => document.querySelector(s);
  const caja = (e) => e && e.getBoundingClientRect();
  const visible = (e) => e && e.offsetParent !== null;
  const lam = caja(q("#lamina")), todo = caja(q("#bTodo"));
  const tabs = caja(q('[role="tablist"]'));
  const cont = caja(q("main") || q(".envoltura"));
  const contW = cont ? Math.min(cont.width, vw) : vw;
  // Columnas de la fila del despiece: los hijos directos de la rejilla que contiene el dibujo
  const fila = q("#lamina").closest(".esq-escenario, .despiece, .escenario");
  const cols = fila ? [...fila.children].filter(visible).map((c) => {
    const b = caja(c);
    // alto del contenido real: el último descendiente visible
    let fin = b.top;
    c.querySelectorAll("*").forEach((n) => { if (visible(n)) { const r = n.getBoundingClientRect(); if (r.height) fin = Math.max(fin, r.bottom); } });
    // hueco = parte de la fila (alto de la columna más larga) que queda vacía bajo el contenido de esta columna
    const fb = caja(fila);
    const hueco = fb.height > 0 ? Math.max(0, fb.bottom - fin) / fb.height : 0;
    // una columna fija (sticky) que cabe en la pantalla acompaña al desplazar: no deja hueco a la vista
    const fija = getComputedStyle(c).position === "sticky" && b.height <= vh;
    return { clase: c.className.split(" ")[0], x: Math.round(b.left), top: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height), hueco: fija ? "0% (fija)" : Math.round(hueco * 100) + "%" };
  }) : [];
  const apoyo = lam ? Math.max(0, lam.top - (caja(q("header, .esq-cabeza"))?.height || 0) - (tabs ? tabs.height + 20 : 0)) : 0;
  return JSON.stringify({
    vista: `${vw}x${vh}`,
    dibujo: lam && { w: Math.round(lam.width), h: Math.round(lam.height), top: Math.round(lam.top), bottom: Math.round(lam.bottom), pctAncho: Math.round(lam.width / contW * 100) + "%", completo: lam.bottom <= vh && lam.top >= 0 },
    desarmarVisible: !!todo && todo.bottom <= vh && todo.top >= 0,
    pestanasVisibles: !!tabs && tabs.bottom <= vh,
    apoyoPct: Math.round(apoyo / vh * 100) + "%",
    columnas: cols,
    columnaMin: cols.length ? Math.min(...cols.map((c) => c.w)) : null,
    desborde: document.documentElement.scrollWidth > vw,
    alto: document.documentElement.scrollHeight,
  });
})();
