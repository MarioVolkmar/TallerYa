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
  [/mt-?03/i, { faro: { forma: "mt" }, direccionales: { tipo: "redondas" }, // (fotos: direccionales redondas pequeñas, stop LED en la cola)
    stop: "led", escape: { forma: "bajo", lata: 0.05 }, horquillaInv: true, tomasAire: true, rinColor: 0x1fa3e0, // (fotos 2025: rines cian)
    tanque: { alto: 0.16, ancho: 0.4, largo: 0.24, nariz: 0.06 }, aleta: { largo: 0.26, baja: 0.2 }, colin: { alto: 0.15, largo: 0.2 } }],
  [/fz\s*25/i, { faro: { forma: "fz" }, tanque: { alto: 0.11, ancho: 0.46, largo: 0.29, nariz: 0.02 },
    aleta: { largo: 0.22, baja: 0.24 }, colin: { alto: 0.11, largo: 0.26 } }],
  [/apache/i, { faro: { forma: "flecha" }, escape: { forma: "corto", sube: 20, doble: true },
    tanque: { alto: 0.13, ancho: 0.36, largo: 0.27, nariz: 0.07 }, aleta: { largo: 0.24, baja: 0.16 }, colin: { alto: 0.16, largo: 0.24 } }],
  [/gixxer/i, { faro: { forma: "gixxer" }, colin: { alto: 0.14, largo: 0.2, partido: true },
    tanque: { alto: 0.14, ancho: 0.4, largo: 0.24, nariz: 0.05 }, aleta: { largo: 0.2, baja: 0.17 } }],
  // (la NS 200 de 2017 en adelante lleva el silenciador bajo el motor, con las dos puntas junto al basculante)
  [/pulsar\s*ns/i, { faro: { forma: "ns" }, escape: { forma: "bajo", puntas: true }, rinColor: 0xc4161c, // (fotos 2024–2026: rines rojos)
    tanque: { alto: 0.135, ancho: 0.36, largo: 0.26, nariz: 0.08 }, aleta: { largo: 0.32, baja: 0.24 }, colin: { alto: 0.17, largo: 0.22 } }],
  // Naked de 125–150 que por cilindraje caerían en "clásica" (fotos en manual_despiece/<moto>/fotos)
  // Raider 125 (Auteco 2024–2026): tanque anguloso con aletas plateadas, faro LED en flecha con luces diurnas en "Y",
  // mofle corto con protector, stop LED en la punta del colín, rines de aleación
  [/raider/i, { familia: "naked", faro: { forma: "raider" }, stop: "led", rines: "aleacion", direccionales: { tipo: "led" },
    // (aletas largas y afiladas, asiento largo casi plano, colín largo; rines de 5 radios en V rectos)
    tanque: { alto: 0.135, ancho: 0.36, largo: 0.25, nariz: 0.07 }, aleta: { largo: 0.27, baja: 0.19 }, escalon: 0.03,
    colin: { alto: 0.13, largo: 0.25 }, escape: { forma: "corto", sube: 18 }, rinDiseno: { n: 5, dobles: true, rectos: true, abre: 0.16 } }],
  // Hunk 150 (Hero Honda, 2007–2014; fotos de Commons): tanque grande con aletas, faro en carenado tipo bikini del
  // color de la moto con visera, amortiguadores dobles con resorte rojo, mofle subido con protector, aleación
  [/hunk\s*150/i, { familia: "naked", faro: { forma: "bikini" }, rines: "aleacion",
    // (generación anterior: asiento largo y plano, colín bajo con agarradera de tubo, mofle largo subido)
    tanque: { alto: 0.14, ancho: 0.4, largo: 0.27, nariz: 0.05 }, aleta: { largo: 0.24, baja: 0.2 }, escalon: 0,
    colin: { alto: 0.06, largo: 0.22 }, escape: { forma: "clasico", sube: 12 }, agarradera: "tubo" }],
  // Hunk 125R (Hero 2024–2026): tanque musculoso con aletas grandes que llegan hasta la horquilla, faro LED compacto
  // con dos cejas diurnas, guardabarros delantero del color de la moto, asiento partido y colín alto con stop LED
  [/hunk/i, { familia: "naked", faro: { forma: "hunk" }, stop: "led", rines: "aleacion", guardaPintado: true,
    tanque: { alto: 0.145, ancho: 0.4, largo: 0.25, nariz: 0.08 }, aleta: { largo: 0.3, baja: 0.21 }, escalon: 0.08,
    asientoPartido: true, colin: { alto: 0.2, largo: 0.17 }, escape: { forma: "corto", sube: 24 } }],
  // FZ 2.0 (FZ-S FI V2, B6U1): tanque ancho y bajo con aletas (antecesora de la FZ25), faro en trapecio con las dos
  // luces de posición arriba, colín largo, mofle corto
  [/\bfz\s*2|\bfz-?s\b|\bfz\s*16|\bfz\s*150/i, { familia: "naked", faro: { forma: "fz" }, rines: "aleacion", guardaPintado: true,
    // (aletas con inserto negro de toma de aire, asiento casi plano, colín largo y bajo)
    tanque: { alto: 0.12, ancho: 0.44, largo: 0.28, nariz: 0.03 }, aleta: { largo: 0.2, baja: 0.21 }, tomasAire: true, escalon: 0.02,
    colin: { alto: 0.1, largo: 0.27 }, escape: { forma: "corto", sube: 10 } }],
  // ----- Doble propósito (enduro) con carrocería propia -----
  // XTZ 150 (fotos Galgo/Incolmotos): sobre la XTZ, máscara negra con el faro adentro, tapas laterales, colín y
  // guardabarros delantero negros (la XTZ 125 es toda del color de la moto, con faro redondo)
  [/\bxtz\s*150/i, { enduro: { modelo: "xtz", tapas: "oscuro", guarda: "oscuro" }, faro: { forma: "mascara", color: "oscuro", alto: 0.21 } }],
  // XR 190L (Honda 2020–2026, inspirada en la CRF): aletas rojas grandes que bajan hasta el frente del motor, máscara
  // alta del color de la moto con el faro adentro, guardabarros alto, asiento largo y plano, colín largo
  [/\bxr\s*190/i, { enduro: { modelo: "xr" }, faro: { forma: "mascara", color: "pintura", alto: 0.21 } }],
  // DR 150 (Suzuki 2021–2026): tanque más ancho arriba en el color de la versión, aletas con la mitad baja negra,
  // tapas laterales y colín negros, máscara negra angulosa
  [/\bdr\s*150/i, { enduro: { modelo: "dr", tapas: "oscuro", guarda: "oscuro" }, faro: { forma: "mascara", color: "oscuro", alto: 0.2 } }],
  // ----- Carenadas -----
  [/pulsar\s*rs/i, { carenado: { cupula: 0.24, cubre: 0.78, dobleFaro: true, quilla: true }, manubrio: "sobreTija",
    colin: { alto: 0.13, largo: 0.22 }, escape: { forma: "corto", sube: 22 } }],
  [/\brc\s*200/i, { carenado: { cupula: 0.12, cubre: 0.82, quilla: true }, manubrio: "clipon", estriberasAtras: true,
    colin: { alto: 0.19, largo: 0.24 }, escalon: 0.08, asientoPartido: true, escape: { forma: "bajo" } }],
  // ----- Scooters -----
  [/dio/i, { scooter: { estilo: "redonda", faroManubrio: true, faroEscudo: true } }],
  [/dynamic/i, { scooter: { estilo: "angulosa", faroManubrio: false } }],
  // ----- Semiautomáticas -----
  [/wave/i, { faro: { forma: "manubrio", ancho: 0.15 }, semi: { escudo: "curvo", asientoLargo: 0.62 } }],
  [/crypton/i, { faro: { forma: "manubrio", ancho: 0.17, agudo: true }, semi: { escudo: "anguloso", asientoLargo: 0.6 } }],
  [/best/i, { faro: { forma: "redondo", r: 0.07, enHorquilla: true }, semi: { escudo: "curvo", asientoLargo: 0.58 } }],
  // ----- Clásicas y commuter -----
  [/\bgn\s*125/i, { tanque: { forma: "gota", alto: 0.1, ancho: 0.3, largo: 0.22 }, faro: { forma: "redondo", r: 0.095, cuba: true },
    relojes: "dos", direccionales: { tipo: "redondas", cromo: true }, stop: "redondo", rines: "aleacion", // (GN 125 ABS actual: rines de aleación negros, fotos en manual_despiece/suzuki-gn-125)
    asientoEscalonado: 0.07, colin: { forma: "corto", alto: 0.07, largo: 0.06 }, manubrio: "alto",
    escape: { forma: "clasico", sube: 9 }, parrilla: true, agarradera: null, guardaTrasCromo: true }],
  // Boxer CT 125 (fotos Auteco 2024–2026): a diferencia de la CT 100, faro dentro de un carenado en trapecio con
  // visera, tanque más anguloso, tapa lateral grande, colín largo con el stop en la punta y rines de aleación
  [/boxer\s*ct\s*125|\bct\s*125/i, { tanque: { forma: "cuadrado", alto: 0.115, ancho: 0.32, largo: 0.26 }, faro: { forma: "trapecio", visera: true },
    rines: "aleacion", direccionales: { tipo: "redondas" }, colin: { forma: "largo", alto: 0.02, largo: 0.16 }, parrilla: true,
    agarradera: null, tapaRectangular: true, guardaPintado: true }],
  // Boxer CT 100 (fotos en manual_despiece/auteco-bajaj-boxer-ct-100): de mandados; asiento largo y plano, colín bajo
  // con parrilla cromada, mofle largo y bajo, rines de radios y fuelles en la horquilla
  [/boxer/i, { tanque: { forma: "gota", alto: 0.09, ancho: 0.32, largo: 0.24 }, faro: { forma: "redondo", r: 0.085, visera: true },
    relojes: "uno", direccionales: { tipo: "redondas" }, stop: "guardabarros", rines: "radios", escalon: 0,
    colin: { forma: "plano", alto: -0.02, largo: 0.17 }, escape: { forma: "clasico", sube: 3 }, parrilla: true, agarradera: null, fuelles: true }],
  // Discover 125 (fotos 2020+): deportiva; tanque con aletas, asiento escalonado, colín alto y afilado con agarraderas
  // partidas, mofle corto subido con protector y rines de aleación de 5 brazos
  [/discover/i, { tanque: { forma: "clasico", alto: 0.125, ancho: 0.34, largo: 0.27, aletas: true }, faro: { forma: "trapecio", visera: true }, rines: "aleacion",
    rinDiseno: { n: 5, rectos: true }, asientoEscalonado: 0.06, colin: { forma: "respingado", alto: 0.1, largo: 0.19 },
    escape: { forma: "corto", sube: 15, protector: true }, agarradera: "aluminio", tapaLarga: true }],
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
    // (urbana retro: aletas chicas, asiento largo y plano, colín bajo con agarradera de tubo)
    aleta: { largo: 0.12, baja: 0.09 }, escalon: 0, colin: { alto: 0.06, largo: 0.18 }, escape: { forma: "corto", sube: 10 }, agarradera: "tubo" }],
  [/cr4/i, { familia: "naked", faro: { forma: "racing" }, tanque: { alto: 0.13, ancho: 0.34, largo: 0.23, nariz: 0.07 },
    // (fotos AKT 2026: cinta lima en el borde de los rines)
    aleta: { largo: 0.22, baja: 0.15 }, escalon: 0.065, colin: { alto: 0.19, largo: 0.18 }, escape: { forma: "corto", sube: 24 }, cintaRin: 0xb5e61d }],
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
