// Calcas de fábrica: el nombre del modelo, la cilindrada y las franjas que cada moto trae de serie.
// Son representaciones estilizadas: el nombre del modelo en texto con una tipografía libre parecida a la de la marca
// (Google Fonts, licencia OFL) y formas propias. Nunca el emblema o símbolo de la marca (diapasón, ala, etc.).
// Todas las calcas de una moto se dibujan en una sola textura (atlas) para pegarlas como una sola malla (1 call).
import * as THREE from "three";

// Tipografías libres parecidas a las de cada marca: familia de Google Fonts, grosor, cursiva, inclinación extra
// (sesgo del lienzo), espaciado entre letras (en fracción del alto) y ancho relativo (estirar o angostar).
export const FUENTES = {
  yamaha: { familia: "Saira", peso: 800, cursiva: true, sesgo: -0.1, espaciado: 0.02, ancho: 1.08 },
  yamaha_script: { familia: "Saira", peso: 900, cursiva: true, sesgo: -0.28, espaciado: -0.02, ancho: 1.15 },
  ktm: { familia: "Teko", peso: 700, cursiva: false, sesgo: -0.16, espaciado: 0.04, ancho: 1.1 },
  bajaj: { familia: "Exo 2", peso: 800, cursiva: true, sesgo: -0.08, espaciado: 0.01, ancho: 1.05 },
  suzuki: { familia: "Kanit", peso: 800, cursiva: true, sesgo: -0.06, espaciado: 0, ancho: 1 },
  honda: { familia: "Kanit", peso: 700, cursiva: true, sesgo: -0.04, espaciado: 0.01, ancho: 1 },
  akt: { familia: "Orbitron", peso: 900, cursiva: false, sesgo: -0.12, espaciado: 0.03, ancho: 1 },
  tvs: { familia: "Racing Sans One", peso: 400, cursiva: false, sesgo: -0.04, espaciado: 0.02, ancho: 1 },
  hero: { familia: "Rajdhani", peso: 700, cursiva: false, sesgo: -0.12, espaciado: 0.02, ancho: 1 },
  generica: { familia: "Oswald", peso: 700, cursiva: false, sesgo: -0.1, espaciado: 0.04, ancho: 1 },
};
const MARCAS = [[/yamaha/i, "yamaha"], [/ktm/i, "ktm"], [/bajaj|pulsar|boxer|discover|dominar/i, "bajaj"], [/suzuki|gixxer|\bgn\b/i, "suzuki"],
  [/honda/i, "honda"], [/akt/i, "akt"], [/tvs|apache/i, "tvs"], [/hero/i, "hero"]];

// Calcas por línea (se busca por nombre en "marca + línea + año"). Cada calca:
//   id, nombre (para la lista), tipo: "texto" | "numero" | "franja", texto, zona (preferidas, en orden),
//   cara: "lado" (costados, ambos) o "frente", posicion (-1 cola … 1 frente, dentro de la zona),
//   altura (-1 abajo … 1 arriba, dentro de la zona), ancho en metros, giro en grados.
const N = (texto, zona, extra = {}) => ({ id: "nombre", nombre: `Nombre ${texto}`, tipo: "texto", texto, zona, cara: "lado", posicion: 0.05, altura: 0.05, ancho: 0.24, ...extra });
const C = (texto, zona, extra = {}) => ({ id: "cilindrada", nombre: `Cilindrada ${texto}`, tipo: "numero", texto, zona, cara: "lado", posicion: -0.2, altura: 0.1, ancho: 0.1, ...extra });
const F = (zona, extra = {}) => ({ id: "franja", nombre: "Franja", tipo: "franja", zona, cara: "lado", posicion: 0, altura: -0.45, ancho: 0.34, ...extra });

const LINEAS = [
  // NMAX (fotos 2020–2024): gráfica sobria; "NMAX" gris en la tapa trasera, "ABS" chico y un filete fino abajo
  [/nmax/i, () => [N("NMAX", ["lateral"], { posicion: -0.55, altura: 0.35, ancho: 0.17, color: "gris" }),
    { id: "abs", nombre: "ABS", tipo: "texto", texto: "ABS", zona: ["lateral"], cara: "lado", posicion: -0.55, altura: 0.08, ancho: 0.055, color: "gris" },
    F(["lateral"], { id: "filete", nombre: "Filete", forma: "filete", posicion: -0.15, altura: -0.42, ancho: 0.55, giro: 3, color: "gris", color2: "acento" })]],
  // Aerox (fotos 2021–2025): "aerox" en minúscula cursiva grande, subiendo en el costado delantero, en el color de
  // acento de la versión; "155" hueco grande en el escudo; rayas paralelas en la tapa trasera y un filete angular abajo
  [/aerox/i, () => [N("aerox", ["lateral"], { fuente: "yamaha_script", posicion: 0.3, altura: -0.15, ancho: 0.4, giro: 13, color: "vivo:#35c4ef" }),
    C("155", ["frontal"], { posicion: -0.35, altura: 0.05, ancho: 0.17, contorno: true, color: "vivo:#35c4ef", estirar: 1.15 }),
    F(["lateral"], { id: "rayas", nombre: "Rayas traseras", forma: "rayas", posicion: -0.6, altura: 0.15, ancho: 0.13, giro: 0, color: "vivo:#35c4ef", color2: "letra" }),
    F(["lateral"], { id: "filete", nombre: "Filete", forma: "filete", posicion: -0.05, altura: -0.6, ancho: 0.62, giro: 5, color: "vivo:#35c4ef", color2: "gris" }),
    { id: "abs", nombre: "ABS", tipo: "texto", texto: "ABS", zona: ["lateral"], cara: "lado", posicion: -0.72, altura: 0.45, ancho: 0.05, color: "gris" }]],
  [/fz\s*25/i, () => [N("FZ25", ["tanque"], { ancho: 0.2 }), F(["tanque"], { altura: -0.5 })]],
  [/\bfz/i, () => [N("FZ", ["tanque"], { ancho: 0.16 }), F(["tanque"], { altura: -0.5 })]],
  [/xtz\s*250/i, () => [N("XTZ", ["tanque"], { ancho: 0.2 }), C("250", ["lateral", "cola"], { ancho: 0.11 })]],
  [/xtz\s*150/i, () => [N("XTZ", ["tanque"], { ancho: 0.2 }), C("150", ["lateral", "cola"], { ancho: 0.11 })]],
  [/xtz/i, () => [N("XTZ", ["tanque"], { ancho: 0.2 }), C("125", ["lateral", "cola"], { ancho: 0.11 })]],
  [/mt-?03/i, () => [N("MT-03", ["tanque"], { ancho: 0.22 }), F(["tanque"], { altura: -0.5 })]],
  [/crypton/i, () => [N("CRYPTON", ["lateral"], { ancho: 0.3, altura: 0.2 }), F(["lateral"], { altura: -0.3 })]],
  [/bws/i, () => [N("BWS", ["lateral"], { ancho: 0.24, altura: 0.2 }), F(["lateral"], { altura: -0.3 })]],
  [/duke/i, (l) => [N("DUKE", ["tanque"], { ancho: 0.24 }), C((l.match(/\b(125|200|250|390)\b/) || [, "200"])[1], ["lateral", "cola"], { ancho: 0.1 }),
    F(["tanque"], { altura: -0.5, giro: -8 })]],
  [/\brc\s*200/i, () => [N("RC", ["frontal"], { posicion: -0.2, altura: 0.05, ancho: 0.2 }), C("200", ["lateral", "cola"], { ancho: 0.11 }),
    F(["frontal"], { posicion: -0.1, altura: -0.45, ancho: 0.4, giro: -6 })]],
  [/\brc\s*390/i, () => [N("RC", ["frontal"], { posicion: -0.2, altura: 0.05, ancho: 0.2 }), C("390", ["lateral", "cola"], { ancho: 0.11 })]],
  [/pulsar\s*ns/i, (l) => [N("PULSAR", ["tanque"], { ancho: 0.28 }), C("NS" + ((l.match(/\b(125|160|200)\b/) || [, "200"])[1]), ["lateral", "cola"], { ancho: 0.14 }),
    F(["tanque"], { altura: -0.5, giro: -5 })]],
  [/pulsar\s*rs/i, () => [N("PULSAR", ["frontal"], { posicion: -0.15, altura: 0.05, ancho: 0.3 }), C("RS200", ["lateral", "cola"], { ancho: 0.15 }),
    F(["frontal"], { posicion: -0.1, altura: -0.45, ancho: 0.42 })]],
  [/pulsar/i, () => [N("PULSAR", ["tanque"], { ancho: 0.28 }), F(["tanque"], { altura: -0.5 })]],
  [/boxer/i, () => [N("BOXER", ["tanque"], { ancho: 0.24 }), F(["tanque"], { altura: -0.5 })]],
  [/discover/i, () => [N("DISCOVER", ["tanque"], { ancho: 0.3 }), F(["tanque"], { altura: -0.5 })]],
  [/gixxer\s*sf/i, () => [N("GIXXER SF", ["frontal"], { posicion: -0.15, altura: 0.05, ancho: 0.34 }), F(["frontal"], { posicion: -0.1, altura: -0.45, ancho: 0.42 })]],
  [/gixxer/i, () => [N("GIXXER", ["tanque"], { ancho: 0.28 }), F(["tanque"], { altura: -0.5, giro: -5 })]],
  [/\bgn\s*125/i, () => [N("GN125", ["lateral", "cola"], { ancho: 0.14 }), F(["tanque"], { altura: 0.05, ancho: 0.36 })]],
  [/nkd/i, () => [N("NKD", ["tanque"], { ancho: 0.2 }), C("125", ["lateral", "cola"], { ancho: 0.1 }), F(["tanque"], { altura: -0.5, giro: -6 })]],
  [/cr4/i, () => [N("CR4", ["tanque"], { ancho: 0.2 }), C("125", ["lateral", "cola"], { ancho: 0.1 }), F(["tanque"], { altura: -0.5, giro: -6 })]],
  [/ttr/i, () => [N("TTR", ["tanque"], { ancho: 0.2 }), C("125", ["lateral", "cola"], { ancho: 0.1 })]],
  [/dynamic/i, () => [N("DYNAMIC", ["lateral"], { ancho: 0.3, altura: 0.2 }), F(["lateral"], { altura: -0.3 })]],
  [/\bdio\b/i, () => [N("Dio", ["lateral"], { ancho: 0.2, altura: 0.2 }), F(["lateral"], { altura: -0.3 })]],
  [/cb\s*125/i, () => [N("CB125F", ["tanque"], { ancho: 0.24 }), F(["tanque"], { altura: -0.5 })]],
  [/cb\s*1[69]0/i, (l) => [N("CB" + (l.match(/\b(160|190)\b/) || [, "190"])[1], ["tanque"], { ancho: 0.24 }), F(["tanque"], { altura: -0.5 })]],
  [/\bxr\s*\d/i, (l) => [N("XR" + (l.match(/\b(125|150|190)\b/) || [, "150"])[1] + "L", ["tanque"], { ancho: 0.22 }), F(["lateral", "cola"], { altura: 0, ancho: 0.3 })]],
  [/wave/i, () => [N("WAVE", ["lateral"], { ancho: 0.24, altura: 0.2 }), F(["lateral"], { altura: -0.3 })]],
  [/apache/i, () => [N("APACHE", ["tanque"], { ancho: 0.26 }), C("RTR", ["lateral", "cola"], { ancho: 0.11 }), F(["tanque"], { altura: -0.5, giro: -6 })]],
  [/eco\s*deluxe/i, () => [N("ECO DELUXE", ["tanque"], { ancho: 0.3 }), F(["tanque"], { altura: -0.5 })]],
  [/\bbest\b/i, () => [N("BEST", ["lateral", "cola"], { ancho: 0.16 }), F(["tanque"], { altura: -0.5 })]],
];

// Por familia, cuando la línea no está en la lista: el nombre del modelo (lo que sigue a la marca) y una franja
const ZONAS_FAMILIA = {
  scooter: { nombre: ["lateral"], franja: ["lateral"] },
  semi: { nombre: ["lateral", "tanque"], franja: ["lateral", "tanque"] },
  carenada: { nombre: ["frontal", "tanque"], franja: ["frontal", "tanque"] },
};

// Calcas de fábrica de una línea, con su tipografía. linea: "marca + línea + año"; familia: la de rasgos.js
export function calcasDeFabrica(linea, familia) {
  const marca = (MARCAS.find(([re]) => re.test(linea)) || [, "generica"])[1];
  const propia = LINEAS.find(([re]) => re.test(linea));
  let lista;
  if (propia) lista = propia[1](linea);
  else {
    const palabras = linea.replace(/\b(19|20)\d\d\b/g, "").trim().split(/\s+/);
    const modelo = (palabras.slice(1).join(" ") || palabras[0] || "").toUpperCase().slice(0, 12);
    const z = ZONAS_FAMILIA[familia] || { nombre: ["tanque", "lateral"], franja: ["tanque", "lateral"] };
    lista = modelo ? [N(modelo, z.nombre, { ancho: Math.min(0.32, 0.06 + modelo.length * 0.03) }), F(z.franja)] : [];
  }
  return lista.map((c) => ({ ...c, fuente: c.fuente || marca }));
}

// ---------- Tipografías: se piden a Google Fonts solo las que usa la moto ----------
const pedidas = new Map();
function cargarFuente(f) {
  if (f.familia === "Oswald" && document.fonts?.check?.(`700 32px "Oswald"`)) return Promise.resolve();
  const clave = `${f.familia}|${f.peso}|${f.cursiva}`;
  if (!pedidas.has(clave)) {
    const familia = f.familia.replace(/ /g, "+");
    const eje = f.cursiva ? `:ital,wght@1,${f.peso}` : `:wght@${f.peso}`;
    const enlace = document.createElement("link");
    enlace.rel = "stylesheet";
    enlace.href = `https://fonts.googleapis.com/css2?family=${familia}${eje}&display=block`;
    document.head.appendChild(enlace);
    const lista = new Promise((ok) => { enlace.onload = ok; enlace.onerror = ok; })
      .then(() => document.fonts.load(`${f.cursiva ? "italic " : ""}${f.peso} 64px "${f.familia}"`))
      .catch(() => {});
    // (sin red o lenta: a los 2,5 s se dibuja con la que haya; mejor una calca con otra letra que ninguna)
    pedidas.set(clave, Promise.race([lista, new Promise((ok) => setTimeout(ok, 2500))]));
  }
  return pedidas.get(clave);
}

// ---------- Dibujo: todas las calcas en un atlas (una fila por calca) ----------
const ANCHO_ATLAS = 1024, ALTO_FILA = 160;
const claridad = (hex) => {
  const n = parseInt(String(hex).replace("#", "").padEnd(6, "0").slice(0, 6), 16);
  return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
};

// Colores: la letra contrasta con la pintura; la franja usa el color secundario si se distingue de la pintura
export function coloresFabrica(pintura, secundario) {
  const clara = claridad(pintura) > 0.55;
  const letra = clara ? "#14181a" : "#f4f4f2";
  const acento = secundario && Math.abs(claridad(secundario) - claridad(pintura)) > 0.25 ? secundario : (clara ? "#2b3135" : "#c9ccd0");
  // (un secundario vivo —amarillo, rojo, cian…— que contrasta es el color de la gráfica de esa versión)
  const vivo = secundario && saturacion(secundario) > 0.35 && Math.abs(claridad(secundario) - claridad(pintura)) > 0.15 ? secundario : null;
  return { letra, acento, contorno: clara ? "#ffffff" : "#000000", gris: clara ? "#5b6166" : "#b9bdc1", pintura, vivo };
}
function saturacion(hex) {
  const n = parseInt(String(hex).replace("#", ""), 16), r = n >> 16, g = (n >> 8) & 255, b = n & 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  return max ? (max - min) / max : 0;
}
// Un color de la gráfica de fábrica (hex propio del modelo o "letra" / "acento" / "gris"); si se confunde con la
// pintura (p. ej. la Aerox azul con su "aerox" azul), se usa la letra que contrasta.
// "vivo:#hex": el secundario vivo de la moto si lo tiene; si no, ese hex (el color de gráfica de fábrica)
function colorDe(nombre, base) {
  if (nombre.startsWith("vivo:")) nombre = base.vivo || nombre.slice(5);
  const hex = base[nombre] || nombre;
  if (/^#[0-9a-f]{6}$/i.test(hex) && Math.abs(claridad(hex) - claridad(base.pintura)) < 0.12 && !base[nombre]) return base.letra;
  return hex;
}
// Colores de fábrica de cada calca (principal p y secundario s), antes de lo que elija el usuario
export function coloresOriginales(c, base) {
  const porTipo = c.tipo === "franja" ? ["acento", "letra"] : c.tipo === "numero" ? ["acento", "contorno"] : ["letra", "contorno"];
  return { p: colorDe(c.color || porTipo[0], base), s: colorDe(c.color2 || porTipo[1], base) };
}

function dibujarTexto(ctx, c, f, y0, col, numero) {
  const alto = ALTO_FILA * (numero ? 0.62 : 0.78);
  ctx.save();
  ctx.font = `${f.cursiva ? "italic " : ""}${f.peso} ${alto}px "${f.familia}", "Oswald", sans-serif`;
  ctx.textBaseline = "middle";
  const esp = f.espaciado * alto;
  const letras = [...c.texto];
  const anchoTexto = letras.reduce((s, l) => s + ctx.measureText(l).width, 0) + esp * (letras.length - 1);
  const sesgo = c.sesgo ?? f.sesgo;
  const margen = 12, disponible = ANCHO_ATLAS - margen * 2 - Math.abs(sesgo) * ALTO_FILA;
  const escala = Math.min(c.estirar ?? f.ancho, disponible / anchoTexto);
  const total = anchoTexto * escala;
  ctx.translate(ANCHO_ATLAS / 2, y0 + ALTO_FILA / 2);
  ctx.transform(escala, 0, sesgo, 1, 0, 0); // estirar o angostar e inclinar como la gráfica de la marca
  let x = -total / escala / 2;
  ctx.lineJoin = "round";
  for (const l of letras) {
    if (c.contorno) {
      // Números huecos (como el "155" grande de la Aerox): solo el borde en el color principal
      ctx.lineWidth = alto * 0.04;
      ctx.strokeStyle = col.p;
      ctx.strokeText(l, x, 0);
    } else {
      ctx.lineWidth = alto * 0.07;
      ctx.globalAlpha = 0.55;
      ctx.strokeStyle = col.s; // (contorno: despega la letra de la pintura)
      ctx.strokeText(l, x, 0);
      ctx.globalAlpha = 1;
      ctx.fillStyle = col.p;
      ctx.fillText(l, x, 0);
    }
    x += ctx.measureText(l).width + esp;
  }
  ctx.restore();
  return total + Math.abs(sesgo) * alto; // ancho que ocupa (para el aspecto)
}

// Formas propias (no son emblemas): cuña doble, rayas paralelas inclinadas y filete angular
function dibujarForma(ctx, c, y0, col) {
  const W = ANCHO_ATLAS, H = ALTO_FILA;
  const poli = (puntos, color) => {
    ctx.fillStyle = color;
    ctx.beginPath();
    puntos.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.closePath();
    ctx.fill();
  };
  ctx.save();
  ctx.translate(0, y0);
  let usado = W - 40;
  if (c.forma === "rayas") {
    // Rayas paralelas inclinadas (3 por defecto), la última en el color secundario
    const n = c.rayas || 3, ancho = H * 0.32, paso = H * 0.48, inclinacion = H * 0.55;
    const total = (n - 1) * paso + ancho + inclinacion, x0 = (W - total) / 2;
    for (let i = 0; i < n; i++) {
      const x = x0 + i * paso;
      poli([[x + inclinacion, H * 0.1], [x + inclinacion + ancho, H * 0.1], [x + ancho, H * 0.9], [x, H * 0.9]], i === n - 1 && n > 2 ? col.s : col.p);
    }
    usado = total + 16;
  } else if (c.forma === "filete") {
    // Filete fino que sigue la línea del carenado y se quiebra hacia arriba al final
    poli([[16, H * 0.6], [W * 0.72, H * 0.52], [W - 16, H * 0.22], [W - 16, H * 0.32], [W * 0.73, H * 0.6], [16, H * 0.68]], col.p);
    poli([[W * 0.3, H * 0.76], [W * 0.7, H * 0.7], [W * 0.71, H * 0.74], [W * 0.3, H * 0.8]], col.s);
  } else {
    // Cuña doble: una gruesa con la punta hacia adelante y una fina debajo
    poli([[20, H * 0.32], [W - 120, H * 0.22], [W - 20, H * 0.42], [60, H * 0.56]], col.p);
    poli([[120, H * 0.66], [W - 60, H * 0.54], [W - 40, H * 0.6], [150, H * 0.74]], col.s);
  }
  ctx.restore();
  return usado;
}

// Dibuja el atlas de las calcas de fábrica. Devuelve la textura y, por calca, su franja de la textura (v0, v1),
// la parte usada a lo ancho (u0, u1) y su aspecto (ancho / alto) para medirla sobre la moto.
// elegidos: { id: { p, s } } con los colores que puso el usuario (lo que falte, de fábrica)
export async function atlasFabrica(lista, base, elegidos = {}) {
  await Promise.all([...new Set(lista.filter((c) => c.tipo !== "franja").map((c) => c.fuente))].map((k) => cargarFuente(FUENTES[k] || FUENTES.generica)));
  const lienzo = document.createElement("canvas");
  lienzo.width = ANCHO_ATLAS;
  lienzo.height = Math.max(1, lista.length) * ALTO_FILA;
  const ctx = lienzo.getContext("2d");
  const regiones = {};
  lista.forEach((c, i) => {
    const y0 = i * ALTO_FILA;
    const col = { ...coloresOriginales(c, base), ...(elegidos[c.id] || {}) };
    const usado = c.tipo === "franja" ? dibujarForma(ctx, c, y0, col) : dibujarTexto(ctx, c, FUENTES[c.fuente] || FUENTES.generica, y0, col, c.tipo === "numero");
    const u0 = Math.max(0, (ANCHO_ATLAS - usado) / 2 - 8) / ANCHO_ATLAS, u1 = 1 - u0;
    // (v de three.js va de abajo hacia arriba: la fila i queda entre 1 - (i+1)/n y 1 - i/n)
    const n = lista.length;
    regiones[c.id] = { u0, u1, v0: 1 - (i + 1) / n, v1: 1 - i / n, aspecto: ((u1 - u0) * ANCHO_ATLAS) / ALTO_FILA };
  });
  const textura = new THREE.CanvasTexture(lienzo);
  textura.colorSpace = THREE.SRGBColorSpace;
  textura.anisotropy = 8;
  return { textura, regiones, lienzo };
}
