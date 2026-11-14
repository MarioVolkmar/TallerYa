// Modelo 3D de la moto del usuario, armado a partir de la ficha técnica de su línea.
// Cada pieza de mantenimiento es un grupo con userData.pieza para colorearla y seleccionarla.
// Este archivo es la entrada: escena, controles e interfaz. El armado y las utilidades están en moto3d/.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { DecalGeometry } from "three/addons/geometries/DecalGeometry.js";
import { V, ETAPAS, CALIDAD, pedazos } from "./moto3d/comun.js";
import { cachePaneles, prepararCache, guardarCache } from "./moto3d/cache.js";
import { construirMoto } from "./moto3d/construir.js";
import { texturaCalca, ponerPlaca } from "./moto3d/texturas.js";


// Línea de tiempo de la carga (ms desde que se abrió la página): __visor.info().tiempos
const TIEMPOS = { modulo: Math.round(performance.now()) };
const marcar = (nombre) => { TIEMPOS[nombre] ??= Math.round(performance.now()); };
const ESTADO_COLOR = { ok: 0x3fbf6b, pronto: 0xe3a72f, vencido: 0xff5a3c, desconocido: 0x8a9096 };
const ETIQUETA = { ok: "Al día", pronto: "Pronto", vencido: "Toca ya", desconocido: "Sin registro" };


const contenedor = document.getElementById("visor");
const datos = JSON.parse(document.getElementById("datos-moto").textContent);
const ficha = document.getElementById("visor-ficha");
const cargando = document.getElementById("visor-cargando");

function avisar(texto) {
  if (cargando) cargando.textContent = texto;
}
// Sin gráficos 3D (o si el armado falla): una imagen fija de una moto con el aviso, en vez del visor vacío
function respaldo(texto) {
  window.__moto3dListo = true; // (para que el aviso de "sin conexión" de la página no lo reemplace)
  // Sin 3D no se puede girar ni cambiar de vista: fuera la ayuda y los controles del visor
  for (const id of ["visor-ayuda", "visor-vivo"]) document.getElementById(id)?.setAttribute("hidden", "");
  const controles = contenedor.querySelector(".visor-controles");
  if (controles) controles.style.display = "none";
  if (!cargando) return;
  cargando.classList.add("visor-respaldo");
  cargando.textContent = "";
  const img = document.createElement("img");
  // Dibujo según el tipo: scooter o moto
  const archivo = datos.specs?.tipo === "scooter" ? "moto-respaldo-scooter.svg" : "moto-respaldo.svg";
  img.src = new URL(`../img/${archivo}`, import.meta.url).href;
  img.alt = "Dibujo de una moto";
  const p = document.createElement("p");
  p.textContent = texto;
  cargando.append(img, p);
}


async function arrancar() {
  window.__moto3dEsperando = false;
  marcar("arranca");
  // La caché se lee mientras se prepara la escena (en paralelo, no antes). Si tarda más de 400 ms, se arma sin ella.
  const lecturaCache = Promise.race([prepararCache(datos), new Promise((r) => setTimeout(r, 400))]).then(() => marcar("cache"));
  try {
    await iniciar(lecturaCache);
  } catch (error) {
    console.error(error);
    respaldo("Tu navegador no pudo mostrar el modelo 3D. El plan de mantenimiento sigue disponible abajo.");
  }
}
// La moto se arma cuando el visor está por aparecer en pantalla: si la persona entra y se queda en otra parte
// de la página (o la pestaña está en segundo plano), el celular no gasta batería armando algo que no se ve.
const caja0 = contenedor.getBoundingClientRect();
// (dentro de la portada, en un iframe, siempre se arma de una: ahí el vigía no siempre se entera de que se ve)
const yaSeVe = "vitrina" in contenedor.dataset || (caja0.top < innerHeight + 300 && caja0.bottom > -300);
if (!yaSeVe && "IntersectionObserver" in window) {
  window.__moto3dEsperando = true;
  const vigia = new IntersectionObserver((entradas) => {
    if (entradas.some((e) => e.isIntersecting)) { vigia.disconnect(); arrancar(); }
  }, { rootMargin: "300px" });
  vigia.observe(contenedor);
} else {
  arrancar();
}

async function iniciar(lecturaCache = Promise.resolve()) {
  const prueba = document.createElement("canvas");
  if (!(prueba.getContext("webgl2") || prueba.getContext("webgl"))) {
    respaldo("Tu navegador no muestra gráficos 3D. El plan de mantenimiento sigue disponible abajo.");
    return;
  }

  // ---------- Escena ----------
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  // Hasta 1,75× en pantallas de alta densidad: casi igual de nítido y bastante menos trabajo para la tarjeta gráfica.
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, CALIDAD.pixeles));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  // La moto y la luz no se mueven: la sombra se recalcula solo cuando cambia algo del modelo.
  renderer.shadowMap.autoUpdate = false;
  renderer.shadowMap.needsUpdate = true;
  // Se dibuja solo cuando algo cambia (cámara, colores, selección), no 60 veces por segundo sin motivo.
  let necesitaCuadro = true;
  function pedirCuadro() { necesitaCuadro = true; }
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = "vitrina" in contenedor.dataset ? 1.45 : 1.05;
  contenedor.prepend(renderer.domElement);

  const escena = new THREE.Scene();
  const camara = new THREE.PerspectiveCamera(34, 1, 0.05, 50);
  const vitrina = "vitrina" in contenedor.dataset;
  const POS_INICIAL = vitrina ? V(2.05, 1.0, 2.4) : V(2.3, 1.25, 2.7);
  camara.position.copy(POS_INICIAL);

  // Reflejos de estudio: hacen que la pintura, el cromo y el aluminio se vean como materiales reales.
  const pmrem = new THREE.PMREMGenerator(renderer);
  escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  marcar("reflejos");
  pmrem.dispose(); // (el mapa de reflejos ya quedó hecho: el generador no se vuelve a usar)
  const hemi = new THREE.HemisphereLight(0xf4ead2, 0x1b2a28, 0.45);
  escena.add(hemi);
  const sol = new THREE.DirectionalLight(0xfff6ea, 2.4);
  sol.position.set(2.5, 4, 3);
  sol.castShadow = true;
  sol.shadow.mapSize.set(CALIDAD.sombra, CALIDAD.sombra); // con el difuminado suave, 1024 se ve igual que 2048 y pesa la cuarta parte
  sol.shadow.radius = 5;
  sol.shadow.bias = -0.0004;
  Object.assign(sol.shadow.camera, { left: -2, right: 2, top: 2, bottom: -2 });
  escena.add(sol);
  const contraluz = new THREE.DirectionalLight(0xffe2b0, 0.55);
  contraluz.position.set(-3, 2, -2);
  escena.add(contraluz);
  if ("vitrina" in contenedor.dataset) {
    // En la portada el fondo es oscuro: una luz de contorno cálida separa la moto del fondo.
    const contorno = new THREE.DirectionalLight(0xffc27a, 1.6);
    contorno.position.set(-2.5, 2.2, -1.5);
    escena.add(contorno);
  }

  const suelo = new THREE.Mesh(new THREE.CircleGeometry(1.7, 48), new THREE.ShadowMaterial({ opacity: 0.32 }));
  suelo.rotation.x = -Math.PI / 2;
  suelo.receiveShadow = true;
  escena.add(suelo);
  const anillo = new THREE.Mesh(
    new THREE.RingGeometry(1.55, 1.58, 64),
    new THREE.MeshBasicMaterial({ color: 0xede3cc, transparent: true, opacity: 0.12 }),
  );
  anillo.rotation.x = -Math.PI / 2;
  anillo.position.y = 0.001;
  if (!vitrina) escena.add(anillo);

  marcar("escena");
  await lecturaCache;
  const t0Armado = performance.now();
  pedazos.desde = performance.now();
  const moto = await construirMoto(datos.specs, datos.color, datos.linea || "");
  pedazos.max = Math.max(pedazos.max, performance.now() - pedazos.desde);
  const msArmado = Math.round(performance.now() - t0Armado);
  marcar("armada");
  // Guarda en el navegador los paneles nuevos (cuando el navegador esté libre, sin frenar el primer cuadro)
  // (con plazo de 2 s: en una pestaña de fondo el navegador casi nunca queda "libre" y no se guardaba)
  if (window.requestIdleCallback) requestIdleCallback(() => guardarCache(), { timeout: 2000 }); else setTimeout(guardarCache, 300);
  escena.add(moto.raiz);
  // Sombra de contacto: un óvalo oscuro y difuso justo debajo de la moto. "Asienta" las llantas en el piso
  // (la sombra del sol sola la hacía ver un poco flotando). Va pegada a la moto para seguirla en las animaciones.
  {
    const c = document.createElement("canvas");
    c.width = c.height = 128;
    const ctx = c.getContext("2d");
    const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    grad.addColorStop(0, "rgba(0,0,0,0.55)");
    grad.addColorStop(0.55, "rgba(0,0,0,0.25)");
    grad.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 128, 128);
    const caja = new THREE.Box3().setFromObject(moto.raiz);
    const contacto = new THREE.Mesh(new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false }));
    contacto.rotation.x = -Math.PI / 2;
    contacto.scale.set((caja.max.x - caja.min.x) * 1.05, (caja.max.z - caja.min.z) * 1.6, 1);
    contacto.position.set((caja.min.x + caja.max.x) / 2 - moto.raiz.position.x, 0.003, 0);
    contacto.userData.calca = true; // los modos Estado y Rayos X no la tocan
    contacto.raycast = () => {};    // ni la toman al tocar la moto
    moto.raiz.add(contacto);
  }
  // Sin placa registrada, la placa lleva la marca: TALLERYA.
  ponerPlaca(moto.placa, datos.placa || "TALLERYA");

  const controles = new OrbitControls(camara, renderer.domElement);
  controles.target.set(0, 0.5, 0);
  controles.enableDamping = true;
  controles.minDistance = 1.3;
  controles.maxDistance = 6;
  controles.maxPolarAngle = Math.PI * 0.49;
  controles.enablePan = false;
  const reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  controles.autoRotate = !reducido;
  controles.autoRotateSpeed = 0.8;
  controles.addEventListener("start", () => { controles.autoRotate = false; });

  // ---------- Animación de la portada (carrusel del motero) ----------
  // Entra rodando y frena (la suspensión delantera se hunde), destella el faro, una onda recorre el piso y el motor
  // "acelera"; luego gira. Al cambiar de moto, la portada pide "salir": arranca con un caballito y se va.
  const anim = { fase: null, t0: 0, alTerminar: null };
  const baseX = moto.raiz.position.x;
  const luces = [moto.M.luz, moto.M.stop];
  const onda = new THREE.Mesh(new THREE.RingGeometry(0.9, 1, 72),
    new THREE.MeshBasicMaterial({ color: 0xf26522, transparent: true, opacity: 0, depthWrite: false }));
  onda.rotation.x = -Math.PI / 2;
  onda.position.y = 0.002;
  if (vitrina) escena.add(onda);
  const suave = (p) => p * p * (3 - 2 * p);
  function girarRuedas(avance) {
    for (const r of moto.ruedas) r.pivote.rotation.z -= avance / r.R;
  }
  const pataAbajo = new THREE.Quaternion();
  function moverPata(abajo) {      // 0 = recogida, 1 = puesta
    if (!moto.pata) return;
    moto.pata.quaternion.slerpQuaternions(moto.pata.userData.recogida, pataAbajo, Math.min(1, Math.max(0, abajo)));
  }
  function animar(fase, alTerminar = null) {
    if (!vitrina || reducido) { alTerminar?.(); return; }
    anim.fase = fase;
    anim.t0 = performance.now();
    anim.alTerminar = alTerminar;
    controles.autoRotate = false;
  }
  let xAnterior = baseX;
  function pasoAnimacion() {
    if (!anim.fase) return false;
    const t = (performance.now() - anim.t0) / 1000;
    const raiz = moto.raiz;
    let x = baseX, giroZ = 0, y = 0, terminado = false;
    if (anim.fase === "entrar") {
      const dur = 2.1;
      const p = Math.min(1, t / dur);
      x = baseX - 3.4 * Math.pow(1 - p, 3);                       // llega rápido y frena suave
      if (p > 0.55) giroZ = -0.045 * Math.sin(Math.PI * (p - 0.55) / 0.45);   // se hunde adelante al frenar
      // Al llegar: faro que destella, onda en el piso y el motor acelerando (vibración leve)
      const tras = t - dur;
      const brillo = tras > 0 ? Math.max(0, 1 - tras / 0.9) : 0;
      luces[0].emissiveIntensity = 1.1 + 2.6 * brillo;
      luces[1].emissiveIntensity = 0.7 + 1.5 * brillo;
      onda.material.opacity = tras > 0 && tras < 1.3 ? 0.55 * (1 - tras / 1.3) : 0;
      const escala = tras > 0 ? 0.6 + tras * 1.6 : 0.6;
      onda.scale.set(escala, escala, 1);
      if (tras > 0.1 && tras < 0.9) y = 0.0025 * Math.sin(tras * 90) * (1 - tras / 0.9);
      moverPata(suave(Math.min(1, Math.max(0, (tras - 0.15) / 0.45))));   // ya detenida, baja el gato
      terminado = tras > 1.4;
    } else if (anim.fase === "salir") {
      // Primero recoge el gato (0,35 s) y luego arranca
      const recoger = 0.35, dur = 1.3;
      moverPata(1 - suave(Math.min(1, t / recoger)));
      const p = Math.max(0, Math.min(1, (t - recoger) / dur));
      x = baseX + 4.2 * p * p * p;                                  // acelera
      giroZ = 0.09 * Math.sin(Math.PI * Math.min(1, p * 1.6));     // caballito al arrancar
      luces[1].emissiveIntensity = 0.7;
      terminado = p >= 1;
    }
    girarRuedas(x - xAnterior);
    xAnterior = x;
    raiz.position.set(x, y, 0);
    // El giro es sobre el centro de la moto: se sube lo que baja la rueda de apoyo (trasera en el caballito,
    // delantera en la frenada) para que nunca se hunda en el piso.
    raiz.rotation.z = giroZ;
    raiz.position.y = y + Math.abs(giroZ) * 0.66;
    renderer.shadowMap.needsUpdate = true;
    if (terminado) {
      const fin = anim.alTerminar;
      if (anim.fase === "entrar") controles.autoRotate = true;
      anim.fase = null;
      fin?.();
    }
    return true;
  }
  if (vitrina) {
    if (!reducido) moverPata(0);
    animar("entrar");
    // Mensajes de la portada: "salir" (y avisa cuando ya se fue) y "entrar" (cuando vuelve a mostrarse esta moto)
    window.addEventListener("message", (e) => {
      if (e.origin !== window.location.origin) return;
      if (e.data === "salir") animar("salir", () => window.parent.postMessage("moto-fuera", window.location.origin));
      if (e.data === "entrar") { xAnterior = baseX - 3.4; moverPata(0); animar("entrar"); }
    });
  }

  // ---------- Moto viva: encenderla y verla de noche ----------
  // Encender: faro y stop a todo, tablero iluminado, saludo de direccionales y el motor temblando en mínimo.
  // Noche: la escena se oscurece, el faro proyecta su haz en el piso y el stop tiñe de rojo atrás.
  const vivo = { encendida: false, noche: false, t0: 0 };
  const exposicionBase = renderer.toneMappingExposure;
  const direccionales = [];
  moto.raiz.traverse((o) => {
    if (o.isMesh && o.material.emissive && o.material.color?.getHex() === 0xffb347 && !direccionales.includes(o.material)) direccionales.push(o.material);
  });
  const brilloDireccional = direccionales.map((m) => m.emissiveIntensity);
  function centroDe(material) {
    // La malla más grande con ese material (p. ej. el faro principal entre todas las luces)
    let mejor = null, tam = -1;
    const caja = new THREE.Box3(), v = new THREE.Vector3();
    moto.raiz.traverse((o) => {
      if (!o.isMesh || o.material !== material) return;
      caja.setFromObject(o).getSize(v);
      if (v.lengthSq() > tam) { tam = v.lengthSq(); mejor = caja.getCenter(new THREE.Vector3()); }
    });
    return mejor && moto.raiz.worldToLocal(mejor);
  }
  const posFaro = centroDe(moto.M.luz), posStop = centroDe(moto.M.stop);
  const haz = new THREE.SpotLight(0xfff1d0, 0, 7, 0.42, 0.65, 1.4);
  const rojoTras = new THREE.PointLight(0xff2a1f, 0, 1.3, 1.6);
  if (posFaro) {
    haz.position.copy(posFaro);
    haz.target.position.copy(posFaro).add(V(2.6, -posFaro.y, 0));
    moto.raiz.add(haz, haz.target);
  }
  if (posStop) { rojoTras.position.copy(posStop).add(V(-0.08, 0, 0)); moto.raiz.add(rojoTras); }
  // De noche hace falta un piso que reciba luz (el de día solo dibuja la sombra): ahí se ve el haz del faro
  const pisoNoche = new THREE.Mesh(new THREE.CircleGeometry(1.7, 64),
    new THREE.MeshStandardMaterial({ color: 0x1a2124, roughness: 0.85, metalness: 0 }));
  pisoNoche.rotation.x = -Math.PI / 2;
  pisoNoche.position.y = -0.0005;
  pisoNoche.receiveShadow = true;
  pisoNoche.visible = false;
  escena.add(pisoNoche);
  function aplicarVivo() {
    const { encendida: e, noche: n } = vivo;
    renderer.toneMappingExposure = exposicionBase * (n ? 0.42 : 1);
    hemi.intensity = n ? 0.1 : 0.45;
    sol.intensity = n ? 0.2 : 2.4;
    contraluz.intensity = n ? 0.12 : 0.55;
    moto.M.luz.emissiveIntensity = e ? (n ? 7 : 2.6) : (n ? 0.5 : 1.1);
    moto.M.stop.emissiveIntensity = e ? (n ? 4.5 : 1.5) : (n ? 0.35 : 0.7);
    moto.M.pantalla.emissiveIntensity = e ? (n ? 2 : 1) : (n ? 0.12 : 0.35);
    haz.intensity = e ? (n ? 14 : 2.5) : 0;
    rojoTras.intensity = e && n ? 1.6 : 0;
    direccionales.forEach((m, i) => { m.emissiveIntensity = brilloDireccional[i] * (n ? 0.5 : 1); });
    pisoNoche.visible = n;
    contenedor.classList.toggle("noche", n);
    renderer.shadowMap.needsUpdate = true;
    pedirCuadro();
  }
  function pasoVivo(t) {
    if (!vivo.encendida || modo !== "moto" || anim.fase) return false;
    const desde = (performance.now() - vivo.t0) / 1000;
    // Saludo: las direccionales parpadean tres veces al encender
    const parpadeo = desde < 2.1 && Math.floor(desde / 0.35) % 2 === 0;
    direccionales.forEach((m, i) => { m.emissiveIntensity = parpadeo ? 3.2 : brilloDireccional[i] * (vivo.noche ? 0.5 : 1); });
    if (reducido) return desde < 2.2;
    // Motor en mínimo: un temblor leve (más fuerte en el arranque)
    const arranque = desde < 0.6 ? 2.4 : 1;
    moto.raiz.position.y = 0.0007 * arranque * Math.sin(t * 92) + 0.0004 * Math.sin(t * 37);
    return true;
  }
  const panelVivo = document.getElementById("visor-vivo");
  if (panelVivo && !vitrina) {
    const bEncender = document.getElementById("vivo-encender"), bNoche = document.getElementById("vivo-noche");
    bEncender.addEventListener("click", () => {
      vivo.encendida = !vivo.encendida;
      vivo.t0 = performance.now();
      bEncender.setAttribute("aria-pressed", String(vivo.encendida));
      bEncender.querySelector("span").textContent = vivo.encendida ? "Apagar" : "Encender";
      if (!vivo.encendida) moto.raiz.position.y = 0;
      aplicarVivo();
    });
    bNoche.addEventListener("click", () => {
      vivo.noche = !vivo.noche;
      bNoche.setAttribute("aria-pressed", String(vivo.noche));
      aplicarVivo();
    });
  }

  // ---------- Estado de las piezas ----------
  // En la portada del inicio (data-modo="moto") se muestra la moto con su pintura, no el estado de las piezas.
  let modo = contenedor.dataset.modo || "estado";
  let seleccionada = null;
  const ghost = new THREE.MeshStandardMaterial({
    color: 0xa7b0b3, transparent: true, opacity: 0.13, depthWrite: false, roughness: 1,
  });
  const matEstado = {};
  for (const [estado, color] of Object.entries(ESTADO_COLOR)) {
    matEstado[estado] = new THREE.MeshStandardMaterial({
      color, emissive: color, emissiveIntensity: 0.25, roughness: 0.55, metalness: 0.1,
    });
  }

  function estadoDe(pieza) {
    return datos.piezas[pieza]?.estado || null;
  }

  const matBorde = new THREE.LineBasicMaterial({ color: 0x9fd3e6, transparent: true, opacity: 0.4 });
  const invisible = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.02, depthWrite: false });

  function aplicarModo() {
    contenedor.classList.toggle("rayos", modo === "rayos");
    calcas.forEach((c) => { c.visible = modo === "moto"; });
    const mallas = [];
    moto.raiz.traverse((obj) => { if (obj.isMesh && !obj.userData.calca) mallas.push(obj); });
    for (const obj of mallas) {
      obj.userData.original ??= obj.material;
      const pieza = piezaDe(obj);
      const estado = pieza && estadoDe(pieza);
      const interno = Boolean(obj.userData.interno);
      obj.visible = (!interno || modo === "rayos") && !obj.userData.oculto;
      if (obj.userData.borde) obj.userData.borde.visible = modo === "rayos" && !estado;

      if (modo === "moto") {
        obj.material = obj.userData.original;
      } else if (modo === "estado") {
        // Un material propio por malla (para el pulso), creado una sola vez.
        obj.material = estado ? (obj.userData.matEstado ??= matEstado[estado].clone()) : ghost;
      } else if (estado) {
        // Rayos X: piezas internas sólidas; sus carcasas, translúcidas para ver adentro.
        if (!obj.userData.matRayos) {
          const m = matEstado[estado].clone();
          if (!interno) Object.assign(m, { transparent: true, opacity: 0.28, depthWrite: false });
          obj.userData.matRayos = m;
        }
        obj.material = obj.userData.matRayos;
      } else {
        if (!obj.userData.borde && !obj.isInstancedMesh) {
          const borde = new THREE.LineSegments(new THREE.EdgesGeometry(obj.geometry, 28), matBorde);
          obj.add(borde);
          obj.userData.borde = borde;
        }
        if (obj.userData.borde) obj.userData.borde.visible = true;
        obj.material = invisible;
      }
      obj.castShadow = modo === "moto" || (Boolean(estado) && obj.visible);
    }
    resaltar(seleccionada);
    renderer.shadowMap.needsUpdate = true;
    pedirCuadro();
  }

  function piezaDe(obj) {
    while (obj && obj !== moto.raiz) {
      if (obj.userData.pieza) return obj.userData.pieza;
      obj = obj.parent;
    }
    return null;
  }

  // Mallas que laten (la pieza seleccionada); así el ciclo de dibujo no recorre toda la moto.
  let pulsando = [];
  function resaltar(pieza) {
    pulsando = [];
    moto.raiz.traverse((obj) => {
      if (!obj.isMesh || obj.userData.calca || !obj.material.emissive) return;
      const activa = Boolean(pieza) && piezaDe(obj) === pieza;
      if (activa) pulsando.push(obj);
      else if (modo === "estado" && piezaDe(obj) && estadoDe(piezaDe(obj))) {
        obj.material.emissiveIntensity = 0.25;
      }
    });
    pedirCuadro();
  }

  function seleccionar(pieza) {
    // Si piden una pieza desde el plan o el despiece estando en Moto, se pasa a Estado para mostrarla.
    if (pieza && modo === "moto") document.querySelector('#visor .visor-modo [data-modo="estado"]')?.click();
    seleccionada = pieza;
    resaltar(pieza);
    document.querySelectorAll(".tarea").forEach((el) => {
      el.classList.toggle("resaltada", Boolean(pieza) && el.dataset.pieza === pieza);
    });
    if (!pieza) { ficha.hidden = true; return; }
    const info = datos.piezas[pieza];
    if (!info) { ficha.hidden = true; return; }
    ficha.hidden = false;
    ficha.innerHTML = "";
    const titulo = document.createElement("div");
    titulo.className = "flex items-center justify-between gap-2";
    titulo.innerHTML = `<p class="titulo text-lg"></p><span class="estado estado-${info.estado}">${ETIQUETA[info.estado]}</span>`;
    titulo.querySelector("p").textContent = info.nombre;
    ficha.appendChild(titulo);
    const lista = document.createElement("ul");
    lista.className = "mt-2 space-y-2 text-sm";
    for (const t of info.tareas) {
      const li = document.createElement("li");
      li.innerHTML = `<p class="font-semibold"></p><p class="text-xs text-suave"></p>`;
      li.children[0].textContent = t.nombre;
      li.children[1].textContent = t.detalle;
      lista.appendChild(li);
    }
    ficha.appendChild(lista);
    // Acciones: ir al plan de mantenimiento de la pieza, o ver su sistema completo en el despiece.
    const acciones = document.createElement("div");
    acciones.className = "ficha-acciones";
    const ir = document.createElement("button");
    ir.type = "button";
    ir.className = "ficha-plan";
    ir.textContent = "Plan mantenimiento";
    ir.addEventListener("click", () => {
      if (window.TallerYaPlan) { window.TallerYaPlan.mostrar(pieza); return; }
      window.TallerYaSecciones?.abrir("plan");
      document.querySelector(`.tarea[data-pieza="${pieza}"]`)?.scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "center" });
    });
    acciones.appendChild(ir);
    if (window.TallerYaDespiece?.tiene(pieza)) {
      const ver = document.createElement("button");
      ver.type = "button";
      // Secundario: botón corto "Piezas" que abre el sistema en el despiece.
      ver.className = "ficha-sistema";
      ver.textContent = "Piezas";
      ver.title = "Ver las piezas de este sistema en el despiece";
      ver.addEventListener("click", () => window.TallerYaDespiece.mostrar(pieza));
      acciones.appendChild(ver);
    }
    ficha.appendChild(acciones);
    // Resolverla: el taller recomendado, su cupón, pedir cita por WhatsApp y más talleres (el mismo contenido de
    // siempre, acomodado para que la ficha no crezca tanto)
    const a = info.acciones;
    if (a) {
      const resolver = document.createElement("div");
      resolver.className = "ficha-resolver";
      const enlace = (clase, url, externo) => {
        const e = document.createElement("a");
        e.className = clase;
        e.href = url;
        if (externo) { e.target = "_blank"; e.rel = "noopener"; }
        return e;
      };
      if (a.taller) {
        const fila = document.createElement("p");
        fila.className = "ficha-taller";
        fila.textContent = info.estado === "ok" ? "Cuando toque: " : "Te recomendamos: ";
        const nombre = enlace("servicio-taller", a.taller.url); // la misma pastilla del plan y la agenda
        nombre.textContent = a.taller.nombre;
        fila.appendChild(nombre);
        resolver.appendChild(fila);
        if (a.cupon) {
          // (el cupón es del taller, no necesariamente de este servicio: se presenta así)
          const cupon = enlace("ficha-cupon", a.cupon.url);
          cupon.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true"><path d="M3 8a2 2 0 0 0 0 4 2 2 0 0 0 0 4v2h18v-2a2 2 0 0 1 0-4 2 2 0 0 1 0-4V6H3z"/><path d="M14 6v12" stroke-dasharray="2 2"/></svg><span><b>Cupón del taller:</b> </span>';
          cupon.querySelector("span").append(a.cupon.titulo);
          resolver.appendChild(cupon);
        }
      }
      // Última fila: pedir cita (si ya toca o pronto) a la izquierda y más talleres a la derecha
      const pie = document.createElement("div");
      pie.className = "ficha-resolver-pie";
      if (a.taller?.whatsapp && info.estado !== "ok") {
        const wa = enlace("ficha-whatsapp", a.taller.whatsapp, true);
        wa.innerHTML = '<svg viewBox="0 0 24 24" width="13" height="13" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2z"/></svg>Pedir cita por WhatsApp';
        pie.appendChild(wa);
      }
      const mas = enlace("ficha-talleres", a.talleres);
      mas.textContent = a.taller ? "Ver más talleres" : "Talleres que lo hacen";
      pie.appendChild(mas);
      resolver.appendChild(pie);
      ficha.appendChild(resolver);
    }
  }

  // ---------- Personalización: colores y calcas ----------
  const calcas = [];
  const rayo = new THREE.Raycaster();

  function zonaMalla(nombre) {
    let encontrada = null;
    moto.raiz.traverse((o) => { if (!encontrada && o.isMesh && o.userData.zonas && o.userData.zonas.includes(nombre)) encontrada = o; });
    return encontrada;
  }

  // Mallas pintadas de la carrocería: ahí se pueden pegar calcas.
  let carroceria = null;
  function mallasCarroceria() {
    if (!carroceria) {
      carroceria = [];
      moto.raiz.traverse((o) => {
        if (o.isMesh && (o.userData.zonas || (o.userData.original ?? o.material) === moto.M.pintura)) carroceria.push(o);
      });
    }
    return carroceria;
  }

  // Ancho base de cada diseño en metros (tamaño 1).
  const ANCHO_BASE = { imagen: 0.2, numero: 0.16, tallerya: 0.3, texto: 0.32, franjas: 0.38, cuadros: 0.34, llamas: 0.36, rayo: 0.32 };
  const PROFUNDIDAD = 0.12;

  // Busca la carrocería justo debajo de un punto (en coordenadas del mundo) siguiendo su normal.
  function superficieEn(punto, normal) {
    rayo.set(punto.clone().addScaledVector(normal, 0.06), normal.clone().negate());
    rayo.far = 0.2;
    const golpe = rayo.intersectObjects(mallasCarroceria(), false)[0];
    rayo.far = Infinity;
    if (!golpe) return null;
    const n = golpe.face.normal.clone().transformDirection(golpe.object.matrixWorld);
    if (n.dot(normal) < 0) n.negate();
    return { malla: golpe.object, punto: golpe.point, normal: n };
  }

  // Orientación de la calca: mirando hacia afuera de la superficie y girada sobre sí misma.
  function orientacion(punto, normal, giro) {
    const ayudante = new THREE.Object3D();
    ayudante.position.copy(punto);
    if (Math.abs(normal.y) > 0.95) ayudante.up.set(1, 0, 0);
    ayudante.lookAt(punto.clone().add(normal));
    ayudante.rotateZ(THREE.MathUtils.degToRad(giro || 0));
    return ayudante;
  }

  function medidas(c, aspecto) {
    let ancho = (ANCHO_BASE[c.diseno] || 0.3) * (c.tamano || 1);
    let alto = ancho / aspecto;
    if (alto > 0.26) { ancho *= 0.26 / alto; alto = 0.26; }
    return { ancho, alto };
  }

  // Lados donde va la calca: el punto elegido y, si "ambos", su reflejo en el otro costado.
  function lados(c) {
    const p = moto.raiz.localToWorld(V(...c.punto));
    const n = V(...c.normal).transformDirection(moto.raiz.matrixWorld);
    const lista = [[p, n]];
    if (c.ambos) {
      const pl = V(c.punto[0], c.punto[1], -c.punto[2]);
      const nl = V(c.normal[0], c.normal[1], -c.normal[2]);
      if (Math.abs(c.punto[2]) > 0.02) lista.push([moto.raiz.localToWorld(pl), nl.transformDirection(moto.raiz.matrixWorld)]);
    }
    return lista;
  }

  let _detalles = null;
  function detallesBajoCalca() {
    if (!_detalles) {
      _detalles = [];
      moto.raiz.traverse((o) => { if (o.isMesh && o.userData.bajoCalca) _detalles.push(o); });
    }
    return _detalles;
  }

  function geometriasCalca(c, aspecto) {
    const { ancho, alto } = medidas(c, aspecto);
    const geos = [];
    for (const [p, n] of lados(c)) {
      const s = superficieEn(p, n);
      if (!s) continue;
      const giro = c.giro || 0;
      const rot = orientacion(s.punto, s.normal, giro).rotation;
      geos.push(new DecalGeometry(s.malla, s.punto, rot, V(ancho, alto, PROFUNDIDAD)));
      // Franjas y detalles pegados sobre la carrocería: la calca también pasa por encima de ellos (como un sticker real)
      for (const detalle of detallesBajoCalca()) {
        const g = new DecalGeometry(detalle, s.punto, rot, V(ancho, alto, PROFUNDIDAD));
        if (g.attributes.position.count) geos.push(g); else g.dispose();
      }
    }
    return geos;
  }

  // Calcas guardadas con el formato anterior (zona fija): se convierten a un punto sobre la carrocería.
  function migrarCalca(c) {
    if (c.punto) return c;
    const m = zonaMalla(c.zona);
    if (!m) return null;
    const caja = new THREE.Box3().setFromObject(m);
    const tam = caja.getSize(new THREE.Vector3());
    const centro = caja.getCenter(new THREE.Vector3());
    const escala = c.tamano || 1;
    const pos = c.posicion || 0;
    let disparos;
    let ancho;
    if (c.zona === "frontal") {
      ancho = tam.z * 0.62 * escala;
      disparos = [[V(caja.max.x + 0.4, centro.y + pos * tam.y * 0.3, 0), V(-1, 0, 0)]];
    } else if (c.zona === "cola") {
      ancho = tam.z * 0.6 * escala;
      disparos = [[V(caja.min.x - 0.4, centro.y + 0.02 + pos * tam.y * 0.2, 0), V(1, 0, 0)]];
    } else {
      ancho = tam.x * (c.zona === "tanque" ? 0.62 : 0.5) * escala;
      const x = centro.x + pos * tam.x * 0.3;
      const y = centro.y + (c.zona === "tanque" ? 0 : tam.y * 0.08);
      disparos = [[V(x, y, caja.max.z + 0.4), V(0, 0, -1)], [V(x, y, caja.min.z - 0.4), V(0, 0, 1)]];
    }
    for (const [origen, direccion] of disparos) {
      rayo.set(origen, direccion);
      const golpe = rayo.intersectObject(m, false)[0];
      if (!golpe) continue;
      const normal = golpe.face.normal.clone().transformDirection(m.matrixWorld);
      if (normal.dot(direccion) > 0) normal.negate();
      const local = moto.raiz.worldToLocal(golpe.point.clone());
      const normalLocal = normal.transformDirection(moto.raiz.matrixWorld.clone().invert());
      const r = (x) => Math.round(x * 10000) / 10000;
      const { zona, posicion, ...resto } = c;
      return {
        ...resto,
        punto: [r(local.x), r(local.y), r(local.z)],
        normal: [r(normalLocal.x), r(normalLocal.y), r(normalLocal.z)],
        tamano: Math.min(1.6, Math.max(0.4, Math.round((ancho / (ANCHO_BASE[c.diseno] || 0.3)) * 20) / 20)),
        giro: 0,
        ambos: zona === "lateral" || zona === "tanque",
      };
    }
    return null;
  }

  // Cada calca guarda lo que ya construyó: mover un control solo rehace lo que cambió
  // (geometría o textura), en vez de reconstruir todas las calcas desde cero.
  const estadoCalcas = [];

  function quitarMallas(e) {
    for (const malla of e.mallas) { malla.removeFromParent(); malla.geometry.dispose(); }
    e.mallas = [];
  }

  function actualizarCalca(e, c, indice) {
    // (con imagen propia la clave lleva el tamaño y el final del archivo: distinguen una imagen de otra)
    const claveTextura = `${c.diseno}|${c.color}|${c.texto || ""}|${c.imagen ? c.imagen.length + c.imagen.slice(-32) : ""}`;
    const claveForma = `${c.diseno}|${c.punto}|${c.normal}|${c.tamano}|${c.giro}|${c.ambos}|${c.texto || ""}`;
    if (e.claveTextura !== claveTextura) {
      const { textura, aspecto } = texturaCalca(c.diseno, c.color, c.texto, c.imagen);
      e.material.map?.dispose();
      e.material.map = textura;
      e.material.needsUpdate = true;
      e.aspecto = aspecto;
      e.claveTextura = claveTextura;
    }
    if (e.claveForma !== claveForma) {
      quitarMallas(e);
      for (const geo of geometriasCalca(c, e.aspecto)) {
        // La calca va pegada a la moto (no a la escena): así la acompaña cuando la moto entra, frena o sale animada.
        moto.raiz.updateMatrixWorld(true);
        geo.applyMatrix4(moto.raiz.matrixWorld.clone().invert());
        const malla = new THREE.Mesh(geo, e.material);
        malla.userData.calca = true;
        malla.renderOrder = 2;
        malla.visible = modo === "moto";
        moto.raiz.add(malla);
        e.mallas.push(malla);
      }
      e.claveForma = claveForma;
    }
    e.mallas.forEach((m) => { m.userData.indice = indice; });
  }

  // Marco punteado alrededor de la calca que se está editando.
  const marco = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(1, 1)),
    new THREE.LineBasicMaterial({ color: 0xf2611d, depthTest: false, transparent: true }),
  );
  marco.renderOrder = 5;
  marco.visible = false;
  escena.add(marco);
  let calcaResaltada = -1;
  let ultimaCfg = null;

  function ponerMarco() {
    const c = ultimaCfg?.calcas?.[calcaResaltada];
    const e = estadoCalcas[calcaResaltada];
    marco.visible = Boolean(c && e && modo === "moto" && !document.getElementById("personalizar")?.hidden);
    if (!marco.visible) { pedirCuadro(); return; }
    const [p, n] = lados(c)[0];
    const s = superficieEn(p, n) || { punto: p, normal: n };
    const { ancho, alto } = medidas(c, e.aspecto);
    const o = orientacion(s.punto.clone().addScaledVector(s.normal, 0.004), s.normal, c.giro);
    marco.position.copy(o.position);
    marco.quaternion.copy(o.quaternion);
    marco.scale.set(ancho * 1.08, alto * 1.08, 1);
    pedirCuadro();
  }

  // Acabados de pintura: brillo, metal y laca de cada uno (se aplican a los dos tonos de la carrocería)
  const ACABADOS = {
    // brillante: laca de fábrica, reflejo nítido
    brillante: { metalness: 0.45, roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.04, iridescence: 0, sheen: 0 },
    // mate: sin laca, luz difusa
    mate: { metalness: 0.05, roughness: 0.92, clearcoat: 0, clearcoatRoughness: 1, iridescence: 0, sheen: 0 },
    // satinado: brillo suave y abierto
    satinado: { metalness: 0.25, roughness: 0.48, clearcoat: 0.6, clearcoatRoughness: 0.42, iridescence: 0, sheen: 0 },
    // metalizado: metal debajo de la laca → resplandor amplio y plateado además del reflejo nítido
    metalizado: { metalness: 0.75, roughness: 0.36, clearcoat: 1, clearcoatRoughness: 0.02, iridescence: 0, sheen: 0.7,
      sheenColor: new THREE.Color(0xb8bec4), sheenRoughness: 0.55 },
    // perlado: tornasol (cambia de tono según el ángulo) y borde claro nacarado
    perlado: { metalness: 0.3, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.03, iridescence: 1, iridescenceIOR: 1.6,
      iridescenceThicknessRange: [200, 900], sheen: 1, sheenColor: new THREE.Color(0xfff4ea), sheenRoughness: 0.3 },
  };

  // Muestras del panel: una esfera pintada con el material real de cada acabado, con los mismos reflejos de
  // estudio que la moto (con degradados CSS todas se veían iguales). Un renderizador chiquito aparte, creado
  // la primera vez que se pide una muestra; cada combinación acabado+color se dibuja una sola vez.
  let estudio = null;
  const muestrasAcabado = new Map();
  function vistaAcabado(acabado, color) {
    const clave = `${acabado}|${color}`;
    if (muestrasAcabado.has(clave)) return muestrasAcabado.get(clave);
    if (!estudio) {
      const r = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
      r.setSize(112, 112);
      r.outputColorSpace = THREE.SRGBColorSpace;
      r.toneMapping = THREE.ACESFilmicToneMapping;
      r.toneMappingExposure = 1.1;
      const e = new THREE.Scene();
      const generador = new THREE.PMREMGenerator(r);
      e.environment = generador.fromScene(new RoomEnvironment(), 0.04).texture;
      generador.dispose();
      const luz = new THREE.DirectionalLight(0xfff6ea, 2.2);
      luz.position.set(-2, 3, 3);
      e.add(luz, new THREE.HemisphereLight(0xf4ead2, 0x1b2a28, 0.4));
      const cam = new THREE.PerspectiveCamera(28, 1, 0.1, 10);
      cam.position.set(0, 0, 4.4);
      const mat = moto.M.pintura.clone();
      e.add(new THREE.Mesh(new THREE.SphereGeometry(1, 64, 40), mat));
      estudio = { r, e, cam, mat };
    }
    Object.assign(estudio.mat, ACABADOS[acabado] || ACABADOS.brillante);
    estudio.mat.color.set(color);
    estudio.mat.needsUpdate = true;
    estudio.r.render(estudio.e, estudio.cam);
    const url = estudio.r.domElement.toDataURL("image/png");
    if (muestrasAcabado.size > 80) muestrasAcabado.delete(muestrasAcabado.keys().next().value);
    muestrasAcabado.set(clave, url);
    return url;
  }
  const COLOR_CHASIS = "#23282b", COLOR_ASIENTO = "#161819";
  function aplicarEstilo(estilo = {}) {
    const acabado = ACABADOS[estilo.acabado] || ACABADOS.brillante;
    for (const m of [moto.M.pintura, moto.M.pintura2]) Object.assign(m, acabado);
    moto.M.pintura2.color.set(estilo.color2 || moto.M.pintura.color);
    moto.M.chasis.color.set(estilo.chasis || COLOR_CHASIS);
    moto.M.asiento.color.set(estilo.asiento || COLOR_ASIENTO);
    const rin = ["radios", "aleacion", "estrella"].includes(estilo.rin) ? estilo.rin : moto.rinFabrica;
    for (const g of [moto.piezas.llanta_del, moto.piezas.llanta_tras]) {
      g.userData.armarRin?.(rin);
      g.traverse((o) => { if (o.userData.rin) o.visible = o.userData.rin === rin; });
      g.traverse((o) => {
        if (!o.userData.aro) return;
        const mat = rin === "radios" ? moto.M.metal : moto.M.rin;
        if (o.material === o.userData.original || !o.userData.original) o.material = mat;
        o.userData.original = mat;
      });
    }
    const puestos = new Set(estilo.accesorios || []);
    for (const [id, g] of Object.entries(moto.accesorios)) g.visible = puestos.has(id);
    const espejo = moto.espejos[estilo.espejos] ? estilo.espejos : "fabrica";
    for (const [nombre, g] of Object.entries(moto.espejos)) g.visible = nombre === espejo;
    if (moto.escapeFabrica) moto.escapeFabrica.visible = !puestos.has("escape");
    const led = moto.accesorios.led?.userData.led;
    if (led) {
      const c = new THREE.Color(estilo.led || "#22d3ee");
      led.material.color.copy(c);
      led.material.emissive.copy(c);
      led.luz.color.copy(c);
    }
    for (const v of moto.visoresFabrica) { v.userData.oculto = puestos.has("parabrisas"); v.visible = !v.userData.oculto; }
    renderer.shadowMap.needsUpdate = true;
  }

  function aplicarPersonalizacion(cfg) {
    moto.M.pintura.color.set(cfg.color);
    aplicarEstilo(cfg.estilo);
    moto.M.rin.color.set(cfg.color_secundario);
    if (moto.M.acento) moto.M.acento.color.set(cfg.color_secundario);
    moto.raiz.updateMatrixWorld(true);
    const lista = cfg.calcas || [];
    while (estadoCalcas.length > lista.length) {
      const e = estadoCalcas.pop();
      quitarMallas(e);
      e.material.map?.dispose();
      e.material.dispose();
    }
    lista.forEach((c, i) => {
      estadoCalcas[i] ??= {
        mallas: [], claveTextura: null, claveForma: null, aspecto: 1,
        material: new THREE.MeshPhysicalMaterial({
          transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -4,
          roughness: 0.3, metalness: 0.05, clearcoat: 1, clearcoatRoughness: 0.08,
        }),
      };
      actualizarCalca(estadoCalcas[i], c, i);
    });
    calcas.length = 0;
    estadoCalcas.forEach((e) => calcas.push(...e.mallas));
    ultimaCfg = cfg;
    ponerMarco();
    pedirCuadro();
  }

  // Las miniaturas se dibujan una vez por combinación y se reutilizan.
  const miniaturas = new Map();
  function miniatura(diseno, color, texto) {
    const clave = `${diseno}|${color}|${texto || ""}`;
    if (!miniaturas.has(clave)) {
      if (miniaturas.size > 60) miniaturas.delete(miniaturas.keys().next().value);
      const { textura, canvas } = texturaCalca(diseno, color, texto);
      textura.dispose();
      miniaturas.set(clave, canvas.toDataURL());
    }
    return miniaturas.get(clave);
  }

  // ---------- Calcas con el mouse: tocar para pegar, arrastrar para mover ----------
  let oyentes = {};
  let colocando = null; // diseño que se va a pegar con el próximo toque
  let arrastrando = -1;
  const rayoPuntero = new THREE.Raycaster();

  function rayoDesde(evento) {
    const r = renderer.domElement.getBoundingClientRect();
    camara.updateMatrixWorld();
    rayoPuntero.setFromCamera(new THREE.Vector2(
      ((evento.clientX - r.left) / r.width) * 2 - 1, -((evento.clientY - r.top) / r.height) * 2 + 1), camara);
    return rayoPuntero;
  }

  // Punto de la carrocería bajo el puntero (solo si no lo tapa otra pieza, como el asiento).
  function carroceriaBajo(evento) {
    const visibles = [];
    moto.raiz.traverse((o) => { if (o.isMesh && o.visible && !o.userData.calca) visibles.push(o); });
    // Las franjas pegadas sobre la carrocería no cuentan: se toca "a través" de ellas la pintura de abajo
    const golpe = rayoDesde(evento).intersectObjects(visibles, false).find((g) => !g.object.userData.bajoCalca);
    if (!golpe || !mallasCarroceria().includes(golpe.object)) return null;
    const n = golpe.face.normal.clone().transformDirection(golpe.object.matrixWorld);
    if (n.dot(rayoPuntero.ray.direction) > 0) n.negate();
    const local = moto.raiz.worldToLocal(golpe.point.clone());
    const nl = n.transformDirection(moto.raiz.matrixWorld.clone().invert());
    const r = (x) => Math.round(x * 10000) / 10000;
    return { punto: [r(local.x), r(local.y), r(local.z)], normal: [r(nl.x), r(nl.y), r(nl.z)] };
  }

  function calcaBajo(evento) {
    if (modo !== "moto" || !calcas.length) return -1;
    const golpe = rayoDesde(evento).intersectObjects(calcas, false)[0];
    return golpe ? golpe.object.userData.indice : -1;
  }

  function editando() { return modo === "moto" && !document.getElementById("personalizar")?.hidden; }

  // Va en fase de captura para adelantarse a los controles de giro de la cámara.
  contenedor.addEventListener("pointerdown", (e) => {
    if (e.target !== renderer.domElement || !editando() || colocando) return;
    const i = calcaBajo(e);
    if (i < 0) return;
    arrastrando = i;
    controles.enabled = false;
    try { renderer.domElement.setPointerCapture(e.pointerId); } catch { /* puntero ya liberado */ }
    renderer.domElement.style.cursor = "grabbing";
    oyentes.alElegir?.(i);
    oyentes.alEmpezarArrastre?.(i);
  }, true);

  renderer.domElement.addEventListener("pointermove", (e) => {
    if (arrastrando < 0) return;
    const sitio = carroceriaBajo(e);
    if (sitio) oyentes.alMover?.(arrastrando, sitio);
  });

  function soltar() {
    if (arrastrando < 0) return;
    arrastrando = -1;
    controles.enabled = true;
    renderer.domElement.style.cursor = "";
    oyentes.alSoltar?.();
  }
  renderer.domElement.addEventListener("pointerup", soltar);
  renderer.domElement.addEventListener("pointercancel", soltar);

  function intentarColocar(evento) {
    const sitio = carroceriaBajo(evento);
    if (!sitio) { oyentes.alFallar?.(); return; }
    const diseno = colocando;
    colocando = null;
    contenedor.classList.remove("colocando");
    oyentes.alColocar?.(diseno, sitio);
  }

  window.addEventListener("calca-imagen-lista", pedirCuadro);
  window.TallerYa3D = {
    aplicar: aplicarPersonalizacion,
    miniatura,
    vistaAcabado,
    escuchar(o) { oyentes = o; },
    colocar(diseno) {
      colocando = diseno || null;
      contenedor.classList.toggle("colocando", Boolean(colocando));
    },
    resaltar(i) { calcaResaltada = i; ponerMarco(); },
    actualizarMarco: ponerMarco,
    verPieza(pieza) {
      seleccionar(pieza);
      contenedor.scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "center" });
    },
    // Qué se puede elegir en esta moto: accesorios que le quedan y el rin que trae de fábrica
    opciones: () => ({ accesorios: Object.keys(moto.accesorios), rinFabrica: moto.rinFabrica, tipo: datos.specs.tipo }),
    verMoto() { document.querySelector('#visor .visor-modo [data-modo="moto"]')?.click(); },
  };
  const crudo = { color: datos.color, color_secundario: datos.color_secundario || "#1c2022", calcas: datos.calcas || [], estilo: datos.estilo || {} };
  moto.raiz.updateMatrixWorld(true);
  const inicial = { ...crudo, calcas: crudo.calcas.map(migrarCalca).filter(Boolean) };
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => {
    aplicarPersonalizacion(inicial);
    window.TallerYa3DInicial = inicial;
    document.dispatchEvent(new CustomEvent("moto3d-listo", { detail: inicial }));
  });

  // ---------- Interacción ----------
  const raycaster = new THREE.Raycaster();
  const puntero = new THREE.Vector2();
  let inicioToque = null;

  // Las piezas solo se pueden tocar en Estado y Rayos X; en Moto el modelo es solo para verla.
  function piezaBajo(evento) {
    if (modo === "moto") return null;
    const r = renderer.domElement.getBoundingClientRect();
    camara.updateMatrixWorld();
    puntero.set(((evento.clientX - r.left) / r.width) * 2 - 1, -((evento.clientY - r.top) / r.height) * 2 + 1);
    raycaster.setFromCamera(puntero, camara);
    for (const hit of raycaster.intersectObject(moto.raiz, true)) {
      const pieza = piezaDe(hit.object);
      if (pieza && datos.piezas[pieza]) return pieza;
    }
    return null;
  }

  renderer.domElement.addEventListener("pointerdown", (e) => { inicioToque = { x: e.clientX, y: e.clientY }; });
  renderer.domElement.addEventListener("pointerup", (e) => {
    if (!inicioToque) return;
    const movido = Math.hypot(e.clientX - inicioToque.x, e.clientY - inicioToque.y) > 6;
    inicioToque = null;
    if (movido) return;
    if (colocando) { intentarColocar(e); return; }
    if (editando()) {
      const i = calcaBajo(e);
      if (i >= 0) { oyentes.alElegir?.(i); return; }
    }
    seleccionar(piezaBajo(e));
  });
  // El cursor de "mano" se calcula como mucho una vez por cuadro, y no mientras se arrastra.
  let ultimoMovimiento = null;
  renderer.domElement.addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse" || e.buttons) return;
    if (!ultimoMovimiento) {
      requestAnimationFrame(() => {
        const m = ultimoMovimiento;
        if (colocando) renderer.domElement.style.cursor = carroceriaBajo(m) ? "copy" : "not-allowed";
        else if (editando() && calcaBajo(m) >= 0) renderer.domElement.style.cursor = "grab";
        else renderer.domElement.style.cursor = piezaBajo(m) ? "pointer" : "";
        ultimoMovimiento = null;
      });
    }
    ultimoMovimiento = { clientX: e.clientX, clientY: e.clientY };
  });

  document.querySelectorAll("#visor .visor-modo button").forEach((boton) => {
    boton.addEventListener("click", () => {
      modo = boton.dataset.modo;
      document.querySelectorAll("#visor .visor-modo button").forEach((b) => b.setAttribute("aria-pressed", String(b === boton)));
      if (modo === "moto") seleccionar(null);
      document.getElementById("visor-ayuda").textContent = modo === "moto" ? "Arrastra para girar" : "Arrastra para girar · toca una pieza";
      // Encender y Noche solo tienen sentido viendo la moto pintada
      const pv = document.getElementById("visor-vivo");
      if (pv) pv.hidden = modo !== "moto";
      if (modo !== "moto") moto.raiz.position.y = vitrina ? moto.raiz.position.y : 0;
      aplicarModo();
      ponerMarco();
    });
  });
  document.getElementById("visor-centrar").addEventListener("click", () => {
    camara.position.copy(POS_INICIAL);
    controles.target.set(0, 0.5, 0);
    seleccionar(null);
  });
  // Las tareas de la agenda ya no saltan al 3D al tocarlas: usan el botón "Ver en el modelo 3D" (TallerYa3D.verPieza).

  function ajustarTamano() {
    const { clientWidth: w, clientHeight: h } = contenedor;
    renderer.setSize(w, h, false);
    camara.aspect = w / h;
    camara.fov = w < 500 && !vitrina ? 44 : 34;
    camara.updateProjectionMatrix();
  }
  new ResizeObserver(ajustarTamano).observe(contenedor);
  ajustarTamano();

  aplicarModo();
  // Al abrir, selecciona lo más urgente para que se vea de una vez qué toca.
  const urgente = Object.entries(datos.piezas).find(([, p]) => p.estado === "vencido");
  if (urgente && contenedor.clientWidth >= 640) seleccionar(urgente[0]);

  // Si el visor no está en pantalla (p. ej. estás en el despiece) o la pestaña está oculta, no se dibuja nada.
  let enPantalla = true;
  new IntersectionObserver(([entrada]) => {
    enPantalla = entrada.isIntersecting;
    if (enPantalla) pedirCuadro();
  }).observe(contenedor);
  controles.addEventListener("change", pedirCuadro);
  new ResizeObserver(pedirCuadro).observe(contenedor);

  // Compila los sombreadores antes del primer cuadro, en paralelo y sin congelar la página (si no, el primer
  // cuadro se lleva de 0,4 a 1,3 s en un computador, y bastante más en un celular, con todo quieto).
  try { await renderer.compileAsync(escena, camara); } catch { /* sin compilación previa: se compila al dibujar */ }
  marcar("compilado");
  const reloj = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    if (!enPantalla || document.hidden) return;
    controles.update();
    if (pasoAnimacion()) necesitaCuadro = true;
    const t = reloj.getElapsedTime();
    if (pasoVivo(t)) necesitaCuadro = true;
    const latiendo = pulsando.length > 0 && modo !== "moto" && !reducido;
    if (modo !== "moto") for (const obj of pulsando) {
      obj.material.emissiveIntensity = 0.35 + (reducido ? 0.3 : 0.3 * (1 + Math.sin(t * 4)));
    }
    if (!necesitaCuadro && !latiendo) return;
    necesitaCuadro = false;
    renderer.render(escena, camara);
    marcar("primerCuadro");
  });
  cargando?.remove();
  document.getElementById("visor-ayuda").hidden = false;
  window.__moto3dListo = true;
  marcar("listo");
  // Al salir de la página se libera la memoria de la tarjeta gráfica (geometrías, materiales, texturas y el
  // contexto WebGL). Si el navegador la guarda para volver con "atrás" (persisted), se deja intacta.
  addEventListener("pagehide", (evento) => {
    if (evento.persisted) return;
    renderer.setAnimationLoop(null);
    const liberados = new Set();
    const liberar = (x) => { if (x && !liberados.has(x)) { liberados.add(x); x.dispose(); } };
    escena.traverse((obj) => {
      liberar(obj.geometry);
      for (const mat of [].concat(obj.material || [])) {
        for (const valor of Object.values(mat)) if (valor?.isTexture) liberar(valor);
        liberar(mat);
      }
    });
    liberar(escena.environment);
    controles.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
    if (estudio) { estudio.r.dispose(); estudio.r.forceContextLoss(); }
  });
  // Para revisar el modelo desde la consola: __visor.vista(x, y, z)
  window.__visor = {
    // Depuración: cuánto tarda en dibujar un cuadro (el primero incluye compilar los sombreadores)
    programas: () => renderer.info.programs.map((p) => p.name + " " + p.cacheKey.length),
    cuadro: () => { const t = performance.now(); renderer.render(escena, camara); renderer.getContext().finish(); return Math.round(performance.now() - t); },
    vista: (x, y, z) => { controles.autoRotate = false; camara.position.set(x, y, z); controles.update(); },
    // Depuración: dónde quedaron las mallas de un color (centro de su caja en coordenadas de la escena)
    mallasDeColor: (hex) => {
      const r = [];
      escena.traverse((o) => {
        if (o.isMesh && (o.userData.original ?? o.material)?.color?.getHexString?.() === hex.replace("#", "")) {
          const c = new THREE.Box3().setFromObject(o).getCenter(new THREE.Vector3());
          r.push([+c.x.toFixed(3), +c.y.toFixed(3), +c.z.toFixed(3)]);
        }
      });
      return r;
    },
    vivo: (encendida, noche) => { Object.assign(vivo, { encendida, noche, t0: performance.now() }); aplicarVivo(); },
    calcas: () => calcas.map((m) => ({ indice: m.userData.indice, vertices: m.geometry.attributes.position?.count || 0, visible: m.visible })),
    calcaBajo: (x, y) => calcaBajo({ clientX: x, clientY: y }),
    modo: () => modo,
    // Rendimiento: tiempo de armado, mallas, triángulos y llamadas de dibujo del último cuadro
    info: () => {
      let mallas = 0, triangulos = 0;
      escena.traverse((o) => {
        if (o.isMesh || o.isInstancedMesh) {
          mallas++;
          const g = o.geometry;
          triangulos += (g.index ? g.index.count : g.attributes.position.count) / 3 * (o.count || 1);
        }
      });
      return { tiempos: TIEMPOS, msArmado, etapas: Object.fromEntries(Object.entries(ETAPAS).map(([k, v]) => [k, Math.round(v)])), calidad: CALIDAD.nombre, panelesDeCache: cachePaneles.aciertos, pedazoMasLargo: Math.round(pedazos.max), panelesGuardados: Object.keys(cachePaneles.guardados).length, mallas, triangulos: Math.round(triangulos), llamadas: renderer.info.render.calls,
        texturas: renderer.info.memory.textures, geometrias: renderer.info.memory.geometries };
    },
    pesadas: (n = 12) => {
      const lista = [];
      escena.traverse((o) => {
        if (!o.isMesh) return;
        const g = o.geometry;
        lista.push([g.type, Math.round((g.index ? g.index.count : g.attributes.position.count) / 3 * (o.count || 1)),
          piezaDe(o) || (o.userData.zonas || []).join("/") || ""]);
      });
      const porTipo = {};
      for (const [t, n2] of lista) porTipo[t] = (porTipo[t] || 0) + n2;
      return { porTipo, top: lista.sort((a, b) => b[1] - a[1]).slice(0, n) };
    },
  };
}
