// Modelo 3D de la moto del usuario, armado a partir de la ficha técnica de su línea.
// Cada pieza de mantenimiento es un grupo con userData.pieza para colorearla y seleccionarla.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
import { DecalGeometry } from "three/addons/geometries/DecalGeometry.js";
import { mergeGeometries, mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";

const ESTADO_COLOR = { ok: 0x3fbf6b, pronto: 0xe3a72f, vencido: 0xff5a3c, desconocido: 0x8a9096 };
const ETIQUETA = { ok: "Al día", pronto: "Pronto", vencido: "Toca ya", desconocido: "Sin registro" };
const V = (x, y, z = 0) => new THREE.Vector3(x, y, z);

const contenedor = document.getElementById("visor");
const datos = JSON.parse(document.getElementById("datos-moto").textContent);
const ficha = document.getElementById("visor-ficha");
const cargando = document.getElementById("visor-cargando");

function avisar(texto) {
  if (cargando) cargando.textContent = texto;
}

try {
  iniciar();
} catch (error) {
  console.error(error);
  avisar("Tu navegador no pudo mostrar el modelo 3D. El plan de mantenimiento sigue disponible abajo.");
}

function iniciar() {
  const prueba = document.createElement("canvas");
  if (!(prueba.getContext("webgl2") || prueba.getContext("webgl"))) {
    avisar("Tu navegador no soporta gráficos 3D. El plan de mantenimiento sigue disponible abajo.");
    return;
  }

  // ---------- Escena ----------
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  // Hasta 1,75× en pantallas de alta densidad: casi igual de nítido y bastante menos trabajo para la tarjeta gráfica.
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.75));
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
  escena.add(new THREE.HemisphereLight(0xf4ead2, 0x1b2a28, 0.45));
  const sol = new THREE.DirectionalLight(0xfff6ea, 2.4);
  sol.position.set(2.5, 4, 3);
  sol.castShadow = true;
  sol.shadow.mapSize.set(1024, 1024); // con el difuminado suave, 1024 se ve igual que 2048 y pesa la cuarta parte
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

  const t0Armado = performance.now();
  const moto = construirMoto(datos.specs, datos.color, datos.linea || "");
  const msArmado = Math.round(performance.now() - t0Armado);
  escena.add(moto.raiz);
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
      obj.visible = !interno || modo === "rayos";
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
        if (!obj.userData.borde) {
          const borde = new THREE.LineSegments(new THREE.EdgesGeometry(obj.geometry, 28), matBorde);
          obj.add(borde);
          obj.userData.borde = borde;
        }
        obj.userData.borde.visible = true;
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
  const ANCHO_BASE = { numero: 0.16, tallerya: 0.3, texto: 0.32, franjas: 0.38, cuadros: 0.34, llamas: 0.36, rayo: 0.32 };
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
    const claveTextura = `${c.diseno}|${c.color}|${c.texto || ""}`;
    const claveForma = `${c.diseno}|${c.punto}|${c.normal}|${c.tamano}|${c.giro}|${c.ambos}|${c.texto || ""}`;
    if (e.claveTextura !== claveTextura) {
      const { textura, aspecto } = texturaCalca(c.diseno, c.color, c.texto);
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

  function aplicarPersonalizacion(cfg) {
    moto.M.pintura.color.set(cfg.color);
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

  window.TallerYa3D = {
    aplicar: aplicarPersonalizacion,
    miniatura,
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
    verMoto() { document.querySelector('#visor .visor-modo [data-modo="moto"]')?.click(); },
  };
  const crudo = { color: datos.color, color_secundario: datos.color_secundario || "#1c2022", calcas: datos.calcas || [] };
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

  const reloj = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    if (!enPantalla || document.hidden) return;
    controles.update();
    if (pasoAnimacion()) necesitaCuadro = true;
    const t = reloj.getElapsedTime();
    const latiendo = pulsando.length > 0 && modo !== "moto" && !reducido;
    if (modo !== "moto") for (const obj of pulsando) {
      obj.material.emissiveIntensity = 0.35 + (reducido ? 0.3 : 0.3 * (1 + Math.sin(t * 4)));
    }
    if (!necesitaCuadro && !latiendo) return;
    necesitaCuadro = false;
    renderer.render(escena, camara);
  });
  cargando?.remove();
  document.getElementById("visor-ayuda").hidden = false;
  window.__moto3dListo = true;
  // Para revisar el modelo desde la consola: __visor.vista(x, y, z)
  window.__visor = {
    vista: (x, y, z) => { controles.autoRotate = false; camara.position.set(x, y, z); controles.update(); },
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
      return { msArmado, mallas, triangulos: Math.round(triangulos), llamadas: renderer.info.render.calls,
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

// =====================================================================
// Construcción procedural
// =====================================================================
function construirMoto(specs, colorPintura, linea = "") {
  const esNmax = /nmax/i.test(linea);
  const raiz = new THREE.Group();
  const tipo = specs.tipo;
  const scooter = tipo === "scooter";

  // ----- Materiales -----
  const M = {
    // Pintura con capa de laca (clearcoat), como la de fábrica
    pintura: new THREE.MeshPhysicalMaterial({ color: colorPintura, metalness: 0.45, roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.06 }),
    oscuro: new THREE.MeshStandardMaterial({ color: 0x1c2022, roughness: 0.6, metalness: 0.25 }),
    chasis: new THREE.MeshPhysicalMaterial({ color: 0x23282b, roughness: 0.42, metalness: 0.6, clearcoat: 0.5, clearcoatRoughness: 0.3 }),
    metal: new THREE.MeshStandardMaterial({ color: 0xc4c9cc, roughness: 0.22, metalness: 0.95 }),
    cromo: new THREE.MeshStandardMaterial({ color: 0xf2f4f5, roughness: 0.05, metalness: 1 }),
    motor: new THREE.MeshStandardMaterial({ color: 0x9ea5a9, roughness: 0.38, metalness: 0.85 }),
    carter: new THREE.MeshStandardMaterial({ color: 0x70777b, roughness: 0.45, metalness: 0.8 }),
    caucho: new THREE.MeshStandardMaterial({ color: 0x181818, roughness: 0.88, metalness: 0 }),
    labrado: new THREE.MeshStandardMaterial({ color: 0x141414, roughness: 0.95, metalness: 0 }),
    pantalla: new THREE.MeshStandardMaterial({ color: 0x0f1a1c, emissive: 0x4fd1c5, emissiveIntensity: 0.35, roughness: 0.15 }),
    rin: new THREE.MeshPhysicalMaterial({ color: 0x2b3033, roughness: 0.3, metalness: 0.7, clearcoat: 0.8, clearcoatRoughness: 0.15 }),
    asiento: new THREE.MeshPhysicalMaterial({ color: 0x161819, roughness: 0.7, sheen: 0.6, sheenRoughness: 0.5, sheenColor: 0x555a5c }),
    rojo: new THREE.MeshPhysicalMaterial({ color: 0xb8321f, roughness: 0.3, metalness: 0.4, clearcoat: 0.7 }),
    resorte: new THREE.MeshPhysicalMaterial({ color: tipo === "sport" ? 0xe3a72f : 0xc0392b, roughness: 0.3, metalness: 0.3, clearcoat: 0.8 }),
    luz: new THREE.MeshStandardMaterial({ color: 0xfff6d8, emissive: 0xfff1c4, emissiveIntensity: 1.1, roughness: 0.1 }),
    stop: new THREE.MeshStandardMaterial({ color: 0xff3b2f, emissive: 0xff2a1f, emissiveIntensity: 0.7, roughness: 0.2 }),
    vidrio: new THREE.MeshPhysicalMaterial({ color: 0xa9bec7, transparent: true, opacity: 0.32, roughness: 0.02, metalness: 0, clearcoat: 1 }),
    radiador: new THREE.MeshStandardMaterial({ color: 0x2a2f31, roughness: 0.55, metalness: 0.7 }),
    bateria: new THREE.MeshStandardMaterial({ color: 0x222628, roughness: 0.6 }),
    bujia: new THREE.MeshStandardMaterial({ color: 0xf1ede4, roughness: 0.25 }),
    aceiteVisible: new THREE.MeshStandardMaterial({ color: 0xd99a1e, transparent: true, opacity: 0.8, roughness: 0.15 }),
    placa: new THREE.MeshStandardMaterial({ color: 0xf2c230, roughness: 0.45 }),
    tablero: new THREE.MeshPhysicalMaterial({ color: 0x0d1012, roughness: 0.1, metalness: 0.2, clearcoat: 1 }),
  };

  // ----- Utilidades de geometría -----
  const piezas = {};
  function grupo(nombre) {
    if (!piezas[nombre]) {
      const g = new THREE.Group();
      g.userData.pieza = nombre;
      raiz.add(g);
      piezas[nombre] = g;
    }
    return piezas[nombre];
  }
  const decor = new THREE.Group();
  raiz.add(decor);

  function zona(m, ...nombres) {
    m.userData.zonas = nombres; // dónde se pueden proyectar calcas
    return m;
  }
  function malla(geo, mat, padre = decor) {
    const m = new THREE.Mesh(geo, mat);
    m.castShadow = true;
    padre.add(m);
    return m;
  }
  function caja(w, h, d, mat, pos, padre, rotZ = 0) {
    const m = malla(new THREE.BoxGeometry(w, h, d), mat, padre);
    m.position.copy(pos);
    m.rotation.z = rotZ;
    return m;
  }
  function tubo(a, b, r, mat, padre, seg = 20) {
    const dir = new THREE.Vector3().subVectors(b, a);
    const m = malla(new THREE.CylinderGeometry(r, r, dir.length(), seg), mat, padre);
    m.position.copy(a).add(b).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
    return m;
  }
  function disco(radio, grosor, mat, pos, padre, seg = 48) {
    const m = malla(new THREE.CylinderGeometry(radio, radio, grosor, seg), mat, padre);
    m.rotation.x = Math.PI / 2;
    m.position.copy(pos);
    return m;
  }
  function perfil(puntos, ancho, mat, padre, z = 0, bisel = 0.014, suave = false, curvas = 28, biselSeg = 6) {
    const vec = puntos.map(([x, y]) => new THREE.Vector2(x, y));
    let forma;
    if (suave) {
      // Contorno curvo que pasa por los puntos: carrocería redondeada.
      forma = new THREE.Shape();
      forma.moveTo(vec[0].x, vec[0].y);
      forma.splineThru([...vec.slice(1), vec[0]]);
    } else {
      forma = new THREE.Shape(vec);
    }
    const geo = new THREE.ExtrudeGeometry(forma, {
      depth: ancho, bevelEnabled: bisel > 0, bevelSize: bisel, bevelThickness: bisel, bevelSegments: biselSeg, curveSegments: curvas,
    });
    geo.translate(0, 0, -ancho / 2 + z);
    if (suave) {
      // Piezas curvas (aletas, franjas, colines…): normales suavizadas para que se vean lisas, sin facetas
      // ni aristas duras entre la cara y el bisel. Cuesta muy poco (no agrega triángulos).
      let lisa = geo.index ? geo.toNonIndexed() : geo.clone();
      lisa.deleteAttribute("uv");
      lisa.deleteAttribute("normal");
      lisa = mergeVertices(lisa, 1e-5);
      lisa.computeVertexNormals();
      geo.dispose();
      return malla(lisa, mat, padre);
    }
    return malla(geo, mat, padre);
  }
  function elipsoide(rx, ry, rz, mat, pos, padre) {
    const m = malla(new THREE.SphereGeometry(1, 28, 18), mat, padre);
    m.scale.set(rx, ry, rz);
    m.position.copy(pos);
    return m;
  }
  function interno(m) {
    m.userData.interno = true; // solo se ve en modo Rayos X
    return m;
  }
  function resorte(a, b, radio, vueltas, mat, padre) {
    const dir = new THREE.Vector3().subVectors(b, a);
    const largo = dir.length();
    const puntos = [];
    for (let i = 0; i <= vueltas * 16; i++) {
      const t = i / (vueltas * 16);
      const ang = t * vueltas * Math.PI * 2;
      puntos.push(V(Math.cos(ang) * radio, t * largo, Math.sin(ang) * radio));
    }
    const geo = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(puntos), vueltas * 16, radio * 0.16, 6);
    const m = malla(geo, mat, padre);
    m.position.copy(a);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
    return m;
  }

  // ----- Dimensiones según la ficha -----
  const s = THREE.MathUtils.clamp(Math.cbrt(specs.cilindraje / 150), 0.78, 1.45); // escala del motor
  const perfilLlanta = { scooter: 0.065, semi: 0.07, calle: 0.075, sport: 0.07, enduro: 0.085 }[tipo];
  const Rf = specs.rin_delantero * 0.0127 + perfilLlanta;
  const Rr = specs.rin_trasero * 0.0127 + perfilLlanta;
  const anchoF = { scooter: 0.11, semi: 0.075, calle: 0.095, sport: 0.115, enduro: 0.085 }[tipo] * (0.9 + 0.1 * s);
  const anchoR = { scooter: 0.13, semi: 0.085, calle: 0.12, sport: 0.155, enduro: 0.105 }[tipo] * (0.9 + 0.15 * s);
  const wb = { scooter: 1.34, semi: 1.22, calle: 1.3, sport: 1.36, enduro: 1.4 }[tipo] + (s - 1) * 0.08;
  const xF = wb / 2;
  const xR = -wb / 2;
  const rake = THREE.MathUtils.degToRad({ scooter: 27, semi: 26, calle: 25, sport: 24, enduro: 27 }[tipo]);
  const largoBarra = { scooter: 0.66, semi: 0.7, calle: 0.76, sport: 0.72, enduro: 0.98 }[tipo];
  const H = V(xF - largoBarra * Math.sin(rake), Rf + largoBarra * Math.cos(rake)); // pipa de dirección
  const alturaAsiento = { scooter: 0.76, semi: 0.74, calle: 0.8, sport: 0.82, enduro: 0.92 }[tipo];
  const despeje = tipo === "enduro" ? 0.1 : 0;
  const P = V(xR + wb * (scooter ? 0.42 : 0.44), Rr + 0.07 + despeje); // pivote del basculante

  // ----- Llantas y frenos -----
  function llanta(x, R, ancho, rin, idLlanta, idFreno, tipoFreno, radios) {
    const g = grupo(idLlanta);
    const centro = V(x, R);
    const rinR = rin * 0.0127;
    // Perfil de la llanta: hombros redondeados como una llanta real (no un aro)
    const h = R - rinR;
    const contornoLlanta = [
      [rinR - 0.004, -ancho * 0.36], [rinR + h * 0.18, -ancho * 0.5], [rinR + h * 0.55, -ancho * 0.52],
      [R - h * 0.16, -ancho * 0.44], [R - h * 0.02, -ancho * 0.26], [R, 0], [R - h * 0.02, ancho * 0.26],
      [R - h * 0.16, ancho * 0.44], [rinR + h * 0.55, ancho * 0.52], [rinR + h * 0.18, ancho * 0.5], [rinR - 0.004, ancho * 0.36],
    ].map(([r, y]) => new THREE.Vector2(r, y));
    const geoLlanta = new THREE.LatheGeometry(contornoLlanta, 72);
    geoLlanta.rotateX(Math.PI / 2);
    const neumatico = malla(geoLlanta, M.caucho, g);
    neumatico.position.copy(centro);
    // Rin con canal (pestañas a los lados)
    const perfilRin = [
      [rinR - 0.02, -ancho * 0.4], [rinR + 0.006, -ancho * 0.42], [rinR + 0.004, -ancho * 0.3], [rinR - 0.012, -ancho * 0.12],
      [rinR - 0.012, ancho * 0.12], [rinR + 0.004, ancho * 0.3], [rinR + 0.006, ancho * 0.42], [rinR - 0.02, ancho * 0.4],
    ].map(([r, y]) => new THREE.Vector2(r, y));
    const geoRin = new THREE.LatheGeometry(perfilRin, 72);
    geoRin.rotateX(Math.PI / 2);
    const aro = malla(geoRin, radios ? M.metal : M.rin, g);
    aro.position.copy(centro);
    const taco = tipo === "enduro" ? [0.016, 0.012, ancho * 0.34] : [0.01, 0.004, ancho * 0.22];
    const nTacos = tipo === "enduro" ? 40 : 56;
    const geoTaco = new THREE.BoxGeometry(...taco);
    const labrado = new THREE.InstancedMesh(geoTaco, M.labrado, nTacos * 2);
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
    for (let i = 0; i < nTacos * 2; i++) {
      const lado = i % 2 ? 1 : -1;
      const a = (Math.floor(i / 2) / nTacos) * Math.PI * 2 + (lado > 0 ? Math.PI / nTacos : 0);
      e.set(0, lado * 0.35, a + Math.PI / 2);
      q.setFromEuler(e);
      m4.compose(V(x + Math.cos(a) * (R - taco[1] * 0.2), R + Math.sin(a) * (R - taco[1] * 0.2), lado * ancho * 0.16), q, V(1, 1, 1));
      labrado.setMatrixAt(i, m4);
    }
    labrado.castShadow = true;
    g.add(labrado);
    disco(0.045, ancho * 0.9, M.metal, centro, g, 16);
    if (radios) {
      for (let i = 0; i < 18; i++) {
        const a = (i / 18) * Math.PI * 2;
        const lado = i % 2 ? 1 : -1;
        tubo(V(x, R, lado * ancho * 0.3), V(x + Math.cos(a) * rinR, R + Math.sin(a) * rinR, lado * 0.01), 0.0035, M.cromo, g, 5);
      }
    } else {
      // Rin de aleación: maza robusta y 5 radios dobles curvos (como los rines de fábrica)
      disco(rinR * 0.3, ancho * 0.72, M.rin, centro, g, 28);
      for (let i = 0; i < 5; i++) {
        const a = (i / 5) * Math.PI * 2 + 0.3;
        for (const d of [-1, 1]) {
          const curva = new THREE.QuadraticBezierCurve3(
            V(x + Math.cos(a) * rinR * 0.26, R + Math.sin(a) * rinR * 0.26, 0),
            V(x + Math.cos(a + d * 0.16) * rinR * 0.62, R + Math.sin(a + d * 0.16) * rinR * 0.62, 0),
            V(x + Math.cos(a + d * 0.24) * rinR * 0.96, R + Math.sin(a + d * 0.24) * rinR * 0.96, 0),
          );
          const radio = malla(new THREE.TubeGeometry(curva, 14, 0.009, 8), M.rin, g);
          radio.scale.z = 1.8; // radio ovalado: más ancho que grueso
        }
      }
      // Tuercas de la maza
      for (let i = 0; i < 5; i++) {
        const a = (i / 5) * Math.PI * 2;
        disco(0.006, ancho * 0.76, M.metal, V(x + Math.cos(a) * rinR * 0.18, R + Math.sin(a) * rinR * 0.18), g, 6);
      }
    }
    // Freno (al lado izquierdo, +z)
    const f = grupo(idFreno);
    const zFreno = ancho * 0.55 + 0.02;
    if (tipoFreno === "disco") {
      const radioDisco = Math.min(rinR * 0.85, idFreno === "freno_del" ? 0.15 : 0.115);
      // Disco tipo pétalo: borde ondulado y anillo de perforaciones
      const petalo = new THREE.Shape();
      for (let i = 0; i <= 96; i++) {
        const t = (i / 96) * Math.PI * 2;
        const r = radioDisco * (1 - 0.035 * (0.5 + 0.5 * Math.cos(t * 12)));
        if (i === 0) petalo.moveTo(Math.cos(t) * r, Math.sin(t) * r); else petalo.lineTo(Math.cos(t) * r, Math.sin(t) * r);
      }
      const hueco = new THREE.Path();
      hueco.absarc(0, 0, radioDisco * 0.58, 0, Math.PI * 2, true);
      petalo.holes.push(hueco);
      const geoDisco = new THREE.ExtrudeGeometry(petalo, { depth: 0.005, bevelEnabled: false, curveSegments: 32 });
      geoDisco.translate(0, 0, -0.0025);
      malla(geoDisco, M.metal, f).position.set(x, R, zFreno);
      for (let i = 0; i < 18; i++) {
        const t = (i / 18) * Math.PI * 2;
        disco(0.0055, 0.007, M.oscuro, V(x + Math.cos(t) * radioDisco * 0.8, R + Math.sin(t) * radioDisco * 0.8, zFreno), f, 8);
      }
      // Porta disco con 5 brazos
      disco(radioDisco * 0.3, 0.01, M.oscuro, V(x, R, zFreno), f, 20);
      for (let i = 0; i < 5; i++) {
        const t = (i / 5) * Math.PI * 2 + 0.6;
        caja(radioDisco * 0.34, 0.016, 0.008, M.oscuro, V(x + Math.cos(t) * radioDisco * 0.42, R + Math.sin(t) * radioDisco * 0.42, zFreno), f, t);
      }
      const ang = idFreno === "freno_del" ? 2.3 : 1.2;
      const posCaliper = V(x + Math.cos(ang) * radioDisco * 0.86, R + Math.sin(ang) * radioDisco * 0.86, zFreno + 0.01);
      // Caliper de cuerpo redondeado, con soporte y purgador
      const cuerpo = perfil([[-0.042, -0.018], [-0.03, 0.026], [0.03, 0.026], [0.042, -0.018], [0, -0.03]], 0.034, M.rojo, f, 0, 0.008, true);
      cuerpo.position.copy(posCaliper);
      cuerpo.rotation.z = ang - Math.PI / 2;
      const soporte = caja(0.05, 0.02, 0.008, M.oscuro, posCaliper.clone().add(V(Math.cos(ang) * 0.03, Math.sin(ang) * 0.03, -0.022)), f, ang);
      soporte.userData.base = true;
      tubo(posCaliper.clone().add(V(Math.cos(ang) * 0.03, Math.sin(ang) * 0.03, 0.012)),
        posCaliper.clone().add(V(Math.cos(ang) * 0.045, Math.sin(ang) * 0.045, 0.018)), 0.003, M.metal, f, 6);
      for (const dz of [-0.012, 0.014]) interno(caja(0.055, 0.035, 0.008, M.oscuro, posCaliper.clone().add(V(0, 0, dz)), f, ang));
    } else {
      disco(Math.min(rinR * 0.5, 0.085), 0.05, M.motor, V(x, R, zFreno - 0.01), f, 28);
      for (const sentido of [1, -1]) {
        const banda = interno(malla(new THREE.TorusGeometry(Math.min(rinR * 0.42, 0.072), 0.008, 6, 16, Math.PI * 0.8), M.oscuro, f));
        banda.position.set(x, R, zFreno - 0.01);
        banda.rotation.z = sentido > 0 ? 0.15 : Math.PI + 0.15;
      }
      tubo(V(x, R + 0.04, zFreno + 0.02), V(x - 0.08, R + 0.08, zFreno + 0.02), 0.008, M.oscuro, f);
    }
    return centro;
  }
  const radios = tipo === "enduro" || tipo === "semi" || (specs.freno_delantero === "tambor" && tipo !== "scooter");
  const centroDel = llanta(xF, Rf, anchoF, specs.rin_delantero, "llanta_del", "freno_del", specs.freno_delantero, radios);
  const centroTras = llanta(xR, Rr, anchoR, specs.rin_trasero, "llanta_tras", "freno_tras", specs.freno_trasero, radios);

  // ----- Suspensión delantera -----
  const susDel = grupo("suspension_del");
  const zBarra = anchoF / 2 + 0.045;
  for (const lado of [1, -1]) {
    const eje = V(xF, Rf, lado * zBarra);
    const pipa = V(H.x, H.y, lado * zBarra);
    const medio = eje.clone().lerp(pipa, 0.55);
    const rBotella = tipo === "enduro" ? 0.028 : 0.022;
    const dirBarra = new THREE.Vector3().subVectors(pipa, eje).normalize();
    tubo(eje.clone().add(dirBarra.clone().multiplyScalar(-0.03)), medio, rBotella, tipo === "sport" ? M.oscuro : M.metal, susDel);
    tubo(medio, pipa, tipo === "enduro" ? 0.022 : 0.017, M.cromo, susDel);
    // Retén con guardapolvo, tapa de la barra y punta donde se sujeta el eje
    tubo(medio, medio.clone().add(dirBarra.clone().multiplyScalar(0.025)), rBotella * 1.08, M.caucho, susDel, 20);
    tubo(pipa.clone().add(dirBarra.clone().multiplyScalar(0.005)), pipa.clone().add(dirBarra.clone().multiplyScalar(0.03)), rBotella * 0.85, M.oscuro, susDel, 6);
    caja(0.055, 0.03, 0.034, tipo === "sport" ? M.oscuro : M.metal, eje.clone().add(dirBarra.clone().multiplyScalar(-0.025)), susDel, rake);
  }
  // Tuerca del eje delantero
  disco(0.014, zBarra * 2 + 0.04, M.metal, V(xF, Rf, 0), susDel, 6);
  caja(0.06, 0.03, zBarra * 2 + 0.05, M.oscuro, V(H.x, H.y, 0), susDel);
  caja(0.06, 0.03, zBarra * 2 + 0.05, M.oscuro, V(H.x + 0.06 * Math.sin(rake), H.y - 0.14, 0), susDel);

  // ----- Manubrio, luces y espejos -----
  const altoManubrio = tipo === "sport" ? 0.02 : tipo === "enduro" ? 0.12 : 0.08;
  const anchoManubrio = tipo === "enduro" ? 0.4 : tipo === "sport" ? 0.3 : 0.34;
  const M1 = V(H.x - 0.05, H.y + altoManubrio, anchoManubrio);
  const M2 = V(H.x - 0.05, H.y + altoManubrio, -anchoManubrio);
  tubo(M1, M2, 0.012, M.chasis, decor);
  tubo(M1, V(M1.x, M1.y, M1.z - 0.1), 0.017, M.caucho, decor);
  tubo(M2, V(M2.x, M2.y, M2.z + 0.1), 0.017, M.caucho, decor);
  for (const lado of [1, -1]) {
    const z = lado * anchoManubrio;
    // Elevador del manubrio sobre la tijera superior
    tubo(V(H.x - 0.04, H.y + 0.01, lado * 0.06), V(H.x - 0.05, H.y + altoManubrio, lado * 0.06), 0.013, M.oscuro, decor, 10);
    // Contrapeso en la punta y comando de luces/encendido junto al puño
    disco(0.016, 0.022, M.metal, V(M1.x, M1.y, z + lado * 0.012), decor, 14);
    const comando = caja(0.04, 0.032, 0.035, M.oscuro, V(M1.x + 0.004, M1.y, z - lado * 0.12), decor);
    comando.rotation.x = lado * 0.1;
    // Manigueta (derecha = freno) y palanca del clutch (izquierda), delante del puño
    const pivote = V(M1.x + 0.03, M1.y + 0.005, z - lado * 0.13);
    caja(0.028, 0.02, 0.03, M.metal, pivote, decor);
    const palanca = new THREE.CatmullRomCurve3([pivote, V(pivote.x + 0.045, pivote.y - 0.004, z - lado * 0.07),
      V(pivote.x + 0.04, pivote.y - 0.008, z - lado * 0.01)]);
    malla(new THREE.TubeGeometry(palanca, 10, 0.0055, 6), M.metal, decor);
    // Depósito del líquido de frenos (solo a la derecha con freno de disco)
    if (lado < 0 && specs.freno_delantero === "disco") caja(0.03, 0.022, 0.035, M.oscuro, V(M1.x - 0.005, M1.y + 0.03, z - lado * 0.17), decor);
  }
  for (const lado of [1, -1]) {
    const base = V(H.x - 0.04, H.y + altoManubrio, lado * (anchoManubrio - 0.06));
    const punta = base.clone().add(V(-0.03, 0.1, lado * 0.08));
    tubo(base, punta, 0.006, M.oscuro, decor);
    elipsoide(0.012, 0.028, 0.045, M.oscuro, punta, decor);
  }
  const naked = tipo === "calle" && !specs.carenado && specs.cilindraje >= 150;
  if (naked) {
    // Faro moderno con carenado corto y visera ahumada (motos naked de 150 cc en adelante)
    const fx = H.x + 0.1, fy = H.y - 0.07;
    const carenadoFaro = perfil([[fx + 0.075, fy - 0.06], [fx + 0.085, fy + 0.03], [fx + 0.03, fy + 0.09], [fx - 0.05, fy + 0.07],
      [fx - 0.05, fy - 0.03], [fx + 0.01, fy - 0.08]], 0.16, M.oscuro, decor, 0, 0.012);
    zona(carenadoFaro, "frontal");
    const lenteN = caja(0.012, 0.05, 0.11, M.luz, V(fx + 0.085, fy - 0.01, 0), decor);
    lenteN.rotation.z = -0.25;
    for (const lado of [1, -1]) {
      const drl = caja(0.01, 0.012, 0.05, M.luz, V(fx + 0.07, fy + 0.04, lado * 0.045), decor);
      drl.rotation.set(lado * 0.5, 0, -0.5);
    }
    perfil([[fx + 0.03, fy + 0.1], [fx + 0.05, fy + 0.17], [fx - 0.02, fy + 0.19], [fx - 0.04, fy + 0.09]], 0.14, M.vidrio, decor, 0, 0.006);
  } else if (!scooter && tipo !== "sport") {
    const faro = disco(tipo === "enduro" ? 0.06 : 0.085, 0.07, M.oscuro, V(H.x + 0.09, H.y - 0.06, 0), decor, 24);
    faro.rotation.set(0, 0, Math.PI / 2);
    const lente = disco(tipo === "enduro" ? 0.05 : 0.075, 0.01, M.luz, V(H.x + 0.126, H.y - 0.06, 0), decor, 24);
    lente.rotation.set(0, 0, Math.PI / 2);
    const aro = malla(new THREE.TorusGeometry(tipo === "enduro" ? 0.053 : 0.079, 0.006, 8, 40), M.cromo, decor);
    aro.position.set(H.x + 0.128, H.y - 0.06, 0);
    aro.rotation.y = Math.PI / 2;
    if (tipo === "enduro") {
      perfil([[0, -0.07], [0.04, -0.085], [0.06, 0.07], [0.015, 0.1], [-0.015, 0.035]], 0.13, M.pintura, decor, 0, 0.01)
        .position.set(H.x + 0.075, H.y - 0.05, 0);
    }
  }

  // ----- Chasis y basculante -----
  const chasis = decor;
  if (!scooter) {
    const bajoMotor = V(P.x + 0.12, P.y - 0.02);
    const espina = V(P.x + 0.08, alturaAsiento - 0.12);
    for (const lado of [1, -1]) {
      const z = lado * 0.07;
      if (tipo === "semi") {
        tubo(V(H.x, H.y - 0.05, 0), V(P.x + 0.25, P.y + 0.08, 0), 0.03, M.chasis, chasis);
      } else {
        tubo(V(H.x - 0.02, H.y - 0.02, z * 0.5), V(espina.x, espina.y, z), 0.02, M.chasis, chasis);
        tubo(V(H.x, H.y - 0.12, z * 0.5), V(bajoMotor.x + 0.25, bajoMotor.y + 0.02, z), 0.018, M.chasis, chasis);
      }
      tubo(V(espina.x, espina.y, z), V(P.x, P.y, z), 0.02, M.chasis, chasis);
      // Subchasis: el colín se angosta hacia la cola, así que los tubos se juntan hacia atrás y terminan por dentro
      // (antes llegaban con la misma separación y atravesaban los costados del colín).
      const zCola = lado * 0.04;
      tubo(V(espina.x, espina.y, z), V(xR + 0.14, alturaAsiento - 0.1, zCola), 0.014, M.chasis, chasis);
      tubo(V(P.x, P.y, z), V(xR + 0.22, alturaAsiento - 0.15, zCola * 1.2), 0.012, M.chasis, chasis);
      // Basculante en sección de caja: más alto junto al pivote y más delgado en el eje trasero
      const ini = V(P.x, P.y, lado * 0.085), fin = V(xR, Rr, lado * (anchoR / 2 + 0.03));
      const largoB = Math.hypot(fin.x - ini.x, fin.y - ini.y);
      const brazo = perfil([[0, -0.03], [largoB, -0.014], [largoB + 0.025, 0], [largoB, 0.014], [0, 0.03], [-0.02, 0]],
        0.026, M.oscuro, chasis, 0, 0.006);
      brazo.position.set(ini.x, ini.y, (ini.z + fin.z) / 2);
      brazo.rotation.z = Math.atan2(fin.y - ini.y, fin.x - ini.x);
      // Tensor de cadena al final del brazo
      caja(0.04, 0.018, 0.03, M.metal, V(xR + 0.02, Rr, fin.z + lado * 0.004), chasis);
    }
    disco(0.03, 0.2, M.oscuro, P, chasis, 12);
  }

  // ----- Motor -----
  const motor = grupo("motor");
  const aceite = grupo("aceite");
  const bujiaG = grupo("bujia");
  const filtro = grupo("filtro_aire");
  const bateria = grupo("bateria");
  const liquida = specs.refrigeracion === "liquido";

  if (scooter) {
    // Motor bajo el asiento, unido al basculante; la transmisión es la correa CVT.
    const E = V(P.x + 0.02, Rr * 0.95);
    caja(0.24 * s, 0.13 * s, 0.2, M.carter, V(E.x - 0.03, E.y - 0.03 * s), aceite);
    disco(0.02, 0.02, M.oscuro, V(E.x - 0.08, E.y - 0.1 * s, -0.1), aceite, 10).rotation.set(0, 0, 0);
    const cilindro = caja(0.2 * s, 0.11 * s, 0.11 * s, M.motor, V(E.x + 0.13 * s, E.y + 0.02), motor, -0.12);
    for (let i = 0; i < (liquida ? 0 : 5); i++) caja(0.012, 0.15 * s, 0.15 * s, M.motor, V(E.x + 0.06 + i * 0.03 * s, E.y + 0.03), motor, -0.12);
    caja(0.07, 0.12 * s, 0.13 * s, M.carter, V(E.x + 0.26 * s, E.y + 0.0), motor, -0.12);
    disco(0.009, 0.06, M.bujia, V(E.x + 0.27 * s, E.y + 0.09 * s, 0), bujiaG, 10).rotation.set(0, 0, 0);
    tubo(V(E.x + 0.27 * s, E.y + 0.07 * s, 0), V(E.x + 0.27 * s, E.y + 0.13 * s, 0), 0.012, M.bujia, bujiaG);
    const correa = grupo("correa");
    perfil([[0, -0.07], [xR - P.x + 0.02, -0.05], [xR - P.x - 0.05, 0.03], [xR - P.x, 0.09], [0.05, 0.1], [-0.05, 0.06], [-0.05, -0.04]],
      0.07, M.carter, correa, 0, 0.02).position.set(P.x, Rr * 0.95 - 0.02, anchoR / 2 + 0.07);
    // En la NMAX la caja del filtro va dentro del carenado (si no, atraviesa la franja inferior y se ve cortada).
    const zFiltro = esNmax ? 0.05 : 0.13;
    caja(0.24, 0.1, 0.12, M.oscuro, V(xR + 0.34, Rr + 0.17, zFiltro), filtro);
    caja(0.12, 0.13, 0.08, M.bateria, V(P.x + 0.32, 0.46, 0), bateria);
    caja(0.03, 0.03, 0.06, M.rojo, V(P.x + 0.38, 0.53, 0.02), bateria);
    cilindro.userData.base = true;
    // Rayos X: pistón, aceite, poleas y correa, elemento del filtro y celdas de la batería
    interno(disco(0.045 * s, 0.05, M.cromo, V(E.x + 0.1 * s, E.y + 0.015), motor, 16)).rotation.set(0, 0, Math.PI / 2 - 0.12);
    interno(caja(0.2 * s, 0.05 * s, 0.17, M.aceiteVisible, V(E.x - 0.03, E.y - 0.07 * s), aceite));
    const zCvt = anchoR / 2 + 0.07;
    const poleaA = V(P.x + 0.02, Rr * 0.95 + 0.01, zCvt);
    const poleaB = V(xR + 0.02, Rr, zCvt);
    interno(disco(0.065, 0.03, M.metal, poleaA, correa, 24));
    interno(disco(0.085, 0.03, M.metal, poleaB, correa, 24));
    const contornoCvt = cascoCirculos([[poleaA.x, poleaA.y, 0.058], [poleaB.x, poleaB.y, 0.078]]);
    interno(malla(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(contornoCvt.map(([x, y]) => V(x, y, zCvt)), true), 90, 0.009, 6, true), M.caucho, correa));
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      interno(disco(0.011, 0.02, M.cromo, poleaA.clone().add(V(Math.cos(a) * 0.04, Math.sin(a) * 0.04, 0.01)), correa, 10));
    }
    for (let i = 0; i < 6; i++) interno(caja(0.012, 0.07, 0.1, M.bujia, V(xR + 0.27 + i * 0.024, Rr + 0.17, zFiltro), filtro));
    for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) interno(caja(0.03, 0.09, 0.03, M.motor, V(P.x + 0.29 + i * 0.033, 0.46, -0.018 + j * 0.036), bateria));
  } else {
    const E = V(P.x + 0.2 * s + 0.04, P.y + 0.05);
    // Cárter (aceite): bloque redondeado con la tapa del clutch (derecha) y la del magneto (izquierda)
    const carter = perfil([[E.x - 0.16 * s, E.y - 0.02], [E.x - 0.12 * s, E.y + 0.07 * s], [E.x + 0.04 * s, E.y + 0.08 * s],
      [E.x + 0.16 * s, E.y + 0.02 * s], [E.x + 0.15 * s, E.y - 0.09 * s], [E.x + 0.02 * s, E.y - 0.12 * s], [E.x - 0.12 * s, E.y - 0.1 * s]],
    0.22 * s, M.carter, aceite, 0, 0.02, true);
    carter.userData.base = true;
    const tapaClutch = disco(0.085 * s, 0.03, M.motor, V(E.x + 0.04 * s, E.y - 0.02, -0.12 * s), aceite, 40);
    disco(0.05 * s, 0.012, M.carter, V(E.x + 0.04 * s, E.y - 0.02, -0.14 * s), aceite, 32);
    disco(0.012, 0.014, M.vidrio, V(E.x + 0.1 * s, E.y - 0.07 * s, -0.13 * s), aceite, 16); // visor del nivel de aceite
    tapaClutch.userData.base = true;
    const tapaMagneto = disco(0.07 * s, 0.03, M.motor, V(E.x - 0.07 * s, E.y + 0.0, 0.12 * s), aceite, 40);
    tapaMagneto.userData.base = true;
    disco(0.022, 0.03, M.oscuro, V(E.x - 0.08 * s, E.y - 0.09 * s, 0.1 * s), aceite, 6); // tapón de drenaje
    for (let i = 0; i < 8; i++) {
      const a = (i / 8) * Math.PI * 2;
      disco(0.005, 0.034, M.metal, V(E.x + 0.04 * s + Math.cos(a) * 0.075 * s, E.y - 0.02 + Math.sin(a) * 0.075 * s, -0.12 * s), aceite, 6);
    }
    // Cilindro y culata (motor)
    const inclinacion = tipo === "semi" ? -1.25 : -0.32;
    const base = V(E.x + 0.07 * s, E.y + 0.06 * s);
    const dirCil = V(-Math.sin(inclinacion), Math.cos(inclinacion));
    const alto = 0.2 * s;
    const cilindro = new THREE.Group();
    cilindro.position.copy(base);
    cilindro.rotation.z = inclinacion;
    motor.add(cilindro);
    caja(0.13 * s, alto, 0.13 * s, M.motor, V(0, alto / 2), cilindro);
    if (!liquida) {
      for (let i = 0; i < 6; i++) caja(0.19 * s, 0.01, 0.19 * s, M.motor, V(0, 0.03 + i * (alto - 0.03) / 6), cilindro);
    }
    caja(0.16 * s, 0.07 * s, 0.16 * s, M.carter, V(0, alto + 0.03 * s), cilindro);
    // Bujía en la culata
    const cabeza = base.clone().add(dirCil.clone().multiplyScalar(alto + 0.07 * s));
    const bujiaPunta = cabeza.clone().add(dirCil.clone().multiplyScalar(0.06));
    tubo(cabeza, bujiaPunta, 0.011, M.bujia, bujiaG, 10);
    tubo(bujiaPunta, bujiaPunta.clone().add(V(-0.06, 0.02, 0.04)), 0.005, M.caucho, bujiaG, 6);
    // Filtro de aire bajo el asiento
    caja(0.18, 0.12, 0.16, M.oscuro, V(P.x - 0.04, alturaAsiento - 0.2, 0), filtro);
    tubo(V(P.x + 0.04, alturaAsiento - 0.22, 0), V(E.x, E.y + 0.12 * s, 0), 0.025, M.caucho, filtro);
    // Batería
    caja(0.11, 0.12, 0.09, M.bateria, V(P.x - 0.2, alturaAsiento - 0.2, 0), bateria);
    caja(0.025, 0.02, 0.025, M.rojo, V(P.x - 0.17, alturaAsiento - 0.135, 0.02), bateria);
    // Rayos X: pistón y válvulas, aceite en el cárter, elemento del filtro y celdas de la batería
    interno(disco(0.05 * s, 0.05 * s, M.cromo, V(0, alto * 0.55), cilindro, 18)).rotation.set(0, 0, 0);
    interno(caja(0.012, alto * 0.5, 0.012, M.metal, V(0, alto * 0.25), cilindro));
    for (const lado of [-1, 1]) {
      interno(caja(0.006, 0.07 * s, 0.006, M.metal, V(lado * 0.025 * s, alto + 0.01, 0), cilindro));
      interno(disco(0.016 * s, 0.006, M.metal, V(lado * 0.025 * s, alto - 0.025, 0), cilindro, 12)).rotation.set(0, 0, 0);
    }
    interno(disco(0.07 * s, 0.03, M.metal, V(E.x, E.y - 0.02, 0), motor, 20));
    interno(caja(0.28 * s, 0.06 * s, 0.2 * s, M.aceiteVisible, V(E.x, E.y - 0.08 * s), aceite));
    for (let i = 0; i < 6; i++) interno(caja(0.01, 0.09, 0.13, M.bujia, V(P.x - 0.1 + i * 0.024, alturaAsiento - 0.2, 0), filtro));
    for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) interno(caja(0.028, 0.09, 0.03, M.motor, V(P.x - 0.23 + i * 0.03, alturaAsiento - 0.2, -0.018 + j * 0.036), bateria));
    // Radiador
    if (liquida) {
      const rad = grupo("refrigeracion");
      const centroRad = V(H.x - 0.12, H.y - 0.36);
      const placa = caja(0.04, 0.2, 0.28, M.radiador, centroRad, rad, -0.2);
      // Aletas del panal en gris oscuro (en plateado se veía como una caja gris asomando entre las aletas del tanque)
      const panal = new THREE.MeshStandardMaterial({ color: 0x3b4245, roughness: 0.5, metalness: 0.6 });
      for (let i = 0; i < 7; i++) caja(0.045, 0.006, 0.27, panal, V(centroRad.x, centroRad.y - 0.09 + i * 0.03), rad, -0.2);
      tubo(V(centroRad.x - 0.02, centroRad.y - 0.08, 0.1), V(E.x + 0.05, E.y + 0.08, 0.1), 0.012, M.caucho, rad);
      placa.userData.base = true;
      // Deflectores del radiador (las naked de 150 cc o más no: ahí las aletas grandes del tanque cubren el radiador)
      if (!specs.carenado && !(tipo === "calle" && specs.cilindraje >= 150)) {
        for (const lado of [1, -1]) {
          perfil([[centroRad.x - 0.06, centroRad.y + 0.1], [centroRad.x + 0.05, centroRad.y + 0.1], [centroRad.x + 0.07, centroRad.y - 0.03],
            [centroRad.x - 0.02, centroRad.y - 0.1]], 0.01, M.oscuro, decor, lado * 0.15, 0.004);
        }
      }
    }
    // Transmisión: cadena y piñones (lado izquierdo)
    const cadena = grupo("cadena");
    const zCad = anchoR / 2 + 0.05;
    const pinon = V(P.x + 0.06, P.y + 0.01, zCad);
    const corona = V(xR, Rr, zCad);
    const rP = 0.035;
    const rC = 0.075 + specs.cilindraje / 4000;
    disco(rP, 0.012, M.metal, pinon, cadena, 14);
    disco(rC, 0.008, M.metal, corona, cadena, 28);
    const contorno = cascoCirculos([[pinon.x, pinon.y, rP + 0.006], [corona.x, corona.y, rC + 0.006]]);
    const curva = new THREE.CatmullRomCurve3(contorno.map(([x, y]) => V(x, y, zCad)), true);
    malla(new THREE.TubeGeometry(curva, 120, 0.0045, 6, true), M.oscuro, cadena);
    const nEslabones = Math.round(curva.getLength() / 0.0127);
    const placa = new THREE.InstancedMesh(new THREE.BoxGeometry(0.0125, 0.0075, 0.004), M.metal, nEslabones * 2);
    const m4c = new THREE.Matrix4(), qc = new THREE.Quaternion();
    for (let i = 0; i < nEslabones; i++) {
      const u = i / nEslabones;
      const pt = curva.getPointAt(u), tg = curva.getTangentAt(u);
      qc.setFromAxisAngle(V(0, 0, 1), Math.atan2(tg.y, tg.x));
      const abierto = i % 2 ? 0.0065 : 0.0045;   // placas exteriores e interiores
      for (const lado of [1, -1]) {
        m4c.compose(V(pt.x, pt.y, zCad + lado * abierto), qc, V(1, 1, 1));
        placa.setMatrixAt(i * 2 + (lado > 0 ? 0 : 1), m4c);
      }
    }
    placa.castShadow = true;
    cadena.add(placa);
    // Corona con dientes y guardacadena sobre el tramo de arriba
    for (let i = 0; i < 36; i++) {
      const a = (i / 36) * Math.PI * 2;
      caja(0.008, 0.01, 0.007, M.metal, V(corona.x + Math.cos(a) * (rC + 0.003), corona.y + Math.sin(a) * (rC + 0.003), zCad), cadena, a);
    }
    const arriba1 = V(pinon.x - 0.02, pinon.y + rP + 0.022), arriba2 = V(corona.x + rC * 0.6, corona.y + rC + 0.02);
    const guarda = caja(arriba1.distanceTo(arriba2), 0.008, 0.05, M.oscuro,
      V((arriba1.x + arriba2.x) / 2, (arriba1.y + arriba2.y) / 2, zCad + 0.005), decor,
      Math.atan2(arriba2.y - arriba1.y, arriba2.x - arriba1.x));
    guarda.userData.base = true;
  }

  // ----- Suspensión trasera -----
  const susTras = grupo("suspension_tras");
  function amortiguador(abajo, arriba) {
    tubo(abajo, arriba, 0.012, M.cromo, susTras, 8);
    const ab = abajo.clone().lerp(arriba, 0.15);
    const ar = abajo.clone().lerp(arriba, 0.85);
    resorte(ab, ar, 0.028, 7, M.resorte, susTras);
    disco(0.02, 0.03, M.oscuro, abajo, susTras, 10);
    disco(0.018, 0.03, M.oscuro, arriba, susTras, 10);
    tubo(ar, arriba, 0.02, M.oscuro, susTras, 12);                       // cuerpo superior
    tubo(abajo, abajo.clone().lerp(arriba, 0.1), 0.016, M.oscuro, susTras, 12);
    if (specs.cilindraje >= 150 && !scooter) {
      const dep = ar.clone().add(V(-0.03, -0.01, 0.03));
      tubo(dep, dep.clone().add(V(0.02, -0.08, 0)), 0.014, M.metal, susTras, 12);   // depósito de gas
    }
  }
  if (specs.suspension_trasera === "doble") {
    for (const lado of [1, -1]) {
      // En las scooter el amortiguador va por dentro del carenado (se ve solo la parte de abajo); antes quedaba
      // justo en la superficie del costado y el resorte la atravesaba.
      const z = lado * (scooter ? 0.105 : anchoR / 2 + 0.035);
      // En las motos de cambios el anclaje de arriba queda justo bajo el colín (antes lo atravesaba por el costado)
      amortiguador(V(xR + 0.06, Rr + 0.03, z), scooter ? V(xR + 0.18, alturaAsiento - 0.12, z) : V(xR + 0.2, alturaAsiento - 0.175, z));
    }
  } else if (scooter) {
    amortiguador(V(xR + 0.08, Rr + 0.05, 0.1), V(xR + 0.16, alturaAsiento - 0.14, 0.1));
  } else {
    amortiguador(V(P.x - 0.12, P.y + 0.02, 0), V(P.x + 0.02, alturaAsiento - 0.16, 0));
  }

  // ----- Escape (lado derecho) -----
  if (scooter) {
    tubo(V(P.x + 0.2, Rr * 0.8, -0.05), V(xR + 0.15, Rr + 0.02, -0.14), 0.02, M.cromo, decor);
    const silenciador = tubo(V(xR + 0.3, Rr + 0.03, -0.15), V(xR - 0.02, Rr + 0.1, -0.15), 0.05, M.oscuro, decor);
    silenciador.userData.base = true;
  } else {
    const salida = V(P.x + 0.32 * s, P.y - 0.03, -0.06);
    const finCodo = tipo === "enduro" ? V(P.x - 0.05, alturaAsiento - 0.15, -0.14) : V(P.x - 0.05, P.y - 0.02, -0.12);
    // Codo de escape curvo: sale de la culata, baja por delante del motor y pasa por debajo
    // (puerto de escape: frente de la culata del cilindro inclinado, ver "Motor")
    if (tipo !== "semi") {
      const culataEsc = V(P.x + 0.2 * s + 0.04 + 0.215 * s, P.y + 0.05 + 0.25 * s, -0.02);
      const codo = new THREE.CatmullRomCurve3([culataEsc, V(culataEsc.x + 0.05, culataEsc.y - 0.12 * s, -0.05),
        V(salida.x + 0.03, salida.y - 0.05, -0.06), salida]);
      malla(new THREE.TubeGeometry(codo, 30, 0.019, 12), M.cromo, decor);
    }
    tubo(salida, finCodo, 0.02, M.cromo, decor);
    const largo = tipo === "sport" ? 0.32 : 0.42;
    const finSil = tipo === "enduro" ? V(xR + 0.05, alturaAsiento - 0.08, -0.15) : V(xR + 0.18, Rr + 0.14, -0.15);
    const iniSil = finCodo.clone().lerp(finSil, 1 - largo / finCodo.distanceTo(finSil));
    const rSil = tipo === "sport" ? 0.055 : 0.045;
    tubo(iniSil, finSil, rSil, M.oscuro, decor, 24);
    tubo(finCodo, iniSil, 0.022, M.cromo, decor);
    // Punta cromada y protector térmico perforado
    const dirSil = new THREE.Vector3().subVectors(finSil, iniSil).normalize();
    tubo(finSil, finSil.clone().add(dirSil.clone().multiplyScalar(0.035)), rSil * 0.55, M.cromo, decor, 20);
    const protectorSil = malla(new THREE.CylinderGeometry(rSil + 0.006, rSil + 0.006, iniSil.distanceTo(finSil) * 0.55, 24, 1, true, 0, Math.PI * 0.9), M.metal, decor);
    protectorSil.position.copy(iniSil.clone().lerp(finSil, 0.45));
    protectorSil.quaternion.setFromUnitVectors(V(0, 1, 0), dirSil);
    protectorSil.rotateY(Math.PI * 0.55);
  }

  // ----- Carrocería específica: Yamaha NMAX (maxi-scooter) -----
  // Paneles curvos que se angostan hacia la nariz y la cola, pintura en dos tonos y detalles propios del modelo.
  function panelAhusado(puntos, ancho, mat, ahusar, bisel = 0.045, deformar = null) {
    // Base liviana (menos segmentos): la suavidad la dan la subdivisión de las tapas y las normales suavizadas.
    const m = perfil(puntos, ancho, mat, decor, 0, bisel, true, 10, 3);
    // Las tapas de una extrusión tienen pocos triángulos grandes: al angostarlas por vértice quedaban "facetadas"
    // (como papel doblado). Se subdividen antes de dar la forma y luego se suavizan las normales.
    let geo = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
    geo.deleteAttribute("uv");
    geo.deleteAttribute("normal");
    geo = subdividir(mergeVertices(geo, 1e-5), 0.06, 4);
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      pos.setZ(i, pos.getZ(i) * ahusar(pos.getX(i), pos.getY(i)));
      if (deformar) {
        const [x, y, z] = deformar(pos.getX(i), pos.getY(i), pos.getZ(i));
        pos.setXYZ(i, x, y, z);
      }
    }
    pos.needsUpdate = true;
    geo.computeVertexNormals();
    m.geometry.dispose();
    m.geometry = geo;
    return m;
  }

  function carroceriaNmax() {
    const pintura = M.pintura;
    const negro = new THREE.MeshPhysicalMaterial({ color: 0x15181a, roughness: 0.45, metalness: 0.15, clearcoat: 0.6, clearcoatRoughness: 0.25 });
    const plastico = new THREE.MeshStandardMaterial({ color: 0x2b3033, roughness: 0.62, metalness: 0.05 });
    const vidrioOscuro = new THREE.MeshPhysicalMaterial({ color: 0x1b2226, transparent: true, opacity: 0.6, roughness: 0.04, clearcoat: 1, depthWrite: false });
    const ambar = new THREE.MeshStandardMaterial({ color: 0xffb347, emissive: 0xff9a1f, emissiveIntensity: 0.35, roughness: 0.25 });
    M.resorte.color.set(0xd6a12c); // resortes dorados de los amortiguadores
    M.acento = negro; // el color de detalles también pinta los acabados negros
    const sube = (y) => y; // alturas en metros (NMAX: asiento 0,765 m)

    // Frontal (escudo) en el color de la moto: se angosta hacia adelante y hacia arriba
    // Escudo más inclinado (como la NMAX real) y con nariz en "V" vista desde arriba
    const puntosEscudo = [[0.5, 0.42], [0.6, 0.47], [xF + 0.05, 0.58], [xF + 0.13, 0.66], [xF + 0.1, 0.76], [xF + 0.03, 0.88],
      [0.6, 0.94], [0.53, 0.92], [0.45, 0.82], [0.41, 0.66], [0.38, 0.47], [0.42, 0.42]];
    const angostarEscudo = (x, y) => (x > 0.48 ? Math.max(0.45, 1 - (x - 0.48) * 1.6) : 1) * (y > 0.84 ? Math.max(0.55, 1 - (y - 0.84) * 2.2) : 1);
    const BISEL_ESCUDO = 0.045, PICO = 0.06;
    const tPico = (x) => Math.min(1, Math.max(0, (x - 0.55) / 0.25));
    const narizV = (x, y, z) => {
      const zn = Math.min(1, Math.abs(z) / (0.2 * angostarEscudo(x, y)));
      return [x - PICO * tPico(x) * zn * zn, y, z];
    };
    zona(panelAhusado(puntosEscudo, 0.4, pintura, angostarEscudo, BISEL_ESCUDO, narizV), "frontal");
    // Dónde queda la superficie delantera del escudo a cierta altura y a cierta distancia del centro (para pegar los faros)
    const frenteEscudo = (y, z) => {
      const frente = puntosEscudo.slice(2, 7);
      let x = frente[0][0];
      for (let i = 0; i < frente.length - 1; i++) {
        const [a, b] = [frente[i], frente[i + 1]];
        if ((y - a[1]) * (y - b[1]) <= 0) { x = a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]); break; }
      }
      x += BISEL_ESCUDO;
      const zn = Math.min(1, Math.abs(z) / (0.2 * angostarEscudo(x, y)));
      return x - PICO * tPico(x) * zn * zn;
    };
    // Mentón negro bajo los faros y escudo interior gris (donde van las rodillas)
    panelAhusado([[0.6, 0.47], [xF + 0.04, 0.6], [xF + 0.1, 0.67], [xF + 0.05, 0.66], [0.62, 0.53]], 0.38, negro,
      (x) => Math.max(0.5, 1 - (x - 0.6) * 1.6), 0.02);
    panelAhusado([[0.37, 0.41], [0.41, 0.86], [0.47, 0.95], [0.45, 0.96], [0.35, 0.88], [0.31, 0.43]], 0.42, plastico, () => 1, 0.012);

    // Faros en V (el sello de la NMAX): dos faros rasgados que bajan hacia el centro, con su luz diurna encima,
    // pegados sobre la superficie del escudo (antes quedaban dentro y no se veían). Inclinación del frente: ~30°.
    const inclinacion = -0.52;
    for (const lado of [1, -1]) {
      const z = lado * 0.068;
      const yF = 0.78;
      const marco = caja(0.012, 0.05, 0.13, negro, V(frenteEscudo(yF, z) + 0.002, yF, z), decor);
      marco.rotation.set(lado * 0.2, -lado * 0.24, inclinacion);
      const faro = caja(0.01, 0.034, 0.112, M.luz, V(frenteEscudo(yF, z) + 0.009, yF, z), decor);
      faro.rotation.set(lado * 0.2, -lado * 0.24, inclinacion);
      // Luz diurna (DRL): franja fina encima de cada faro
      const yD = 0.835, zD = lado * 0.09;
      const drl = caja(0.008, 0.01, 0.12, M.luz, V(frenteEscudo(yD, zD) + 0.006, yD, zD), decor);
      drl.rotation.set(lado * 0.14, -lado * 0.3, inclinacion);
      // Direccionales a los lados del escudo
      const yA = 0.7, zA = lado * 0.13;
      const direccional = caja(0.022, 0.02, 0.05, ambar, V(frenteEscudo(yA, zA) + 0.004, yA, zA), decor);
      direccional.rotation.set(0, -lado * 0.55, inclinacion);
    }
    caja(0.01, 0.012, 0.07, M.luz, V(frenteEscudo(0.72, 0) + 0.006, 0.72, 0), decor).rotation.z = -0.35; // luz de posición central

    // Parabrisas oscuro
    panelAhusado([[0.58, 0.955], [xF + 0.03, 0.89], [xF - 0.01, 0.96], [0.6, 1.06], [0.54, 1.05]], 0.3, vidrioOscuro,
      (x, y) => Math.max(0.65, 1 - (y - 0.95) * 1.4), 0.008);

    // Cubre-manubrio negro y tablero
    caja(0.13, 0.05, 0.42, negro, V(H.x - 0.01, H.y + 0.1, 0), decor).rotation.z = -0.15;
    const tablero = caja(0.06, 0.004, 0.16, M.tablero, V(H.x + 0.02, H.y + 0.128, 0), decor);
    tablero.rotation.z = -0.35;

    // Guardabarros delantero envolvente (negro)
    const guarda = malla(new THREE.TorusGeometry(Rf + 0.035, 0.016, 8, 32, Math.PI * 0.62), negro, decor);
    guarda.position.set(xF, Rf, 0);
    guarda.rotation.z = Math.PI * 0.16;
    guarda.scale.z = 4.5;

    // Piso plano con túnel central y faldón negro
    caja(0.42, 0.03, 0.34, negro, V(0.16, 0.365, 0), decor);
    perfil([[0.0, 0.38], [0.04, 0.45], [0.26, 0.46], [0.32, 0.38]], 0.15, plastico, decor, 0, 0.02, true);
    panelAhusado([[-0.12, 0.37], [0.42, 0.37], [0.44, 0.3], [0.3, 0.22], [0.0, 0.2], [-0.16, 0.27]], 0.4, negro, () => 1, 0.018);

    // Carenado trasero en el color de la moto, angostándose hacia la cola
    zona(panelAhusado([[-0.06, 0.38], [-0.02, 0.62], [-0.1, 0.68], [-0.45, 0.72], [xR - 0.13, 0.78], [xR - 0.23, 0.8],
      [xR - 0.21, 0.72], [xR - 0.11, 0.62], [-0.55, 0.5], [-0.3, 0.44]], 0.28, pintura,
      (x) => (x < -0.6 ? Math.max(0.55, 1 - (-0.6 - x) * 1.3) : 1)), "lateral", "cola");
    // Tapa lateral en "bumerán" (rasgo de la NMAX): franja oscura que cruza el costado en diagonal hacia la cola
    for (const lado of [1, -1]) {
      perfil([[-0.08, 0.5], [-0.14, 0.56], [-0.58, 0.69], [-0.66, 0.68], [-0.6, 0.64], [-0.16, 0.5]], 0.006, negro, decor,
        lado * 0.188, 0.003).userData.bajoCalca = true;
    }
    // Franja negra inferior del carenado
    panelAhusado([[-0.1, 0.38], [-0.3, 0.44], [-0.55, 0.5], [-0.62, 0.46], [-0.3, 0.385]], 0.3, negro, () => 1, 0.04);

    // Asiento de dos niveles (conductor más bajo, parrillero más alto)
    panelAhusado([[0.02, 0.68], [0.0, 0.74], [-0.1, sube(0.775)], [-0.36, 0.77], [-0.42, 0.8], [-0.48, 0.82],
      [xR - 0.11, 0.835], [xR - 0.17, 0.805], [xR - 0.13, 0.765], [-0.45, 0.725], [-0.05, 0.685]], 0.3, M.asiento,
      (x) => (x > -0.1 ? 0.78 : x < -0.7 ? Math.max(0.6, 1 - (-0.7 - x) * 1.6) : 1), 0.03);

    // Parrilla trasera (agarradera)
    const parrilla = new THREE.CatmullRomCurve3([
      // Por fuera del asiento y del bisel del carenado (antes quedaba escondida dentro de ellos)
      V(-0.5, 0.82, 0.2), V(-0.72, 0.85, 0.2), V(xR - 0.17, 0.87, 0.13), V(xR - 0.2, 0.875, 0),
      V(xR - 0.17, 0.87, -0.13), V(-0.72, 0.85, -0.2), V(-0.5, 0.82, -0.2),
    ]);
    malla(new THREE.TubeGeometry(parrilla, 60, 0.012, 10), negro, decor);

    // Stop trasero en la punta de la cola
    const stop = caja(0.02, 0.035, 0.17, M.stop, V(xR - 0.235, 0.765, 0), decor);
    stop.rotation.z = 0.35;
    for (const lado of [1, -1]) caja(0.025, 0.02, 0.04, ambar, V(xR - 0.2, 0.73, lado * 0.12), decor);

    // Tapa del escape plateada (protector térmico)
    const protector = malla(new THREE.CylinderGeometry(0.056, 0.056, 0.28, 24, 1, true, 0, Math.PI), M.metal, decor);
    protector.position.set(xR + 0.2, Rr + 0.08, -0.205);
    protector.rotation.set(0, 0, Math.PI / 2 - 0.15);

    // Radiador (la NMAX es refrigerada por líquido): costado izquierdo, adelante del motor
    if (specs.refrigeracion === "liquido") {
      const rad = grupo("refrigeracion");
      // Dentro del faldón del piso: antes asomaba por el costado como una barra oscura.
      caja(0.05, 0.16, 0.12, M.radiador, V(0.02, 0.3, 0.1), rad);
      for (let i = 0; i < 6; i++) caja(0.052, 0.006, 0.11, M.metal, V(0.02, 0.24 + i * 0.024, 0.1), rad);
    }
  }

  // ----- Carrocería (color del usuario) -----
  const pintura = M.pintura;
  let pata = null;
  if (scooter && esNmax) {
    carroceriaNmax();
  } else if (scooter) {
    // Piso, escudo frontal y carenado trasero
    caja(0.46, 0.04, 0.28, M.oscuro, V(0.14, 0.31, 0), decor);
    // Escudo frontal: se angosta hacia la nariz y hacia arriba
    zona(panelAhusado([[xF - 0.07, Rf + 0.12], [H.x + 0.13, H.y - 0.04], [H.x + 0.03, H.y + 0.1], [H.x - 0.1, H.y - 0.04],
      [0.3, 0.46], [0.36, 0.33], [0.5, 0.31]], 0.34, pintura,
    (x, y) => (x > H.x ? Math.max(0.5, 1 - (x - H.x) * 2.2) : 1) * (y > H.y - 0.06 ? Math.max(0.6, 1 - (y - H.y + 0.06) * 2.5) : 1), 0.03), "frontal");
    // Escudo interior gris (rodillas) y piso con faldón negro
    panelAhusado([[0.28, 0.33], [0.34, 0.46], [H.x - 0.12, H.y - 0.06], [H.x - 0.16, H.y - 0.1], [0.24, 0.42], [0.22, 0.33]], 0.3, M.oscuro, () => 1, 0.012);
    panelAhusado([[-0.12, 0.32], [0.44, 0.32], [0.46, 0.27], [0.32, 0.2], [0.0, 0.19], [-0.16, 0.25]], 0.3, M.oscuro, () => 1, 0.018);
    // Frente del escudo a una altura dada (recta entre su punto bajo y su punto alto delanteros)
    const frenteEscudo = (y) => {
      const ax = xF - 0.07, ay = Rf + 0.12, bx = H.x + 0.13, by = H.y - 0.04;
      return ax + ((y - ay) / (by - ay)) * (bx - ax);
    };
    // Faro con aro negro, pegado por fuera del escudo (antes quedaba hundido y no se veía)
    const yFaro = H.y - 0.08;
    disco(0.066, 0.03, M.oscuro, V(frenteEscudo(yFaro) + 0.03, yFaro, 0), decor, 24).rotation.set(0, 0, Math.PI / 2);
    disco(0.056, 0.012, M.luz, V(frenteEscudo(yFaro) + 0.048, yFaro, 0), decor, 24).rotation.set(0, 0, Math.PI / 2);
    // Direccionales delanteras en el escudo
    const ambarEscudo = new THREE.MeshStandardMaterial({ color: 0xffb347, emissive: 0xff9a1f, emissiveIntensity: 0.35, roughness: 0.25 });
    for (const lado of [1, -1]) {
      caja(0.03, 0.025, 0.045, ambarEscudo, V(frenteEscudo(H.y - 0.17) + 0.025, H.y - 0.17, lado * 0.085), decor, -0.35);
    }
    // Carenado trasero: se angosta hacia la cola
    zona(panelAhusado([[-0.04, 0.33], [0.0, alturaAsiento - 0.12], [xR + 0.08, alturaAsiento - 0.06], [xR - 0.1, alturaAsiento - 0.1],
      [xR - 0.03, alturaAsiento - 0.24], [xR + 0.16, Rr + 0.21], [-0.26, 0.4]], 0.3, pintura,
    (x) => (x < xR + 0.3 ? Math.max(0.5, 1 - (xR + 0.3 - x) * 1.4) : 1), 0.035), "lateral", "cola");
    perfil([[0.02, alturaAsiento - 0.11], [-0.04, alturaAsiento - 0.02], [-0.3, alturaAsiento - 0.03],
      [xR + 0.06, alturaAsiento + 0.01], [xR + 0.04, alturaAsiento - 0.06]], 0.25, M.asiento, decor, 0, 0.025, true);
    caja(0.04, 0.04, 0.16, M.stop, V(xR - 0.11, alturaAsiento - 0.12, 0), decor);
    // Rasgos propios de la scooter: tapetes de caucho en el piso, franja lateral oscura y parrilla trasera
    for (let i = 0; i < 6; i++) caja(0.014, 0.006, 0.22, M.caucho, V(-0.02 + i * 0.065, 0.334, 0), decor);
    for (const lado of [1, -1]) {
      perfil([[-0.02, 0.4], [-0.08, 0.46], [xR + 0.12, alturaAsiento - 0.16], [xR + 0.06, alturaAsiento - 0.17], [xR + 0.1, alturaAsiento - 0.2],
        [-0.12, 0.4]], 0.006, M.oscuro, decor, lado * 0.186, 0.003).userData.bajoCalca = true;
    }
    const parrillaScooter = new THREE.CatmullRomCurve3([
      V(-0.28, alturaAsiento + 0.02, 0.15), V(xR + 0.12, alturaAsiento + 0.035, 0.155), V(xR - 0.04, alturaAsiento + 0.04, 0.08),
      V(xR - 0.04, alturaAsiento + 0.04, -0.08), V(xR + 0.12, alturaAsiento + 0.035, -0.155), V(-0.28, alturaAsiento + 0.02, -0.15),
    ]);
    malla(new THREE.TubeGeometry(parrillaScooter, 50, 0.011, 8), M.chasis, decor);
    // guardabarros delantero
    const guarda = malla(new THREE.TorusGeometry(Rf + 0.03, 0.012, 6, 24, Math.PI * 0.55), pintura, decor);
    guarda.position.set(xF, Rf, 0);
    guarda.rotation.z = Math.PI * 0.2;
    guarda.scale.z = 8;
  } else {
    const tanqueX = H.x - (tipo === "enduro" ? 0.24 : 0.3);
    const tanqueY = alturaAsiento + (tipo === "sport" ? 0.07 : 0.06);
    if (tipo === "semi") {
      // Moto de paso bajo: escudo de piernas y panel bajo el asiento
      perfil([[H.x - 0.02, H.y - 0.02], [H.x - 0.1, H.y - 0.04], [P.x + 0.32, P.y + 0.12], [P.x + 0.4, P.y + 0.06], [H.x + 0.02, H.y - 0.22]],
        0.3, pintura, decor, 0, 0.025);
      zona(perfil([[P.x + 0.06, P.y + 0.12], [P.x + 0.04, alturaAsiento - 0.06], [xR + 0.06, alturaAsiento - 0.04], [xR + 0.2, P.y + 0.2]],
        0.24, pintura, decor, 0, 0.025, true), "lateral", "cola");
      disco(0.07, 0.06, M.oscuro, V(H.x + 0.03, H.y + 0.06, 0), decor, 20).rotation.set(0, 0, Math.PI / 2);
    } else {
      // Tanque esculpido: alto adelante, cae hacia el asiento y se angosta abajo (hueco para las rodillas)
      const tx = tanqueX, ty = tanqueY;
      const altoT = tipo === "enduro" ? 0.09 : 0.11;
      const anchoT = tipo === "enduro" ? 0.26 : tipo === "sport" ? 0.34 : 0.32;
      const tanque = panelAhusado([
        [tx + 0.25, ty - 0.03], [tx + 0.24, ty + altoT * 0.55], [tx + 0.15, ty + altoT], [tx - 0.02, ty + altoT * 0.95],
        [tx - 0.17, ty + altoT * 0.45], [tx - 0.25, ty - 0.04], [tx - 0.14, ty - altoT * 0.95], [tx + 0.12, ty - altoT * 0.9],
      ], anchoT, pintura, (x, y) => {
        const atras = x < tx - 0.05 ? Math.max(0.55, 1 - (tx - 0.05 - x) * 2.2) : 1;
        const abajo = y < ty - 0.02 ? Math.max(0.6, 1 - (ty - 0.02 - y) * 3.2) : 1;
        const arriba = y > ty + altoT * 0.6 ? Math.max(0.7, 1 - (y - ty - altoT * 0.6) * 4) : 1;
        return atras * abajo * arriba;
      }, 0.035);
      zona(tanque, "tanque");
      // Tapa de gasolina con aro
      disco(0.032, 0.012, M.oscuro, V(tx + 0.06, ty + altoT + 0.03, 0), decor, 24).rotation.set(0, 0, 0);
      disco(0.024, 0.016, M.cromo, V(tx + 0.06, ty + altoT + 0.036, 0), decor, 24).rotation.set(0, 0, 0);
      if (tipo !== "enduro" && !specs.carenado) {
        // Aletas laterales del tanque (moto naked)
        for (const lado of [1, -1]) {
          // En las naked de 150 cc o más (tipo NS 200) las aletas son grandes: bajan y cubren el radiador
          const grande = specs.cilindraje >= 150;
          // Grande: arriba nace bajo el tanque, adelante termina detrás de la horquilla y abajo cubre el radiador por el costado
          const radX = H.x - 0.12, radY = H.y - 0.36;
          const contornoAleta = grande
            ? [[tx + 0.04, ty + 0.05], [tx + 0.24, ty + 0.07], [H.x + 0.02, radY + 0.16], [H.x + 0.04, radY + 0.04],
              [radX + 0.02, radY - 0.1], [radX - 0.1, radY - 0.06], [tx + 0.06, ty - 0.1]]
            : [[tx + 0.26, ty + 0.03], [tx + 0.12, ty + 0.06], [tx + 0.03, ty - 0.04], [tx + 0.08, ty - 0.1], [tx + 0.21, ty - 0.08]];
          const aleta = perfil(contornoAleta, 0.014, pintura, decor, lado * (grande ? 0.168 : anchoT / 2 - 0.01), 0.006, grande);
          if (grande) {
            // Inclinada: el borde de arriba se mete hacia el tanque (queda escondido bajo él) y el de abajo abraza el radiador
            const pos = aleta.geometry.attributes.position;
            const yAlto = ty + 0.06, yBajo = radY - 0.09;
            for (let i = 0; i < pos.count; i++) {
              const t = Math.min(1, Math.max(0, (pos.getY(i) - yBajo) / (yAlto - yBajo)));
              pos.setZ(i, pos.getZ(i) * (1 - 0.14 * t));
            }
            pos.needsUpdate = true;
            aleta.geometry.computeVertexNormals();
            // Panel inferior negro de contraste en la punta de la aleta (como en las naked tipo NS 200)
            perfil([[H.x + 0.035, radY + 0.05], [radX + 0.025, radY - 0.085], [radX - 0.05, radY - 0.03], [H.x - 0.01, radY + 0.1]],
              0.006, M.oscuro, decor, lado * 0.178, 0.003, true);
          }
          zona(aleta, "tanque");
          perfil([[tx + 0.2, ty - 0.06], [tx + 0.13, ty + 0.0], [tx + 0.08, ty - 0.03], [tx + 0.1, ty - 0.08]],
            0.008, M.oscuro, decor, lado * (anchoT / 2 + 0.002), 0.003);
        }
      }
      if (tipo === "enduro") {
        for (const lado of [1, -1]) {
          perfil([[0, 0], [0.22, 0.06], [0.2, -0.16], [0.05, -0.2]], 0.02, pintura, decor, lado * 0.124, 0.008)
            .position.set(tanqueX - 0.02, tanqueY - 0.02, 0);
        }
      }
    }
    // Asiento
    const inicioAsiento = tipo === "semi" ? P.x + 0.05 : tanqueX - 0.2;
    const finAsiento = xR + 0.06;
    const escalon = tipo === "sport" ? 0.05 : 0;
    // Asiento acolchado: más ancho donde se sienta el conductor, se angosta hacia la cola (escalón en las deportivas)
    const mitad = (inicioAsiento + finAsiento) / 2;
    const anchoAsiento = tipo === "enduro" ? 0.2 : 0.27;
    panelAhusado([[inicioAsiento, alturaAsiento - 0.04], [inicioAsiento + 0.02, alturaAsiento + 0.015], [inicioAsiento + 0.1, alturaAsiento + 0.035],
      [mitad, alturaAsiento + 0.025], [mitad - 0.02, alturaAsiento + 0.03 + escalon], [finAsiento + 0.1, alturaAsiento + 0.05 + escalon],
      [finAsiento + 0.02, alturaAsiento + 0.03 + escalon], [finAsiento + 0.04, alturaAsiento - 0.03]], anchoAsiento, M.asiento,
    (x, y) => (x > inicioAsiento + 0.14 ? Math.max(0.55, 1 - (x - inicioAsiento - 0.14) * 1.2) : 1)
      * (x < mitad - 0.05 ? Math.max(0.55, 1 - (mitad - 0.05 - x) * 1.4) : 1), 0.03);
    // Colín afilado que sube hacia atrás, con tapas laterales
    zona(panelAhusado([[P.x + 0.04, alturaAsiento - 0.06], [finAsiento + 0.02, alturaAsiento - 0.01 + escalon],
      [xR - 0.06, alturaAsiento + escalon + 0.01], [xR - 0.1, alturaAsiento + escalon - 0.025], [xR + 0.08, alturaAsiento - 0.12],
      [P.x - 0.1, alturaAsiento - 0.2], [P.x + 0.06, alturaAsiento - 0.14]], tipo === "semi" ? 0.24 : 0.22, pintura,
    // En la semiautomática el colín sigue al panel de debajo del asiento (mismo ancho y poco angostamiento),
    // para que se vean como una sola pieza y no como un bulto aparte.
    (x) => (x < P.x - 0.1 ? Math.max(tipo === "semi" ? 0.7 : 0.35, 1 - (P.x - 0.1 - x) * (tipo === "semi" ? 0.6 : 1.6)) : 1), 0.02),
    "lateral", "cola");
    // Stop LED en la punta del colín
    // Stop: carcasa negra con la mica roja encendida y una franja clara al centro (luz de reversa/placa)
    const posStop = V(xR - 0.1, alturaAsiento + escalon - 0.012, 0);
    caja(0.03, 0.04, 0.125, M.oscuro, posStop.clone().add(V(0.012, 0.004, 0)), decor).rotation.z = 0.5;
    const stopLed = caja(0.012, 0.03, 0.11, M.stop, posStop, decor);
    stopLed.rotation.z = 0.5;
    caja(0.004, 0.008, 0.05, M.luz, posStop.clone().add(V(-0.007, -0.002, 0)), decor).rotation.z = 0.5;
    // Guardabarros trasero (hugger) sobre la llanta; la placa y sus direccionales van más abajo, detrás de la llanta
    const hugger = malla(new THREE.TorusGeometry(Rr + 0.03, 0.01, 6, 24, Math.PI * 0.32), M.oscuro, decor);
    hugger.position.set(xR, Rr, 0);
    hugger.rotation.z = Math.PI * 0.42;
    hugger.scale.z = (anchoR / 2 + 0.012) / 0.01; // el tubo de 1 cm se ensancha hasta cubrir la llanta
    // Guardabarros delantero
    if (tipo === "enduro") {
      perfil([[-0.2, 0], [0.25, 0.03], [0.24, -0.02], [-0.18, -0.05]], 0.1, pintura, decor, 0, 0.01)
        .position.set(H.x - 0.04, H.y - 0.22, 0);
    } else {
      // Las motos de calle sencillas (≤125 cc, tipo Boxer) llevan guardabarros cromado; las naked, negro
      const guardaMat = tipo === "calle" ? (specs.cilindraje <= 125 ? M.cromo : M.oscuro) : pintura;
      const guarda = malla(new THREE.TorusGeometry(Rf + 0.025, 0.012, 6, 24, Math.PI * 0.5), guardaMat, decor);
      guarda.position.set(xF, Rf, 0);
      guarda.rotation.z = Math.PI * 0.22;
      guarda.scale.z = 6;
    }
    // Carenado deportivo
    if (specs.carenado) {
      // Carenado deportivo: nariz afilada que se angosta adelante, costados que se recogen hacia el motor
      const angostar = (x, y) => (x > H.x ? Math.max(0.42, 1 - (x - H.x) * 2.4) : 1) * (y < P.y + 0.12 ? 0.82 : 1);
      // Nariz redondeada: adelante los bordes se recogen hacia atrás (vista de planta en "V" suave) y el lomo se curva,
      // en vez de la cara plana de antes.
      const puntosCarenado = [[H.x + 0.24, H.y - 0.12], [H.x + 0.1, H.y + 0.08], [H.x - 0.06, H.y + 0.1], [tanqueX + 0.18, tanqueY - 0.04],
        [P.x + 0.34, P.y + 0.16], [P.x + 0.4, P.y + 0.02], [H.x - 0.04, H.y - 0.3], [H.x + 0.12, H.y - 0.26]];
      const xs = puntosCarenado.map((q) => q[0]), ys = puntosCarenado.map((q) => q[1]);
      const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
      const redondearNariz = (x, y, z) => {
        const media = 0.18 * angostar(x, y);
        const zn = Math.min(1, Math.abs(z) / media);
        const t = Math.min(1, Math.max(0, (x - H.x + 0.08) / 0.32));
        const lomo = y > H.y - 0.06 ? Math.min(1, (y - H.y + 0.06) / 0.14) : 0;
        // Costados abombados: el centro del panel sale un poco, como un carenado inyectado (no una lámina plana)
        const u = Math.min(1, Math.max(0, (x - x0) / (x1 - x0))), v = Math.min(1, Math.max(0, (y - y0) / (y1 - y0)));
        const bombeo = 1 + 0.22 * Math.sin(Math.PI * u) * Math.sin(Math.PI * v);
        return [x - 0.065 * t * zn * zn, y - 0.035 * lomo * zn * zn, z * bombeo];
      };
      zona(panelAhusado(puntosCarenado, 0.36, pintura, angostar, 0.03, redondearNariz), "frontal");
      // Rejillas de ventilación en los costados del carenado (tres ranuras oscuras inclinadas)
      for (const lado of [1, -1]) {
        for (let k = 0; k < 3; k++) {
          const ranura = caja(0.1, 0.012, 0.01, M.oscuro, V(H.x - 0.08 - k * 0.03, H.y - 0.17 - k * 0.045, lado * 0.205), decor, 0.55);
          ranura.rotation.y = lado * 0.12;
        }
      }
      // Quilla negra bajo el motor
      panelAhusado([[P.x + 0.2, P.y - 0.02], [P.x + 0.45, P.y - 0.04], [P.x + 0.42, P.y - 0.12], [P.x + 0.22, P.y - 0.1]], 0.26,
        M.oscuro, (x) => (x > P.x + 0.38 ? 0.7 : 1), 0.02);
      perfil([[H.x + 0.08, H.y + 0.08], [H.x - 0.03, H.y + 0.24], [H.x - 0.08, H.y + 0.22], [H.x - 0.06, H.y + 0.1]], 0.26, M.vidrio, decor, 0, 0.01);
      // Faros gemelos sobre la nariz (antes quedaban dentro del carenado y no se veían), con su marco negro
      for (const lado of [1, -1]) {
        // (el carenado tiene un bisel de 3 cm: los faros van por fuera de esa superficie)
        caja(0.02, 0.05, 0.07, M.oscuro, V(H.x + 0.238, H.y - 0.085, lado * 0.045), decor, -0.62);
        caja(0.012, 0.04, 0.058, M.luz, V(H.x + 0.246, H.y - 0.082, lado * 0.045), decor, -0.62);
      }
      // Toma de aire central bajo los faros
      caja(0.016, 0.026, 0.06, M.oscuro, V(H.x + 0.262, H.y - 0.14, 0), decor, -0.35);
    }
  }

  // ----- Detalles que dan realismo -----
  // Tablero de instrumentos
  const tablero = caja(0.07, 0.05, 0.14, M.tablero, V(H.x - 0.07, H.y + altoManubrio + 0.05, 0), decor);
  tablero.rotation.z = -0.5;
  // la cara de arriba del tablero mira hacia (sen 0,5; cos 0,5): la pantalla va pegada a esa cara
  caja(0.052, 0.003, 0.11, M.pantalla, V(H.x - 0.07 + Math.sin(0.5) * 0.026, H.y + altoManubrio + 0.05 + Math.cos(0.5) * 0.026, 0), decor, -0.5);
  if (!scooter) {
    const ambar = new THREE.MeshStandardMaterial({ color: 0xffb347, emissive: 0xff9a1f, emissiveIntensity: 0.35, roughness: 0.25 });
    for (const lado of [1, -1]) {
      // Direccional delantera en su tallo, a los lados del faro
      const base = V(H.x + 0.04, H.y - 0.12, lado * 0.09);
      const punta = base.clone().add(V(0.04, 0.0, lado * 0.06));
      if (!specs.carenado) {
        tubo(base, punta, 0.006, M.oscuro, decor, 8);
        const dir = caja(0.03, 0.018, 0.022, ambar, punta.clone().add(V(0.012, 0, lado * 0.008)), decor);
        dir.rotation.y = -lado * 0.3;
      }
    }
    // Agarradera del parrillero (motos de calle y enduro)
    if (tipo !== "sport") {
      // Por encima del colín y por fuera del asiento del parrillero (antes quedaba medio enterrada en el costado),
      // con dos soportes que bajan hasta el colín a cada lado.
      const y = alturaAsiento + 0.025;
      // (el asiento tiene bisel: la agarradera va un poco más afuera para no quedar escondida dentro de él)
      const agarradera = new THREE.CatmullRomCurve3([V(P.x - 0.14, y - 0.01, 0.18), V(xR + 0.16, y + 0.01, 0.15),
        V(xR + 0.03, y + 0.02, 0.09), V(xR + 0.03, y + 0.02, -0.09), V(xR + 0.16, y + 0.01, -0.15), V(P.x - 0.14, y - 0.01, -0.18)]);
      malla(new THREE.TubeGeometry(agarradera, 60, 0.0095, 10), M.chasis, decor);
      for (const lado of [1, -1]) {
        for (const [x, zz] of [[P.x - 0.14, 0.18], [xR + 0.2, 0.15]]) {
          tubo(V(x, y - 0.012, lado * zz), V(x, alturaAsiento - 0.05, lado * (zz - 0.04)), 0.008, M.chasis, decor, 8);
        }
      }
    }
    // Cable del clutch (izquierda) y del acelerador (derecha), del manubrio al motor
    const cableClutch = new THREE.CatmullRomCurve3([V(H.x - 0.02, H.y + altoManubrio, anchoManubrio - 0.13),
      V(H.x + 0.04, H.y - 0.05, 0.11), V(H.x - 0.08, H.y - 0.25, 0.12), V(P.x + 0.32, P.y + 0.1, 0.13)]);
    malla(new THREE.TubeGeometry(cableClutch, 40, 0.0035, 6), M.oscuro, decor);
    const cableGas = new THREE.CatmullRomCurve3([V(H.x - 0.02, H.y + altoManubrio, -anchoManubrio + 0.12),
      V(H.x + 0.03, H.y - 0.04, -0.1), V(H.x - 0.12, H.y - 0.16, -0.08), V(P.x + 0.12, alturaAsiento - 0.24, -0.04)]);
    malla(new THREE.TubeGeometry(cableGas, 40, 0.0032, 6), M.oscuro, decor);
  }
  // Manguera del freno delantero (del manubrio al caliper)
  if (specs.freno_delantero === "disco") {
    const curvaFreno = new THREE.CatmullRomCurve3([
      V(H.x - 0.04, H.y + altoManubrio, anchoManubrio - 0.1), V(H.x + 0.05, H.y - 0.05, zBarra + 0.03),
      V(xF - 0.02, Rf + 0.22, zBarra + 0.03), V(xF - 0.05, Rf + 0.1, anchoF * 0.55 + 0.04),
    ]);
    malla(new THREE.TubeGeometry(curvaFreno, 48, 0.0045, 8), M.oscuro, decor);
  }
  if (!scooter) {
    // Posapiés del conductor
    for (const lado of [1, -1]) {
      tubo(V(P.x + 0.08, P.y - 0.04, lado * 0.09), V(P.x + 0.08, P.y - 0.04, lado * 0.2), 0.013, M.caucho, decor);
    }
    // Posapiés del parrillero
    for (const lado of [1, -1]) {
      tubo(V(P.x - 0.16, P.y + 0.02, lado * 0.09), V(P.x - 0.17, P.y + 0.03, lado * 0.19), 0.011, M.caucho, decor, 10);
      tubo(V(P.x - 0.06, P.y + 0.1, lado * 0.09), V(P.x - 0.16, P.y + 0.02, lado * 0.1), 0.008, M.chasis, decor, 8);
    }
  }
  // ----- Personalidad por tipo de moto -----
  if (!scooter) {
    const Em = V(P.x + 0.2 * s + 0.04, P.y + 0.05); // centro del motor (el mismo de la sección "Motor")
    if ((tipo === "calle" || tipo === "semi") && specs.cilindraje <= 125) {
      // Defensa cromada delante del motor (muy común en las motos de trabajo en Colombia)
      for (const lado of [1, -1]) {
        const defensa = new THREE.CatmullRomCurve3([
          V(Em.x + 0.2 * s, Em.y + 0.24, lado * 0.06), V(Em.x + 0.32 * s, Em.y + 0.15, lado * 0.22),
          V(Em.x + 0.33 * s, Em.y - 0.01, lado * 0.27), V(Em.x + 0.24 * s, Em.y - 0.1, lado * 0.15),
        ]);
        malla(new THREE.TubeGeometry(defensa, 28, 0.014, 12), M.cromo, decor);
      }
    }
    if (tipo === "calle" && specs.cilindraje >= 150 && !specs.carenado) {
      // Chasis perimetral a la vista: dos largueros plateados que bajan de la tijera al pivote pasando bajo el tanque
      const chasisVisto = new THREE.MeshStandardMaterial({ color: 0xb8bec2, roughness: 0.35, metalness: 0.75 });
      for (const lado of [1, -1]) {
        const larguero = new THREE.CatmullRomCurve3([V(H.x - 0.03, H.y - 0.06, lado * 0.05), V(H.x - 0.16, H.y - 0.13, lado * 0.115),
          V(P.x + 0.2, P.y + 0.2, lado * 0.125), V(P.x + 0.04, P.y + 0.08, lado * 0.11), V(P.x, P.y, lado * 0.09)]);
        malla(new THREE.TubeGeometry(larguero, 40, 0.017, 10), chasisVisto, decor);
      }
      // Naked: quilla corta bajo el motor, en negro
      panelAhusado([[Em.x - 0.1 * s, Em.y - 0.12 * s], [Em.x + 0.2 * s, Em.y - 0.11 * s], [Em.x + 0.24 * s, Em.y - 0.03 * s],
        [Em.x + 0.16 * s, Em.y - 0.16 * s], [Em.x - 0.06 * s, Em.y - 0.17 * s]], 0.24, M.oscuro, (x) => (x > Em.x + 0.15 * s ? 0.75 : 1), 0.015);
    }
    if ((tipo === "calle" && specs.cilindraje <= 125) || tipo === "semi" || tipo === "enduro") {
      // Parrilla metálica trasera detrás del asiento (casi todas las motos de trabajo en Colombia la llevan)
      const yP = alturaAsiento + 0.06, x0 = xR + 0.06, x1 = xR - 0.15, zP = 0.085;
      const marcoP = new THREE.CatmullRomCurve3([V(x0, yP, zP), V(x1 + 0.02, yP, zP), V(x1, yP, zP * 0.6), V(x1, yP, -zP * 0.6),
        V(x1 + 0.02, yP, -zP), V(x0, yP, -zP)]);
      malla(new THREE.TubeGeometry(marcoP, 40, 0.008, 8), M.chasis, decor);
      for (let k = 1; k <= 3; k++) tubo(V(x0 + (x1 - x0) * k / 4, yP, zP), V(x0 + (x1 - x0) * k / 4, yP, -zP), 0.006, M.chasis, decor, 6);
      for (const lado of [1, -1]) {
        tubo(V(x0, yP, lado * zP), V(x0 + 0.02, alturaAsiento - 0.02, lado * (zP - 0.01)), 0.008, M.chasis, decor, 8);
        tubo(V(x1 + 0.06, yP, lado * zP), V(x1 + 0.08, alturaAsiento - 0.03, lado * (zP - 0.02)), 0.008, M.chasis, decor, 8);
      }
      // Pedal de arranque (patada) al lado derecho, detrás del motor
      const ejeP = V(Em.x - 0.1 * s, Em.y + 0.02, -0.12 * s - 0.03);
      tubo(ejeP, V(Em.x - 0.22 * s, Em.y - 0.06, -0.12 * s - 0.04), 0.008, M.cromo, decor, 8);
      tubo(V(Em.x - 0.22 * s, Em.y - 0.06, -0.12 * s - 0.04), V(Em.x - 0.22 * s, Em.y - 0.06, -0.12 * s - 0.09), 0.009, M.caucho, decor, 8);
      disco(0.014, 0.02, M.oscuro, ejeP, decor, 12).rotation.set(0, 0, 0);
    }
    if (tipo === "enduro") {
      // Enduro: protector de cárter (cubre el motor por debajo) y cubremanos
      panelAhusado([[Em.x - 0.12 * s, Em.y - 0.15 * s], [Em.x + 0.18 * s, Em.y - 0.15 * s], [Em.x + 0.26 * s, Em.y - 0.04 * s],
        [Em.x + 0.24 * s, Em.y - 0.02 * s], [Em.x + 0.15 * s, Em.y - 0.12 * s], [Em.x - 0.1 * s, Em.y - 0.12 * s]], 0.2, M.metal,
      () => 1, 0.01);
      for (const lado of [1, -1]) {
        const cubre = elipsoide(0.075, 0.032, 0.022, pintura, V(H.x + 0.035, H.y + altoManubrio + 0.005, lado * (anchoManubrio - 0.07)), decor);
        cubre.rotation.y = -lado * 0.25;
      }
    }
  }

  // Gato lateral (lado izquierdo), apoyado en el piso, en todas las motos. Va en su propio grupo con pivote arriba
  // para recogerlo cuando la moto anda. En las scooter sale de debajo del piso.
  const arribaPata = scooter ? V(P.x + 0.12, P.y - 0.06, 0.12) : V(P.x + 0.02, P.y - 0.05, 0.1);
  const piePata = scooter ? V(P.x - 0.06, 0.012, 0.24) : V(P.x - 0.2, 0.012, 0.23);
  pata = new THREE.Group();
  pata.position.copy(arribaPata);
  decor.add(pata);
  tubo(V(0, 0, 0), piePata.clone().sub(arribaPata), 0.01, M.chasis, pata, 10);
  caja(0.045, 0.008, 0.03, M.chasis, piePata.clone().sub(arribaPata), pata);
  // Recogida: queda acostada hacia atrás, pegada al chasis
  const haciaPie = piePata.clone().sub(arribaPata).normalize();
  pata.userData.recogida = new THREE.Quaternion().setFromUnitVectors(haciaPie, V(-0.97, 0.12, 0.2).normalize());

  // Placa amarilla (como en Colombia) detrás de la llanta trasera, sobre su porta placa negro y colgada de un soporte
  // que baja desde la cola. Se calcula para que nunca toque la llanta.
  const yPlaca = Rr + (scooter ? 0.17 : 0.2);
  const hBorde = yPlaca - 0.042 - Rr;
  const xPlaca = xR - Math.sqrt(Math.max(0, Rr * Rr - hBorde * hBorde)) - 0.05;
  const inclinacion = -0.22; // arriba hacia adelante, como cuelga bajo la cola
  caja(0.012, 0.1, 0.222, M.oscuro, V(xPlaca + 0.008, yPlaca, 0), decor).rotation.z = inclinacion;
  const placa = caja(0.006, 0.084, 0.204, M.placa, V(xPlaca, yPlaca, 0), decor);
  placa.userData.conservar = true; // la lámina con el número se le pega después: no se une con otras piezas
  placa.rotation.z = inclinacion;
  const arribaSoporte = scooter ? V(xR - 0.03, yPlaca + 0.15, 0) : V(xR - 0.03, alturaAsiento - 0.11, 0);
  for (const z of [0.05, -0.05]) {
    tubo(V(arribaSoporte.x, arribaSoporte.y, z), V(xPlaca + 0.03, yPlaca + 0.055, z), 0.008, M.oscuro, decor, 8);
  }
  // Reflector rojo bajo la placa (obligatorio en Colombia)
  const reflector = new THREE.MeshStandardMaterial({ color: 0xc62828, emissive: 0x7a0c0c, emissiveIntensity: 0.35, roughness: 0.25 });
  const posRefl = V(xPlaca + 0.004 + Math.sin(inclinacion) * 0.06, yPlaca - 0.062, 0);
  caja(0.01, 0.022, 0.07, M.oscuro, posRefl.clone().add(V(0.004, 0, 0)), decor).rotation.z = inclinacion;
  caja(0.006, 0.016, 0.06, reflector, posRefl, decor).rotation.z = inclinacion;
  if (!scooter) {
    // Palanca de cambios (izquierda) y pedal del freno trasero (derecha), delante de los posapiés
    tubo(V(P.x + 0.06, P.y - 0.02, 0.15), V(P.x + 0.21, P.y - 0.005, 0.165), 0.007, M.chasis, decor, 8);
    tubo(V(P.x + 0.21, P.y - 0.005, 0.15), V(P.x + 0.21, P.y - 0.005, 0.2), 0.008, M.caucho, decor, 8);
    tubo(V(P.x + 0.04, P.y - 0.06, -0.15), V(P.x + 0.2, P.y - 0.075, -0.16), 0.007, M.chasis, decor, 8);
    caja(0.035, 0.008, 0.03, M.chasis, V(P.x + 0.21, P.y - 0.075, -0.17), decor);
    // Pito bajo el faro
    if (!specs.carenado) {
      const pito = disco(0.024, 0.014, M.oscuro, V(H.x + 0.03, H.y - 0.21, 0.03), decor, 18);
      pito.rotation.set(0, 0, Math.PI / 2);
    }
  }
  // Luz de placa y direccionales a los lados
  caja(0.02, 0.014, 0.05, M.oscuro, V(xPlaca + 0.016, yPlaca + 0.066, 0), decor).rotation.z = inclinacion;
  if (!scooter) {
    const ambarTras = new THREE.MeshStandardMaterial({ color: 0xffb347, emissive: 0xff9a1f, emissiveIntensity: 0.3 });
    for (const lado of [1, -1]) {
      tubo(V(xPlaca + 0.03, yPlaca + 0.06, lado * 0.08), V(xPlaca + 0.02, yPlaca + 0.06, lado * 0.15), 0.006, M.oscuro, decor, 6);
      caja(0.035, 0.02, 0.025, ambarTras, V(xPlaca + 0.015, yPlaca + 0.06, lado * 0.162), decor);
    }
  }

  // Rendimiento: las piezas decorativas sueltas que comparten material (tornillos, soportes, cables, aletas…)
  // se unen en una sola malla por material. Menos mallas = menos llamadas de dibujo = anda mejor en celulares.
  // No se tocan las piezas con datos propios (carrocería para calcas, franjas, piezas internas, etc.).
  unirDecorado(decor);
  // Lo mismo dentro de cada pieza de mantenimiento: la pieza se sigue reconociendo por su grupo (al tocarla,
  // al colorear su estado), así que unir sus mallas no cambia nada para el usuario.
  for (const g of Object.values(piezas)) unirDecorado(g);

  // Centra la moto en el origen para que gire sobre sí misma.
  const caja3 = new THREE.Box3().setFromObject(raiz);
  raiz.position.x = -(caja3.min.x + caja3.max.x) / 2;
  // Ejes para girar las ruedas en la animación de la portada: el rin, la llanta y los radios cuelgan de un pivote en el centro
  const ruedas = [[piezas.llanta_del, centroDel, Rf], [piezas.llanta_tras, centroTras, Rr]].map(([g, centro, R]) => {
    const pivote = new THREE.Group();
    pivote.position.copy(centro);
    g.add(pivote);
    for (const hijo of [...g.children]) if (hijo !== pivote) pivote.attach(hijo);
    return { pivote, R };
  });
  return { raiz, piezas, M, ruedas, pata, placa };
}

// =====================================================================
// Calcas: diseños propios dibujados en canvas
// =====================================================================
function aclarar(hex, cantidad) {
  const c = new THREE.Color(hex);
  c.lerp(new THREE.Color(0xffffff), cantidad);
  return `#${c.getHexString()}`;
}

function texturaCalca(diseno, color, texto) {
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

// Contorno convexo de dos círculos (para el recorrido de la cadena).
function cascoCirculos(circulos) {
  const puntos = [];
  for (const [cx, cy, r] of circulos) {
    for (let i = 0; i < 40; i++) {
      const a = (i / 40) * Math.PI * 2;
      puntos.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]);
    }
  }
  puntos.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cruz = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const inferior = [];
  for (const p of puntos) {
    while (inferior.length >= 2 && cruz(inferior.at(-2), inferior.at(-1), p) <= 0) inferior.pop();
    inferior.push(p);
  }
  const superior = [];
  for (const p of puntos.slice().reverse()) {
    while (superior.length >= 2 && cruz(superior.at(-2), superior.at(-1), p) <= 0) superior.pop();
    superior.push(p);
  }
  return inferior.slice(0, -1).concat(superior.slice(0, -1));
}

// Número de la placa sobre la placa trasera, como las placas de Colombia: fondo amarillo, borde negro,
// todos los caracteres en una sola fila (ABC 12D) y el país abajo en letra pequeña.
function ponerPlaca(placa, texto) {
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
    new THREE.MeshStandardMaterial({ map: textura, roughness: 0.45, metalness: 0.05, polygonOffset: true, polygonOffsetFactor: -2 }),
  );
  lamina.rotation.y = -Math.PI / 2;
  lamina.position.x = -0.0036;
  placa.add(lamina);
}

// Subdivisión adaptativa: solo se parten las aristas más largas que `maximo` (las de las tapas grandes); las caras
// ya densas quedan igual. Como la decisión es por arista (compartida entre vecinos), no quedan grietas ni "T".
function subdividir(geo, maximo, vueltas = 4) {
  const pos = Array.from(geo.attributes.position.array);
  let idx = Array.from(geo.index.array);
  const largo = (a, b) => Math.hypot(pos[a * 3] - pos[b * 3], pos[a * 3 + 1] - pos[b * 3 + 1], pos[a * 3 + 2] - pos[b * 3 + 2]);
  for (let v = 0; v < vueltas; v++) {
    const medios = new Map();
    const clave = (a, b) => (a < b ? a * 4194304 + b : b * 4194304 + a);
    let partidas = 0;
    for (let i = 0; i < idx.length; i += 3) {
      for (const [a, b] of [[idx[i], idx[i + 1]], [idx[i + 1], idx[i + 2]], [idx[i + 2], idx[i]]]) {
        const k = clave(a, b);
        if (!medios.has(k) && largo(a, b) > maximo) {
          medios.set(k, pos.length / 3);
          pos.push((pos[a * 3] + pos[b * 3]) / 2, (pos[a * 3 + 1] + pos[b * 3 + 1]) / 2, (pos[a * 3 + 2] + pos[b * 3 + 2]) / 2);
          partidas++;
        }
      }
    }
    if (!partidas) break;
    const nuevo = [];
    for (let i = 0; i < idx.length; i += 3) {
      const t = [idx[i], idx[i + 1], idx[i + 2]];
      const m = [medios.get(clave(t[0], t[1])), medios.get(clave(t[1], t[2])), medios.get(clave(t[2], t[0]))];
      const n = m.filter((x) => x !== undefined).length;
      if (n === 0) { nuevo.push(...t); continue; }
      if (n === 3) { nuevo.push(t[0], m[0], m[2], m[0], t[1], m[1], m[2], m[1], t[2], m[0], m[1], m[2]); continue; }
      // Girar para que la (primera) arista partida sea la de t[0]→t[1]
      let r = 0;
      if (n === 1) r = m.findIndex((x) => x !== undefined);
      else r = m[0] === undefined ? 1 : m[1] === undefined ? 2 : 0; // con dos partidas: la que sigue a la no partida
      const a = t[r], b = t[(r + 1) % 3], c = t[(r + 2) % 3];
      const mab = m[r], mbc = m[(r + 1) % 3];
      if (n === 1) nuevo.push(a, mab, c, mab, b, c);
      else nuevo.push(mab, b, mbc, a, mab, mbc, a, mbc, c);
    }
    idx = nuevo;
  }
  const salida = new THREE.BufferGeometry();
  salida.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  salida.setIndex(idx);
  return salida;
}

// Une las mallas sueltas de un grupo que comparten material en una sola (ver "Rendimiento" en construirMoto).
function unirDecorado(grupo) {
  const porMaterial = new Map();
  for (const m of [...grupo.children]) {
    if (!m.isMesh || m.isInstancedMesh || m.children.length || Object.keys(m.userData).length) continue;
    if (!porMaterial.has(m.material)) porMaterial.set(m.material, []);
    porMaterial.get(m.material).push(m);
  }
  for (const [material, lista] of porMaterial) {
    if (lista.length < 3) continue;
    const geos = lista.map((m) => {
      m.updateMatrix();
      const g = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
      for (const k of Object.keys(g.attributes)) if (k !== "position" && k !== "normal") g.deleteAttribute(k);
      if (!g.attributes.normal) g.computeVertexNormals();
      g.applyMatrix4(m.matrix);
      return g;
    });
    const unida = mergeGeometries(geos);
    geos.forEach((g) => g.dispose());
    if (!unida) continue;
    for (const m of lista) { grupo.remove(m); m.geometry.dispose(); }
    const malla = new THREE.Mesh(unida, material);
    malla.castShadow = true;
    grupo.add(malla);
  }
}
