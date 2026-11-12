// Modelo 3D de la moto del usuario, armado a partir de la ficha técnica de su línea.
// Cada pieza de mantenimiento es un grupo con userData.pieza para colorearla y seleccionarla.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

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
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  contenedor.prepend(renderer.domElement);

  const escena = new THREE.Scene();
  const camara = new THREE.PerspectiveCamera(34, 1, 0.05, 50);
  const POS_INICIAL = V(2.3, 1.25, 2.7);
  camara.position.copy(POS_INICIAL);

  escena.add(new THREE.HemisphereLight(0xf4ead2, 0x1b2a28, 1.35));
  const sol = new THREE.DirectionalLight(0xffffff, 2.2);
  sol.position.set(2.5, 4, 3);
  sol.castShadow = true;
  sol.shadow.mapSize.set(1024, 1024);
  Object.assign(sol.shadow.camera, { left: -2, right: 2, top: 2, bottom: -2 });
  escena.add(sol);
  const contraluz = new THREE.DirectionalLight(0xe3a72f, 0.7);
  contraluz.position.set(-3, 2, -2);
  escena.add(contraluz);

  const suelo = new THREE.Mesh(new THREE.CircleGeometry(1.7, 48), new THREE.ShadowMaterial({ opacity: 0.38 }));
  suelo.rotation.x = -Math.PI / 2;
  suelo.receiveShadow = true;
  escena.add(suelo);
  const anillo = new THREE.Mesh(
    new THREE.RingGeometry(1.55, 1.58, 64),
    new THREE.MeshBasicMaterial({ color: 0xede3cc, transparent: true, opacity: 0.12 }),
  );
  anillo.rotation.x = -Math.PI / 2;
  anillo.position.y = 0.001;
  escena.add(anillo);

  const moto = construirMoto(datos.specs, datos.color);
  escena.add(moto.raiz);

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

  // ---------- Estado de las piezas ----------
  let modo = "estado";
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
    const mallas = [];
    moto.raiz.traverse((obj) => { if (obj.isMesh) mallas.push(obj); });
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
        obj.material = estado ? matEstado[estado].clone() : ghost;
      } else if (estado) {
        // Rayos X: piezas internas sólidas; sus carcasas, translúcidas para ver adentro.
        const m = matEstado[estado].clone();
        if (!interno) Object.assign(m, { transparent: true, opacity: 0.28, depthWrite: false });
        obj.material = m;
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
  }

  function piezaDe(obj) {
    while (obj && obj !== moto.raiz) {
      if (obj.userData.pieza) return obj.userData.pieza;
      obj = obj.parent;
    }
    return null;
  }

  function resaltar(pieza) {
    moto.raiz.traverse((obj) => {
      if (!obj.isMesh || !obj.material.emissive) return;
      const activa = pieza && piezaDe(obj) === pieza;
      obj.userData.pulso = activa;
      if (!activa && modo === "estado" && piezaDe(obj) && estadoDe(piezaDe(obj))) {
        obj.material.emissiveIntensity = 0.25;
      }
    });
  }

  function seleccionar(pieza) {
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
    const ir = document.createElement("button");
    ir.type = "button";
    ir.className = "boton-texto mt-3";
    ir.textContent = "Ver en el plan";
    ir.addEventListener("click", () => {
      document.querySelector(`.tarea[data-pieza="${pieza}"]`)?.scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "center" });
    });
    ficha.appendChild(ir);
    if (window.TallerYaDespiece?.tiene(pieza)) {
      const ver = document.createElement("button");
      ver.type = "button";
      ver.className = "boton-texto mt-3 ml-4";
      ver.textContent = "Ver despiece";
      ver.addEventListener("click", () => window.TallerYaDespiece.mostrar(pieza));
      ficha.appendChild(ver);
    }
  }

  // ---------- Interacción ----------
  const raycaster = new THREE.Raycaster();
  const puntero = new THREE.Vector2();
  let inicioToque = null;

  function piezaBajo(evento) {
    const r = renderer.domElement.getBoundingClientRect();
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
    if (!movido) seleccionar(piezaBajo(e));
  });
  renderer.domElement.addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse") return;
    renderer.domElement.style.cursor = piezaBajo(e) ? "pointer" : "";
  });

  document.querySelectorAll(".visor-modo button").forEach((boton) => {
    boton.addEventListener("click", () => {
      modo = boton.dataset.modo;
      document.querySelectorAll(".visor-modo button").forEach((b) => b.setAttribute("aria-pressed", String(b === boton)));
      aplicarModo();
    });
  });
  document.getElementById("visor-centrar").addEventListener("click", () => {
    camara.position.copy(POS_INICIAL);
    controles.target.set(0, 0.5, 0);
    seleccionar(null);
  });
  document.querySelectorAll(".tarea").forEach((el) => {
    el.addEventListener("click", (e) => {
      if (e.target.closest("details, form, a, button")) return;
      seleccionar(el.dataset.pieza);
      contenedor.scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "center" });
    });
  });

  function ajustarTamano() {
    const { clientWidth: w, clientHeight: h } = contenedor;
    renderer.setSize(w, h, false);
    camara.aspect = w / h;
    camara.fov = w < 500 ? 44 : 34;
    camara.updateProjectionMatrix();
  }
  new ResizeObserver(ajustarTamano).observe(contenedor);
  ajustarTamano();

  aplicarModo();
  // Al abrir, selecciona lo más urgente para que se vea de una vez qué toca.
  const urgente = Object.entries(datos.piezas).find(([, p]) => p.estado === "vencido");
  if (urgente && contenedor.clientWidth >= 640) seleccionar(urgente[0]);

  const reloj = new THREE.Clock();
  renderer.setAnimationLoop(() => {
    const t = reloj.getElapsedTime();
    moto.raiz.traverse((obj) => {
      if (obj.isMesh && obj.userData.pulso && obj.material.emissive) {
        obj.material.emissiveIntensity = 0.35 + (reducido ? 0.3 : 0.3 * (1 + Math.sin(t * 4)));
      }
    });
    controles.update();
    renderer.render(escena, camara);
  });
  cargando?.remove();
  document.getElementById("visor-ayuda").hidden = false;
  window.__moto3dListo = true;
}

// =====================================================================
// Construcción procedural
// =====================================================================
function construirMoto(specs, colorPintura) {
  const raiz = new THREE.Group();
  const tipo = specs.tipo;
  const scooter = tipo === "scooter";

  // ----- Materiales -----
  const M = {
    pintura: new THREE.MeshStandardMaterial({ color: colorPintura, metalness: 0.35, roughness: 0.38 }),
    oscuro: new THREE.MeshStandardMaterial({ color: 0x1e2325, roughness: 0.75, metalness: 0.2 }),
    chasis: new THREE.MeshStandardMaterial({ color: 0x2b3134, roughness: 0.55, metalness: 0.5 }),
    metal: new THREE.MeshStandardMaterial({ color: 0xbfc5c9, roughness: 0.28, metalness: 0.9 }),
    cromo: new THREE.MeshStandardMaterial({ color: 0xe6eaec, roughness: 0.12, metalness: 1 }),
    motor: new THREE.MeshStandardMaterial({ color: 0x6b7276, roughness: 0.45, metalness: 0.7 }),
    carter: new THREE.MeshStandardMaterial({ color: 0x4a5054, roughness: 0.5, metalness: 0.6 }),
    caucho: new THREE.MeshStandardMaterial({ color: 0x151515, roughness: 0.95 }),
    asiento: new THREE.MeshStandardMaterial({ color: 0x17191a, roughness: 0.9 }),
    rojo: new THREE.MeshStandardMaterial({ color: 0xc0392b, roughness: 0.4, metalness: 0.3 }),
    resorte: new THREE.MeshStandardMaterial({ color: tipo === "sport" ? 0xe3a72f : 0xc0392b, roughness: 0.35, metalness: 0.4 }),
    luz: new THREE.MeshStandardMaterial({ color: 0xfff6d8, emissive: 0xfff1c4, emissiveIntensity: 0.9 }),
    stop: new THREE.MeshStandardMaterial({ color: 0xff3b2f, emissive: 0xff2a1f, emissiveIntensity: 0.6 }),
    vidrio: new THREE.MeshStandardMaterial({ color: 0x9fb4bd, transparent: true, opacity: 0.35, roughness: 0.05 }),
    radiador: new THREE.MeshStandardMaterial({ color: 0x2a2f31, roughness: 0.6, metalness: 0.6 }),
    bateria: new THREE.MeshStandardMaterial({ color: 0x222628, roughness: 0.6 }),
    bujia: new THREE.MeshStandardMaterial({ color: 0xf1ede4, roughness: 0.3 }),
    aceiteVisible: new THREE.MeshStandardMaterial({ color: 0xd99a1e, transparent: true, opacity: 0.8, roughness: 0.2 }),
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
  function tubo(a, b, r, mat, padre, seg = 12) {
    const dir = new THREE.Vector3().subVectors(b, a);
    const m = malla(new THREE.CylinderGeometry(r, r, dir.length(), seg), mat, padre);
    m.position.copy(a).add(b).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
    return m;
  }
  function disco(radio, grosor, mat, pos, padre, seg = 32) {
    const m = malla(new THREE.CylinderGeometry(radio, radio, grosor, seg), mat, padre);
    m.rotation.x = Math.PI / 2;
    m.position.copy(pos);
    return m;
  }
  function perfil(puntos, ancho, mat, padre, z = 0, bisel = 0.014, suave = false) {
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
      depth: ancho, bevelEnabled: bisel > 0, bevelSize: bisel, bevelThickness: bisel, bevelSegments: 3, curveSegments: 12,
    });
    geo.translate(0, 0, -ancho / 2 + z);
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
    const neumatico = malla(new THREE.TorusGeometry(rinR + (R - rinR) / 2, (R - rinR) / 2, 18, 48), M.caucho, g);
    neumatico.position.copy(centro);
    neumatico.scale.z = ancho / (R - rinR);
    const aro = malla(new THREE.TorusGeometry(rinR, 0.012, 8, 48), M.metal, g);
    aro.position.copy(centro);
    disco(0.045, ancho * 0.9, M.metal, centro, g, 16);
    if (radios) {
      for (let i = 0; i < 18; i++) {
        const a = (i / 18) * Math.PI * 2;
        const lado = i % 2 ? 1 : -1;
        tubo(V(x, R, lado * ancho * 0.3), V(x + Math.cos(a) * rinR, R + Math.sin(a) * rinR, lado * 0.01), 0.0035, M.cromo, g, 5);
      }
    } else {
      for (let i = 0; i < 5; i++) {
        const a = (i / 5) * Math.PI * 2 + 0.3;
        const brazo = caja(rinR * 0.95, 0.03, 0.025, M.oscuro, V(x + Math.cos(a) * rinR * 0.5, R + Math.sin(a) * rinR * 0.5), g);
        brazo.rotation.z = a;
      }
    }
    // Freno (al lado izquierdo, +z)
    const f = grupo(idFreno);
    const zFreno = ancho * 0.55 + 0.02;
    if (tipoFreno === "disco") {
      const radioDisco = Math.min(rinR * 0.85, 0.15);
      disco(radioDisco, 0.006, M.metal, V(x, R, zFreno), f, 40);
      disco(radioDisco * 0.45, 0.012, M.oscuro, V(x, R, zFreno), f, 20);
      const ang = idFreno === "freno_del" ? 2.3 : 1.2;
      const posCaliper = V(x + Math.cos(ang) * radioDisco * 0.88, R + Math.sin(ang) * radioDisco * 0.88, zFreno + 0.01);
      caja(0.07, 0.05, 0.04, M.rojo, posCaliper, f, ang);
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
  llanta(xF, Rf, anchoF, specs.rin_delantero, "llanta_del", "freno_del", specs.freno_delantero, radios);
  llanta(xR, Rr, anchoR, specs.rin_trasero, "llanta_tras", "freno_tras", specs.freno_trasero, radios);

  // ----- Suspensión delantera -----
  const susDel = grupo("suspension_del");
  const zBarra = anchoF / 2 + 0.045;
  for (const lado of [1, -1]) {
    const eje = V(xF, Rf, lado * zBarra);
    const pipa = V(H.x, H.y, lado * zBarra);
    const medio = eje.clone().lerp(pipa, 0.55);
    tubo(eje, medio, tipo === "enduro" ? 0.028 : 0.022, tipo === "sport" ? M.oscuro : M.metal, susDel);
    tubo(medio, pipa, tipo === "enduro" ? 0.022 : 0.017, M.cromo, susDel);
  }
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
    const base = V(H.x - 0.04, H.y + altoManubrio, lado * (anchoManubrio - 0.06));
    const punta = base.clone().add(V(-0.03, 0.1, lado * 0.08));
    tubo(base, punta, 0.006, M.oscuro, decor);
    elipsoide(0.012, 0.028, 0.045, M.oscuro, punta, decor);
  }
  if (!scooter && tipo !== "sport") {
    const faro = disco(tipo === "enduro" ? 0.06 : 0.085, 0.07, M.oscuro, V(H.x + 0.09, H.y - 0.06, 0), decor, 24);
    faro.rotation.set(0, Math.PI / 2, 0);
    const lente = disco(tipo === "enduro" ? 0.05 : 0.075, 0.01, M.luz, V(H.x + 0.126, H.y - 0.06, 0), decor, 24);
    lente.rotation.set(0, Math.PI / 2, 0);
    if (tipo === "enduro") {
      perfil([[0, -0.1], [0.05, -0.12], [0.08, 0.1], [0.02, 0.14], [-0.02, 0.05]], 0.18, M.pintura, decor).position.set(H.x + 0.07, H.y - 0.06, 0);
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
      tubo(V(espina.x, espina.y, z), V(xR + 0.12, alturaAsiento - 0.1, z), 0.014, M.chasis, chasis);
      tubo(V(P.x, P.y, z), V(xR + 0.18, alturaAsiento - 0.14, z), 0.012, M.chasis, chasis);
      // basculante
      tubo(V(P.x, P.y, lado * 0.085), V(xR, Rr, lado * (anchoR / 2 + 0.03)), 0.022, M.oscuro, chasis);
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
    caja(0.24, 0.1, 0.12, M.oscuro, V(xR + 0.34, Rr + 0.17, 0.13), filtro);
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
    for (let i = 0; i < 6; i++) interno(caja(0.012, 0.07, 0.1, M.bujia, V(xR + 0.27 + i * 0.024, Rr + 0.17, 0.13), filtro));
    for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) interno(caja(0.03, 0.09, 0.03, M.motor, V(P.x + 0.29 + i * 0.033, 0.46, -0.018 + j * 0.036), bateria));
  } else {
    const E = V(P.x + 0.2 * s + 0.04, P.y + 0.05);
    // Cárter (aceite)
    caja(0.32 * s, 0.17 * s, 0.24 * s, M.carter, V(E.x, E.y - 0.03), aceite);
    disco(0.022, 0.03, M.oscuro, V(E.x - 0.08 * s, E.y + 0.06, 0.13 * s), aceite, 12);
    elipsoide(0.07, 0.07, 0.03, M.carter, V(E.x + 0.05, E.y, 0.12 * s), aceite);
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
      for (let i = 0; i < 7; i++) caja(0.045, 0.006, 0.27, M.metal, V(centroRad.x, centroRad.y - 0.09 + i * 0.03), rad, -0.2);
      tubo(V(centroRad.x - 0.02, centroRad.y - 0.08, 0.1), V(E.x + 0.05, E.y + 0.08, 0.1), 0.012, M.caucho, rad);
      placa.userData.base = true;
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
    malla(new THREE.TubeGeometry(curva, 120, 0.007, 6, true), M.oscuro, cadena);
  }

  // ----- Suspensión trasera -----
  const susTras = grupo("suspension_tras");
  function amortiguador(abajo, arriba) {
    tubo(abajo, arriba, 0.012, M.cromo, susTras, 8);
    const ab = abajo.clone().lerp(arriba, 0.15);
    const ar = abajo.clone().lerp(arriba, 0.85);
    resorte(ab, ar, 0.028, 7, M.resorte, susTras);
    disco(0.02, 0.03, M.oscuro, abajo, susTras, 10);
  }
  if (specs.suspension_trasera === "doble") {
    for (const lado of [1, -1]) {
      const z = lado * (scooter ? 0.13 : anchoR / 2 + 0.035);
      amortiguador(V(xR + 0.06, Rr + 0.03, z), V(xR + 0.18, alturaAsiento - 0.12, z));
    }
  } else if (scooter) {
    amortiguador(V(xR + 0.08, Rr + 0.05, 0.14), V(xR + 0.16, alturaAsiento - 0.14, 0.14));
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
    tubo(salida, finCodo, 0.02, M.cromo, decor);
    const largo = tipo === "sport" ? 0.32 : 0.42;
    const finSil = tipo === "enduro" ? V(xR + 0.05, alturaAsiento - 0.08, -0.15) : V(xR + 0.18, Rr + 0.14, -0.15);
    const iniSil = finCodo.clone().lerp(finSil, 1 - largo / finCodo.distanceTo(finSil));
    tubo(iniSil, finSil, tipo === "sport" ? 0.055 : 0.045, M.oscuro, decor);
    tubo(finCodo, iniSil, 0.022, M.cromo, decor);
  }

  // ----- Carrocería (color del usuario) -----
  const pintura = M.pintura;
  if (scooter) {
    // Piso, escudo frontal y carenado trasero
    caja(0.46, 0.04, 0.28, M.oscuro, V(0.14, 0.31, 0), decor);
    perfil([[xF - 0.07, Rf + 0.12], [H.x + 0.13, H.y - 0.04], [H.x + 0.03, H.y + 0.1], [H.x - 0.1, H.y - 0.04],
      [0.3, 0.46], [0.36, 0.33], [0.5, 0.31]], 0.32, pintura, decor, 0, 0.025, true);
    disco(0.06, 0.02, M.luz, V(H.x + 0.12, H.y - 0.07, 0), decor, 20).rotation.set(0, Math.PI / 2, 0);
    perfil([[-0.04, 0.33], [0.0, alturaAsiento - 0.12], [xR + 0.08, alturaAsiento - 0.06], [xR - 0.1, alturaAsiento - 0.1],
      [xR - 0.03, alturaAsiento - 0.24], [xR + 0.16, Rr + 0.21], [-0.26, 0.4]], 0.27, pintura, decor, 0, 0.03, true);
    perfil([[0.02, alturaAsiento - 0.11], [-0.04, alturaAsiento - 0.02], [-0.3, alturaAsiento - 0.03],
      [xR + 0.06, alturaAsiento + 0.01], [xR + 0.04, alturaAsiento - 0.06]], 0.25, M.asiento, decor, 0, 0.025, true);
    caja(0.04, 0.04, 0.16, M.stop, V(xR - 0.11, alturaAsiento - 0.12, 0), decor);
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
      perfil([[P.x + 0.06, P.y + 0.12], [P.x + 0.04, alturaAsiento - 0.06], [xR + 0.06, alturaAsiento - 0.04], [xR + 0.2, P.y + 0.2]],
        0.24, pintura, decor, 0, 0.025, true);
      disco(0.07, 0.06, M.oscuro, V(H.x + 0.03, H.y + 0.06, 0), decor, 20).rotation.set(0, Math.PI / 2, 0);
    } else {
      const tanque = elipsoide(tipo === "sport" ? 0.24 : 0.23, tipo === "enduro" ? 0.1 : 0.11, tipo === "enduro" ? 0.12 : 0.15,
        pintura, V(tanqueX, tanqueY, 0), decor);
      tanque.rotation.z = tipo === "sport" ? 0.18 : 0.08;
      caja(0.03, 0.02, 0.05, M.cromo, V(tanqueX + 0.02, tanqueY + 0.11, 0), decor);
      if (tipo === "enduro") {
        for (const lado of [1, -1]) {
          perfil([[0, 0], [0.22, 0.06], [0.2, -0.16], [0.05, -0.2]], 0.02, pintura, decor, lado * 0.15, 0.008)
            .position.set(tanqueX - 0.02, tanqueY - 0.02, 0);
        }
      }
    }
    // Asiento
    const inicioAsiento = tipo === "semi" ? P.x + 0.05 : tanqueX - 0.2;
    const finAsiento = xR + 0.06;
    const escalon = tipo === "sport" ? 0.05 : 0;
    perfil([[inicioAsiento, alturaAsiento - 0.04], [inicioAsiento + 0.03, alturaAsiento + 0.03], [(inicioAsiento + finAsiento) / 2, alturaAsiento + 0.03],
      [finAsiento + 0.12, alturaAsiento + 0.04 + escalon], [finAsiento, alturaAsiento + 0.02 + escalon], [finAsiento + 0.04, alturaAsiento - 0.03]],
      tipo === "enduro" ? 0.2 : 0.25, M.asiento, decor, 0, 0.025);
    // Colín y tapas laterales
    perfil([[P.x + 0.02, alturaAsiento - 0.05], [finAsiento - 0.04, alturaAsiento - 0.02 + escalon], [xR - 0.08, alturaAsiento + escalon - 0.04],
      [xR + 0.1, alturaAsiento - 0.14], [P.x - 0.12, alturaAsiento - 0.2]], 0.2, pintura, decor, 0, 0.02, true);
    caja(0.03, 0.04, 0.12, M.stop, V(xR - 0.08, alturaAsiento + escalon - 0.05, 0), decor);
    tubo(V(xR - 0.04, alturaAsiento - 0.1, 0), V(xR - 0.12, Rr + 0.15, 0), 0.01, M.oscuro, decor);
    caja(0.01, 0.12, 0.16, M.oscuro, V(xR - 0.13, Rr + 0.1, 0), decor);
    // Guardabarros delantero
    if (tipo === "enduro") {
      perfil([[-0.2, 0], [0.25, 0.03], [0.24, -0.02], [-0.18, -0.05]], 0.1, pintura, decor, 0, 0.01)
        .position.set(H.x - 0.04, H.y - 0.22, 0);
    } else {
      const guarda = malla(new THREE.TorusGeometry(Rf + 0.025, 0.012, 6, 24, Math.PI * 0.5), tipo === "calle" ? M.oscuro : pintura, decor);
      guarda.position.set(xF, Rf, 0);
      guarda.rotation.z = Math.PI * 0.22;
      guarda.scale.z = 6;
    }
    // Carenado deportivo
    if (specs.carenado) {
      perfil([[H.x + 0.22, H.y - 0.14], [H.x + 0.08, H.y + 0.08], [H.x - 0.06, H.y + 0.1], [tanqueX + 0.18, tanqueY - 0.04],
        [P.x + 0.3, P.y + 0.12], [P.x + 0.42, P.y - 0.08], [H.x + 0.06, H.y - 0.36]], 0.42, pintura, decor, 0, 0.03, true);
      perfil([[H.x + 0.08, H.y + 0.08], [H.x - 0.03, H.y + 0.24], [H.x - 0.08, H.y + 0.22], [H.x - 0.06, H.y + 0.1]], 0.26, M.vidrio, decor, 0, 0.01);
      for (const lado of [1, -1]) caja(0.02, 0.03, 0.08, M.luz, V(H.x + 0.2, H.y - 0.1, lado * 0.07), decor, -0.6);
    }
  }

  // Centra la moto en el origen para que gire sobre sí misma.
  const caja3 = new THREE.Box3().setFromObject(raiz);
  raiz.position.x = -(caja3.min.x + caja3.max.x) / 2;
  return { raiz, piezas };
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
