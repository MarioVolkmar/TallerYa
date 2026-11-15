// Rasgos de silueta por familia y por línea (datos, sin geometría). construir.js los convierte en piezas medidas
// desde las anclas de la moto (pipa H, pivote P, eje trasero xR, altura del asiento), nunca con coordenadas sueltas.
// Medidas en metros y relativas: alto/largo/ancho de cada volumen, cuánto sube el colín, etc.

// Base por familia: lo que comparten todas las motos de ese estilo
const FAMILIAS = {
  naked: {
    tanque: { forma: "cuna", alto: 0.13, ancho: 0.36, largo: 0.25, nariz: 0.06 },
    aleta: { largo: 0.2, baja: 0.16 },
    colin: { forma: "afilado", alto: 0.12, largo: 0.2 },
    escalon: 0.055, escape: { forma: "corto", sube: 20 }, faro: { forma: "compacto" },
    parrilla: false, agarradera: "partida", manubrio: "normal",
  },
  clasica: {
    tanque: { forma: "clasico", alto: 0.11, ancho: 0.32, largo: 0.25 },
    colin: { forma: "plano", alto: 0.0, largo: 0.1 },
    escalon: 0, escape: { forma: "clasico", sube: 4 }, faro: { forma: "redondo", r: 0.085 },
    parrilla: false, agarradera: "tubo", manubrio: "normal",
  },
  carenada: {
    colin: { forma: "afilado", alto: 0.14, largo: 0.22 }, escalon: 0.06,
    escape: { forma: "corto", sube: 22 }, parrilla: false, agarradera: null, manubrio: "sobreTija",
    carenado: { cupula: 0.2, cubre: 0.6 },
  },
  scooter: { parrilla: true, agarradera: null, manubrio: "normal", faro: { forma: "escudo" } },
  semi: {
    colin: { forma: "plano", alto: 0, largo: 0.1 }, escalon: 0, escape: { forma: "clasico", sube: 4 },
    parrilla: "pequena", agarradera: null, manubrio: "normal", faro: { forma: "manubrio" },
  },
  enduro: { parrilla: true, agarradera: "tubo", manubrio: "normal", escape: { forma: "enduro" } },
};

// Diferencias de cada línea sobre su familia (se buscan por nombre en "marca + línea + año")
const LINEAS = [
  // ----- Naked modernas -----
  [/duke/i, { faro: { forma: "duke" }, direccionales: { tipo: "led" }, stop: "led", escape: { forma: "bajo" }, horquillaInv: true, chasisColor: 0xf06a12, rinColor: 0xf06a12,
    tanque: { alto: 0.15, ancho: 0.32, largo: 0.21, nariz: 0.09 }, aleta: { largo: 0.16, baja: 0.12 }, colin: { alto: 0.2, largo: 0.17 } }],
  [/mt-?03/i, { faro: { forma: "mt" }, direccionales: { tipo: "led" }, stop: "led", escape: { forma: "bajo", lata: 0.05 }, horquillaInv: true, tomasAire: true,
    tanque: { alto: 0.16, ancho: 0.4, largo: 0.24, nariz: 0.06 }, aleta: { largo: 0.26, baja: 0.2 }, colin: { alto: 0.15, largo: 0.2 } }],
  [/fz\s*25/i, { faro: { forma: "fz" }, tanque: { alto: 0.11, ancho: 0.46, largo: 0.29, nariz: 0.02 },
    aleta: { largo: 0.22, baja: 0.24 }, colin: { alto: 0.11, largo: 0.26 } }],
  [/apache/i, { faro: { forma: "flecha" }, escape: { forma: "corto", sube: 20, doble: true },
    tanque: { alto: 0.13, ancho: 0.36, largo: 0.27, nariz: 0.07 }, aleta: { largo: 0.24, baja: 0.16 }, colin: { alto: 0.16, largo: 0.24 } }],
  [/gixxer/i, { faro: { forma: "gixxer" }, colin: { alto: 0.14, largo: 0.2, partido: true },
    tanque: { alto: 0.14, ancho: 0.4, largo: 0.24, nariz: 0.05 }, aleta: { largo: 0.2, baja: 0.17 } }],
  // (la NS 200 de 2017 en adelante lleva el silenciador bajo el motor, con las dos puntas junto al basculante)
  [/pulsar\s*ns/i, { faro: { forma: "ns" }, escape: { forma: "bajo", puntas: true },
    tanque: { alto: 0.135, ancho: 0.36, largo: 0.26, nariz: 0.08 }, aleta: { largo: 0.32, baja: 0.24 }, colin: { alto: 0.17, largo: 0.22 } }],
  // ----- Carenadas -----
  [/pulsar\s*rs/i, { carenado: { cupula: 0.24, cubre: 0.78, dobleFaro: true, quilla: true }, manubrio: "sobreTija",
    colin: { alto: 0.13, largo: 0.22 }, escape: { forma: "corto", sube: 22 } }],
  [/\brc\s*200/i, { carenado: { cupula: 0.12, cubre: 0.82, quilla: true }, manubrio: "clipon", estriberasAtras: true,
    colin: { alto: 0.19, largo: 0.24 }, escalon: 0.08, asientoPartido: true, escape: { forma: "bajo" } }],
  // ----- Scooters -----
  [/dio/i, { scooter: { estilo: "redonda", faroManubrio: true } }],
  [/dynamic/i, { scooter: { estilo: "angulosa", faroManubrio: false } }],
  // ----- Semiautomáticas -----
  [/wave/i, { faro: { forma: "manubrio", ancho: 0.15 }, semi: { escudo: "curvo", asientoLargo: 0.62 } }],
  [/crypton/i, { faro: { forma: "manubrio", ancho: 0.17, agudo: true }, semi: { escudo: "anguloso", asientoLargo: 0.6 } }],
  [/best/i, { faro: { forma: "redondo", r: 0.07, enHorquilla: true }, semi: { escudo: "curvo", asientoLargo: 0.58 } }],
  // ----- Clásicas y commuter -----
  [/\bgn\s*125/i, { tanque: { forma: "gota", alto: 0.1, ancho: 0.3, largo: 0.22 }, faro: { forma: "redondo", r: 0.095, cuba: true },
    relojes: "dos", direccionales: { tipo: "redondas", cromo: true }, stop: "redondo", rines: "radios", asientoEscalonado: 0.07, colin: { forma: "corto", alto: 0.07, largo: 0.06 }, manubrio: "alto",
    escape: { forma: "clasico", sube: 9 }, parrilla: true, agarradera: null, guardaTrasCromo: true }],
  [/boxer/i, { tanque: { forma: "gota", alto: 0.09, ancho: 0.32, largo: 0.24 }, faro: { forma: "redondo", r: 0.085, visera: true },
    relojes: "uno", direccionales: { tipo: "redondas" }, stop: "guardabarros",
    colin: { forma: "plano", alto: -0.01, largo: 0.15 }, parrilla: true, agarradera: null, fuelles: true }],
  [/discover/i, { tanque: { forma: "clasico", alto: 0.115, ancho: 0.33, largo: 0.27, aletas: true }, faro: { forma: "trapecio", visera: true },
    colin: { forma: "largo", alto: 0.02, largo: 0.16 }, parrilla: true, agarradera: null, tapaLarga: true }],
  [/eco\s*deluxe/i, { tanque: { forma: "cuadrado", alto: 0.135, ancho: 0.32, largo: 0.28 }, faro: { forma: "rectangular" }, relojes: "uno",
    // (fotos de la HF Deluxe/HF 100 en manual_despiece/hero-eco-deluxe-100: rines de aleación de 5 brazos, direccionales de bombillo)
    rines: "aleacion", direccionales: { tipo: "redondas" },
    colin: { forma: "plano", alto: 0.02, largo: 0.05 }, parrilla: true, agarradera: null, tapaRectangular: true }],
  [/cb\s*125/i, { tanque: { forma: "aletas", alto: 0.12, ancho: 0.34, largo: 0.26, aletaAlto: 0.16 },
    faro: { forma: "agudo", ancho: 0.15, alto: 0.1, punta: 0.07 }, colin: { forma: "respingado", alto: 0.08, largo: 0.18 },
    escape: { forma: "corto", sube: 14, protector: true }, agarradera: "aluminio" }],
  // NKD y CR4: naked de 125 (la línea declara su familia). NKD urbana y sobria; CR4 más racing.
  // NKD (como la foto real): faro redondo grande con aro cromado, sin máscara, colgado de orejas en la horquilla; dos relojes
  // redondos; direccionales de bombillo en vástagos negros; stop sobre el guardabarros; rines de radios
  [/nkd/i, { familia: "naked", faro: { forma: "redondo", r: 0.09, orejas: true }, relojes: "dos", direccionales: { tipo: "redondas" },
    stop: "guardabarros", rines: "radios", tanque: { alto: 0.12, ancho: 0.34, largo: 0.24, nariz: 0.04 },
    aleta: { largo: 0.18, baja: 0.13 }, escalon: 0.04, colin: { alto: 0.1, largo: 0.21 }, escape: { forma: "corto", sube: 16 } }],
  [/cr4/i, { familia: "naked", faro: { forma: "racing" }, tanque: { alto: 0.13, ancho: 0.34, largo: 0.23, nariz: 0.07 },
    aleta: { largo: 0.22, baja: 0.15 }, escalon: 0.065, colin: { alto: 0.19, largo: 0.18 }, escape: { forma: "corto", sube: 24 } }],
];

function mezclar(a, b) {
  const r = { ...a };
  for (const [k, v] of Object.entries(b || {})) {
    r[k] = v && typeof v === "object" && !Array.isArray(v) && a[k] && typeof a[k] === "object" ? { ...a[k], ...v } : v;
  }
  return r;
}

export function rasgosDe(linea, specs) {
  const t = specs.tipo;
  const propia = LINEAS.find(([re]) => re.test(linea));
  const familia = propia?.[1].familia || (t === "scooter" ? "scooter" : t === "semi" ? "semi" : t === "enduro" ? "enduro"
    : t === "sport" || specs.carenado ? "carenada" : specs.cilindraje >= 150 ? "naked" : "clasica");
  let r = { familia, ...FAMILIAS[familia] };
  if (propia) r = mezclar(r, propia[1]);
  r.conocida = !!propia;
  return r;
}
