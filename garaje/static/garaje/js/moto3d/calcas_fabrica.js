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
  tvs_script: { familia: "Kanit", peso: 600, cursiva: true, sesgo: -0.3, espaciado: 0, ancho: 1.05 },
  cuadrada: { familia: "Orbitron", peso: 800, cursiva: false, sesgo: -0.18, espaciado: 0.06, ancho: 1.1 },
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
  // FZ25 (fotos 2024–2026): sobria; "FZ" plateado en la cubierta negra del tanque, "25" del color de la versión
  // debajo y "ABS" chico en el guardabarros
  [/fz\s*25/i, () => [N("FZ", ["tanque"], { posicion: 0.55, altura: -0.45, ancho: 0.09, color: "gris" }),
    C("25", ["tanque"], { posicion: 0.6, altura: -0.75, ancho: 0.05, color: "vivo:#3a5bd9", color2: "contorno" }),
    { id: "abs", nombre: "ABS", tipo: "texto", texto: "ABS", zona: ["frontal"], cara: "lado", posicion: 0.6, altura: -0.6, ancho: 0.04, color: "gris" }]],
  // FZ 2.0 (FZ-S FI V2, fotos de Commons): "FZ-S" plateado grande en la aleta, barra del color de la versión encima
  // y "FI" chico en la tapa lateral
  [/\bfz\s*2(?!5)|\bfz-?s\b|\bfz\s*1[56]/i, () => [N("FZ-S", ["tanque"], { posicion: 0.3, altura: -0.35, ancho: 0.13, giro: 4, color: "gris" }),
    F(["tanque"], { id: "barra", nombre: "Barra de la aleta", forma: "barra", angosto: 0.6, posicion: 0.3, altura: 0.05, ancho: 0.17, giro: 6, color: "vivo:#2a8fd6" }),
    C("FI", ["lateral", "cola"], { posicion: 0, altura: -0.2, ancho: 0.05, color: "gris", color2: "contorno" })]],
  [/\bfz/i, () => [N("FZ", ["tanque"], { ancho: 0.16 }), F(["tanque"], { altura: -0.5 })]],
  // XTZ (fotos XTZ150 2024–2026): "XTZ150" plateado arriba en la cubierta del tanque, bloques inclinados del
  // color de la versión debajo y una barra en la cola
  [/xtz/i, (l) => [N("XTZ" + ((l.match(/\b(125|150|250)\b/) || [, "125"])[1]), ["tanque"], { posicion: 0.05, altura: 0.1, ancho: 0.16, giro: 6, color: "gris" }),
    F(["tanque"], { id: "rayas", nombre: "Bloques del tanque", forma: "rayas", rayas: 4, posicion: 0.1, altura: -0.15, ancho: 0.11, color: "vivo:#2f5fd6", color2: "vivo:#2f5fd6" }),
    F(["cola", "lateral"], { id: "barra", nombre: "Barra de la cola", forma: "barra", angosto: 0.6, posicion: 0, altura: 0, ancho: 0.2, giro: 8, color: "vivo:#2f5fd6" })]],
  // MT-03 (fotos 2025): en la cubierta delantera del tanque, una barra inclinada del color de la versión y "MT-03"
  // oscuro de letra cuadrada debajo
  [/mt-?03/i, () => [F(["tanque"], { id: "barra", nombre: "Barra del tanque", forma: "barra", angosto: 0.55, posicion: 0.2, altura: 0.1, ancho: 0.2, giro: -18, color: "vivo:#29a8e8" }),
    N("MT-03", ["tanque"], { fuente: "cuadrada", posicion: 0.3, altura: -0.45, ancho: 0.11, giro: -12, color: "letra" })]],
  // Crypton FI (fotos 2026): filete morado a lo largo de la cola, "CRYPTON" chico arriba, "115" oscuro atrás y una
  // franja morada en el escudo
  [/crypton/i, () => [F(["lateral"], { id: "filete", nombre: "Filete", forma: "filete", posicion: -0.25, altura: 0.05, ancho: 0.5, giro: -8, color: "vivo:#7b4fb0", color2: "vivo:#7b4fb0" }),
    N("CRYPTON", ["lateral"], { posicion: -0.5, altura: 0.5, ancho: 0.13, giro: -5, color: "vivo:#7b4fb0" }),
    C("115", ["lateral"], { posicion: -0.7, altura: 0.25, ancho: 0.06, color: "letra", color2: "contorno" }),
    F(["frontal"], { id: "barra", nombre: "Franja del escudo", forma: "barra", angosto: 0.5, posicion: 0, altura: 0, ancho: 0.14, giro: 60, color: "vivo:#7b4fb0" })]],
  [/bws/i, () => [N("BWS", ["lateral"], { ancho: 0.24, altura: 0.2 }), F(["lateral"], { altura: -0.3 })]],
  // Duke (fotos 200 de 2024–2026): "200" naranja enorme y ladeado en la cubierta blanca del tanque, filete naranja
  // y "DUKE" chico oscuro en la cola
  [/duke/i, (l) => [C((l.match(/\b(125|200|250|390)\b/) || [, "200"])[1], ["tanque"], { posicion: 0.15, altura: -0.25, ancho: 0.22, giro: 10, color: "vivo:#f26a1b", color2: "contorno", estirar: 1.2 }),
    F(["tanque"], { id: "filete", nombre: "Filete", forma: "filete", posicion: 0.1, altura: 0.3, ancho: 0.3, giro: 6, color: "vivo:#f26a1b", color2: "gris" }),
    N("DUKE", ["lateral", "cola"], { posicion: -0.2, altura: -0.1, ancho: 0.1, color: "letra" })]],
  // RC 200 (fotos 2024–2026): en el costado del carenado, cortes angulares claros, "RC" grande claro con "200"
  // naranja debajo, y un filete naranja en la cola
  [/\brc\s*200/i, () => [F(["frontal"], { id: "rayas", nombre: "Cortes del carenado", forma: "rayas", rayas: 3, posicion: -0.45, altura: -0.05, ancho: 0.14, color: "letra", color2: "letra" }),
    N("RC", ["frontal"], { posicion: 0.05, altura: 0.15, ancho: 0.13, color: "letra" }),
    C("200", ["frontal"], { posicion: 0.1, altura: -0.25, ancho: 0.07, color: "vivo:#f26a1b", color2: "contorno" }),
    F(["cola", "lateral"], { id: "barra", nombre: "Barra de la cola", forma: "barra", angosto: 0.6, posicion: 0, altura: 0, ancho: 0.2, giro: 8, color: "vivo:#f26a1b" })]],
  [/\brc\s*390/i, () => [N("RC", ["frontal"], { posicion: -0.2, altura: 0.05, ancho: 0.2 }), C("390", ["lateral", "cola"], { ancho: 0.11 })]],
  // Pulsar NS (fotos NS200 2024–2026): "200" grande con borde rojo en la cubierta del tanque, rayas rojas y azules
  // que suben hacia atrás y "NS" chico en la cola
  [/pulsar\s*ns/i, (l) => [C((l.match(/\b(125|160|200)\b/) || [, "200"])[1], ["tanque"], { posicion: 0.2, altura: -0.35, ancho: 0.17, giro: 8, color: "vivo:#1f3a8a", color2: "#c4161c" }),
    F(["tanque"], { id: "rayas", nombre: "Rayas del tanque", forma: "rayas", posicion: -0.4, altura: 0.1, ancho: 0.1, color: "#c4161c", color2: "vivo:#1f3a8a" }),
    N("NS", ["cola", "lateral"], { posicion: 0, altura: 0.1, ancho: 0.06, color: "gris" })]],
  // Pulsar RS 200 (fotos 2024–2026): carenado sobrio; "RS200" claro abajo en el carenado, sobre la quilla, y
  // "PULSAR" chico gris arriba
  [/pulsar\s*rs/i, () => [C("RS200", ["frontal"], { posicion: -0.1, altura: -0.5, ancho: 0.14, color: "letra", color2: "contorno" }),
    N("PULSAR", ["frontal"], { posicion: -0.3, altura: 0.35, ancho: 0.12, color: "gris" })]],
  [/pulsar/i, () => [N("PULSAR", ["tanque"], { ancho: 0.28 }), F(["tanque"], { altura: -0.5 })]],
  // Boxer CT 100 (fotos pocas y dudosas): cuña azul y blanca en el tanque con "CT" grande cursivo encima y "BOXER"
  // chico en la tapa lateral
  // Boxer CT 125 (fotos Galgo 2024–2026): cuña lima y negra en el tanque, "CT125" lima en cursiva encima y "BOXER"
  // chico en la tapa lateral
  [/boxer\s*ct\s*125|\bct\s*125/i, () => [F(["tanque"], { id: "cuna", nombre: "Cuña del tanque", angosto: 0.4, posicion: 0.05, altura: -0.3, ancho: 0.26, color: "vivo:#b5e61d", color2: "#1b1e20" }),
    N("CT125", ["tanque"], { posicion: 0.0, altura: 0.1, ancho: 0.11, color: "vivo:#b5e61d", color2: "contorno" }),
    N("BOXER", ["lateral", "cola"], { id: "modelo", nombre: "BOXER", posicion: 0, altura: -0.2, ancho: 0.1, color: "gris" })]],
  [/boxer/i, () => [F(["tanque"], { id: "cuna", nombre: "Cuña del tanque", angosto: 0.4, posicion: 0, altura: -0.25, ancho: 0.26, color: "vivo:#2a4bd0", color2: "#ffffff" }),
    N("CT", ["tanque"], { id: "ct", nombre: "CT", posicion: -0.05, altura: 0.1, ancho: 0.08, color: "letra" }),
    F(["lateral"], { id: "tapa", nombre: "Tapa lateral plateada", forma: "barra", angosto: 0.8, posicion: 0, altura: 0, ancho: 0.2, color: "#c9cdd1" }),
    N("BOXER", ["lateral", "cola"], { posicion: 0, altura: -0.2, ancho: 0.1, color: "gris" })]],
  // Discover 125 (fotos 2020+): flecha lima en la aleta del tanque, "125" encima y "DISCOVER" claro en el colín
  [/discover/i, () => [F(["tanque"], { id: "flecha", nombre: "Flecha del tanque", forma: "flecha", angosto: 0.45, posicion: 0.25, altura: -0.3, ancho: 0.2, color: "vivo:#cfe01f", color2: "#1b1e20" }),
    C("125", ["tanque"], { posicion: -0.15, altura: 0.15, ancho: 0.06, color: "vivo:#cfe01f", color2: "contorno" }),
    N("DISCOVER", ["cola", "lateral"], { posicion: 0, altura: -0.1, ancho: 0.16, color: "letra" })]],
  [/gixxer\s*sf/i, () => [N("GIXXER SF", ["frontal"], { posicion: -0.15, altura: 0.05, ancho: 0.34 }), F(["frontal"], { posicion: -0.1, altura: -0.45, ancho: 0.42 })]],
  // Gixxer 150 (fotos 2024–2026): en la cubierta del tanque, una fila de trazos claros hacia adelante, un filete
  // claro y "GIXXER" del color de la versión abajo; barra del mismo color en la cola
  [/gixxer/i, () => [F(["tanque"], { id: "trazos", nombre: "Trazos del tanque", forma: "trazos", angosto: 0.7, posicion: 0.15, altura: -0.15, ancho: 0.15, color: "letra" }),
    N("GIXXER", ["tanque"], { posicion: 0.35, altura: -0.6, ancho: 0.15, giro: 6, color: "vivo:#1f6fd1" }),
    F(["cola", "lateral"], { id: "barra", nombre: "Barra de la cola", forma: "barra", angosto: 0.6, posicion: 0, altura: 0, ancho: 0.18, giro: 10, color: "vivo:#1f6fd1" })]],
  // GN 125 (fotos 2024–2026): "GN" grande rojo con borde oscuro en el tanque sobre una cuña roja; en la tapa lateral,
  // barra roja y "GN125F" chico
  [/\bgn\s*125/i, () => [F(["tanque"], { id: "cuna", nombre: "Cuña del tanque", angosto: 0.4, posicion: -0.05, altura: -0.15, ancho: 0.24, color: "#c4161c", color2: "#141414" }),
    N("GN", ["tanque"], { posicion: 0.05, altura: -0.1, ancho: 0.11, color: "#c4161c", color2: "#141414" }),
    F(["lateral", "cola"], { id: "barra", nombre: "Barra lateral", forma: "barra", angosto: 0.6, posicion: 0, altura: 0.1, ancho: 0.13, color: "#c4161c" }),
    N("GN125F", ["lateral", "cola"], { id: "modelo", nombre: "Modelo GN125F", posicion: 0, altura: -0.45, ancho: 0.08, color: "gris" })]],
  // NKD (fotos AKT 2026): tanque liso con un bloque oscuro adelante arriba y una barra lima detrás; barra lima y
  // "NKD" chico en la tapa lateral
  [/nkd/i, () => [F(["tanque"], { id: "flecha", nombre: "Flecha del tanque", forma: "flecha", angosto: 0.4, posicion: 0.35, altura: 0.1, ancho: 0.17, color: "vivo:#c6e23a", color2: "#1b1e20" }),
    F(["lateral", "cola"], { id: "barra", nombre: "Barra lateral", forma: "barra", angosto: 0.6, posicion: 0.1, altura: -0.3, ancho: 0.14, color: "vivo:#c6e23a" }),
    N("NKD", ["lateral", "cola"], { posicion: 0, altura: -0.52, ancho: 0.1, color: "gris" })]],
  // CR4 (fotos AKT 2026): "125" lima enorme en el costado del tanque, "CR4" hueco gris en la tapa del tanque y un
  // filete lima en la cola
  [/cr4/i, () => [C("125", ["tanque"], { posicion: -0.1, altura: -0.1, ancho: 0.22, color: "vivo:#b5e61d", color2: "contorno", estirar: 1.25 }),
    N("CR4", ["tanque"], { posicion: 0.6, altura: -0.05, ancho: 0.15, giro: 22, contorno: true, color: "gris" }),
    F(["cola"], { id: "filete", nombre: "Filete de la cola", forma: "filete", posicion: 0, altura: 0.1, ancho: 0.32, giro: 8, color: "vivo:#b5e61d", color2: "gris" })]],
  [/ttr/i, () => [N("TTR", ["tanque"], { ancho: 0.2 }), C("125", ["lateral", "cola"], { ancho: 0.1 })]],
  // Dynamic Pro (fotos AKT 2026): "DYNAMIC" claro subiendo en la tapa trasera, filete lima por el borde del
  // carenado y "125" chico en el escudo
  [/dynamic/i, () => [N("DYNAMIC", ["lateral"], { posicion: -0.5, altura: 0.35, ancho: 0.27, giro: 12, color: "letra" }),
    F(["lateral"], { id: "filete", nombre: "Filete", forma: "filete", posicion: -0.3, altura: -0.1, ancho: 0.38, giro: 10, color: "vivo:#c6e23a", color2: "vivo:#c6e23a" }),
    C("125", ["frontal"], { posicion: 0.2, altura: 0.2, ancho: 0.06, color: "gris", color2: "contorno" })]],
  // Dio (fotos 2024–2026): muy sobria; solo "Dio" chico en cursiva gris en el costado trasero
  [/\bdio\b/i, () => [N("Dio", ["lateral"], { fuente: "tvs_script", posicion: -0.4, altura: 0.3, ancho: 0.08, color: "gris" })]],
  // CB125F (fotos 2024–2026): "CB" grande claro en la cubierta del tanque con rayas rojas detrás y "CB125F" chico
  // en la tapa lateral
  [/cb\s*125/i, () => [F(["tanque"], { id: "rayas", nombre: "Rayas del tanque", forma: "rayas", rayas: 5, posicion: -0.15, altura: -0.2, ancho: 0.13, color: "vivo:#d0202a", color2: "vivo:#d0202a" }),
    N("CB", ["tanque"], { posicion: 0.25, altura: -0.1, ancho: 0.1, contorno: true, color: "letra" }),
    N("CB125F", ["lateral", "cola"], { id: "modelo", nombre: "Modelo CB125F", posicion: 0, altura: -0.3, ancho: 0.08, color: "gris" })]],
  [/cb\s*1[69]0/i, (l) => [N("CB" + (l.match(/\b(160|190)\b/) || [, "190"])[1], ["tanque"], { ancho: 0.24 }), F(["tanque"], { altura: -0.5 })]],
  // XR 190L (fotos Galgo 2020–2026): cuña blanca y negra grande en la aleta con "XR 190L" grande (≈ 60 % de la aleta, en diagonal) blanco de borde negro encima
  [/\bxr\s*190/i, () => [F(["tanque"], { id: "cuna", nombre: "Cuña de la aleta", angosto: 0.45, posicion: 0.0, altura: -0.25, ancho: 0.28, color: "#f2f2f2", color2: "#141414" }),
    N("XR 190L", ["tanque"], { posicion: -0.2, altura: -0.1, ancho: 0.15, giro: 10, color: "#f4f4f2", color2: "#141414" })]],
  // DR 150 (fotos Galgo 2025): filete del color de la versión a lo largo de la tapa lateral negra y "DR150" claro
  [/\bdr\s*150/i, () => [F(["lateral", "cola"], { id: "filete", nombre: "Filete lateral", forma: "filete", posicion: 0, altura: -0.1, ancho: 0.3, giro: 6, color: "vivo:#d6e02a", color2: "vivo:#d6e02a" }),
    N("DR150", ["tanque"], { posicion: -0.05, altura: -0.45, ancho: 0.11, color: "#e8e8e8" })]],
  // Raider 125 (fotos Auteco 2024–2026): rayas finas en la aleta, "125" con borde en el tanque y "RAIDER" en la tapa
  [/raider/i, () => [F(["tanque"], { id: "rayas", nombre: "Rayas de la aleta", forma: "rayas", rayas: 3, posicion: 0.2, altura: -0.35, ancho: 0.1, color: "letra", color2: "vivo:#e23b2e" }),
    C("125", ["tanque"], { posicion: -0.2, altura: 0.0, ancho: 0.07, color: "vivo:#e23b2e", color2: "contorno" }),
    N("RAIDER", ["lateral", "cola"], { posicion: 0, altura: -0.2, ancho: 0.16, color: "letra" })]],
  // Hunk 150 (Hero Honda 2007–2014, fotos de Commons): "Hunk" grande en cursiva en el tanque, franja del color de la
  // gráfica en la aleta y "150" chico en la tapa lateral
  [/hunk\s*150/i, () => [N("Hunk", ["tanque"], { fuente: "tvs_script", posicion: 0.05, altura: 0.0, ancho: 0.17, giro: 6, color: "letra" }),
    F(["tanque"], { id: "franja", nombre: "Franja de la aleta", forma: "barra", angosto: 0.6, posicion: 0.3, altura: -0.45, ancho: 0.16, giro: 4, color: "vivo:#c4161c" }),
    C("150", ["lateral", "cola"], { posicion: 0, altura: -0.1, ancho: 0.06, color: "gris", color2: "contorno" })]],
  // Hunk 125R (fotos Galgo 2024–2026): flecha del color de la versión sobre negro en la aleta, "HUNK" claro y "125R"
  // chico en la cola
  [/hunk/i, () => [F(["tanque"], { id: "flecha", nombre: "Flecha de la aleta", forma: "flecha", angosto: 0.4, posicion: 0.3, altura: -0.15, ancho: 0.18, color: "vivo:#d0202a", color2: "#1b1e20" }),
    N("HUNK", ["tanque"], { posicion: -0.1, altura: 0.15, ancho: 0.17, color: "letra" }),
    C("125R", ["cola", "lateral"], { posicion: 0, altura: 0, ancho: 0.07, color: "gris", color2: "contorno" })]],
  // XR150L (fotos 2024–2026): cuña doble clara y oscura grande en la cubierta del tanque y "XR150L" chico en la cola
  [/\bxr\s*\d/i, (l) => [F(["tanque"], { id: "cuna", nombre: "Cuña del tanque", angosto: 0.45, posicion: 0.1, altura: -0.2, ancho: 0.26, color: "#f2f2f2", color2: "#141414" }),
    N("XR" + (l.match(/\b(125|150|190)\b/) || [, "150"])[1] + "L", ["cola", "lateral"], { posicion: 0, altura: 0, ancho: 0.11, color: "letra" })]],
  // Wave 110 S (fotos pocas): filete azul y blanco por el costado trasero y "WAVE" chico encima
  [/wave/i, () => [F(["lateral"], { id: "filete", nombre: "Filete", forma: "filete", posicion: -0.3, altura: 0, ancho: 0.4, giro: -6, color: "vivo:#2a4bd0", color2: "#ffffff" }),
    N("WAVE", ["lateral"], { posicion: -0.5, altura: 0.4, ancho: 0.14, color: "letra" })]],
  // Apache RTR 160 (fotos 2024–2026): tres zarpazos del color de la versión atrás en el tanque, "Apache" en letra
  // cursiva clara en el panel bajo el asiento y "RTR" chico en la cola
  [/apache/i, () => [F(["tanque"], { id: "rayas", nombre: "Zarpazos del tanque", forma: "rayas", posicion: -0.3, altura: -0.1, ancho: 0.09, giro: -10, color: "vivo:#2c5fd8", color2: "#141414" }),
    N("Apache", ["lateral", "cola"], { fuente: "tvs_script", posicion: 0.1, altura: -0.45, ancho: 0.13, giro: 8, color: "gris" }),
    C("RTR", ["cola", "lateral"], { posicion: -0.3, altura: 0.2, ancho: 0.06, color: "vivo:#2c5fd8", color2: "contorno" })]],
  // Eco Deluxe (fotos de la HF 100, la misma moto): cuña doble plata y roja en el tanque con la punta adelante;
  // en la tapa lateral, otra cuña igual encima del nombre
  [/eco\s*deluxe/i, () => [F(["tanque"], { id: "cuna", nombre: "Cuña del tanque", angosto: 0.35, posicion: 0.05, altura: -0.05, ancho: 0.32, color: "#c9cdd1", color2: "#c4161c" }),
    F(["lateral", "cola"], { id: "cuna_lateral", nombre: "Cuña lateral", angosto: 0.5, posicion: 0, altura: -0.3, ancho: 0.13, color: "#c9cdd1", color2: "#c4161c" }),
    N("ECO DELUXE", ["lateral", "cola"], { posicion: 0, altura: -0.6, ancho: 0.15, color: "letra" })]],
  // Best 125 (fotos pocas): filete oscuro y claro por el costado trasero y "Best" cursivo
  [/\bbest\b/i, () => [F(["lateral", "cola"], { id: "filete", nombre: "Filete", forma: "filete", posicion: -0.2, altura: 0, ancho: 0.4, giro: -6, color: "#141414", color2: "#f2f2f2" }),
    N("Best", ["lateral", "cola"], { fuente: "tvs_script", posicion: -0.45, altura: 0.4, ancho: 0.1, color: "letra" })]],
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
  // angosto (0–1): la forma ocupa esa fracción del ancho, así queda más alta para el mismo ancho sobre la moto
  const angosto = c.forma === "rayas" ? 1 : c.angosto || 1;
  ctx.translate((W * (1 - angosto)) / 2, 0);
  ctx.scale(angosto, 1);
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
  } else if (c.forma === "flecha") {
    // Bloque oscuro en punta hacia adelante con una barra inclinada de color detrás (como la del tanque de la NKD)
    poli([[W * 0.42, H * 0.08], [W - 16, H * 0.08], [W - 16, H * 0.5], [W * 0.6, H * 0.92], [W * 0.5, H * 0.92]], col.s);
    poli([[W * 0.2, H * 0.08], [W * 0.38, H * 0.08], [W * 0.26, H * 0.92], [W * 0.08, H * 0.92]], col.p);
    usado = W * 0.94;
  } else if (c.forma === "trazos") {
    // Fila de trazos inclinados que se alargan hacia adelante y terminan en una barra larga
    const n = 5;
    for (let i = 0; i < n; i++) {
      const x = 16 + i * W * 0.11, largo = W * (0.04 + i * 0.012);
      poli([[x + H * 0.2, H * 0.3], [x + H * 0.2 + largo, H * 0.3], [x + largo, H * 0.7], [x, H * 0.7]], col.p);
    }
    poli([[W * 0.62 + H * 0.2, H * 0.3], [W - 16, H * 0.3], [W - 16 - H * 0.2, H * 0.7], [W * 0.62, H * 0.7]], col.p);
  } else if (c.forma === "barra") {
    // Barra fina inclinada, con la punta trasera cortada en diagonal (c.grueso la engruesa: 1 = la fina de siempre)
    const g = 74 * (c.grueso || 1);
    poli([[16, H * 0.72], [W - 16 - g, H * 0.28], [W - 16, H * 0.28], [16 + g, H * 0.72]], col.p);
  } else {
    // Cuña doble: una gruesa con la punta hacia adelante y una fina debajo
    poli([[20, H * 0.32], [W - 120, H * 0.22], [W - 20, H * 0.42], [60, H * 0.56]], col.p);
    poli([[120, H * 0.66], [W - 60, H * 0.54], [W - 40, H * 0.6], [150, H * 0.74]], col.s);
  }
  ctx.restore();
  return usado * angosto;
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
