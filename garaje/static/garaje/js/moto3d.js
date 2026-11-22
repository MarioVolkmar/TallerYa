// Modelo 3D de la moto del usuario, armado a partir de la ficha técnica de su línea.
// Cada pieza de mantenimiento es un grupo con userData.pieza para colorearla y seleccionarla.
// Este archivo es la entrada: escena, controles e interfaz. El armado y las utilidades están en moto3d/.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { V, ETAPAS, CALIDAD, pedazos, medir, ceder } from "./moto3d/comun.js";
import { cachePaneles, prepararCache, guardarCache } from "./moto3d/cache.js";
import { construirMoto } from "./moto3d/construir.js";
import { texturaCalca, ponerPlaca } from "./moto3d/texturas.js";
import { unirEstaticas } from "./moto3d/geometria.js";
import { rasgosDe } from "./moto3d/rasgos.js";
import { glbDeLinea, montarGlb } from "./moto3d/glb.js"; // piloto: carrocería GLB con ?modelo3d=glb


// Línea de tiempo de la carga (ms desde que se abrió la página): __visor.info().tiempos
const TIEMPOS = { modulo: Math.round(performance.now()) };
const marcar = (nombre) => { TIEMPOS[nombre] ??= Math.round(performance.now()); };
// Complementos que no hacen falta para el primer cuadro (reflejos de estudio y calcas): se piden después,
// así no alargan la descarga inicial (con 4G cada archivo cuenta).
let RoomEnvironment = null, DecalGeometry = null, Fabrica = null;
function extras() {
  // (las calcas de fábrica van aparte: si su archivo falla, se reintenta una vez y nunca tumba los reflejos ni las calcas propias)
  extras.promesa ??= Promise.all([import("three/addons/environments/RoomEnvironment.js"), import("three/addons/geometries/DecalGeometry.js"),
    import("./moto3d/calcas_fabrica.js").catch(() => import("./moto3d/calcas_fabrica.js?r=1")).catch(() => null)])
    .then(([r, d, f]) => { RoomEnvironment = r.RoomEnvironment; DecalGeometry = d.DecalGeometry; Fabrica = f; });
  return extras.promesa;
}
const ESTADO_COLOR = { ok: 0x3fbf6b, pronto: 0xe3a72f, vencido: 0xff5a3c, desconocido: 0x8a9096 };
const ETIQUETA = { ok: "Al día", pronto: "Pronto", vencido: "Toca ya", desconocido: "Sin registro" };


const contenedor = document.getElementById("visor");
const datos = JSON.parse(document.getElementById("datos-moto").textContent);
// (settings.CALCAS_PERSONALIZADAS: false apaga las calcas que pega el usuario; las de fábrica quedan)
const CALCAS_PROPIAS = datos.calcas_personalizadas !== false;
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
  // Sin revisar errores de sombreadores (con ?depurar3d sí): cada revisión es una consulta síncrona a la GPU por programa
  renderer.debug.checkShaderErrors = new URLSearchParams(location.search).has("depurar3d");
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
  // Se generan después del primer cuadro, junto con las sombras (cuestan de 0,15 a 0,7 s): mientras tanto, una luz
  // de relleno hace sus veces para que la moto no salga oscura.
  function generarReflejos() {
    const pmrem = new THREE.PMREMGenerator(renderer);
    escena.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    pmrem.dispose(); // (el mapa de reflejos ya quedó hecho: el generador no se vuelve a usar)
    marcar("reflejos");
  }
  const relleno = new THREE.AmbientLight(0xf4ead2, 1.2);
  escena.add(relleno);
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
  // En la portada el fondo es oscuro: una luz de contorno cálida separa la moto del fondo.
  const contorno = new THREE.DirectionalLight(0xffc27a, "vitrina" in contenedor.dataset ? 1.6 : 0);
  contorno.position.set(-2.5, 2.2, -1.5);
  if ("vitrina" in contenedor.dataset) escena.add(contorno);

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
  // Carrocería realista de la línea, si la tiene (moto3d/glb.js; ?modelo3d=procedural la apaga); si falla, queda la procedural
  const urlGlb = glbDeLinea(datos.linea);
  if (urlGlb) {
    try { await montarGlb(moto, urlGlb); marcar("glb"); } catch (e) { console.warn("GLB sin cargar: queda la moto procedural", e); }
  }
  pedazos.max = Math.max(pedazos.max, performance.now() - pedazos.desde);
  const msArmado = Math.round(performance.now() - t0Armado);
  marcar("armada");
  // Guarda en el navegador los paneles nuevos (cuando el navegador esté libre, sin frenar el primer cuadro)
  // (con plazo de 2 s: en una pestaña de fondo el navegador casi nunca queda "libre" y no se guardaba)
  if (window.requestIdleCallback) requestIdleCallback(() => guardarCache(), { timeout: 2000 }); else setTimeout(guardarCache, 300);
  // Espejo de lado: la moto (genérica y GLB de Tripo) se arma con +z = izquierda del piloto, y con el frente en +x eso
  // es la derecha en three.js: sin este espejo el escape salía a la izquierda (19-nov-2026). Ver espejarTextura (comun.js).
  moto.raiz.scale.z = -1;
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
  // Al llegar, cada rueda rueda hasta quedar EXACTAMENTE en su ángulo 0 (pedido del usuario, 21-nov-2026): el giro sale de
  // lo que falta por recorrer, así que frena con la moto y termina en su posición original, nunca torcida (en «salir» y en
  // otra «entrar» ya no arrastra el ángulo de antes).
  function ruedasHacia(falta) {
    for (const r of moto.ruedas) r.pivote.rotation.z = falta / r.R;
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
      luces[0].emissiveIntensity = baseLuces.luz + 2.6 * brillo;
      luces[1].emissiveIntensity = baseLuces.stop + 1.5 * brillo;
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
      luces[1].emissiveIntensity = baseLuces.stop;
      terminado = p >= 1;
    }
    if (anim.fase === "entrar") ruedasHacia(baseX - x);
    else girarRuedas(x - xAnterior);
    xAnterior = x;
    raiz.position.set(x, y, 0);
    // El giro es sobre el centro de la moto: se sube lo que baja la rueda de apoyo (trasera en el caballito,
    // delantera en la frenada) para que nunca se hunda en el piso.
    raiz.rotation.z = giroZ;
    raiz.position.y = y + Math.abs(giroZ) * 0.66;
    renderer.shadowMap.needsUpdate = true;
    if (terminado) {
      const fin = anim.alTerminar;
      if (anim.fase === "entrar") ruedasHacia(0);
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
      // Modo noche del carrusel: la portada lo manda a todas las motos
      if (e.data === "noche" || e.data === "dia") { vivo.noche = e.data === "noche"; aplicarVivo(); }
    });
    // Avisa a la portada que ya escucha: así le reenvía día/noche (si lo mandó antes de que cargara el modelo, se perdía)
    if (window.parent !== window) window.parent.postMessage("moto-lista", window.location.origin);
  }

  // ---------- Moto viva: encenderla y verla de noche ----------
  // Encender: faro y stop a todo, tablero iluminado, saludo de direccionales y el motor temblando en mínimo.
  // Noche: la escena se oscurece, el faro proyecta su haz en el piso y el stop tiñe de rojo atrás.
  const vivo = { encendida: false, noche: false, t0: 0 };
  const exposicionBase = renderer.toneMappingExposure;
  const direccionales = [];
  moto.raiz.traverse((o) => {
    // (las de lente ámbar se reconocen por su color; las de mica transparente, por la marca del material)
    if (o.isMesh && o.material.emissive && (o.material.color?.getHex() === 0xffb347 || o.material.userData.direccional) && !direccionales.includes(o.material)) direccionales.push(o.material);
  });
  const brilloDireccional = direccionales.map((m) => m.emissiveIntensity);

  // Dónde quedan el faro y el stop: si el constructor da las anclas (moto.anclas.faro / .stop), esas; si no, el
  // extremo delantero (o trasero) de todo lo que usa el material de la luz (o del stop). No sirve el centro de la
  // malla: el constructor une las mallas iguales y una luz de placa o una franja corrían el centro a media moto.
  function extremoDe(material, sentido) {
    const puntos = [], v = new THREE.Vector3();
    moto.raiz.updateMatrixWorld(true);
    const aLocal = new THREE.Matrix4().copy(moto.raiz.matrixWorld).invert();
    moto.raiz.traverseVisible((o) => { // (solo lo visible: sin accesorios apagados, como el reflectivo del baúl)
      if (!o.isMesh || o.material !== material) return;
      const m = new THREE.Matrix4().multiplyMatrices(aLocal, o.matrixWorld), pos = o.geometry.attributes.position;
      for (let i = 0; i < pos.count; i++) puntos.push(v.fromBufferAttribute(pos, i).applyMatrix4(m).clone());
    });
    if (!puntos.length) return null;
    const borde = sentido > 0 ? Math.max(...puntos.map((p) => p.x)) : Math.min(...puntos.map((p) => p.x));
    const cerca = puntos.filter((p) => Math.abs(p.x - borde) < 0.06);
    return cerca.reduce((a, p) => a.add(p), new THREE.Vector3()).divideScalar(cerca.length);
  }
  // (si el único material de luz queda atrás —p. ej. solo la luz de placa—, no hay faro: sin cono ni halo en la cola)
  // Lámparas reales (construir.js: anclas.lamparas, centro de la cara de cada lente y su normal): los efectos de
  // noche nacen ahí. Sin ellas, como antes: el ancla del faro/stop o el extremo de su material.
  const lamparas = moto.anclas?.lamparas || [];
  // (a lo sumo dos conos: los dos lentes de faro más grandes; la CR4 tiene tres de tamaño parecido. Los halos van en
  // todos los lentes, también en las luces de posición del GLB, que no echan cono: cono false, p. ej. los ojos de la MT-03)
  const todosFaro = lamparas.filter((l) => l.tipo === "faro" && l.principal !== false);
  const conCono = todosFaro.filter((l) => l.cono !== false);
  const lentesFaro = (conCono.length ? conCono : todosFaro)
    .sort((a, b) => (b.ancho || 0) * (b.alto || 0) - (a.ancho || 0) * (a.alto || 0)).slice(0, 2);
  const lentesStop = lamparas.filter((l) => l.tipo === "stop" && l.principal !== false);
  const lentesAmbar = lamparas.filter((l) => l.tipo === "direccional");
  // Luces de accesorios (exploradoras): se prenden con el faro, pero solo si el accesorio está puesto
  const lentesAuxiliares = lamparas.filter((l) => l.tipo === "auxiliar" && moto.accesorios?.[l.accesorio]);
  const promedio = (lista) => lista.reduce((a, v) => a.add(v), new THREE.Vector3()).divideScalar(lista.length);
  const posFaro = lentesFaro.length ? promedio(lentesFaro.map((l) => l.pos)) : moto.anclas?.faro?.clone() ?? ((p) => (p && p.x > 0 ? p : null))(extremoDe(moto.M.luz, 1));
  const posStop = lentesStop.length ? promedio(lentesStop.map((l) => l.pos)) : moto.anclas?.stop?.clone() ?? extremoDe(moto.M.stop, -1);
  const dirStop = lentesStop.length ? promedio(lentesStop.map((l) => l.dir)).normalize() : V(-1, 0, 0);
  // Hacia dónde alumbra un faro: su normal llevada al piso (el haz cae unos 2,6 m adelante)
  // (modelo completo: las micas de Tripo miran en V hacia afuera; el haz se lleva casi al frente, como en la moto real)
  const haciaPiso = (pos, dir) => {
    const plano = V(dir.x, 0, moto.raiz.userData.modeloCompleto ? dir.z * 0.25 : dir.z);
    if (plano.lengthSq() < 1e-4) plano.set(1, 0, 0);
    return plano.normalize().multiplyScalar(2.6).add(V(0, -pos.y, 0)).normalize();
  };
  const dirFaro = lentesFaro.length ? promedio(lentesFaro.map((l) => l.dir)).normalize() : V(1, 0, 0);
  const haz = new THREE.SpotLight(0xfff1d0, 0, 7, 0.42, 0.65, 1.4);
  const rojoTras = new THREE.PointLight(0xff2a1f, 0, 1.3, 1.6);
  if (posFaro) {
    haz.position.copy(posFaro);
    haz.target.position.copy(posFaro).addScaledVector(haciaPiso(posFaro, dirFaro), 2.8);
    moto.raiz.add(haz, haz.target);
  }
  if (posStop) { rojoTras.position.copy(posStop).addScaledVector(dirStop, 0.08); moto.raiz.add(rojoTras); }
  // De noche hace falta un piso que reciba luz (el de día solo dibuja la sombra): ahí se ve el haz del faro.
  // Se desvanece hacia el borde (en la portada no debe verse un disco).
  const lienzoPiso = document.createElement("canvas");
  lienzoPiso.width = lienzoPiso.height = 128;
  {
    const c = lienzoPiso.getContext("2d"), g = c.createRadialGradient(64, 64, 10, 64, 64, 64);
    g.addColorStop(0, "#fff"); g.addColorStop(0.55, "#bbb"); g.addColorStop(1, "#000");
    c.fillStyle = g; c.fillRect(0, 0, 128, 128);
  }
  const pisoNoche = new THREE.Mesh(new THREE.CircleGeometry(1.7, 64),
    new THREE.MeshStandardMaterial({ color: 0x2c3539, roughness: 0.8, metalness: 0, transparent: true, opacity: 0,
      alphaMap: new THREE.CanvasTexture(lienzoPiso), depthWrite: false }));
  pisoNoche.rotation.x = -Math.PI / 2;
  pisoNoche.position.y = -0.0005;
  pisoNoche.receiveShadow = true;
  pisoNoche.visible = false;
  escena.add(pisoNoche);
  // Halos (un "bloom" barato, sin posproceso): un brillo aditivo sobre el faro y el stop, solo de noche
  const lienzoHalo = document.createElement("canvas");
  lienzoHalo.width = lienzoHalo.height = 64;
  {
    const c = lienzoHalo.getContext("2d"), g = c.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, "rgba(255,255,255,1)"); g.addColorStop(0.25, "rgba(255,255,255,.45)"); g.addColorStop(1, "rgba(255,255,255,0)");
    c.fillStyle = g; c.fillRect(0, 0, 64, 64);
  }
  const texturaHalo = new THREE.CanvasTexture(lienzoHalo);
  function halo(color, pos, tam) {
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: texturaHalo, color, transparent: true, opacity: 0,
      depthWrite: false })); // (mezcla normal, no aditiva: el lienzo es transparente y lo aditivo no se veía sobre el fondo)
    sp.scale.set(tam, tam, 1);
    sp.position.copy(pos);
    sp.visible = false;
    sp.raycast = () => {};
    moto.raiz.add(sp);
    return sp;
  }
  // Cono de luz del faro: un haz visible hacia adelante y abajo (se desvanece hacia la base), además de
  // la luz que proyecta la SpotLight en el piso. Nace en la cara de cada lente principal (dos en los faros dobles,
  // más angostos) y cuelga de la moto (se mueve con ella).
  const conos = [];
  let conoEnModo = true; // (el cono solo se ve de noche, encendida y en el modo "moto")
  if (posFaro) {
    const lienzoCono = document.createElement("canvas");
    lienzoCono.width = 4; lienzoCono.height = 64;
    const cc = lienzoCono.getContext("2d"), gc = cc.createLinearGradient(0, 0, 0, 64);
    gc.addColorStop(0, "#fff"); gc.addColorStop(0.35, "#777"); gc.addColorStop(1, "#000");
    cc.fillStyle = gc; cc.fillRect(0, 0, 4, 64);
    const largo = 1.6;
    const fuentes = lentesFaro.length ? lentesFaro : [{ pos: posFaro, dir: dirFaro }];
    const material = new THREE.MeshBasicMaterial({ color: 0xfff1d0, transparent: true, opacity: 0, alphaMap: new THREE.CanvasTexture(lienzoCono),
      depthWrite: false, side: THREE.DoubleSide });
    const geo = new THREE.ConeGeometry(fuentes.length > 1 ? 0.3 : 0.42, largo, 28, 1, true);
    geo.translate(0, -largo / 2, 0); // la punta en el faro
    // (uv.v: 1 en la punta, 0 en la base; el degradado del lienzo va de arriba = punta a abajo = base)
    for (const l of fuentes) {
      const cono = new THREE.Mesh(geo, material);
      cono.quaternion.setFromUnitVectors(V(0, -1, 0), haciaPiso(l.pos, l.dir));
      cono.position.copy(l.pos).addScaledVector(l.dir, 0.004); // (pegado a la cara del lente, sin hundirse)
      cono.visible = false;
      cono.raycast = () => {};
      cono.userData.conservar = true;
      moto.raiz.add(cono);
      conos.push(cono);
    }
  }
  // Halos chicos pegados a cada lente (a 1,5 cm de su cara, del tamaño del lente): se tapan solos cuando el lente
  // mira para otro lado. Faro y stop de noche con la moto encendida; los ámbar solo mientras parpadean.
  const tamHalo = (l, k, min, max) => Math.min(max, Math.max(min, Math.max(l.ancho || 0, l.alto || 0) * k));
  const halos = [], halosAmbar = [];
  if (todosFaro.length) for (const l of todosFaro) halos.push({ sp: halo(0xfff1c8, l.pos.clone().addScaledVector(l.dir, 0.015), tamHalo(l, 2.4, 0.14, 0.32)), fuerza: 0.85 });
  else if (posFaro) halos.push({ sp: halo(0xfff1c8, posFaro.clone().add(V(0.1, 0, 0)), 0.55), fuerza: 0.85 });
  if (lentesStop.length) for (const l of lentesStop) halos.push({ sp: halo(0xff3322, l.pos.clone().addScaledVector(l.dir, 0.015), tamHalo(l, 2.6, 0.1, 0.22)), fuerza: 0.75 });
  else if (posStop) halos.push({ sp: halo(0xff3322, posStop.clone().add(V(-0.07, 0, 0)), 0.3), fuerza: 0.75 });
  for (const l of lentesAuxiliares) halos.push({ sp: halo(0xfff1c8, l.pos.clone().addScaledVector(l.dir, 0.012), tamHalo(l, 2.8, 0.1, 0.2)), fuerza: 0.8, accesorio: moto.accesorios[l.accesorio] });
  for (const l of lentesAmbar) halosAmbar.push(halo(0xffa531, l.pos.clone().addScaledVector(l.dir, 0.012), tamHalo(l, 2.6, 0.08, 0.16)));
  // De noche los reflejos se marcan más (pintura y cromos lucen); se guarda el valor de día de cada material
  const conReflejo = new Map();
  moto.raiz.traverse((o) => {
    for (const m of [].concat(o.material || [])) if (m.envMapIntensity !== undefined && !conReflejo.has(m)) conReflejo.set(m, m.envMapIntensity);
  });
  const LUNA = new THREE.Color(0x9db4ff), SOL = sol.color.clone();
  const CIELO_DIA = hemi.color.clone(), CIELO_NOCHE = new THREE.Color(0x5d74b8);
  const SUELO_DIA = hemi.groundColor.clone(), SUELO_NOCHE = new THREE.Color(0x0b1220);
  const contornoDia = contorno.intensity;
  // Valores de las luces sin animación (la entrada de la portada destella encima de estos)
  const baseLuces = { luz: 1.1, stop: 0.7 };
  // k: 0 = día, 1 = noche. Va hacia el objetivo en ~600 ms (al instante con "reducir movimiento")
  const transicion = { k: 0, desde: 0, t0: 0, dur: 600 };
  // Entrada de los reflejos de estudio y las sombras (segunda etapa de la carga): de 0 a 1 en ~300 ms
  const fundido = { reflejo: 1, t0: 0 };
  const mezcla = (a, b, k) => a + (b - a) * k;
  function pintarVivo(k) {
    // Las luces solo se prenden con la moto encendida; de noche y apagada todo queda apagado (solo el ambiente).
    // En la portada la moto del carrusel cuenta como encendida (entra rodando).
    const e = vivo.encendida || vitrina;
    renderer.toneMappingExposure = exposicionBase * mezcla(1, 0.4, k);
    hemi.intensity = mezcla(0.45, 0.16, k);
    hemi.color.copy(CIELO_DIA).lerp(CIELO_NOCHE, k);
    hemi.groundColor.copy(SUELO_DIA).lerp(SUELO_NOCHE, k);
    sol.intensity = mezcla(2.4, 0.55, k); // de noche hace de luna: azulada y suave
    sol.color.copy(SOL).lerp(LUNA, k);
    contraluz.intensity = mezcla(0.55, 0.18, k);
    contorno.intensity = mezcla(contornoDia, contornoDia * 0.35, k);
    // (modelo completo: apagada, la mica se ve clara —sin el brillo de día de la genérica— y encendida brilla más fuerte;
    // el reflector cromado del faro se prende con la tira LED y el stop tiñe el piso de atrás más lejos)
    const comp = !!moto.raiz.userData.modeloCompleto;
    baseLuces.luz = e ? mezcla(comp ? 4.5 : 2.6, comp ? 14 : 11, k) : mezcla(comp ? 0.1 : 1.1, 0, k);
    baseLuces.stop = e ? mezcla(comp ? 3.4 : 1.5, comp ? 10 : 7, k) : mezcla(comp ? 0.12 : 0.7, 0, k);
    if (moto.M.luz_reflector) moto.M.luz_reflector.emissiveIntensity = comp && e ? mezcla(0.7, 3.2, k) : 0;
    rojoTras.distance = comp ? 1.9 : 1.3;
    if (!anim.fase) { moto.M.luz.emissiveIntensity = baseLuces.luz; moto.M.stop.emissiveIntensity = baseLuces.stop; }
    // (soloEncendida: pantalla con dibujo, que apagada no muestra nada; la genérica deja un brillo tenue de día)
    // (modelo completo: la pantalla es la zona del tablero de Tripo marcada «tacómetro»; apagada queda negra, encendida brilla)
    moto.M.pantalla.emissiveIntensity = e ? mezcla(comp ? 1.6 : 1, 3, k) : moto.M.pantalla.userData.soloEncendida || comp ? 0 : mezcla(0.35, 0, k);
    haz.intensity = e ? mezcla(2.5, 26, k) : 0;
    rojoTras.intensity = e ? (comp ? 3 : 2.4) * k : 0;
    direccionales.forEach((m, i) => { m.emissiveIntensity = brilloDireccional[i] * mezcla(1, e ? 1.3 : 0, k); });
    // Neón inferior (accesorio LED): solo con la moto encendida y de noche; apagada no deja luz (ni de día)
    const led = moto.accesorios.led?.userData.led;
    if (led) { led.luz.intensity = led.puesto && e ? 0.9 * k : 0; led.material.emissiveIntensity = e ? 2.2 * k : 0; }
    // (el reflejo del estudio también ilumina lo opaco: se baja en lo mate y se sube en cromos y metales)
    for (const [m, base] of conReflejo) m.envMapIntensity = base * mezcla(1, m.metalness >= 0.6 ? 1.7 : 0.7, k) * fundido.reflejo;
    // Luz de relleno: hace de reflejos hasta que estos llegan, y se desvanece mientras entran (ver fundido)
    relleno.intensity = (escena.environment ? 1.2 * (1 - fundido.reflejo) : 1.2) * mezcla(1, 0.3, k);
    suelo.material.opacity = 0.32 * (escena.environment ? fundido.reflejo : 1);
    pisoNoche.visible = k > 0.01;
    pisoNoche.material.opacity = k;
    for (const h of halos) { h.sp.visible = e && k > 0.01 && (!h.accesorio || h.accesorio.visible); h.sp.material.opacity = h.fuerza * k; }
    if (!vivo.encendida) for (const sp of halosAmbar) sp.visible = false;
    for (const cono of conos) { cono.visible = conoEnModo && e && k > 0.01; cono.material.opacity = (conos.length > 1 ? 0.18 : 0.22) * k; }
    renderer.shadowMap.needsUpdate = true;
  }
  function aplicarVivo() {
    contenedor.classList.toggle("noche", vivo.noche);
    Object.assign(transicion, { desde: transicion.k, t0: performance.now(), dur: reducido || document.hidden || !enPantalla ? 0 : 600 });
    // (oculto o fuera de vista no hay cuadros que lleven la transición: se aplica de una, si no las luces quedaban a medias)
    pasoTransicion();
    pedirCuadro();
  }
  function pasoTransicion() {
    const objetivo = vivo.noche ? 1 : 0;
    const p = transicion.dur ? Math.min(1, (performance.now() - transicion.t0) / transicion.dur) : 1;
    const suave = p * p * (3 - 2 * p);
    const k = mezcla(transicion.desde, objetivo, suave);
    const cambio = Math.abs(k - transicion.k) > 1e-4 || p < 1;
    transicion.k = k;
    pintarVivo(k);
    return cambio;
  }
  function pasoVivo(t) {
    const enTransicion = transicion.k !== (vivo.noche ? 1 : 0) && pasoTransicion();
    if (!vivo.encendida || modo !== "moto" || anim.fase) return enTransicion;
    const desde = (performance.now() - vivo.t0) / 1000;
    // Saludo: las direccionales parpadean tres veces al encender
    const parpadeo = desde < 2.1 && Math.floor(desde / 0.35) % 2 === 0;
    direccionales.forEach((m, i) => { m.emissiveIntensity = parpadeo ? (moto.raiz.userData.modeloCompleto ? 6 : 3.2) : brilloDireccional[i] * (vivo.noche ? 0.5 : 1); });
    // (el ámbar de cada direccional brilla en su lente mientras parpadea; de día apenas se nota)
    for (const sp of halosAmbar) { sp.visible = parpadeo && transicion.k > 0.01; sp.material.opacity = 0.9 * transicion.k; }
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
  // (la vista "Estado" se unió a Rayos X: si algo aún pide "estado", cae en rayos)
  let modo = contenedor.dataset.modo === "moto" ? "moto" : "rayos";
  let seleccionada = null;
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
  // Rayos X, piezas sin estado: no se dibujan (material.visible = false, sin call) pero siguen tocándose con el rayo
  // (Mesh.raycast no mira el material); de ellas solo se ven sus bordes, todos juntos en una sola malla de líneas.
  const invisible = new THREE.MeshBasicMaterial({ visible: false });
  const bordes = { malla: null, clave: "", listos: false };
  function actualizarBordes(lista) {
    const clave = lista.map((o) => o.id).join(",");
    if (bordes.clave === clave) { if (bordes.malla) bordes.malla.visible = lista.length > 0; return; }
    bordes.clave = clave;
    if (bordes.malla) { bordes.malla.removeFromParent(); bordes.malla.geometry.dispose(); bordes.malla = null; }
    if (!lista.length) return;
    moto.raiz.updateMatrixWorld(true);
    const aLocal = moto.raiz.matrixWorld.clone().invert(), m = new THREE.Matrix4(), v = new THREE.Vector3();
    // (las aristas de cada malla se calculan una vez y se guardan; aquí solo se llevan a la moto y se juntan)
    const partes = lista.map((o) => (o.userData.aristas ??= new THREE.EdgesGeometry(o.geometry, 28).attributes.position.array));
    const P = new Float32Array(partes.reduce((n, a) => n + a.length, 0));
    let k = 0;
    lista.forEach((o, i) => {
      m.multiplyMatrices(aLocal, o.matrixWorld);
      const a = partes[i];
      for (let j = 0; j < a.length; j += 3) { v.set(a[j], a[j + 1], a[j + 2]).applyMatrix4(m); P[k++] = v.x; P[k++] = v.y; P[k++] = v.z; }
    });
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(P, 3));
    bordes.malla = new THREE.LineSegments(geo, matBorde);
    bordes.malla.raycast = () => {};
    moto.raiz.add(bordes.malla);
  }

  // Rayos X, piezas con estado: se dibujan juntas, una malla por estado (y por interna o carcasa), en vez de una por
  // pieza (bajaba de ~66 llamadas a ≤8). Las mallas de cada pieza quedan sin dibujar pero se siguen tocando; la pieza
  // seleccionada se dibuja aparte con su material propio, para que lata.
  const grupos = { mallas: [], clave: "", lista: [] };
  function geometriaEnMoto(o, aLocal) {
    // (posiciones y normales sin índice, en el espacio de la malla, calculadas una vez)
    o.userData.plano ??= (() => {
      const g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry;
      if (!g.attributes.normal) g.computeVertexNormals();
      const r = { P: g.attributes.position.array.slice(), N: g.attributes.normal.array.slice() };
      if (g !== o.geometry) g.dispose();
      return r;
    })();
    const m = new THREE.Matrix4().multiplyMatrices(aLocal, o.matrixWorld), nm = new THREE.Matrix3().getNormalMatrix(m);
    const { P, N } = o.userData.plano, Pm = new Float32Array(P.length), Nm = new Float32Array(N.length), v = new THREE.Vector3();
    for (let j = 0; j < P.length; j += 3) {
      v.set(P[j], P[j + 1], P[j + 2]).applyMatrix4(m); Pm[j] = v.x; Pm[j + 1] = v.y; Pm[j + 2] = v.z;
      v.set(N[j], N[j + 1], N[j + 2]).applyMatrix3(nm).normalize(); Nm[j] = v.x; Nm[j + 1] = v.y; Nm[j + 2] = v.z;
    }
    return { P: Pm, N: Nm };
  }
  function agruparRayos() {
    const lista = modo === "rayos" ? grupos.lista : [];
    // Cada malla con estado: la de la pieza seleccionada con su material (late); las demás, sin dibujar
    for (const o of lista) o.material = piezaDe(o) === seleccionada ? o.userData.matRayos : invisible;
    const juntas = lista.filter((o) => o.visible && piezaDe(o) !== seleccionada);
    const clave = juntas.map((o) => o.id).join(",");
    if (grupos.clave === clave) return;
    grupos.clave = clave;
    for (const g of grupos.mallas) { g.removeFromParent(); g.geometry.dispose(); }
    grupos.mallas = [];
    if (!juntas.length) return;
    moto.raiz.updateMatrixWorld(true);
    const aLocal = moto.raiz.matrixWorld.clone().invert();
    const porMaterial = new Map();
    for (const o of juntas) {
      const estado = estadoDe(piezaDe(o)), interno = Boolean(o.userData.interno), k = estado + "|" + interno;
      if (!porMaterial.has(k)) porMaterial.set(k, { material: o.userData.matRayos, partes: [] });
      porMaterial.get(k).partes.push(geometriaEnMoto(o, aLocal));
    }
    for (const { material, partes } of porMaterial.values()) {
      const n = partes.reduce((t, p) => t + p.P.length, 0), P = new Float32Array(n), N = new Float32Array(n);
      let k = 0;
      for (const p of partes) { P.set(p.P, k); N.set(p.N, k); k += p.P.length; }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(P, 3));
      geo.setAttribute("normal", new THREE.BufferAttribute(N, 3));
      // (material propio del grupo: el de las piezas sirve para que lata la seleccionada)
      const malla = new THREE.Mesh(geo, (material.userData.deGrupo ??= Object.assign(material.clone(), { emissiveIntensity: 0.25 })));
      malla.raycast = () => {};
      malla.castShadow = true;
      malla.userData.grupoRayos = true;
      moto.raiz.add(malla);
      grupos.mallas.push(malla);
    }
  }

  // Vista Moto: todo lo fijo que comparte material se dibuja en una sola malla por material (sin las ruedas ni el
  // gato, que se mueven). Las mallas originales quedan sin dibujar pero siguen ahí para pegar calcas y para los otros
  // modos. Se rehace cuando cambia lo que se ve (accesorios, rin, retrovisores) o al volver de Rayos X.
  const gruposMoto = { mallas: [], clave: "" };
  let moviles = null;
  function planoCompleto(o) {
    return (o.userData.planoUV ??= (() => {
      const g = o.geometry.index ? o.geometry.toNonIndexed() : o.geometry;
      if (!g.attributes.normal) g.computeVertexNormals();
      const r = { P: g.attributes.position.array.slice(), N: g.attributes.normal.array.slice(), U: g.attributes.uv ? g.attributes.uv.array.slice() : null };
      if (g !== o.geometry) g.dispose();
      return r;
    })());
  }
  function agruparMoto() {
    moviles ??= new Set([...(moto.ruedas || []).map((r) => r.pivote), moto.pata].filter(Boolean));
    const enMovil = (o) => { for (let q = o; q && q !== moto.raiz; q = q.parent) if (moviles.has(q)) return true; return false; };
    const porMaterial = new Map();
    if (modo === "moto") {
      moto.raiz.traverseVisible((o) => {
        if (!o.isMesh || o.isInstancedMesh || o.userData.calca || o.userData.grupoRayos || o.userData.grupoMoto || conos.includes(o)) return;
        const material = o.userData.original ?? o.material;
        if (!material || material === invisible || Array.isArray(material) || o.morphTargetInfluences || enMovil(o)) return;
        if (!porMaterial.has(material)) porMaterial.set(material, []);
        porMaterial.get(material).push(o);
      });
    }
    // (solo se juntan los materiales con 2 o más mallas; con textura, solo si todas traen coordenadas de textura)
    const juntar = [...porMaterial].filter(([m, l]) => l.length > 1 && (!m.map || l.every((o) => o.geometry.attributes.uv)));
    const clave = juntar.map(([, l]) => l.map((o) => o.id).join(".")).join("|");
    if (gruposMoto.clave === clave) { for (const [, l] of juntar) for (const o of l) o.material = invisible; return; }
    gruposMoto.clave = clave;
    for (const g of gruposMoto.mallas) { g.removeFromParent(); g.geometry.dispose(); }
    gruposMoto.mallas = [];
    if (modo === "moto") for (const [m, l] of porMaterial) if (!juntar.some(([mj]) => mj === m)) for (const o of l) o.material = m;
    if (!juntar.length) return;
    moto.raiz.updateMatrixWorld(true);
    const aLocal = moto.raiz.matrixWorld.clone().invert(), v = new THREE.Vector3(), mt = new THREE.Matrix4(), nm = new THREE.Matrix3();
    for (const [material, lista] of juntar) {
      const planos = lista.map(planoCompleto), conUV = planos.every((q) => q.U);
      const n = planos.reduce((t, q) => t + q.P.length, 0);
      const P = new Float32Array(n), N = new Float32Array(n), U = conUV ? new Float32Array((n / 3) * 2) : null;
      let k = 0, ku = 0;
      lista.forEach((o, i) => {
        mt.multiplyMatrices(aLocal, o.matrixWorld); nm.getNormalMatrix(mt);
        const q = planos[i];
        for (let j = 0; j < q.P.length; j += 3) {
          v.set(q.P[j], q.P[j + 1], q.P[j + 2]).applyMatrix4(mt); P[k] = v.x; P[k + 1] = v.y; P[k + 2] = v.z;
          v.set(q.N[j], q.N[j + 1], q.N[j + 2]).applyMatrix3(nm).normalize(); N[k] = v.x; N[k + 1] = v.y; N[k + 2] = v.z;
          k += 3;
        }
        if (U) { U.set(q.U, ku); ku += q.U.length; }
        o.material = invisible;
      });
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(P, 3));
      geo.setAttribute("normal", new THREE.BufferAttribute(N, 3));
      if (U) geo.setAttribute("uv", new THREE.BufferAttribute(U, 2));
      const malla = new THREE.Mesh(geo, material);
      malla.castShadow = true;
      malla.receiveShadow = true;
      malla.raycast = () => {};
      malla.userData.grupoMoto = true;
      moto.raiz.add(malla);
      gruposMoto.mallas.push(malla);
    }
    renderer.shadowMap.needsUpdate = true;
  }

  // Oculta por un padre (accesorio no puesto, estilo de rin o espejo sin usar, escape de fábrica cambiado…): en Rayos X
  // los bordes y los grupos se juntan en mallas colgadas de la raíz, así que hay que mirar toda la cadena.
  const ocultaArriba = (o) => { for (let p = o.parent; p && p !== moto.raiz; p = p.parent) if (!p.visible) return true; return false; };

  function aplicarModo() {
    contenedor.classList.toggle("rayos", modo === "rayos");
    calcas.forEach((c) => { c.visible = modo === "moto"; });
    if (fabrica.malla) fabrica.malla.visible = modo === "moto";
    const mallas = [];
    // (sin el cono del faro: su visibilidad la lleva la noche; si no, quedaba visible de día con opacidad 0 y gastaba un call)
    moto.raiz.traverse((obj) => { if (obj.isMesh && !obj.userData.calca && !obj.userData.grupoRayos && !obj.userData.grupoMoto && !conos.includes(obj)) mallas.push(obj); });
    conoEnModo = modo === "moto";
    for (const cono of conos) cono.visible = conoEnModo && cono.material.opacity > 0.002;
    const conBorde = [];
    grupos.lista = [];
    for (const obj of mallas) {
      obj.userData.original ??= obj.material;
      const pieza = piezaDe(obj);
      const estado = pieza && estadoDe(pieza);
      const interno = Boolean(obj.userData.interno);
      obj.visible = (!interno || modo === "rayos") && !obj.userData.oculto;
      const seVe = obj.visible && !ocultaArriba(obj);

      if (modo === "moto") {
        obj.material = obj.userData.original;
      } else if (estado) {
        // Rayos X: piezas internas sólidas; sus carcasas, translúcidas para ver adentro.
        if (!obj.userData.matRayos) {
          const m = matEstado[estado].clone();
          if (!interno) Object.assign(m, { transparent: true, opacity: 0.28, depthWrite: false });
          obj.userData.matRayos = m;
        }
        obj.material = obj.userData.matRayos;
        if (seVe) grupos.lista.push(obj);
      } else {
        if (seVe && !obj.isInstancedMesh) conBorde.push(obj);
        obj.material = invisible;
      }
      obj.castShadow = modo === "moto" || (Boolean(estado) && seVe);
    }
    // (al abrir, las aristas de Rayos X se calculan después del primer cuadro: costaban ~0,1 s antes de verlo)
    if (bordes.listos) actualizarBordes(modo === "rayos" ? conBorde : []);
    agruparRayos();
    agruparMoto();
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
    if (modo === "rayos") agruparRayos(); // (la seleccionada sale del grupo para latir sola)
    pulsando = [];
    moto.raiz.traverse((obj) => {
      if (!obj.isMesh || obj.userData.calca || !obj.material.emissive) return;
      const activa = Boolean(pieza) && piezaDe(obj) === pieza;
      if (activa) pulsando.push(obj);
      else if (modo === "rayos" && piezaDe(obj) && estadoDe(piezaDe(obj))) {
        obj.material.emissiveIntensity = 0.25;
      }
    });
    pedirCuadro();
  }

  function seleccionar(pieza) {
    // Si piden una pieza desde el plan o el despiece estando en Moto, se pasa a Rayos X para mostrarla.
    if (pieza && modo === "moto") document.querySelector('#visor .visor-modo [data-modo="rayos"]')?.click();
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

  // Recorte de la malla alrededor de la calca: DecalGeometry recorre y recorta cada triángulo de la malla, y con
  // las mallas unidas (toda la carrocería en una) eso tomaba más de 1 s en un celular. Antes se descartan, en el
  // espacio de la malla, los triángulos que quedan lejos (comparar distancias es mucho más barato que recortar).
  function recorteCerca(malla, puntoMundo, radio) {
    const geo = malla.geometry, pos = geo.attributes.position, nor = geo.attributes.normal;
    if (!nor) return malla;
    const c = malla.worldToLocal(puntoMundo.clone()), r2 = radio * radio;
    const idx = geo.index ? geo.index.array : null, n = idx ? idx.length : pos.count;
    const P = [], N = [];
    const cerca = (i) => { const dx = pos.getX(i) - c.x, dy = pos.getY(i) - c.y, dz = pos.getZ(i) - c.z; return dx * dx + dy * dy + dz * dz < r2; };
    for (let t = 0; t < n; t += 3) {
      const a = idx ? idx[t] : t, b = idx ? idx[t + 1] : t + 1, d = idx ? idx[t + 2] : t + 2;
      if (!(cerca(a) || cerca(b) || cerca(d))) continue;
      for (const i of [a, b, d]) { P.push(pos.getX(i), pos.getY(i), pos.getZ(i)); N.push(nor.getX(i), nor.getY(i), nor.getZ(i)); }
    }
    const sub = new THREE.BufferGeometry();
    sub.setAttribute("position", new THREE.Float32BufferAttribute(P, 3));
    sub.setAttribute("normal", new THREE.Float32BufferAttribute(N, 3));
    const m = new THREE.Mesh(sub);
    m.matrixAutoUpdate = false;
    m.matrixWorld.copy(malla.matrixWorld);
    return m;
  }

  function geometriasCalca(c, aspecto) {
    const { ancho, alto } = medidas(c, aspecto);
    return geometriasCon(c, ancho, alto);
  }
  function geometriasCon(c, ancho, alto, profundidad = PROFUNDIDAD) {
    const geos = [];
    for (const [p, n] of lados(c)) {
      const s = superficieEn(p, n);
      if (!s) continue;
      const giro = c.giro || 0;
      const rot = orientacion(s.punto, s.normal, giro).rotation;
      // (radio: media diagonal de la calca más un margen; los paneles están subdivididos, sus triángulos son chicos)
      const radio = Math.hypot(ancho, alto) / 2 + Math.max(0.12, profundidad / 2 + 0.02);
      const conCalca = (malla) => {
        const recorte = recorteCerca(malla, s.punto, radio);
        const g = new DecalGeometry(recorte, s.punto, rot, V(ancho, alto, profundidad));
        if (recorte !== malla) recorte.geometry.dispose();
        return g;
      };
      geos.push(conCalca(s.malla));
      // Franjas y detalles pegados sobre la carrocería: la calca también pasa por encima de ellos (como un sticker real)
      // (modelo completo: el costado de Tripo viene en varias piezas, p. ej. panel negro y tapa brillante; la calca sigue
      // por las piezas vecinas con zona en vez de cortarse en la costura)
      const vecinas = moto.raiz.userData.modeloCompleto ? mallasCarroceria().filter((m) => m !== s.malla) : [];
      for (const detalle of [...detallesBajoCalca(), ...vecinas]) {
        const g = conCalca(detalle);
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
      // (los dos lados y los detalles que cruza van en una sola malla: una llamada por calca)
      moto.raiz.updateMatrixWorld(true);
      const aLocal = moto.raiz.matrixWorld.clone().invert();
      const partes = geometriasCalca(c, e.aspecto).filter((g) => g.attributes.position.count);
      partes.forEach((g) => g.applyMatrix4(aLocal));
      const unida = partes.length > 1 ? unirGeometrias(partes) : partes[0];
      if (partes.length > 1) partes.forEach((g) => g.dispose());
      for (const geo of unida ? [unida] : []) {
        // La calca va pegada a la moto (no a la escena): así la acompaña cuando la moto entra, frena o sale animada.
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

  // ---------- Calcas de fábrica: nombre del modelo, cilindrada y franjas que la moto trae de serie ----------
  // Todas van en una sola malla con una textura atlas (1 call). Se pueden quitar una por una (estilo.sin_fabrica).
  const fabrica = { lista: null, regiones: null, claveColor: "", material: null, geos: {}, malla: null, claveMalla: "" };
  function zonaParaFabrica(zonas) {
    const mallas = [];
    moto.raiz.traverse((o) => { if (o.isMesh && o.visible && o.userData.zonas) mallas.push(o); });
    for (const z of zonas) {
      let mejor = null, area = -1;
      for (const m of mallas) {
        if (!m.userData.zonas.includes(z)) continue;
        const caja = new THREE.Box3().setFromObject(m), t = caja.getSize(new THREE.Vector3());
        if (t.x * t.y > area) { area = t.x * t.y; mejor = { malla: m, caja }; }
      }
      if (mejor) return mejor;
    }
    return null;
  }
  // Dónde va cada calca: un rayo desde el costado (o el frente) hacia la zona, en la posición relativa de la lista
  function ubicarFabrica(c) {
    const z = zonaParaFabrica(c.zona);
    if (!z) return null;
    const { malla, caja } = z, t = caja.getSize(new THREE.Vector3()), centro = caja.getCenter(new THREE.Vector3());
    // (c.en [x, y]: punto exacto sobre la moto; si no, la posición relativa dentro de la zona)
    const y = c.en ? c.en[1] : centro.y + (c.altura || 0) * t.y / 2, x = c.en ? c.en[0] : centro.x + (c.posicion || 0) * t.x / 2;
    const disparos = c.cara === "frente" ? [[V(caja.max.x + 0.4, y, 0), V(-1, 0, 0)]]
      : [[V(x, y, caja.max.z + 0.4), V(0, 0, -1)], [V(x, y, caja.min.z - 0.4), V(0, 0, 1)]];
    // (modelo completo con «en»: la zona puede venir en varias piezas de Tripo; vale la primera que toque el rayo)
    const blancos = [malla];
    if (c.en && moto.raiz.userData.modeloCompleto) moto.raiz.traverse((o) => { if (o.isMesh && o.visible && o !== malla && o.userData.zonas?.some((zz) => c.zona.includes(zz))) blancos.push(o); });
    for (const [origen, dir] of disparos) {
      rayo.set(origen, dir);
      const golpe = rayo.intersectObjects(blancos, false)[0];
      if (!golpe) continue;
      const normal = golpe.face.normal.clone().transformDirection(golpe.object.matrixWorld);
      if (normal.dot(dir) > 0) normal.negate();
      const local = moto.raiz.worldToLocal(golpe.point.clone());
      const nl = normal.transformDirection(moto.raiz.matrixWorld.clone().invert());
      // (siempre del lado +z: "ambos" pone el reflejo en el otro costado)
      if (c.cara !== "frente" && local.z < 0) { local.z = -local.z; nl.z = -nl.z; }
      return { punto: local.toArray(), normal: nl.toArray(), ambos: c.cara !== "frente", giro: c.giro || 0 };
    }
    return null;
  }
  // Geometría de una calca de fábrica, con las coordenadas de textura llevadas a su franja del atlas (en la moto)
  function geometriaFabrica(c) {
    const r = fabrica.regiones[c.id], ubicada = ubicarFabrica(c);
    if (!r || !ubicada) return [];
    const ancho = c.ancho, alto = Math.min(0.14, ancho / r.aspecto);
    moto.raiz.updateMatrixWorld(true);
    const aLocal = moto.raiz.matrixWorld.clone().invert();
    // (más hondas que las propias: van sobre carenados y tanques muy curvos, que se salían de la caja de proyección)
    // (modelo completo: caja de 5 cm, porque Tripo deja superficies internas detrás del panel que salían como calca doble)
    const hondo = moto.raiz.userData.modeloCompleto ? 0.05 : Math.min(0.3, Math.max(0.14, ancho * 0.9));
    return geometriasCon(ubicada, ancho, alto, hondo).map((g) => {
      const uv = g.attributes.uv;
      for (let i = 0; i < uv.count; i++) uv.setXY(i, r.u0 + uv.getX(i) * (r.u1 - r.u0), r.v0 + uv.getY(i) * (r.v1 - r.v0));
      g.applyMatrix4(aLocal);
      return g;
    });
  }
  function unirGeometrias(lista) {
    let n = 0;
    for (const g of lista) n += g.attributes.position.count;
    const P = new Float32Array(n * 3), Nn = new Float32Array(n * 3), U = new Float32Array(n * 2);
    let k = 0;
    for (const g of lista) {
      P.set(g.attributes.position.array, k * 3); Nn.set(g.attributes.normal.array, k * 3); U.set(g.attributes.uv.array, k * 2);
      k += g.attributes.position.count;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(P, 3));
    geo.setAttribute("normal", new THREE.BufferAttribute(Nn, 3));
    geo.setAttribute("uv", new THREE.BufferAttribute(U, 2));
    return geo;
  }
  // Arma o actualiza las calcas de fábrica según la pintura y las que el usuario quitó
  async function aplicarFabrica(cfg) {
    if (!Fabrica || !DecalGeometry) return;
    // (GLB sin zonas de carrocería: sin calcas de fábrica, que van sobre los paneles con zona; el que las trae sí las lleva)
    if (moto.raiz.userData.glb && !moto.raiz.userData.glbZonas) return;
    if (!fabrica.lista) {
      // (un modelo cargado puede traer sus propias calcas, ya ubicadas sobre él; si no, las de la línea)
      fabrica.lista = moto.raiz.userData.calcasFabrica || Fabrica.calcasDeFabrica(datos.linea || "", rasgosDe(datos.linea || "", datos.specs || {}).familia);
      fabrica.material = new THREE.MeshPhysicalMaterial({
        transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -3,
        roughness: 0.3, metalness: 0.05, clearcoat: 1, clearcoatRoughness: 0.08,
      });
    }
    if (!fabrica.lista.length) return;
    const pintura = "#" + moto.M.pintura.color.getHexString(), secundario = cfg.color_secundario || datos.color_secundario || "";
    const elegidos = cfg.estilo?.color_fabrica || {};
    const claveColor = pintura + secundario + JSON.stringify(elegidos);
    fabrica.base = Fabrica.coloresFabrica(pintura, secundario);
    if (fabrica.claveColor !== claveColor) {
      fabrica.claveColor = claveColor;
      const { textura, regiones } = await Fabrica.atlasFabrica(fabrica.lista, fabrica.base, elegidos);
      if (fabrica.claveColor !== claveColor) { textura.dispose(); return; } // (llegó otro color mientras se dibujaba)
      fabrica.material.map?.dispose();
      fabrica.material.map = textura;
      fabrica.material.needsUpdate = true;
      fabrica.regiones ??= regiones; // (las franjas del atlas no cambian con el color)
    }
    const quitadas = new Set(cfg.estilo?.sin_fabrica || []);
    const puestas = fabrica.lista.filter((c) => !quitadas.has(c.id));
    const claveMalla = puestas.map((c) => c.id).join(",");
    if (fabrica.claveMalla === claveMalla) { pedirCuadro(); return; }
    fabrica.claveMalla = claveMalla;
    const raiz = moto.raiz, pos = raiz.position.clone(), giro = raiz.rotation.z;
    raiz.position.set(baseX, 0, 0); raiz.rotation.z = 0; raiz.updateMatrixWorld(true);
    for (const c of puestas) fabrica.geos[c.id] ??= geometriaFabrica(c);
    raiz.position.copy(pos); raiz.rotation.z = giro; raiz.updateMatrixWorld(true);
    if (fabrica.malla) { fabrica.malla.removeFromParent(); fabrica.malla.geometry.dispose(); fabrica.malla = null; }
    const partes = puestas.flatMap((c) => fabrica.geos[c.id]);
    if (partes.length) {
      const malla = new THREE.Mesh(unirGeometrias(partes), fabrica.material);
      malla.userData.calca = true;
      malla.userData.fabrica = true;
      malla.renderOrder = 1; // (debajo de las calcas propias)
      malla.visible = modo === "moto";
      malla.raycast = () => {};
      raiz.add(malla);
      fabrica.malla = malla;
    }
    pedirCuadro();
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
    if (!RoomEnvironment) { extras(); return ""; } // (los reflejos aún vienen en camino)
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
  const COLOR_CHASIS = "#23282b", COLOR_ASIENTO = "#161819", SECUNDARIO_FABRICA = "#1c2022";
  // rinesDeFabrica: el color de rines es el de serie (ver aplicarPersonalizacion)
  function aplicarEstilo(estilo = {}, rinesDeFabrica = true) {
    const acabado = ACABADOS[estilo.acabado] || ACABADOS.brillante;
    for (const m of [moto.M.pintura, moto.M.pintura2]) Object.assign(m, acabado);
    moto.M.pintura2.color.set(estilo.color2 || moto.M.pintura.color);
    moto.M.chasis.color.set(estilo.chasis || COLOR_CHASIS);
    // Chasis a la vista (largueros de las naked, trellis naranja de la Duke): de serie su color de fábrica; con un
    // color de chasis elegido, ese
    moto.M.chasisVisto?.color.set(estilo.chasis || moto.M.chasisVisto.userData.fabrica);
    moto.M.asiento.color.set(estilo.asiento || COLOR_ASIENTO);
    const rin = ["radios", "aleacion", "estrella"].includes(estilo.rin) ? estilo.rin : moto.rinFabrica;
    // (modelo completo: la rueda queda tal cual viene del GLB, sin estilos de rin; «Rines y detalles» solo le cambia el
    // color: de fábrica, el material del GLB; con un color elegido, el de los rines)
    if (moto.raiz.userData.modeloCompleto) {
      for (const g of [moto.piezas.llanta_del, moto.piezas.llanta_tras]) g.traverse((o) => {
        if (o.isMesh && (o.userData.rin || o.userData.aro) && o.userData.glbMat) o.material = rinesDeFabrica ? o.userData.glbMat : moto.M.rin;
      });
    }
    for (const g of moto.raiz.userData.modeloCompleto ? [] : [moto.piezas.llanta_del, moto.piezas.llanta_tras]) {
      g.userData.armarRin?.(rin);
      g.traverse((o) => { if (o.userData.rin) o.visible = o.userData.rin === rin; });
      g.traverse((o) => {
        if (!o.userData.aro) return;
        // Aro de radios: plateado de serie; con un color de rines elegido, ese (antes quedaba siempre en metal y el
        // color se perdía al pasar a radios, o no se veía en las motos que traen radios de fábrica)
        const mat = rin === "radios" && rinesDeFabrica ? moto.M.metal : moto.M.rin;
        // (solo a mallas: un grupo con material hacía fallar compileAsync, y los sombreadores se compilaban de golpe al dibujar)
        if (o.isMesh && (o.material === o.userData.original || !o.userData.original)) o.material = mat;
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
      // (prendido o apagado lo decide pintarVivo: el neón solo brilla con la moto encendida y de noche)
      led.puesto = puestos.has("led");
    }
    // (las luces de los accesorios —neón, exploradoras— dependen de qué quedó puesto)
    pintarVivo(transicion.k);
    for (const v of moto.visoresFabrica) { v.userData.oculto = puestos.has("parabrisas"); v.visible = !v.userData.oculto; }
    renderer.shadowMap.needsUpdate = true;
  }

  function aplicarPersonalizacion(cfg) {
    moto.M.pintura.color.set(cfg.color);
    // Con el secundario de serie (SECUNDARIO_FABRICA, la muestra "De fábrica" de Personalizar), los rines conservan su
    // color de fábrica (Duke naranja, NS rojo, MT-03 cian; aro plateado en los de radios) y la cinta del rin el suyo
    // (CR4). Con un color elegido —el negro también: es otra muestra, #15181a—, todo estilo de rin toma ese color.
    const deFabrica = String(cfg.color_secundario).toLowerCase() === SECUNDARIO_FABRICA;
    // (modelo completo, 21-nov-2026: solo color de la moto, rines, sillín y acabado de la pintura; sin calcas mientras el
    // GLB no traiga las suyas. Lo guardado de otras opciones se ignora: no se borra, por si la moto vuelve a la genérica)
    const completo = !!moto.raiz.userData.modeloCompleto;
    const est = cfg.estilo || {};
    aplicarEstilo(completo ? { acabado: est.acabado, asiento: est.asiento } : est, deFabrica);
    // (calcas personalizadas apagadas en settings.CALCAS_PERSONALIZADAS, 21-nov-2026: no se dibujan, pero lo guardado
    // queda intacto; las de fábrica siguen con sus interruptores)
    if (!CALCAS_PROPIAS || (completo && !moto.raiz.userData.calcasModelo)) cfg = { ...cfg, calcas: [] };
    moto.M.rin.color.set(deFabrica && moto.rinColor != null ? moto.rinColor : cfg.color_secundario);
    moto.M.cinta?.color.set(deFabrica ? moto.M.cinta.userData.fabrica : cfg.color_secundario);
    if (moto.M.acento) moto.M.acento.color.set(cfg.color_secundario);
    for (const m of moto.M.secundarios || []) m.color.set(deFabrica ? m.userData.fabrica : cfg.color_secundario); // (tapas blancas de la XR 190L)
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
    aplicarFabrica(cfg); // (las de fábrica: según la pintura y las que se quitaron)
    // (en Rayos X, los bordes y grupos se rehacen con los accesorios que quedaron puestos)
    if (modo === "rayos" && bordes.listos) aplicarModo(); else agruparMoto();
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
    // Calcas de fábrica de esta moto (para la pestaña "De fábrica" de Personalizar)
    // (con sus colores de fábrica según la pintura actual: principal p y secundario s)
    calcasFabrica: () => (fabrica.lista || []).map((c) => ({ id: c.id, nombre: c.nombre, original: fabrica.base ? Fabrica.coloresOriginales(c, fabrica.base) : { p: "#ffffff", s: "#000000" } })),
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
    // y los colores de fábrica que la personalización respeta mientras no se elija otro (rines y chasis a la vista)
    // (colorRinFabrica: cómo se ven los rines "De fábrica" con el estilo de rin de `estilo`)
    opciones: (estilo = {}) => {
      const hex = (c) => (c == null ? null : "#" + new THREE.Color(c).getHexString());
      const rin = ["radios", "aleacion", "estrella"].includes(estilo.rin) ? estilo.rin : moto.rinFabrica;
      return { accesorios: Object.keys(moto.accesorios), espejos: Object.keys(moto.espejos || {}), rinFabrica: moto.rinFabrica, tipo: datos.specs.tipo,
        estiloRin: !moto.raiz.userData.modeloCompleto, // (modelo completo: sin cambio de estilo de rin, solo de color)
        modeloCompleto: !!moto.raiz.userData.modeloCompleto,
        // (pestaña Calcas: si hay calcas de fábrica o, con las personalizadas encendidas, si el modelo las admite)
        calcas: !!(moto.raiz.userData.calcasFabrica || []).length || (CALCAS_PROPIAS && (!moto.raiz.userData.modeloCompleto || !!moto.raiz.userData.calcasModelo)),
        calcasPropias: CALCAS_PROPIAS,
        secundarioFabrica: SECUNDARIO_FABRICA,
        colorRinFabrica: hex(rin === "radios" ? moto.M.metal.color : moto.rinColor ?? moto.M.cinta?.userData.fabrica ?? SECUNDARIO_FABRICA),
        colorChasisFabrica: hex(moto.M.chasisVisto?.userData.fabrica) };
    },
    verMoto() { document.querySelector('#visor .visor-modo [data-modo="moto"]')?.click(); },
  };
  const crudo = { color: datos.color, color_secundario: datos.color_secundario || SECUNDARIO_FABRICA, calcas: datos.calcas || [], estilo: datos.estilo || {} };
  moto.raiz.updateMatrixWorld(true);
  const inicial = { ...crudo, calcas: crudo.calcas.map(migrarCalca).filter(Boolean) };
  const personalizada = Promise.all([document.fonts ? document.fonts.ready : null, extras().catch(() => {})]).then(() => {
    medir("personalizacion", () => aplicarPersonalizacion(inicial));
    marcar("personalizado");
    // (los accesorios —baúl, parabrisas…— cambian el tamaño de la moto: la vitrina la vuelve a medir y encuadrar)
    if (vitrina) { medidaMoto = null; ajustarTamano(); }
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
    // Vitrina: encuadre normalizado por el tamaño real de cada modelo (todas las motos se ven del mismo tamaño).
    // Ancho: la diagonal horizontal de la moto (lo más ancha que se ve al girar) ocupa la fracción --encuadre del
    // lienzo; alto: la moto ocupa ≤70 % del alto. La cámara mira al
    // centro de la caja. La portada deja el lienzo más alto que la moto para que el cono y la sombra se desvanezcan.
    if (vitrina && w > 40 && h > 40) {
      const caja = tamanoMoto();
      const tan2 = 2 * Math.tan(THREE.MathUtils.degToRad(camara.fov / 2));
      // Qué parte del ancho del lienzo ocupa la diagonal de la moto: lo dice la portada (variable CSS --encuadre del
      // carrusel, distinta en escritorio, tablet y celular, porque el lienzo y su columna cambian)
      let celular = false, fraccion = 0.56;
      try {
        celular = window.parent.innerWidth < 768;
        const v = parseFloat(getComputedStyle(window.frameElement.closest(".portada-carrusel")).getPropertyValue("--encuadre"));
        if (v > 0 && v <= 1) fraccion = v;
      } catch { /* (portada de otro origen o vista suelta: fracción por defecto) */ }
      const d = Math.max(controles.minDistance, caja.diagonal / (fraccion * tan2 * camara.aspect), caja.alto / (0.7 * tan2));
      controles.maxDistance = Math.max(6, d);
      // Dirección de la cámara: el giro horizontal actual, pero siempre la misma inclinación de 3/4 (la de POS_INICIAL):
      // así nunca queda en un estado intermedio (mirando desde arriba) aunque el iframe cargue con otro tamaño
      const desde = camara.position.clone().sub(controles.target);
      const plano = Math.hypot(desde.x, desde.z) > 1e-3 ? V(desde.x, 0, desde.z).normalize() : V(POS_INICIAL.x, 0, POS_INICIAL.z).normalize();
      const inclinacion = Math.atan2(POS_INICIAL.y - 0.5, Math.hypot(POS_INICIAL.x, POS_INICIAL.z));
      desde.copy(plano.multiplyScalar(Math.cos(inclinacion))).setY(Math.sin(inclinacion));
      controles.target.copy(caja.centro);
      if (celular) controles.target.y -= 0.12; // (en el celular la moto va un poco más arriba: abajo se desvanecen el cono y la sombra)
      camara.position.copy(caja.centro).add(desde.setLength(d));
      encajarAlto(celular);
      controles.update();
    }
  }
  // Que quepa completa también a lo alto (manubrio y espejos de las enduro): con la caja real de cada pieza visible se
  // mira cómo queda al girar la cámara alrededor (12 ángulos). Si se sale, solo se aleja la cámara en su misma
  // dirección (mismo ángulo de 3/4 y mismo punto de mira), con tope: nunca se acerca ni cambia la altura de la vista.
  function encajarAlto(celular) {
    const puntos = tamanoMoto().puntos;
    if (!puntos?.length) return;
    const ARRIBA = 0.88, ABAJO = celular ? -0.8 : -0.95; // (en el celular el borde de abajo se desvanece)
    const cam = camara.clone(), eje = V(0, 1, 0), q = new THREE.Vector3(), centro = controles.target;
    const base = camara.position.clone().sub(centro);
    const cabe = (k) => {
      const rel = base.clone().multiplyScalar(k);
      for (let a = 0; a < 12; a++) {
        cam.position.copy(centro).add(rel.clone().applyAxisAngle(eje, (a * Math.PI) / 6));
        cam.lookAt(centro);
        cam.updateMatrixWorld(true);
        for (const p of puntos) {
          q.copy(p).project(cam);
          if (q.z > 1 || q.y > ARRIBA || q.y < ABAJO) return false; // (z > 1: detrás de la cámara)
        }
      }
      return true;
    };
    let k = 1;
    while (k < 1.6 && !cabe(k)) k += 0.04;
    if (k === 1) return;
    camara.position.copy(centro).add(base.multiplyScalar(k));
    controles.maxDistance = Math.max(controles.maxDistance, camara.position.distanceTo(centro));
  }
  // Tamaño de la moto para encuadrarla, medido una vez: por las ruedas (distancia entre ejes más los dos radios)
  // y los accesorios puestos, que no cambian con calcas ni animaciones; la caja de la carrocería pesaba distinto según el momento
  // (pata, suspensión, accesorios que llegan después). Diagonal: largo × 1,12 (manubrio y espejos al girar).
  let medidaMoto = null;
  function tamanoMoto() {
    if (medidaMoto) return medidaMoto;
    const raiz = moto.raiz, pos = raiz.position.clone(), giro = raiz.rotation.z;
    raiz.position.set(baseX, 0, 0); raiz.rotation.z = 0;
    raiz.updateMatrixWorld(true);
    const ruedas = (moto.ruedas || []).map((r) => ({ x: r.pivote.getWorldPosition(new THREE.Vector3()).x, R: r.R }));
    let largo, centroX, alto = 1.2;
    if (ruedas.length >= 2) {
      const del = ruedas.reduce((a, r) => (r.x > a.x ? r : a)), tras = ruedas.reduce((a, r) => (r.x < a.x ? r : a));
      let x0 = tras.x - tras.R, x1 = del.x + del.R;
      // Los accesorios puestos que sobresalen (baúl, parrilla…) también cuentan: si no, tapaban el texto al girar
      for (const g of Object.values(moto.accesorios || {})) {
        if (!g.visible) continue;
        const c = new THREE.Box3().setFromObject(g);
        if (!c.isEmpty()) { x0 = Math.min(x0, c.min.x); x1 = Math.max(x1, c.max.x); }
      }
      largo = x1 - x0;
      centroX = (x0 + x1) / 2;
    } else {
      const caja = new THREE.Box3().setFromObject(raiz), t = caja.getSize(new THREE.Vector3());
      largo = t.x; centroX = caja.getCenter(new THREE.Vector3()).x; alto = t.y;
    }
    // Caja real de lo que se ve (manubrio, espejos, accesorios puestos; sin la sombra de contacto, halos ni conos):
    // las esquinas de la caja de cada pieza (la caja total exageraba lo alto al girar), para que encajarAlto mire
    // que quepa a lo alto
    const puntos = [];
    raiz.traverseVisible((o) => {
      if (!o.isMesh || o.userData.calca || o.material?.visible === false || !o.geometry) return;
      if (!o.geometry.boundingBox) o.geometry.computeBoundingBox();
      const b = o.geometry.boundingBox;
      for (let i = 0; i < 8; i++) {
        const p = V(i & 1 ? b.max.x : b.min.x, i & 2 ? b.max.y : b.min.y, i & 4 ? b.max.z : b.min.z).applyMatrix4(o.matrixWorld);
        if (Number.isFinite(p.x + p.y + p.z)) puntos.push(p);
      }
    });
    raiz.position.copy(pos); raiz.rotation.z = giro;
    raiz.updateMatrixWorld(true);
    medidaMoto = { centro: new THREE.Vector3(centroX, 0.58, 0), diagonal: largo * 1.12, alto, puntos };
    return medidaMoto;
  }
  new ResizeObserver(ajustarTamano).observe(contenedor);
  ajustarTamano();

  medir("modo1", aplicarModo);
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

  // Une las mallas fijas por material (pieza por pieza): menos de la mitad de llamadas de dibujo por cuadro
  let paginaCerrada = false;
  // Precalentar los sombreadores: three.js lee los uniforms de cada programa la primera vez que dibuja con él, en
  // un solo bloque (compileAsync no lo cubre); con 15–20 programas eso congelaba un celular 1–3 s. Aquí se dibuja
  // en un solo píxel del lienzo (todavía escondido), de a pocos materiales por vez y soltando la página entre
  // tanda y tanda. (No a un render target: ahí three.js usa otros sombreadores, sin tone mapping.)
  async function precalentar() {
    const t0 = performance.now();
    const muestras = new Map();
    escena.traverseVisible((o) => {
      if ((o.isMesh || o.isSprite) && o.material && !Array.isArray(o.material)) {
        const clave = o.material.uuid + (o.isInstancedMesh ? "|i" : "");
        if (!muestras.has(clave)) muestras.set(clave, o);
      }
    });
    const guardado = [];
    escena.traverse((o) => { if (o.isMesh || o.isSprite) guardado.push([o, o.visible, o.frustumCulled]); });
    const lista = [...muestras.values()];
    const lienzo = renderer.domElement, visibilidad = lienzo.style.visibility;
    const tam = renderer.getSize(new THREE.Vector2());
    try {
      lienzo.style.visibility = "hidden";
      renderer.setScissorTest(true);
      renderer.setViewport(0, 0, 1, 1);
      renderer.setScissor(0, 0, 1, 1);
      for (const [o] of guardado) o.visible = false;
      for (let i = 0; i < lista.length; i += 3) {
        const tanda = lista.slice(i, i + 3);
        for (const o of tanda) {
          o.frustumCulled = false; // (en la portada la moto espera fuera de cuadro: igual hay que compilarla)
          for (let p = o; p && p !== escena; p = p.parent) if (p.isMesh || p.isSprite) p.visible = true;
        }
        renderer.render(escena, camara);
        for (const o of tanda) for (let p = o; p && p !== escena; p = p.parent) if (p.isMesh || p.isSprite) p.visible = false;
        await ceder();
        if (paginaCerrada) return;
      }
    } finally {
      for (const [o, v, f] of guardado) { o.visible = v; o.frustumCulled = f; }
      renderer.setScissorTest(false);
      renderer.setViewport(0, 0, tam.x, tam.y);
      lienzo.style.visibility = visibilidad;
      renderer.shadowMap.needsUpdate = true; // (la sombra se dibujó a pedazos: se rehace en el cuadro real)
    }
    ETAPAS.precalentar = (ETAPAS.precalentar || 0) + performance.now() - t0;
  }
  // Antes de unir, cada malla vuelve a su material original: si el modo inicial es Estado, varias llevan el mismo
  // fantasma translúcido y se habrían unido piezas de materiales distintos (luego, en modo Moto, quedaban
  // translúcidas o con el material de otra). Después de unir se vuelve a aplicar el modo.
  moto.raiz.traverse((o) => { if (o.isMesh && o.userData.original) o.material = o.userData.original; });
  const mallasUnidas = medir("unirEstaticas", () => unirEstaticas(moto.raiz, [...moto.ruedas.map((r) => r.pivote), moto.pata].filter(Boolean), !vitrina));
  medir("modo2", aplicarModo);
  marcar("unido");
  // Compila los sombreadores antes del primer cuadro, en paralelo y sin congelar la página (si no, el primer
  // cuadro se lleva de 0,4 a 1,3 s en un computador, y bastante más en un celular, con todo quieto).
  // Primer cuadro en dos tiempos: primero sin sombras (sombreadores más simples: la moto aparece antes) y las
  // sombras se compilan después en segundo plano. Mientras tanto se deja quieto el último cuadro (sin tirones).
  // En celulares y equipos modestos (calidad baja) no hay sombras proyectadas: basta la sombra de contacto bajo
  // la moto. Ahí los reflejos se generan de una, antes del primer cuadro: una sola etapa y un solo juego de
  // sombreadores (cambiar sombras o reflejos después obliga a rehacerlos todos, y eso traba un celular).
  const unaEtapa = CALIDAD.nombre === "baja";
  renderer.shadowMap.enabled = false;
  if (unaEtapa) {
    suelo.visible = false;
    try { await extras(); generarReflejos(); } catch { /* sin reflejos de estudio: queda la luz de relleno */ }
    pintarVivo(transicion.k);
  }
  // Boceto en la ficha: compilar los sombreadores reales tarda ~0,6 s en un computador (varios segundos en un
  // celular). Mientras tanto se muestra un cuadro hecho con materiales simples (un solo sombreador Lambert, con el
  // color de cada pieza), congelado como imagen sobre el lienzo, hasta que llega el primer cuadro real.
  let boceto = null, bocetoPendiente = null;
  if (!vitrina && enPantalla && !document.hidden) {
    const simples = new Map(), cambiados = [];
    escena.traverseVisible((o) => {
      if (!o.isMesh || !o.material || Array.isArray(o.material) || o.material.visible === false) return;
      const m = o.material;
      // Lo que solo existe por su textura o su sombra (sombra de contacto, calcas, halos, el piso de sombras) sin ella
      // quedaba como un rectángulo o un disco liso: en el boceto no se dibuja
      if (m.isShadowMaterial || (m.map && m.transparent) || m.isSpriteMaterial) {
        if (!simples.has(m)) simples.set(m, new THREE.MeshBasicMaterial({ visible: false }));
        cambiados.push([o, m]);
        o.material = simples.get(m);
        return;
      }
      if (!simples.has(m)) simples.set(m, new THREE.MeshLambertMaterial({ color: m.color ?? 0x8a8f94, transparent: m.transparent, opacity: m.opacity, side: m.side, depthWrite: m.depthWrite }));
      cambiados.push([o, m]);
      o.material = simples.get(m);
    });
    try {
      renderer.render(escena, camara);
      boceto = document.createElement("canvas");
      boceto.width = renderer.domElement.width;
      boceto.height = renderer.domElement.height;
      boceto.getContext("2d").drawImage(renderer.domElement, 0, 0);
      boceto.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none";
      renderer.domElement.after(boceto);
      cargando?.remove();
    } catch { boceto = null; }
    for (const [o, m] of cambiados) o.material = m;
    for (const s of simples.values()) s.dispose();
    marcar("boceto");
  }
  // Los colores y calcas guardados cambian materiales (texturas, calcas nuevas): se aplican antes de compilar, para
  // que compileAsync cubra todas las variantes y nada corra ni dibuje mientras la tarjeta gráfica compila (si no,
  // las variantes que faltaban se compilaban de golpe al dibujar y la espera de GPU se volvía síncrona).
  await Promise.race([personalizada, new Promise((r) => setTimeout(r, 3000))]);
  try { await renderer.compileAsync(escena, camara); } catch { /* sin compilación previa: se compila al dibujar */ }
  marcar("compilaAsync");
  if (paginaCerrada) return; // (se salió de la página mientras compilaba: el contexto ya se liberó)
  await precalentar();
  if (paginaCerrada) return;
  marcar("compilado");
  const reloj = new THREE.Clock();
  const limite30 = vitrina && CALIDAD.nombre === "baja";
  let ultimoCuadro = -1;
  const sombras = { estado: unaEtapa ? "listas" : "pendiente", desde: 0 }; // pendiente → compilando → listas
  // Al pasar a la etapa con sombras cada material compila su variante nueva y la de la primera etapa queda guardada
  // sin uso (en la GPU y en la cuenta de programas). Ya dibujado un cuadro con sombras, se sueltan esas viejas:
  // solo las que tienen reemplazo y no son las que el material usa ahora (las de piezas ocultas se quedan).
  function soltarProgramasViejos(viejos) {
    try {
      const lista = renderer.info.programs;
      escena.traverse((o) => {
        for (const m of [].concat(o.material || [])) {
          const p = renderer.properties.get(m);
          if (!p.programs || p.programs.size < 2) continue;
          for (const [clave, prog] of p.programs) {
            if (!viejos.has(prog) || prog === p.currentProgram) continue;
            p.programs.delete(clave);
            if (--prog.usedTimes === 0) { const i = lista.indexOf(prog); if (i >= 0) { lista[i] = lista[lista.length - 1]; lista.pop(); } prog.destroy(); }
          }
        }
      });
    } catch { /* si cambia algo interno de three, se quedan como estaban */ }
  }
  async function activarSombras() {
    sombras.estado = "compilando";
    const viejos = new Set(renderer.info.programs);
    try { await extras(); generarReflejos(); } catch { /* sin reflejos de estudio: queda la luz de relleno */ }
    // (la luz de relleno no se quita: se apaga de a poco; quitarla cambiaría otra vez los sombreadores)
    fundido.reflejo = 0;
    pintarVivo(transicion.k);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.needsUpdate = true;
    try { await renderer.compileAsync(escena, camara); } catch { /* se compilan al dibujar */ }
    if (paginaCerrada) return;
    sombras.estado = "listas";
    marcar("sombras");
    requestAnimationFrame(() => requestAnimationFrame(() => { if (!paginaCerrada) soltarProgramasViejos(viejos); }));
    fundido.t0 = performance.now();
    // En la portada la moto todavía no había entrado (esperaba fuera de cuadro): la entrada arranca ahora
    if (vitrina && anim.fase === "entrar") anim.t0 = performance.now();
    pedirCuadro();
  }
  renderer.setAnimationLoop(() => {
    if (!enPantalla || document.hidden) return;
    if (sombras.estado === "compilando") return;
    // Reflejos y sombras: un momento después del primer cuadro. En la portada, de una (la moto aún está fuera de
    // cuadro, esperando para entrar); en la ficha, si no hay una animación en curso.
    if (sombras.estado === "pendiente" && sombras.desde && (vitrina || (performance.now() - sombras.desde > 250 && !anim.fase))) { activarSombras(); return; }
    if (sombras.estado === "listas" && fundido.reflejo < 1) {
      fundido.reflejo = reducido ? 1 : Math.min(1, (performance.now() - fundido.t0) / 300);
      pintarVivo(transicion.k);
      necesitaCuadro = true;
    }
    controles.update();
    if (pasoAnimacion()) necesitaCuadro = true;
    const t = reloj.getElapsedTime();
    if (pasoVivo(t)) necesitaCuadro = true;
    const latiendo = pulsando.length > 0 && modo !== "moto" && !reducido;
    if (modo !== "moto") for (const obj of pulsando) {
      obj.material.emissiveIntensity = 0.35 + (reducido ? 0.3 : 0.3 * (1 + Math.sin(t * 4)));
    }
    if (!necesitaCuadro && !latiendo) return;
    // En la portada, en celulares, a 30 cuadros por segundo basta para el giro (la mitad de trabajo y de batería)
    if (limite30 && t - ultimoCuadro < 1 / 31) return;
    ultimoCuadro = t;
    necesitaCuadro = false;
    renderer.render(escena, camara);
    marcar("primerCuadro");
    sombras.desde ||= performance.now();
    if (bocetoPendiente) { const b = bocetoPendiente; bocetoPendiente = null; requestAnimationFrame(() => b.remove()); }
  });
  // Primer cuadro en este mismo momento, sin esperar al siguiente refresco de la pantalla
  if (enPantalla && !document.hidden) {
    pasoAnimacion(); // (en la portada, la moto ya en su punto de partida de la entrada)
    extras(); // (ya con la moto en pantalla, se piden los complementos de reflejos y calcas)
    renderer.render(escena, camara);
    marcar("primerCuadro");
    sombras.desde = performance.now();
    necesitaCuadro = false;
  }
  // (el cuadro real ya se dibujó: se quita el boceto en el próximo refresco, para que no parpadee)
  // Si no se pudo dibujar (pestaña oculta o fuera de vista), el boceto se quita cuando el bucle dibuje el primero:
  // así nunca queda a la vista el lienzo con el render del boceto.
  if (boceto) {
    if (TIEMPOS.primerCuadro) requestAnimationFrame(() => boceto.remove());
    else { bocetoPendiente = boceto; pedirCuadro(); }
  }
  // Las aristas de Rayos X, en cuanto la página quede libre
  const conAristas = () => { if (paginaCerrada) return; bordes.listos = true; aplicarModo(); pedirCuadro(); };
  if (window.requestIdleCallback) requestIdleCallback(conAristas, { timeout: 600 }); else setTimeout(conAristas, 200);
  cargando?.remove();
  document.getElementById("visor-ayuda").hidden = false;
  window.__moto3dListo = true;
  marcar("listo");
  // Al salir de la página se libera la memoria de la tarjeta gráfica (geometrías, materiales, texturas y el
  // contexto WebGL). Si el navegador la guarda para volver con "atrás" (persisted), se deja intacta.
  addEventListener("pagehide", (evento) => {
    if (evento.persisted) return;
    paginaCerrada = true;
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
    // Depuración: cajas de los accesorios y del asiento (para revisar que no se crucen)
    _moto: moto, _esc: escena, _ren: renderer, _cam: camara, _ctl: controles,
    fabrica: () => ({ lista: (fabrica.lista || []).map((c) => c.id), regiones: fabrica.regiones, vertices: fabrica.malla?.geometry.attributes.position.count || 0, visible: Boolean(fabrica.malla?.visible) }),
    _medida: () => medidaMoto, _reencuadrar: () => { medidaMoto = null; ajustarTamano(); return medidaMoto; },
    // Depuración: estado de las sombras diferidas (y forzarlas, p. ej. en una pestaña sin cuadros)
    sombras: async (forzar = false) => { if (forzar && sombras.estado === "pendiente") await activarSombras(); return sombras.estado; },
    cajas: () => {
      const r = (b) => [b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z].map((n) => Math.round(n * 1000) / 1000);
      const salida = {};
      for (const [id, g] of Object.entries(moto.accesorios)) salida[id] = r(new THREE.Box3().setFromObject(g));
      const asiento = new THREE.Box3();
      moto.raiz.traverse((o) => { if (o.isMesh && o.material === moto.M.asiento) asiento.union(new THREE.Box3().setFromObject(o)); });
      salida.asiento = r(asiento);
      return salida;
    },
    cuadro: () => { pasoTransicion(); const t = performance.now(); renderer.render(escena, camara); renderer.getContext().finish(); return Math.round(performance.now() - t); },
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
      // (solo lo que se dibuja: visible y con material visible; las originales agrupadas no cuentan)
      escena.traverseVisible((o) => {
        if ((o.isMesh || o.isInstancedMesh) && o.material?.visible !== false) {
          mallas++;
          const g = o.geometry;
          triangulos += (g.index ? g.index.count : g.attributes.position.count) / 3 * (o.count || 1);
        }
      });
      return { tiempos: TIEMPOS, msGuardarCache: cachePaneles.msGuardar, mallasUnidas, msArmado, etapas: Object.fromEntries(Object.entries(ETAPAS).map(([k, v]) => [k, Math.round(v)])), calidad: CALIDAD.nombre, panelesDeCache: cachePaneles.aciertos, pedazoMasLargo: Math.round(pedazos.max), panelesGuardados: Object.keys(cachePaneles.guardados).length, mallas, triangulos: Math.round(triangulos), llamadas: renderer.info.render.calls,
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
