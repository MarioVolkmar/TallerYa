// revisar-ux · verificación automática de diseño y usabilidad de TallerYa.
// Uso: pegar el archivo entero en javascript_tool UNA vez por origen (queda en localStorage). En las demás páginas:
//   const s=document.createElement('script'); s.textContent='window.__uxRes='+localStorage.revisarUX;
//   document.head.append(s); s.remove(); window.__uxRes
// (la CSP del sitio bloquea eval() en varias páginas, pero permite scripts en línea). Devuelve un resumen corto:
//   { url, ancho, scrollH, total, hallazgos: [{ t: tipo, n: cuántos, ej: [hasta 4 ejemplos] }] }
// El detalle completo queda en window.__ux (p. ej. `window.__ux['toque<44']`), sin volver a correrlo.
// Solo lee: no cambia la página (recorre el scroll y lo deja donde estaba).
window.revisarUX = () => {
  const W = innerWidth, H = innerHeight, sx0 = scrollX, sy0 = scrollY;
  const det = {};
  const add = (t, el, extra) => { (det[t] ||= []).push(desc(el) + (extra ? ' · ' + extra : '')); };
  const txt = el => (el.innerText || el.textContent || el.getAttribute?.('aria-label') || '').replace(/\s+/g, ' ').trim();
  function desc(el) {
    if (!el || !el.tagName) return '?';
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    const c = [...el.classList].filter(k => !/^(?:[a-z]+:)?(?:[mp][trblxy]?|w|h|gap|flex|grid|items|justify|text|font|rounded|bg|border|inline|block|hidden|relative|absolute)(?:-|$)/.test(k)).slice(0, 2);
    if (c.length) s += '.' + c.join('.');
    const t = txt(el).slice(0, 38);
    return t ? `${s} «${t}»` : s;
  }
  const visible = el => {
    if (el.checkVisibility && !el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const docTop = el => el.getBoundingClientRect().top + scrollY;

  // ---------- color ----------
  const parse = s => { const m = s && s.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
  const lum = c => { const f = v => (v /= 255) <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; return .2126 * f(c.r) + .7152 * f(c.g) + .0722 * f(c.b); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const mix = (top, bot) => ({ r: top.r * top.a + bot.r * (1 - top.a), g: top.g * top.a + bot.g * (1 - top.a), b: top.b * top.a + bot.b * (1 - top.a), a: 1 });
  // Fondos posibles detrás del elemento (varios si hay degradado). null = foto/imagen: no se puede medir.
  function fondos(el) {
    const capas = [];
    for (let e = el; e; e = e.parentElement) {
      const cs = getComputedStyle(e);
      const img = cs.backgroundImage;
      if (img && img !== 'none' && e !== document.body && e !== document.documentElement) {
        if (/url\(/.test(img) && !/gradient/.test(img)) return null;
        const cols = (img.match(/rgba?\([^)]+\)/g) || []).map(parse);
        if (cols.length) { capas.push(cols); if (cols.every(c => c.a >= .95)) break; }
      }
      const bg = parse(cs.backgroundColor);
      if (bg && bg.a > 0) { capas.push([bg]); if (bg.a >= .95) break; }
    }
    let res = [parse(getComputedStyle(document.body).backgroundColor) || { r: 17, g: 21, b: 23, a: 1 }];
    if (res[0].a < 1) res = [{ r: 17, g: 21, b: 23, a: 1 }];
    for (let i = capas.length - 1; i >= 0; i--) res = capas[i].flatMap(c => res.map(b => mix(c, b)));
    return res;
  }

  // ---------- textos visibles (hojas con texto propio) ----------
  const hojas = new Set();
  const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: n => n.nodeValue.trim().length && !n.parentElement.closest('script,style,noscript,template,svg,[hidden],[aria-hidden="true"],#djDebug') ? 1 : 3
  });
  const nodos = [];
  while (tw.nextNode() && nodos.length < 4000) { nodos.push(tw.currentNode); hojas.add(tw.currentNode.parentElement); }
  const hojasVis = [...hojas].filter(visible);

  // 1. Scroll horizontal y elementos que se salen del ancho
  const scrollH = document.documentElement.scrollWidth > W + 1;
  const recorta = e => { for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p).overflowX; if (o !== 'visible') return true; } return false; };
  for (const el of document.body.querySelectorAll('*')) {
    if (det.desborde?.length > 30) break;
    const r = el.getBoundingClientRect();
    if (r.width > 1 && (r.right > W + 1 || r.left < -1) && getComputedStyle(el).position !== 'fixed' && !recorta(el) && visible(el))
      if (!el.parentElement || el.parentElement.getBoundingClientRect().right <= W + 1) add('desborde', el, `x ${Math.round(r.left)}→${Math.round(r.right)} de ${W}`);
  }

  // 2. Texto cortado (ellipsis / overflow oculto que corta el contenido)
  for (const el of hojasVis) {
    const cs = getComputedStyle(el);
    if ((cs.overflow !== 'visible' || cs.textOverflow === 'ellipsis') && el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) add('texto-cortado', el, `${el.scrollWidth}>${el.clientWidth}px`);
  }

  // 3. Texto tapado por otro elemento opaco (botones, flotantes, barra inferior). Recorre la página en pasos.
  const opaco = e => { const cs = getComputedStyle(e); const bg = parse(cs.backgroundColor); return (bg && bg.a > .5) || (cs.backgroundImage !== 'none' && e !== document.body) || e.tagName === 'IMG' || e.tagName === 'svg'; };
  const fijo = e => { for (let p = e; p && p !== document.body; p = p.parentElement) { const q = getComputedStyle(p).position; if (q === 'fixed' || q === 'sticky') return true; } return false; };
  const vistos = new Set();
  const altoDoc = Math.min(document.documentElement.scrollHeight, 30000);
  for (let y = 0; y <= altoDoc; y += Math.round(H * .8)) {
    scrollTo(sx0, y);
    for (const n of nodos) {
      const el = n.parentElement;
      if (vistos.has(el) || !hojasVis.includes(el)) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      const rs = [...rg.getClientRects()].filter(r => r.width > 2 && r.height > 2);
      for (const r of [rs[0], rs[rs.length - 1]]) {
        if (!r) continue;
        const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
        if (cy < 0 || cy > H || cx < 0 || cx > W) continue;
        const hit = document.elementFromPoint(cx, cy);
        if (!hit || hit === el || el.contains(hit) || hit.contains(el)) continue;
        let tapa = null;
        for (let p = hit; p && !p.contains(el); p = p.parentElement) if (opaco(p)) { tapa = p; break; }
        if (tapa && fijo(tapa)) {
          // Un fijo/sticky (cabecera, barra inferior, WhatsApp) solo es problema si el texto no se puede sacar de debajo:
          // se centra el texto y se mira otra vez (lo del final de la página sin espacio reservado sigue tapado).
          const y0 = scrollY; el.scrollIntoView({ block: 'center' });
          const r2 = [...rg.getClientRects()].filter(q => q.width > 2)[0];
          const h2 = r2 && document.elementFromPoint(r2.left + r2.width / 2, r2.top + r2.height / 2);
          const sigue = h2 && h2 !== el && !el.contains(h2) && !h2.contains(el) && fijo(h2);
          scrollTo(sx0, y0);
          if (!sigue) continue;
        }
        if (tapa) { vistos.add(el); add(fijo(tapa) ? 'tapado-por-flotante' : 'solape', el, 'bajo ' + desc(tapa).slice(0, 50)); break; }
      }
    }
  }
  scrollTo(sx0, sy0);

  // 4. Objetivos de toque < 44 px (los enlaces dentro de un párrafo son excepción de WCAG)
  const toques = document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=tab],[role=switch],[tabindex="0"],label:has(input[type=checkbox]),label:has(input[type=radio])');
  for (const el of toques) {
    if (!visible(el) || el.closest('label:has(input)') && el.tagName === 'INPUT' && ['checkbox', 'radio'].includes(el.type)) continue;
    const r = el.getBoundingClientRect();
    const minimo = W < 768 ? 44 : 24; // con mouse basta 24 px (WCAG 2.5.8); en celular, 44
    if (r.width >= minimo && r.height >= minimo) continue;
    if (el.tagName === 'A' && el.closest('p') && txt(el.closest('p')).length > txt(el).length + 15) continue;
    add(Math.min(r.width, r.height) < 24 ? 'toque<24' : 'toque<44', el, `${Math.round(r.width)}×${Math.round(r.height)}`);
  }

  // 5. Contraste AA (4,5:1; 3:1 si es texto grande ≥24px o ≥18,7px negrita)
  for (const el of hojasVis) {
    const cs = getComputedStyle(el);
    const c = parse(cs.color); if (!c) continue;
    const fs = parseFloat(cs.fontSize), grande = fs >= 24 || (fs >= 18.66 && +cs.fontWeight >= 700);
    const fb = fondos(el); if (!fb) continue;
    const peor = Math.min(...fb.map(b => ratio(c.a < 1 ? mix(c, b) : c, b)));
    if (peor < (grande ? 2.95 : 4.45)) add('contraste', el, `${peor.toFixed(2)}:1${grande ? ' (grande)' : ''}`);
  }

  // 6. Enlaces subrayados sueltos (fuera de un párrafo con más texto): deben ser botón o chip
  for (const a of document.querySelectorAll('a[href]')) {
    if (!visible(a) || !getComputedStyle(a).textDecorationLine.includes('underline')) continue;
    const p = a.closest('p,li,dd,td');
    if (p && txt(p).length > txt(a).length + 15) continue;
    add('enlace-suelto', a);
  }

  // 7. Minúscula inicial en chips, etiquetas, botones, títulos y frases (lo que se ve, no lo que va en mayúsculas por CSS)
  const SEL = 'h1,h2,h3,h4,h5,h6,button,label,legend,th,dt,summary,p,li,.btn,[class*=chip],[class*=insignia],[class*=chapa],[class*=etiqueta],[class*=estado],[class*=label],[class*=boton],[class*=aviso],[class*=titulo]';
  for (const el of hojasVis) {
    if (!el.matches(SEL) && !el.parentElement?.matches(SEL)) continue;
    const cs = getComputedStyle(el);
    if (cs.textTransform === 'uppercase' || cs.textTransform === 'capitalize') continue;
    const t = txt(el);
    if (el.previousSibling && el.previousSibling.nodeType === 3 && el.previousSibling.nodeValue.trim()) continue; // va dentro de una frase
    if (/^[a-záéíóúñü]/.test(t) && !/^(km|cc|kg|ml|cm|mm|hp|rpm|x\d|vs\b|www|http|e-?mail|iOS|iPhone)/i.test(t)) add('minuscula', el);
  }

  // 8. «—», «None», «undefined» o celdas vacías: un dato que falta necesita una acción («Agrega la placa»)
  for (const el of hojasVis) {
    const t = txt(el);
    if (/^(—|–|-|--|n\/?a|none|null|undefined|nan|sin dato)$/i.test(t) || /\b(None|undefined|NaN|null)\b/.test(t)) add('dato-vacio', el);
  }
  for (const el of document.querySelectorAll('td,dd')) if (visible(el) && !txt(el) && !el.querySelector('img,svg,input,button,a')) add('dato-vacio', el, 'celda vacía');

  // 9. Sin nombre accesible (botones/enlaces solo con ícono, imágenes sin alt)
  for (const el of document.querySelectorAll('a[href],button,[role=button]')) {
    if (!visible(el)) continue;
    const nombre = txt(el) || el.getAttribute('aria-label') || el.getAttribute('title') || el.querySelector('img[alt]:not([alt=""])') || (el.getAttribute('aria-labelledby') && document.getElementById(el.getAttribute('aria-labelledby')));
    if (!nombre) add('sin-nombre', el, el.outerHTML.slice(0, 60));
  }
  for (const im of document.querySelectorAll('img:not([alt])')) if (visible(im)) add('sin-nombre', im, 'img sin alt');
  for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=submit]),select,textarea')) {
    if (!visible(el)) continue;
    if (!(el.labels?.length || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.title)) add('sin-nombre', el, 'campo sin label');
  }

  // 10. Congruencia con la guía (anexo-guia.md): colores fuera de la paleta, fuentes que no son Oswald/Archivo, radios fuera de la escala.
  // Agrupa por valor: «rgb(...) ×N · ejemplo». Lo que salga aquí se cambia al token más cercano o se justifica y se suma a la guía.
  const PALETA = '111517 161c1e 1d2427 252e31 354044 ede3cc c9bfa7 f2611d ff9a3c e3a72f 1f3a36 3fbf6b ff5a3c 8a9096 1a0d05 1a0a05 0b0e0f 1fae5b 26c568 04140a ff8a6b ff8a70 949b9d 3a4549 f4c55a ffd477 f0b33a 2a1d02 1d1405 86dba6 ff7a5f efe6d2 fbf8f1 000000'
    .split(' ').map(h => ({ r: parseInt(h.slice(0, 2), 16), g: parseInt(h.slice(2, 4), 16), b: parseInt(h.slice(4), 16) }));
  const lejos = c => Math.min(...PALETA.map(p => Math.hypot(p.r - c.r, p.g - c.g, p.b - c.b))) > 30;
  const RADIOS = [0, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24];
  const grupos = { 'color-fuera': new Map(), 'fuente-fuera': new Map(), 'radio-fuera': new Map() };
  const anota = (k, v, el) => { const g = grupos[k]; const x = g.get(v) || { n: 0, el }; x.n++; g.set(v, x); };
  for (const el of document.body.querySelectorAll('*')) {
    if (el.closest('svg,#djDebug,canvas') || !visible(el)) continue;
    const cs = getComputedStyle(el);
    if (hojas.has(el)) {
      const c = parse(cs.color); if (c && c.a >= .9 && lejos(c)) anota('color-fuera', 'texto ' + cs.color, el);
      const f = cs.fontFamily.split(',')[0].replace(/["']/g, '').trim();
      if (!/^(Oswald|Archivo|ui-monospace|monospace|SFMono-Regular|Menlo|Consolas)$/i.test(f) && !/emoji/i.test(f)) anota('fuente-fuera', f, el);
    }
    const bg = parse(cs.backgroundColor); if (bg && bg.a >= .9 && lejos(bg)) anota('color-fuera', 'fondo ' + cs.backgroundColor, el);
    if (parseFloat(cs.borderTopWidth) > 0 && cs.borderTopStyle !== 'none') { const b = parse(cs.borderTopColor); if (b && b.a >= .9 && lejos(b)) anota('color-fuera', 'borde ' + cs.borderTopColor, el); }
    if (cs.borderTopStyle === 'dashed' || cs.borderTopStyle === 'dotted') anota('color-fuera', 'borde ' + cs.borderTopStyle + ' (preferencias: nada punteado salvo zonas de carga)', el);
    const rad = parseFloat(cs.borderTopLeftRadius);
    if (rad > 0 && !cs.borderTopLeftRadius.includes('%')) {
      const alto = el.getBoundingClientRect().height;
      if (rad < alto / 2 - 1 && !RADIOS.some(v => Math.abs(v - rad) < .6)) anota('radio-fuera', Math.round(rad * 10) / 10 + 'px', el);
    }
  }
  for (const [k, g] of Object.entries(grupos)) for (const [v, x] of [...g].sort((a, b) => b[1].n - a[1].n)) (det[k] ||= []).push(`${v} ×${x.n} · ${desc(x.el).slice(0, 50)}`);

  window.__ux = det;
  const orden = ['color-fuera', 'fuente-fuera', 'radio-fuera', 'desborde', 'tapado-por-flotante', 'solape', 'texto-cortado', 'toque<24', 'dato-vacio', 'contraste', 'enlace-suelto', 'sin-nombre', 'minuscula', 'toque<44'];
  const hallazgos = orden.filter(k => det[k]).map(k => ({ t: k, n: det[k].length, ej: [...new Set(det[k])].slice(0, 4) }));
  return { url: location.pathname, ancho: W, scrollH, total: hallazgos.reduce((s, h) => s + h.n, 0), hallazgos };
};
try { localStorage.revisarUX = '(' + window.revisarUX + ')()'; } catch (e) {}
window.revisarUX();
