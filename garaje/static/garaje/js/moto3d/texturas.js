// Texturas dibujadas en canvas: letras de la llanta, calcas y placa.
import * as THREE from "three";
import { CALIDAD } from "./comun.js";

// =====================================================================
// Calcas: diseños propios dibujados en canvas
// =====================================================================
export function aclarar(hex, cantidad) {
  const c = new THREE.Color(hex);
  c.lerp(new THREE.Color(0xffffff), cantidad);
  return `#${c.getHexString()}`;
}

// Textura de las letras de la llanta: el anillo usa coordenadas planas, así que el texto se dibuja en círculo
// sobre un lienzo cuadrado (una vez por medida).
// (caché guardada en la función: este archivo arma la moto antes de llegar a las constantes de abajo)
export function materialLetrasLlanta(medida, enRadio, alto) {
  const letrasLlanta = (materialLetrasLlanta.cache ??= new Map());
  const clave = `${medida}|${enRadio.toFixed(2)}`;
  if (!letrasLlanta.has(clave)) {
    const lado = CALIDAD.nombre === "baja" ? 512 : 1024;
    const c = document.createElement("canvas");
    c.width = c.height = lado;
    const ctx = c.getContext("2d");
    ctx.translate(lado / 2, lado / 2);
    ctx.fillStyle = "rgba(205, 205, 200, 0.55)";
    const fuente = lado * 0.5 * alto;
    ctx.font = `700 ${fuente}px Archivo, Arial, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const radio = lado * 0.5 * enRadio;
    for (const [texto, inicio] of [["TALLERYA", 0], [medida + "  TUBELESS", Math.PI]]) {
      const paso = (fuente * 0.78) / radio;
      let a = inicio - ((texto.length - 1) * paso) / 2;
      for (const letra of texto) {
        ctx.save();
        ctx.rotate(a);
        ctx.translate(0, -radio);
        ctx.fillText(letra, 0, 0);
        ctx.restore();
        a += paso;
      }
    }
    const textura = new THREE.CanvasTexture(c);
    textura.colorSpace = THREE.SRGBColorSpace;
    textura.anisotropy = 4;
    // (Physical con una capa de barniz casi nula: así comparte el sombreador con las calcas, que llevan barniz)
    letrasLlanta.set(clave, new THREE.MeshPhysicalMaterial({
      map: textura, transparent: true, depthWrite: false, roughness: 0.9, polygonOffset: true, polygonOffsetFactor: -2,
      clearcoat: 0.02, clearcoatRoughness: 1,
    }));
  }
  return letrasLlanta.get(clave);
}

export function texturaCalca(diseno, color, texto, imagen = "") {
  if (diseno === "imagen") {
    // Imagen propia: lienzo cuadrado transparente; la imagen (ya reducida a 256 px en el navegador) se dibuja
    // centrada cuando termina de cargar, y se avisa para volver a dibujar la escena.
    const lienzo = document.createElement("canvas");
    lienzo.width = lienzo.height = 256;
    const textura = new THREE.CanvasTexture(lienzo);
    textura.colorSpace = THREE.SRGBColorSpace;
    textura.anisotropy = 8;
    if (imagen) {
      const img = new Image();
      img.onload = () => {
        const k = Math.min(256 / img.width, 256 / img.height);
        const w = img.width * k, h = img.height * k;
        lienzo.getContext("2d").drawImage(img, (256 - w) / 2, (256 - h) / 2, w, h);
        textura.needsUpdate = true;
        window.dispatchEvent(new Event("calca-imagen-lista"));
      };
      img.src = imagen;
    }
    return { textura, aspecto: 1, canvas: lienzo };
  }
  const W = 512;
  const alturas = { franjas: 128, cuadros: 128, texto: 128, llamas: 256, rayo: 256, numero: 512, tallerya: 160 };
  const H = alturas[diseno] || 128;
  const lienzo = document.createElement("canvas");
  lienzo.width = diseno === "numero" ? 512 : W;
  lienzo.height = H;
  const ctx = lienzo.getContext("2d");
  const contorno = "#14181a";

  if (diseno === "franjas") {
    ctx.fillStyle = color;
    ctx.fillRect(0, 18, W, 36);
    ctx.fillRect(0, 74, W, 36);
    ctx.fillStyle = aclarar(color, 0.6);
    ctx.fillRect(0, 60, W, 4);
  } else if (diseno === "cuadros") {
    const lado = 32;
    for (let fila = 0; fila < 3; fila++) {
      for (let col = 0; col < W / lado; col++) {
        if ((fila + col) % 2 === 0) { ctx.fillStyle = color; ctx.fillRect(col * lado, 16 + fila * lado, lado, lado); }
      }
    }
  } else if (diseno === "llamas") {
    const grad = ctx.createLinearGradient(0, 0, W, 0);
    grad.addColorStop(0, color);
    grad.addColorStop(1, aclarar(color, 0.55));
    for (const [y0, largo, grosor] of [[128, 500, 70], [90, 380, 45], [170, 420, 50], [60, 280, 30], [200, 300, 34]]) {
      ctx.beginPath();
      ctx.moveTo(0, y0 - grosor / 2);
      ctx.bezierCurveTo(largo * 0.35, y0 - grosor, largo * 0.6, y0 - grosor * 0.2, largo, y0 - grosor * 0.7);
      ctx.bezierCurveTo(largo * 0.7, y0 + grosor * 0.1, largo * 0.4, y0 + grosor * 0.9, 0, y0 + grosor / 2);
      ctx.closePath();
      ctx.fillStyle = grad;
      ctx.fill();
      ctx.lineWidth = 4;
      ctx.strokeStyle = contorno;
      ctx.stroke();
    }
  } else if (diseno === "rayo") {
    const puntos = [[20, 150], [240, 60], [220, 120], [492, 40], [260, 210], [290, 140], [20, 210]];
    ctx.beginPath();
    puntos.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
    ctx.lineWidth = 8;
    ctx.strokeStyle = contorno;
    ctx.stroke();
  } else if (diseno === "numero") {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(256, 256, 240, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(256, 256, 196, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = contorno;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const numero = (texto || "27").slice(0, 3);
    ctx.font = `700 ${numero.length > 2 ? 200 : 260}px Oswald, Arial, sans-serif`;
    ctx.fillText(numero, 256, 270);
  } else if (diseno === "texto") {
    const frase = (texto || "TALLERYA").toUpperCase();
    let tamano = 100;
    ctx.font = `700 ${tamano}px Oswald, Arial, sans-serif`;
    while (ctx.measureText(frase).width > W - 30 && tamano > 30) { tamano -= 6; ctx.font = `700 ${tamano}px Oswald, Arial, sans-serif`; }
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.lineWidth = 10;
    ctx.strokeStyle = contorno;
    ctx.strokeText(frase, W / 2, H / 2 + 4);
    ctx.fillStyle = color;
    ctx.fillText(frase, W / 2, H / 2 + 4);
  } else if (diseno === "tallerya") {
    ctx.fillStyle = "#e3a72f";
    ctx.beginPath();
    ctx.arc(108, 50, 26, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(20, 140); ctx.lineTo(72, 58); ctx.lineTo(102, 98); ctx.lineTo(128, 72); ctx.lineTo(176, 140);
    ctx.closePath();
    ctx.fill();
    ctx.font = "700 88px Oswald, Arial, sans-serif";
    ctx.textBaseline = "alphabetic";
    ctx.lineWidth = 8;
    ctx.strokeStyle = contorno;
    ctx.strokeText("TALLER", 192, 128);
    ctx.fillStyle = color;
    ctx.fillText("TALLER", 192, 128);
    const ancho = ctx.measureText("TALLER").width;
    ctx.strokeText("YA", 192 + ancho, 128);
    ctx.fillStyle = "#f2611d";
    ctx.fillText("YA", 192 + ancho, 128);
  }

  const textura = new THREE.CanvasTexture(lienzo);
  textura.colorSpace = THREE.SRGBColorSpace;
  textura.anisotropy = 8;
  return { textura, aspecto: lienzo.width / lienzo.height, canvas: lienzo };
}

// Número de la placa sobre la placa trasera, como las placas de Colombia: fondo amarillo, borde negro,
// todos los caracteres en una sola fila (ABC 12D) y el país abajo en letra pequeña.
export function ponerPlaca(placa, texto) {
  const lienzo = document.createElement("canvas");
  lienzo.width = 612;
  lienzo.height = 252;
  const ctx = lienzo.getContext("2d");
  const textura = new THREE.CanvasTexture(lienzo);
  textura.colorSpace = THREE.SRGBColorSpace;
  textura.anisotropy = 4;
  const limpio = String(texto).toUpperCase().replace(/[^A-Z0-9]/g, "");
  // Placa de moto (ABC12D): letras y números separados. Cualquier otro texto (p. ej. TALLERYA) va tal cual.
  const esPlaca = /^[A-Z]{3}[0-9]{2}[A-Z0-9]?$/.test(limpio);
  const fila = esPlaca ? `${limpio.slice(0, 3)} ${limpio.slice(3)}` : limpio;
  const marca = limpio === "TALLERYA";
  function dibujar() {
    ctx.fillStyle = "#f2c230";
    ctx.fillRect(0, 0, 612, 252);
    ctx.strokeStyle = "#111517";
    ctx.lineWidth = 12;
    ctx.beginPath();
    ctx.roundRect(10, 10, 592, 232, 22);
    ctx.stroke();
    ctx.fillStyle = "#111517";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const fuente = '"Oswald", "Arial Narrow", sans-serif';
    ctx.font = `700 150px ${fuente}`;
    const ancho = ctx.measureText(fila).width;
    const escala = Math.min(1, 540 / ancho);
    ctx.save();
    ctx.translate(306, 112);
    ctx.scale(escala, 1);
    if (marca) {
      // TALLER en negro y YA en naranja lava, como el logo
      const anchoTaller = ctx.measureText("TALLER").width;
      const inicio = -ancho / 2;
      ctx.textAlign = "left";
      ctx.fillText("TALLER", inicio, 0);
      ctx.fillStyle = "#f26522";
      ctx.fillText("YA", inicio + anchoTaller, 0);
      ctx.fillStyle = "#111517";
      ctx.textAlign = "center";
    } else {
      ctx.fillText(fila, 0, 0);
    }
    ctx.restore();
    ctx.font = `500 26px ${fuente}`;
    ctx.fillText("C O L O M B I A", 306, 214);
    textura.needsUpdate = true;
  }
  dibujar();
  // Si la tipografía de la marca aún no había cargado, se vuelve a dibujar cuando llegue.
  document.fonts?.load('700 150px "Oswald"').then(dibujar).catch(() => {});
  const lamina = new THREE.Mesh(
    new THREE.PlaneGeometry(0.196, 0.08),
    // (transparente y con barniz leve, igual que las calcas: comparte su sombreador; la textura es opaca, se ve igual)
    new THREE.MeshPhysicalMaterial({ map: textura, roughness: 0.45, metalness: 0.05, polygonOffset: true, polygonOffsetFactor: -2,
      transparent: true, clearcoat: 0.3, clearcoatRoughness: 0.5 }),
  );
  lamina.rotation.y = -Math.PI / 2;
  lamina.position.x = -0.0036;
  placa.add(lamina);
}
