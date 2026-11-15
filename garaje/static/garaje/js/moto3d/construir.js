// Construcción procedural de la moto a partir de su ficha técnica.
import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { V, medir, CALIDAD, seg, ceder } from "./comun.js";
import { cachePaneles } from "./cache.js";
import { materialLetrasLlanta } from "./texturas.js";
import { cascoCirculos, subdividir, unirVertices, unirDecorado } from "./geometria.js";
import { rasgosDe } from "./rasgos.js";

// =====================================================================
// Construcción procedural
// =====================================================================
export async function construirMoto(specs, colorPintura, linea = "") {
  const esNmax = /nmax/i.test(linea);
  // Aerox: misma plataforma de maxi-scooter que la NMAX, pero deportiva (frente afilado, doble faro, túnel alto, colín corto)
  const esAerox = /aerox/i.test(linea);
  const esMaxi = esNmax || esAerox;
  // Rasgos propios de modelos populares en Medellín (sobre la base genérica de su tipo)
  const esXtz = /xtz/i.test(linea);
  const esTt = /\btt\b/i.test(linea);
  let escapeFabrica = null, escapeInfo = null; // silenciador de fábrica (se cambia por el deportivo)
  const raiz = new THREE.Group();
  const tipo = specs.tipo;
  const scooter = tipo === "scooter";
  // Rasgos de silueta de la familia y de la línea (tanque, colín, faro, escape, carenado…): ver rasgos.js
  const R = rasgosDe(linea, specs);
  const R_ = R; // (dentro de llanta() la R es el radio de la rueda)
  const fam = R.familia;

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
    rin: new THREE.MeshPhysicalMaterial({ color: R.rinColor ?? 0x2b3033, roughness: 0.3, metalness: 0.7, clearcoat: 0.8, clearcoatRoughness: 0.15 }),
    asiento: new THREE.MeshPhysicalMaterial({ color: 0x161819, roughness: 0.7, sheen: 0.6, sheenRoughness: 0.5, sheenColor: 0x555a5c }),
    rojo: new THREE.MeshPhysicalMaterial({ color: 0xb8321f, roughness: 0.3, metalness: 0.4, clearcoat: 0.7 }),
    resorte: new THREE.MeshPhysicalMaterial({ color: tipo === "sport" ? 0xe3a72f : 0xc0392b, roughness: 0.3, metalness: 0.3, clearcoat: 0.8 }),
    luz: new THREE.MeshStandardMaterial({ color: 0xfff6d8, emissive: 0xfff1c4, emissiveIntensity: 1.1, roughness: 0.1 }),
    stop: new THREE.MeshStandardMaterial({ color: 0xff3b2f, emissive: 0xff2a1f, emissiveIntensity: 0.7, roughness: 0.2 }),
    vidrio: new THREE.MeshPhysicalMaterial({ color: 0xa9bec7, transparent: true, opacity: 0.45, roughness: 0.02, metalness: 0, clearcoat: 1 }),
    radiador: new THREE.MeshStandardMaterial({ color: 0x2a2f31, roughness: 0.55, metalness: 0.7 }),
    bateria: new THREE.MeshStandardMaterial({ color: 0x222628, roughness: 0.6 }),
    bujia: new THREE.MeshStandardMaterial({ color: 0xf1ede4, roughness: 0.25 }),
    aceiteVisible: new THREE.MeshStandardMaterial({ color: 0xd99a1e, transparent: true, opacity: 0.8, roughness: 0.15 }),
    placa: new THREE.MeshStandardMaterial({ color: 0xf2c230, roughness: 0.45 }),
    tablero: new THREE.MeshPhysicalMaterial({ color: 0x0d1012, roughness: 0.1, metalness: 0.2, clearcoat: 1 }),
    // Ámbar de las direccionales (uno solo para todas: cada material distinto es otra llamada de dibujo)
    ambar: new THREE.MeshStandardMaterial({ color: 0xffb347, emissive: 0xff9a1f, emissiveIntensity: 0.35, roughness: 0.25 }),
  };

  // El tablero en el mismo negro de las demás piezas oscuras (un material menos = una llamada de dibujo menos)
  M.tablero = M.oscuro;
  // Segundo tono de la carrocería (colín y costados traseros): igual al principal hasta que la persona elija otro
  M.pintura2 = M.pintura.clone();
  // Metal por ambas caras para las medias cañas (protectores de escape): por una sola cara se veían cortadas
  // (las medias cañas se ven por las dos caras duplicando la geometría al revés, no con un material de doble cara:
  // ese material pedía un programa de sombreado más, y el tope es 16)
  M.metalDoble = M.metal;
  const dosCaras = (geo) => {
    const a = geo.index ? geo.toNonIndexed() : geo;
    if (a.attributes.uv) a.deleteAttribute("uv");
    const b = a.clone();
    const p = b.attributes.position.array, n = b.attributes.normal.array;
    for (let i = 0; i < p.length; i += 9) for (let k = 0; k < 3; k++) {
      [p[i + 3 + k], p[i + 6 + k]] = [p[i + 6 + k], p[i + 3 + k]];
      [n[i + 3 + k], n[i + 6 + k]] = [n[i + 6 + k], n[i + 3 + k]];
    }
    for (let i = 0; i < n.length; i++) n[i] = -n[i];
    return mergeGeometries([a, b]);
  };
  // Luna de los retrovisores: espejo de verdad (refleja el ambiente casi sin difuminar, con un leve tono frío)
  M.espejo = new THREE.MeshPhysicalMaterial({ color: 0xeef3f6, metalness: 1, roughness: 0.05, envMapIntensity: 3.2,
    emissive: 0x2a3a46, emissiveIntensity: 0.6, clearcoat: 1, clearcoatRoughness: 0 });

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
  // Los tubos curvos (TubeGeometry) quedan huecos en las puntas: se les pega una media esfera en cada extremo
  // para que se vean cerrados (defensas, parrillas, agarraderas, cables, radios…).
  function conTapas(geo) {
    const { path, radius, radialSegments } = geo.parameters;
    const tapas = [0, 1].map((t) => {
      const s = new THREE.SphereGeometry(radius, Math.max(6, radialSegments), Math.max(4, radialSegments >> 1));
      const p = path.getPointAt(t);
      s.translate(p.x, p.y, p.z);
      return s;
    });
    const unida = mergeGeometries([geo, ...tapas]);
    if (!unida) return geo;
    geo.dispose();
    tapas.forEach((s) => s.dispose());
    return unida;
  }
  function malla(geo, mat, padre = decor) {
    if (geo.type === "TubeGeometry") {
      const { path, tubularSegments, radius, radialSegments, closed } = geo.parameters;
      if (CALIDAD.seg < 1) {
        geo.dispose();
        geo = new THREE.TubeGeometry(path, seg(tubularSegments, 4), radius, seg(radialSegments, 5), closed);
      }
      // (los tubos finos —cables, radios, agarraderas— no llevan tapas: sus puntas quedan metidas en otra pieza y no se ven)
      if (!closed && radius >= 0.01) geo = medir("tapas", () => conTapas(geo));
    }
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
  function tubo(a, b, r, mat, padre, segs = 20) {
    const dir = new THREE.Vector3().subVectors(b, a);
    const m = malla(new THREE.CylinderGeometry(r, r, dir.length(), Math.max(5, Math.round(segs * CALIDAD.seg))), mat, padre);
    m.position.copy(a).add(b).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
    return m;
  }
  // Piezas repetidas (radios, tuercas, perforaciones, dientes, tornillos): una sola geometría dibujada muchas veces
  // con InstancedMesh. Menos memoria y menos trabajo al armar que una malla por copia.
  const _ejeY = V(0, 1, 0), _m4 = new THREE.Matrix4(), _q = new THREE.Quaternion(), _uno = V(1, 1, 1);
  function instancias(geo, mat, matrices, padre) {
    // Pocas copias: una malla normal con las copias ya ubicadas, que después se une con las demás piezas de su material
    // (una InstancedMesh siempre cuesta su propia llamada de dibujo)
    // (siempre como malla normal: una InstancedMesh necesita su propio programa de sombreado, y el tope es 16)
    if (matrices.length > 0) {
      const base = geo.index ? geo.toNonIndexed() : geo.clone();
      if (base.attributes.uv) base.deleteAttribute("uv");
      const unida = mergeGeometries(matrices.map((mx) => base.clone().applyMatrix4(mx)));
      base.dispose(); geo.dispose();
      return malla(unida, mat, padre);
    }
    const m = new THREE.InstancedMesh(geo, mat, matrices.length);
    matrices.forEach((x, i) => m.setMatrixAt(i, x));
    m.castShadow = true;
    padre.add(m);
    return m;
  }
  // Matriz de una copia: cilindro de largo 1 estirado entre a y b; disco con su eje a lo largo de z; caja girada en z
  const enTubo = (a, b) => {
    const dir = new THREE.Vector3().subVectors(b, a);
    return new THREE.Matrix4().compose(a.clone().add(b).multiplyScalar(0.5), _q.clone().setFromUnitVectors(_ejeY, dir.clone().normalize()), V(1, dir.length(), 1));
  };
  const qDisco = new THREE.Quaternion().setFromEuler(new THREE.Euler(Math.PI / 2, 0, 0));
  const enDisco = (pos) => new THREE.Matrix4().compose(pos, qDisco, _uno);
  const enCaja = (pos, rotZ = 0) => new THREE.Matrix4().compose(pos, new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, rotZ)), _uno);
  const cil = (r, alto, segs) => new THREE.CylinderGeometry(r, r, alto, Math.max(5, Math.round(segs * CALIDAD.seg)));
  function disco(radio, grosor, mat, pos, padre, segs = 48) {
    const m = malla(new THREE.CylinderGeometry(radio, radio, grosor, Math.max(6, Math.round(segs * CALIDAD.seg))), mat, padre);
    m.rotation.x = Math.PI / 2;
    m.position.copy(pos);
    return m;
  }
  // Geometría guardada en la caché del navegador (posición, normales e índices)
  function deCache(clave) {
    const guardado = cachePaneles.guardados[clave];
    if (!guardado) return null;
    cachePaneles.aciertos++;
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(guardado.p), 3));
    g.setAttribute("normal", new THREE.BufferAttribute(new Float32Array(guardado.n), 3));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(guardado.i), 1));
    return g;
  }
  function aCache(clave, geo) {
    cachePaneles.nuevos[clave] = {
      p: geo.attributes.position.array.slice().buffer, n: geo.attributes.normal.array.slice().buffer,
      i: Uint32Array.from(geo.index.array).buffer,
    };
  }
  const claveContorno = (puntos) => JSON.stringify(puntos.map((q) => q.map((v) => +v.toFixed(5))));
  // (18 segmentos por curva y 3 en el bisel: con las normales suavizadas se ve igual de liso que con 28 y 6, con menos de la mitad de triángulos)
  function perfil(puntos, ancho, mat, padre, z = 0, bisel = 0.014, suave = false, curvas = 18, biselSeg = 3, lisar = true) {
    // Piezas chicas (cálipers, tapas, soportes: menos de 10 cm): menos segmentos en la curva y el bisel, no se notan
    const xsP = puntos.map((q) => q[0]), ysP = puntos.map((q) => q[1]);
    if (Math.max(Math.max(...xsP) - Math.min(...xsP), Math.max(...ysP) - Math.min(...ysP)) < 0.1) {
      curvas = Math.max(6, Math.round(curvas * 0.6));
      biselSeg = Math.min(biselSeg, 2);
    }
    if (CALIDAD.nombre === "baja") biselSeg = Math.min(biselSeg, 2); // (en móvil el bisel de 3 pasos no se distingue del de 2)
    // Las piezas curvas suavizadas se guardan en la caché del navegador (extruir y suavizar es lo que más tarda)
    const clave = suave && lisar ? `perfil|${claveContorno(puntos)}|${ancho}|${z}|${bisel}|${curvas}|${biselSeg}` : null;
    const guardada = clave && deCache(clave);
    if (guardada) return malla(guardada, mat, padre);
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
    const geo = medir("extruir", () => new THREE.ExtrudeGeometry(forma, {
      depth: ancho, bevelEnabled: bisel > 0, bevelSize: bisel, bevelThickness: bisel, bevelSegments: biselSeg, curveSegments: seg(curvas, 6),
    }));
    geo.translate(0, 0, -ancho / 2 + z);
    if (suave && lisar) {
      // Piezas curvas (aletas, franjas, colines…): normales suavizadas para que se vean lisas, sin facetas
      // ni aristas duras entre la cara y el bisel. Cuesta muy poco (no agrega triángulos).
      let lisa = geo.index ? geo.toNonIndexed() : geo.clone();
      lisa.deleteAttribute("uv");
      lisa.deleteAttribute("normal");
      lisa = medir("suavizar", () => { const l = unirVertices(lisa); l.computeVertexNormals(); return l; });
      geo.dispose();
      aCache(clave, lisa);
      return malla(lisa, mat, padre);
    }
    return malla(geo, mat, padre);
  }
  function elipsoide(rx, ry, rz, mat, pos, padre) {
    const m = malla(new THREE.SphereGeometry(1, seg(20), seg(12)), mat, padre);
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
  const perfilLlanta = { scooter: esAerox ? 0.08 : esMaxi ? 0.065 : 0.075, semi: 0.07, calle: 0.075, sport: 0.07, enduro: 0.085 }[tipo];
  const Rf = specs.rin_delantero * 0.0127 + perfilLlanta;
  const Rr = specs.rin_trasero * 0.0127 + perfilLlanta;
  const anchoF = { scooter: 0.11, semi: 0.075, calle: 0.095, sport: 0.115, enduro: 0.085 }[tipo] * (0.9 + 0.1 * s);
  const anchoR = { scooter: 0.13, semi: 0.085, calle: 0.12, sport: 0.155, enduro: 0.105 }[tipo] * (0.9 + 0.15 * s);
  // (las scooter pequeñas de rin 10-12" son más cortas que las maxi: así las ruedas se ven proporcionadas)
  const wb = (scooter && !esMaxi ? 1.27 : { scooter: 1.34, semi: 1.22, calle: 1.3, sport: 1.36, enduro: 1.4 }[tipo]) + (s - 1) * 0.08;
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
    const geoLlanta = new THREE.LatheGeometry(contornoLlanta, seg(72));
    geoLlanta.rotateX(Math.PI / 2);
    const neumatico = malla(geoLlanta, M.caucho, g);
    neumatico.position.copy(centro);
    // Rin con canal (pestañas a los lados)
    const perfilRin = [
      [rinR - 0.02, -ancho * 0.4], [rinR + 0.006, -ancho * 0.42], [rinR + 0.004, -ancho * 0.3], [rinR - 0.012, -ancho * 0.12],
      [rinR - 0.012, ancho * 0.12], [rinR + 0.004, ancho * 0.3], [rinR + 0.006, ancho * 0.42], [rinR - 0.02, ancho * 0.4],
    ].map(([r, y]) => new THREE.Vector2(r, y));
    const geoRin = new THREE.LatheGeometry(perfilRin, seg(72));
    geoRin.rotateX(Math.PI / 2);
    const aro = malla(geoRin, radios ? M.metal : M.rin, g);
    aro.userData.aro = true; // cambia de material según el estilo de rin (no se une con otras piezas)
    aro.position.copy(centro);
    const taco = tipo === "enduro" ? [0.016, 0.012, ancho * 0.34] : [0.01, 0.004, ancho * 0.22];
    const nTacos = Math.round((tipo === "enduro" ? 40 : 56) * (CALIDAD.nombre === "baja" ? 0.6 : 1));
    const geoTaco = new THREE.BoxGeometry(...taco);
    const matTacos = [];
    const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler();
    for (let i = 0; i < nTacos * 2; i++) {
      const lado = i % 2 ? 1 : -1;
      const a = (Math.floor(i / 2) / nTacos) * Math.PI * 2 + (lado > 0 ? Math.PI / nTacos : 0);
      e.set(0, lado * 0.35, a + Math.PI / 2);
      q.setFromEuler(e);
      m4.compose(V(x + Math.cos(a) * (R - taco[1] * 0.2), R + Math.sin(a) * (R - taco[1] * 0.2), lado * ancho * 0.16), q, V(1, 1, 1));
      matTacos.push(m4.clone());
    }
    // Letras en el costado de la llanta (marca y medida), dibujadas en círculo sobre un anillo transparente
    const medida = `${Math.round(ancho * 1000 / 5) * 5}/${tipo === "scooter" ? 90 : 80}-${rin}`;
    const matLetras = materialLetrasLlanta(medida, (rinR + h * 0.5) / (rinR + h * 0.8), (h * 0.3) / (rinR + h * 0.8));
    // Los dos costados en una sola malla (una llamada de dibujo por llanta)
    const anillos = [1, -1].map((lado) => {
      const r = new THREE.RingGeometry(rinR + h * 0.22, rinR + h * 0.8, seg(64));
      if (lado < 0) r.rotateY(Math.PI);
      return r.translate(0, 0, lado * ancho * 0.535);
    });
    const anillo = malla(mergeGeometries(anillos), matLetras, g);
    anillos.forEach((r) => r.dispose());
    anillo.position.set(x, R, 0);
    anillo.castShadow = false;
    anillo.userData.conservar = true; // lleva textura: no se une con otras piezas
    instancias(geoTaco, M.labrado, matTacos, g);
    // (el buje del eje va dentro de cada estilo de rin: así se une con sus tuercas o radios en una sola malla)
    const buje = (v) => disco(0.045, ancho * 0.9, M.metal, centro, v, 16);
    // Tres estilos de rin; solo se arma el que se ve (el de fábrica o el elegido). Los otros se arman la primera vez
    // que la persona los elige al personalizar: así el armado inicial hace un tercio del trabajo de los rines.
    g.userData.aro = aro;
    const armarRin = {
      radios(v) {
        buje(v);
        instancias(cil(0.0035, 1, 5), M.cromo, Array.from({ length: 18 }, (_, i) => {
          const a = (i / 18) * Math.PI * 2;
          const lado = i % 2 ? 1 : -1;
          return enTubo(V(x, R, lado * ancho * 0.3), V(x + Math.cos(a) * rinR, R + Math.sin(a) * rinR, lado * 0.01));
        }), v);
      },
      aleacion(v) {
        buje(v);
        // Maza robusta y radios de aleación con el diseño de fábrica de la línea (rasgos.js `rinDiseno`): por defecto
        // 5 radios dobles curvos; `n` radios, `dobles` (en V) o sencillos más gruesos, `rectos` o curvos, `abre` (cuánto
        // se separan las dos ramas en el aro)
        const D = { n: 5, dobles: true, rectos: false, abre: 0.24, ...(R_.rinDiseno || {}) };
        disco(rinR * 0.3, ancho * 0.72, M.rin, centro, v, 28);
        for (let i = 0; i < D.n; i++) {
          const a = (i / D.n) * Math.PI * 2 + 0.3;
          for (const d of D.dobles ? [-1, 1] : [0]) {
            const giro = D.rectos ? 0.6 : 1; // (recto: el punto medio sobre la línea entre la maza y el aro)
            const curva = new THREE.QuadraticBezierCurve3(
              V(x + Math.cos(a) * rinR * 0.26, R + Math.sin(a) * rinR * 0.26, 0),
              V(x + Math.cos(a + d * D.abre * 0.66 * giro) * rinR * 0.62, R + Math.sin(a + d * D.abre * 0.66 * giro) * rinR * 0.62, 0),
              V(x + Math.cos(a + d * D.abre) * rinR * 0.96, R + Math.sin(a + d * D.abre) * rinR * 0.96, 0),
            );
            const radio = malla(new THREE.TubeGeometry(curva, D.rectos ? 6 : 14, D.dobles ? 0.009 : 0.012, 8), M.rin, v);
            radio.scale.z = D.dobles ? 1.8 : 2.2; // radio ovalado: más ancho que grueso
          }
        }
        tuercas(v);
      },
      estrella(v) {
        buje(v);
        // Deportivo: 7 radios rectos y delgados en estrella
        disco(rinR * 0.24, ancho * 0.7, M.rin, centro, v, 24);
        instancias(new THREE.BoxGeometry(rinR * 0.78, 0.016, 0.03), M.rin, Array.from({ length: 7 }, (_, i) => {
          const a = (i / 7) * Math.PI * 2;
          return enCaja(V(x + Math.cos(a) * rinR * 0.6, R + Math.sin(a) * rinR * 0.6), a);
        }), v);
        tuercas(v);
      },
    };
    function tuercas(v) {
      instancias(cil(0.006, ancho * 0.76, 6), M.metal, Array.from({ length: 5 }, (_, i) => {
        const a = (i / 5) * Math.PI * 2;
        return enDisco(V(x + Math.cos(a) * rinR * 0.18, R + Math.sin(a) * rinR * 0.18));
      }), v);
    }
    // Arma (si hace falta) y devuelve el grupo de un estilo de rin. Después del armado la llanta gira sobre un pivote:
    // el grupo nuevo se pasa al pivote conservando su posición.
    g.userData.armarRin = (nombre) => {
      const ya = (g.userData.pivoteRueda || g).children.find((o) => o.userData.rin === nombre);
      if (ya || !armarRin[nombre]) return ya;
      const v = new THREE.Group();
      v.userData.rin = nombre;
      g.add(v);
      armarRin[nombre](v);
      unirDecorado(v);
      if (g.userData.pivoteRueda) g.userData.pivoteRueda.attach(v);
      return v;
    };
    g.userData.armarRin(rinFabrica);
    if (R_.cintaRin) {
      // Cinta de color en el borde del rin, por ambas caras (CR4, Gixxer): un aro fino pegado a la pestaña
      M.cinta ??= new THREE.MeshStandardMaterial({ color: R_.cintaRin, roughness: 0.35, metalness: 0.2 });
      for (const lado of [1, -1]) {
        const cinta = malla(new THREE.TorusGeometry(rinR - 0.006, 0.0035, 4, seg(48)), M.cinta, g);
        cinta.position.set(x, R, lado * ancho * 0.41);
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
      instancias(cil(0.0055, 0.007, 8), M.oscuro, Array.from({ length: 18 }, (_, i) => {
        const t = (i / 18) * Math.PI * 2;
        return enDisco(V(x + Math.cos(t) * radioDisco * 0.8, R + Math.sin(t) * radioDisco * 0.8, zFreno));
      }), f);
      // Porta disco con 5 brazos
      disco(radioDisco * 0.3, 0.01, M.oscuro, V(x, R, zFreno), f, 20);
      for (let i = 0; i < 5; i++) {
        const t = (i / 5) * Math.PI * 2 + 0.6;
        caja(radioDisco * 0.34, 0.016, 0.008, M.oscuro, V(x + Math.cos(t) * radioDisco * 0.42, R + Math.sin(t) * radioDisco * 0.42, zFreno), f, t);
      }
      const ang = idFreno === "freno_del" ? 2.3 : 1.2;
      const posCaliper = V(x + Math.cos(ang) * radioDisco * 0.86, R + Math.sin(ang) * radioDisco * 0.86, zFreno + 0.01);
      // Caliper de cuerpo redondeado, con soporte y purgador
      const cuerpo = perfil([[-0.042, -0.018], [-0.03, 0.026], [0.03, 0.026], [0.042, -0.018], [0, -0.03]], 0.034, M.carter, f, 0, 0.008, true) // (gris: en rojo, de lado parecía un reflectivo en el eje);
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
  const radios = R.rines ? R.rines === "radios"
    : tipo === "enduro" || tipo === "semi" || (specs.freno_delantero === "tambor" && tipo !== "scooter");
  // Estilo de rin de fábrica: radios, aleación (con el diseño de la línea) o estrella (7 radios rectos)
  const rinFabrica = radios ? "radios" : R.rines === "estrella" ? "estrella" : "aleacion";
  const centroDel = medir("llantas", () => llanta(xF, Rf, anchoF, specs.rin_delantero, "llanta_del", "freno_del", specs.freno_delantero, radios));
  await ceder();
  const centroTras = medir("llantas", () => llanta(xR, Rr, anchoR, specs.rin_trasero, "llanta_tras", "freno_tras", specs.freno_trasero, radios));

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
  // ----- Suspensión delantera -----
  const susDel = grupo("suspension_del");
  const zBarra = anchoF / 2 + 0.045;
  for (const lado of [1, -1]) {
    const eje = V(xF, Rf, lado * zBarra);
    const pipa = V(H.x, H.y, lado * zBarra);
    const medio = eje.clone().lerp(pipa, R.horquillaInv ? 0.36 : 0.55);
    const rBotella = tipo === "enduro" ? 0.028 : R.horquillaInv ? 0.026 : 0.022;
    const dirBarra = new THREE.Vector3().subVectors(pipa, eje).normalize();
    if (R.horquillaInv) {
      // Horquilla invertida: la botella gruesa arriba (de la tijera hacia abajo) y la barra delgada abajo, hacia el eje
      tubo(medio, pipa.clone().add(dirBarra.clone().multiplyScalar(0.02)), rBotella, M.oscuro, susDel);
      tubo(eje.clone().add(dirBarra.clone().multiplyScalar(-0.03)), medio, 0.019, M.cromo, susDel);
    } else {
      tubo(eje.clone().add(dirBarra.clone().multiplyScalar(-0.03)), medio, rBotella, tipo === "sport" ? M.oscuro : M.metal, susDel);
      tubo(medio, pipa, tipo === "enduro" ? 0.022 : 0.017, M.cromo, susDel);
    }
    // Retén con guardapolvo, tapa de la barra y punta donde se sujeta el eje
    tubo(medio, medio.clone().add(dirBarra.clone().multiplyScalar(0.025)), rBotella * 1.08, M.caucho, susDel, 20);
    if (R.fuelles) {
      // Boxer: fuelles de caucho (acordeón) que protegen las barras de la suspensión
      for (let k = 0; k < 7; k++) {
        const pk = medio.clone().add(dirBarra.clone().multiplyScalar(0.03 + k * 0.016));
        tubo(pk, pk.clone().add(dirBarra.clone().multiplyScalar(0.012)), k % 2 ? rBotella * 0.95 : rBotella * 1.12, M.caucho, susDel, 16);
      }
    }
    tubo(pipa.clone().add(dirBarra.clone().multiplyScalar(0.005)), pipa.clone().add(dirBarra.clone().multiplyScalar(0.03)), rBotella * 0.85, M.oscuro, susDel, 6);
    caja(0.055, 0.03, 0.034, tipo === "sport" ? M.oscuro : M.metal, eje.clone().add(dirBarra.clone().multiplyScalar(-0.025)), susDel, rake);
  }
  // Tuerca del eje delantero
  disco(0.014, zBarra * 2 + 0.04, M.metal, V(xF, Rf, 0), susDel, 6);
  caja(0.06, 0.03, zBarra * 2 + 0.05, M.oscuro, V(H.x, H.y, 0), susDel);
  caja(0.06, 0.03, zBarra * 2 + 0.05, M.oscuro, V(H.x + 0.06 * Math.sin(rake), H.y - 0.14, 0), susDel);

  // ----- Manubrio, luces y espejos -----
  // Deportiva con carenado: los semimanubrios van por encima del borde del carenado (más abajo lo atravesaban
  // y la punta del puño asomaba por el costado; el tablero también quedaba enterrado)
  // Estilo del manubrio (rasgos.js): alto y echado atrás (clásica tipo GN), semimanubrios bajo la tijera (clip-ons de
  // la RC) o sobre la tijera (RS); en las demás, el de su tipo.
  const estiloManubrio = R.manubrio;
  const altoManubrio = estiloManubrio === "clipon" ? -0.035 : estiloManubrio === "sobreTija" ? 0.11 : estiloManubrio === "alto" ? 0.15
    : tipo === "sport" ? (specs.carenado ? 0.11 : 0.02) : tipo === "enduro" ? 0.12 : 0.08;
  const anchoManubrio = tipo === "enduro" ? 0.4 : estiloManubrio === "clipon" ? 0.27 : tipo === "sport" ? 0.3 : estiloManubrio === "alto" ? 0.36 : 0.34;
  const atrasManubrio = estiloManubrio === "alto" ? 0.13 : estiloManubrio === "clipon" ? 0.08 : estiloManubrio === "sobreTija" ? 0.1 : 0.05;
  const M1 = V(H.x - atrasManubrio, H.y + altoManubrio, anchoManubrio);
  const M2 = V(H.x - atrasManubrio, H.y + altoManubrio, -anchoManubrio);
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
    // (va sentado sobre la abrazadera de la manigueta; antes quedaba suelto 3 cm por encima del manubrio)
    if (lado < 0 && specs.freno_delantero === "disco") caja(0.03, 0.022, 0.035, M.oscuro, V(M1.x + 0.02, M1.y + 0.025, z - lado * 0.15), decor);
  }
  // Retrovisores en tres estilos (se elige al personalizar): de fábrica ovalados, redondos cromados y en la punta del manubrio
  const espejos = {};
  for (const estiloEspejo of ["fabrica", "redondos", "puntas"]) {
    const g = new THREE.Group();
    g.userData.espejos = estiloEspejo;
    g.visible = estiloEspejo === "fabrica";
    raiz.add(g);
    espejos[estiloEspejo] = g;
    for (const lado of [1, -1]) {
      const base = V(H.x - 0.04, H.y + altoManubrio, lado * (anchoManubrio - 0.06));
      if (estiloEspejo === "fabrica") {
        // Carcasa ovalada con el espejo (cromado) mirando hacia atrás
        const punta = base.clone().add(V(-0.03, 0.12, lado * 0.09));
        tubo(base, punta, 0.0065, M.oscuro, g);
        elipsoide(0.017, 0.04, 0.064, M.oscuro, punta, g);
        elipsoide(0.006, 0.034, 0.056, M.espejo, punta.clone().add(V(-0.013, 0, 0)), g);
      } else if (estiloEspejo === "redondos") {
        // Clásicos redondos: tallo cromado alto y aro cromado
        const punta = base.clone().add(V(-0.02, 0.16, lado * 0.06));
        tubo(base, punta, 0.006, M.cromo, g);
        // (eje del disco a lo largo de la moto: la luna mira hacia atrás, al conductor; antes quedaba mirando al cielo)
        disco(0.042, 0.018, M.cromo, punta, g, 28).rotation.set(0, 0, Math.PI / 2);
        disco(0.044, 0.006, M.oscuro, punta.clone().add(V(-0.008, 0, 0)), g, 28).rotation.set(0, 0, Math.PI / 2);
        disco(0.037, 0.004, M.espejo, punta.clone().add(V(-0.012, 0, 0)), g, 28).rotation.set(0, 0, Math.PI / 2);
      } else {
        // En la punta del manubrio (bar-end): cuelgan por fuera de los puños
        const fin = V(M1.x, M1.y, lado * (anchoManubrio + 0.024)); // (justo en el contrapeso del puño)
        const brazo = fin.clone().add(V(-0.01, -0.02, lado * 0.05));
        tubo(fin, brazo, 0.007, M.oscuro, g);
        elipsoide(0.012, 0.034, 0.05, M.oscuro, brazo.clone().add(V(0, 0, lado * 0.03)), g).rotation.y = lado * 0.3;
        elipsoide(0.004, 0.029, 0.044, M.espejo, brazo.clone().add(V(-0.009, 0, lado * 0.03)), g).rotation.y = lado * 0.3;
      }
    }
  }
  const naked = fam === "naked";
  // ----- Faros: forma propia de cada línea (rasgos.js), anclada a la pipa de dirección -----
  const formaFaro = R.faro?.forma;
  const fx = H.x + 0.1, fy = H.y - 0.07; // frente del faro en las motos de calle
  // Lente encendida girada (rotación en x = inclinación hacia los lados, en z = hacia atrás)
  const lente = (w, h, d, pos, rx = 0, rz = -0.25, mat = M.luz) => { const m = caja(w, h, d, mat, pos, decor); m.rotation.set(rx, 0, rz); return m; };
  // Faro redondo desnudo (sin máscara): carcasa, lente, aro cromado; la GN con la cuba cromada grande de las clásicas.
  // Con "orejas" (NKD) cuelga de dos platinas que salen de las barras de la horquilla, como en la moto real.
  function faroRedondo(f) {
    const r = f.r || 0.085;
    const cuerpo = f.cuba ? elipsoide(0.05, r + 0.004, r + 0.004, M.cromo, V(H.x + 0.07, H.y - 0.06, 0), decor) // (la lámpara queda por delante de la cuba)
      : disco(r, 0.07, M.oscuro, V(H.x + 0.09, H.y - 0.06, 0), decor, 24);
    if (!f.cuba) cuerpo.rotation.set(0, 0, Math.PI / 2);
    disco(r - 0.01, 0.01, M.luz, V(H.x + 0.126 + (f.cuba ? 0.012 : 0), H.y - 0.06, 0), decor, 24).rotation.set(0, 0, Math.PI / 2);
    const aro = malla(new THREE.TorusGeometry(r - 0.006, 0.006, 8, 40), M.cromo, decor);
    aro.position.set(H.x + 0.128 + (f.cuba ? 0.012 : 0), H.y - 0.06, 0);
    aro.rotation.y = Math.PI / 2;
    if (f.orejas) {
      for (const lado of [1, -1]) for (const dy of [0.03, -0.035]) {
        const y = H.y - 0.06 + dy, xBarra = xF - (y - Rf) * Math.tan(rake);
        tubo(V(xBarra, y, lado * zBarra), V(H.x + 0.08, y, lado * (r * 0.92)), 0.007, M.oscuro, decor, 8);
      }
    }
  }
  if (naked && formaFaro === "redondo") {
    faroRedondo(R.faro);
  } else if (naked) {
    // Naked: faro compacto y anguloso con su máscara negra; cada línea con su "cara"
    const mascara = {
      duke: [[fx + 0.07, fy - 0.11], [fx + 0.085, fy + 0.02], [fx + 0.05, fy + 0.12], [fx - 0.04, fy + 0.1], [fx - 0.05, fy - 0.06], [fx + 0.02, fy - 0.12]],
      mt: [[fx + 0.07, fy - 0.07], [fx + 0.09, fy + 0.0], [fx + 0.06, fy + 0.06], [fx - 0.05, fy + 0.07], [fx - 0.05, fy - 0.04], [fx + 0.0, fy - 0.08]],
      fz: [[fx + 0.08, fy - 0.06], [fx + 0.085, fy + 0.04], [fx + 0.03, fy + 0.09], [fx - 0.05, fy + 0.07], [fx - 0.05, fy - 0.03], [fx + 0.01, fy - 0.08]],
      flecha: [[fx + 0.11, fy - 0.07], [fx + 0.07, fy + 0.04], [fx + 0.02, fy + 0.1], [fx - 0.05, fy + 0.08], [fx - 0.05, fy - 0.04], [fx + 0.03, fy - 0.08]],
      gixxer: [[fx + 0.075, fy - 0.055], [fx + 0.085, fy + 0.03], [fx + 0.04, fy + 0.08], [fx - 0.05, fy + 0.065], [fx - 0.05, fy - 0.03], [fx + 0.01, fy - 0.07]],
      racing: [[fx + 0.1, fy - 0.05], [fx + 0.075, fy + 0.04], [fx + 0.0, fy + 0.1], [fx - 0.05, fy + 0.08], [fx - 0.05, fy - 0.04], [fx + 0.03, fy - 0.07]],
      // Raider: máscara alta en flecha, punta abajo y adelante; Hunk: compacta y ancha, casi vertical
      raider: [[fx + 0.1, fy - 0.08], [fx + 0.08, fy + 0.03], [fx + 0.03, fy + 0.11], [fx - 0.05, fy + 0.09], [fx - 0.05, fy - 0.05], [fx + 0.04, fy - 0.1]],
      // Hunk 150: carenado tipo bikini, más alto y adelantado, del color de la moto
      bikini: [[fx + 0.08, fy - 0.08], [fx + 0.1, fy + 0.03], [fx + 0.06, fy + 0.11], [fx - 0.05, fy + 0.1], [fx - 0.05, fy - 0.05], [fx + 0.01, fy - 0.09]],
      hunk: [[fx + 0.08, fy - 0.065], [fx + 0.09, fy + 0.03], [fx + 0.05, fy + 0.085], [fx - 0.05, fy + 0.07], [fx - 0.05, fy - 0.04], [fx + 0.01, fy - 0.08]],
    }[formaFaro] || [[fx + 0.075, fy - 0.06], [fx + 0.085, fy + 0.03], [fx + 0.03, fy + 0.09], [fx - 0.05, fy + 0.07], [fx - 0.05, fy - 0.03], [fx + 0.01, fy - 0.08]];
    const anchoMascara = formaFaro === "fz" ? 0.2 : formaFaro === "mt" ? 0.22 : formaFaro === "hunk" ? 0.19 : formaFaro === "bikini" ? 0.2 : formaFaro === "duke" ? 0.14 : 0.16;
    // Forma vista de frente (se ahúsa por altura y hacia adelante, para que no sea una caja):
    // Duke alta y estrecha en rombo; MT-03 ancha abajo y recogida arriba; las demás, recogidas hacia la punta
    const xAtras = fx - 0.05;
    const formaFrente = {
      duke: (x, y) => Math.max(0.45, 1 - Math.abs(y - fy) / 0.13 * 0.55) * Math.max(0.6, 1 - (x - xAtras) * 3),
      mt: (x, y) => (y > fy + 0.02 ? Math.max(0.7, 1 - (y - fy - 0.02) * 6) : 1) * Math.max(0.8, 1 - (x - xAtras) * 1.5),
    }[formaFaro] || ((x) => Math.max(0.6, 1 - (x - xAtras) * 2.5));
    zona(panelAhusado(mascara, anchoMascara, formaFaro === "duke" || formaFaro === "bikini" ? M.pintura : M.oscuro, formaFrente, 0.012), "frontal");
    // Frente de la máscara a una altura (para pegar las lentes por fuera)
    const xm = (y) => {
      let x = fx + 0.07;
      for (let i = 0; i < 2; i++) { const [a, b] = [mascara[i], mascara[i + 1]]; if ((y - a[1]) * (y - b[1]) <= 0) x = a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]); }
      return x + 0.014;
    };
    if (formaFaro === "duke") {
      // Duke: faro partido en vertical (dos lentes apiladas) dentro de la máscara del color de la moto, con marco negro
      caja(0.02, 0.18, 0.07, M.oscuro, V(xm(fy) - 0.004, fy, 0), decor, -0.12);
      lente(0.012, 0.065, 0.05, V(xm(fy + 0.042) + 0.004, fy + 0.042, 0), 0, -0.12);
      lente(0.012, 0.065, 0.05, V(xm(fy - 0.042) + 0.004, fy - 0.042, 0), 0, -0.12);
    } else if (formaFaro === "mt") {
      // MT-03: "cara" con dos LED finos rasgados arriba (ojos) y el proyector central abajo
      for (const lado of [1, -1]) lente(0.01, 0.016, 0.08, V(xm(fy + 0.03) - 0.004, fy + 0.03, lado * 0.06), lado * 0.35, -0.6);
      caja(0.016, 0.05, 0.1, M.oscuro, V(xm(fy - 0.035) - 0.002, fy - 0.035, 0), decor, -0.2);
      lente(0.01, 0.036, 0.085, V(xm(fy - 0.035) + 0.006, fy - 0.035, 0), 0, -0.2);
    } else if (formaFaro === "fz") {
      // FZ 25: faro ancho en trapecio con las luces diurnas en las esquinas de arriba
      lente(0.012, 0.055, 0.15, V(xm(fy - 0.005), fy - 0.005, 0), 0, -0.3);
      for (const lado of [1, -1]) lente(0.01, 0.012, 0.06, V(xm(fy + 0.045) - 0.008, fy + 0.045, lado * 0.06), lado * 0.4, -0.5);
    } else if (formaFaro === "flecha") {
      // Apache: faro en flecha (punta adelante y abajo) con las dos luces en V que bajan hacia la punta
      for (const lado of [1, -1]) lente(0.01, 0.014, 0.085, V(fx + 0.085, fy + 0.0, lado * 0.035), -lado * 0.55, -0.85);
      lente(0.012, 0.035, 0.06, V(fx + 0.1, fy - 0.045, 0), 0, -0.85);
    } else if (formaFaro === "racing") {
      // CR4: dos luces rasgadas en V que se juntan hacia la punta, y una luz chica al centro abajo
      for (const lado of [1, -1]) lente(0.01, 0.014, 0.07, V(fx + 0.08, fy + 0.01, lado * 0.032), lado * 0.45, -0.75);
      lente(0.01, 0.02, 0.04, V(fx + 0.095, fy - 0.04, 0), 0, -0.7);
    } else if (formaFaro === "raider") {
      // Raider: proyector LED al centro y dos luces diurnas que forman una "Y" (brazos que suben hacia afuera)
      caja(0.016, 0.05, 0.075, M.oscuro, V(xm(fy - 0.03) - 0.004, fy - 0.03, 0), decor, -0.45);
      lente(0.01, 0.036, 0.06, V(xm(fy - 0.03) + 0.004, fy - 0.03, 0), 0, -0.45);
      lente(0.01, 0.04, 0.012, V(xm(fy + 0.015) - 0.002, fy + 0.015, 0), 0, -0.45);
      for (const lado of [1, -1]) lente(0.01, 0.012, 0.075, V(xm(fy + 0.05) - 0.01, fy + 0.05, lado * 0.035), lado * 0.6, -0.6);
    } else if (formaFaro === "hunk") {
      // Hunk 125R: faro LED rectangular ancho al centro con dos cejas diurnas en ángulo encima
      caja(0.016, 0.05, 0.12, M.oscuro, V(xm(fy - 0.012) - 0.004, fy - 0.012, 0), decor, -0.2);
      lente(0.01, 0.038, 0.105, V(xm(fy - 0.012) + 0.004, fy - 0.012, 0), 0, -0.2);
      for (const lado of [1, -1]) lente(0.01, 0.011, 0.065, V(xm(fy + 0.042) - 0.006, fy + 0.042, lado * 0.05), lado * 0.35, -0.45);
    } else if (formaFaro === "bikini") {
      // Hunk 150: un solo faro ancho y anguloso con su marco negro y dos luces de posición chicas debajo
      caja(0.016, 0.07, 0.13, M.oscuro, V(xm(fy + 0.01) - 0.004, fy + 0.01, 0), decor, -0.2);
      lente(0.01, 0.058, 0.115, V(xm(fy + 0.01) + 0.004, fy + 0.01, 0), 0, -0.2);
      for (const lado of [1, -1]) lente(0.008, 0.012, 0.03, V(xm(fy - 0.045) - 0.004, fy - 0.045, lado * 0.04), 0, -0.1);
    } else if (formaFaro === "gixxer") {
      // Gixxer: faro compacto horizontal con dos "cejas" de luz diurna encima
      lente(0.012, 0.04, 0.1, V(xm(fy - 0.015), fy - 0.015, 0), 0, -0.3);
      for (const lado of [1, -1]) lente(0.01, 0.01, 0.055, V(xm(fy + 0.04) - 0.006, fy + 0.04, lado * 0.045), lado * 0.5, -0.5);
    } else {
      lente(0.012, 0.05, 0.11, V(fx + 0.085, fy - 0.01, 0), 0, -0.25);
      for (const lado of [1, -1]) {
        const drl = caja(0.01, 0.012, formaFaro === "ns" ? 0.07 : 0.05, M.luz, V(fx + 0.07, fy + 0.04, lado * (formaFaro === "ns" ? 0.05 : 0.045)), decor);
        drl.rotation.set(lado * 0.5, 0, -0.5);
        if (formaFaro === "ns") {
          // Pulsar NS: "ojos de lobo" (dos luces diurnas en ángulo a los lados del faro) con su marco negro
          lente(0.012, 0.016, 0.06, V(fx + 0.06, fy - 0.045, lado * 0.06), -lado * 0.6, -0.35);
          caja(0.008, 0.026, 0.07, M.oscuro, V(fx + 0.054, fy - 0.045, lado * 0.06), decor).rotation.set(-lado * 0.6, 0, -0.35);
        }
      }
    }
    // Visera ahumada corta sobre la máscara (más alta en la Duke, casi nada en la FZ)
    const alzaVisera = formaFaro === "duke" || formaFaro === "bikini" ? 0.03 : formaFaro === "fz" ? -0.03 : 0;
    const top = mascara.reduce((a, q) => (q[1] > a[1] ? q : a));
    perfil([[top[0] - 0.01, top[1]], [top[0] + 0.02, top[1] + 0.07 + alzaVisera], [top[0] - 0.05, top[1] + 0.09 + alzaVisera], [top[0] - 0.07, top[1] - 0.005]],
      anchoMascara - 0.03, M.vidrio, decor, 0, 0.006);
  } else if (fam === "clasica") {
    const f = R.faro || {};
    if (formaFaro === "trapecio" || formaFaro === "agudo") {
      // Commuter con carenado de faro en el color de la moto: trapecio con visera (Discover) o anguloso y afilado (CB, NKD, CR4)
      const an = f.ancho || 0.15, al = f.alto || 0.11, pu = f.punta || 0.04;
      const cara = formaFaro === "trapecio"
        ? [[fx + 0.06, fy - 0.08], [fx + 0.075, fy + 0.04], [fx + 0.02, fy + 0.1], [fx - 0.06, fy + 0.08], [fx - 0.06, fy - 0.05], [fx - 0.0, fy - 0.1]]
        : [[fx + 0.03 + pu, fy - al * 0.55], [fx + 0.04 + pu * 0.5, fy + al * 0.25], [fx + 0.0, fy + al * 0.75], [fx - 0.07, fy + al * 0.6], [fx - 0.06, fy - al * 0.4], [fx - 0.0, fy - al * 0.7]];
      zona(perfil(cara, an + 0.04, M.pintura, decor, 0, 0.012), "frontal");
      const frente = (y) => cara[0][0] + (cara[1][0] - cara[0][0]) * (y - cara[0][1]) / (cara[1][1] - cara[0][1]) + 0.014;
      const yL = formaFaro === "trapecio" ? fy - 0.02 : fy - al * 0.15;
      const giro = Math.atan2(cara[1][0] - cara[0][0], cara[1][1] - cara[0][1]);
      caja(0.016, (formaFaro === "trapecio" ? 0.09 : al * 0.55) + 0.014, an + 0.01, M.oscuro, V(frente(yL) - 0.006, yL, 0), decor, -giro);
      lente(0.01, formaFaro === "trapecio" ? 0.085 : al * 0.5, an, V(frente(yL), yL, 0), 0, -giro);
      if (f.drl) for (const lado of [1, -1]) lente(0.008, 0.01, 0.07, V(frente(yL + al * 0.32) - 0.004, yL + al * 0.32, lado * 0.05), lado * 0.45, -giro - 0.2);
      if (f.visera || formaFaro === "trapecio") {
        const t = cara[2];
        perfil([[t[0], t[1] - 0.005], [t[0] + 0.02, t[1] + 0.06], [t[0] - 0.05, t[1] + 0.075], [t[0] - 0.07, t[1] - 0.01]], an, M.vidrio, decor, 0, 0.006);
      }
    } else if (formaFaro === "rectangular") {
      // Eco Deluxe: faro rectangular en su caja negra con borde cromado (sin carenado)
      caja(0.075, 0.115, 0.165, M.oscuro, V(fx + 0.0, fy - 0.01, 0), decor, -0.12);
      caja(0.012, 0.12, 0.17, M.cromo, V(fx + 0.04, fy - 0.006, 0), decor, -0.12);
      lente(0.012, 0.095, 0.145, V(fx + 0.045, fy - 0.006, 0), 0, -0.12);
    } else {
      faroRedondo(f); // Boxer, GN
      if (f.visera) perfil([[H.x + 0.06, H.y - 0.06 + f.r * 0.6], [H.x + 0.13, H.y - 0.06 + f.r + 0.02], [H.x + 0.07, H.y - 0.06 + f.r + 0.05],
        [H.x + 0.02, H.y - 0.06 + f.r * 0.7]], f.r * 2 + 0.02, M.pintura, decor, 0, 0.008);
    }
  } else if (fam === "semi" && formaFaro === "redondo") {
    // Semiautomática con faro en la horquilla (Best): redondo y chico, con su carcasa en el color de la moto
    const r = R.faro.r || 0.07;
    zona(disco(r + 0.012, 0.08, M.pintura, V(H.x + 0.08, H.y - 0.05, 0), decor, 24), "frontal").rotation.set(0, 0, Math.PI / 2 - 0.2);
    disco(r, 0.012, M.luz, V(H.x + 0.122, H.y - 0.04, 0), decor, 24).rotation.set(0, 0, Math.PI / 2 - 0.2);
  } else if (tipo === "enduro" && formaFaro === "mascara") {
    // Doble propósito con máscara alta tipo porta número (XR 190L del color de la moto, DR 150 negra): baja casi hasta
    // el guardabarros alto, el faro rectangular adentro con su marco negro y una visera ahumada corta arriba
    const f = R.faro, al = f.alto || 0.25, mc = f.color === "oscuro" ? M.oscuro : M.pintura;
    // (inclinada con la horquilla y por delante de las barras, para no atravesarlas)
    const fk = (y) => xF - (y - Rf) * Math.tan(rake) + 0.026;
    const y0 = H.y - 0.185, y1 = y0 + al, yF = y1 - 0.06; // (abajo, justo encima del guardabarros alto)
    const cara = [[fk(y0), y0 + 0.01], [fk(y0) + 0.055, y0], [fk(yF) + 0.075, yF], [fk(y1) + 0.03, y1], [fk(y1) - 0.005, y1 - 0.01]];
    zona(perfil(cara, 0.2, mc, decor, 0, 0.012), "frontal"); // (tapa las barras de la horquilla por delante)
    // Frente de la máscara (entre el 2.º y el 3.er punto del contorno) a una altura
    const xf = (y) => cara[1][0] + (cara[2][0] - cara[1][0]) * (y - cara[1][1]) / (cara[2][1] - cara[1][1]) + 0.012;
    const yL = y0 + (yF - y0) * 0.55, giro = Math.atan2(cara[2][0] - cara[1][0], cara[2][1] - cara[1][1]);
    caja(0.016, 0.085, 0.115, M.oscuro, V(xf(yL) - 0.004, yL, 0), decor, -giro);
    lente(0.01, 0.07, 0.1, V(xf(yL) + 0.002, yL, 0), 0, -giro);
    const t = cara[3];
    perfil([[t[0] - 0.01, t[1] - 0.005], [t[0] + 0.03, t[1] + 0.045], [t[0] - 0.02, t[1] + 0.055], [t[0] - 0.04, t[1] - 0.01]], 0.13, M.vidrio, decor, 0, 0.006);
  } else if (!scooter && !(tipo === "sport" && specs.carenado) && fam !== "semi") { // (las carenadas llevan los faros en el carenado)
    const faro = disco(tipo === "enduro" ? 0.06 : 0.085, 0.07, M.oscuro, V(H.x + 0.09, H.y - 0.06, 0), decor, 24);
    faro.rotation.set(0, 0, Math.PI / 2);
    const lenteE = disco(tipo === "enduro" ? 0.05 : 0.075, 0.01, M.luz, V(H.x + 0.126, H.y - 0.06, 0), decor, 24);
    lenteE.rotation.set(0, 0, Math.PI / 2);
    const aro = malla(new THREE.TorusGeometry(tipo === "enduro" ? 0.053 : 0.079, 0.006, 8, 40), M.cromo, decor);
    aro.position.set(H.x + 0.128, H.y - 0.06, 0);
    aro.rotation.y = Math.PI / 2;
    if (tipo === "enduro") {
      perfil([[0, -0.07], [0.04, -0.085], [0.06, 0.07], [0.015, 0.1], [-0.015, 0.035]], 0.13, M.pintura, decor, 0, 0.01)
        .position.set(H.x + 0.075, H.y - 0.05, 0);
    }
  }
  // Manubrio carenado con el faro (semiautomáticas Wave y Crypton, scooter Dio): tapa que envuelve el centro del
  // manubrio, con la lente adelante
  const manubrioCarenado = (fam === "semi" && formaFaro === "manubrio") || (scooter && !!R.scooter?.faroManubrio);
  if (manubrioCarenado) {
    const an = R.faro?.ancho || 0.16, agudo = R.faro?.agudo;
    const mx = H.x - 0.03, my = H.y + altoManubrio;
    const tapa = agudo
      ? [[mx + 0.13, my - 0.07], [mx + 0.12, my + 0.0], [mx + 0.02, my + 0.06], [mx - 0.1, my + 0.045], [mx - 0.1, my - 0.03], [mx + 0.02, my - 0.1]]
      : [[mx + 0.12, my - 0.06], [mx + 0.11, my + 0.02], [mx + 0.03, my + 0.06], [mx - 0.09, my + 0.045], [mx - 0.1, my - 0.03], [mx + 0.0, my - 0.09]];
    const tapaM = zona(panelAhusado(tapa, an + 0.12, M.pintura, (x) => (x > mx + 0.04 ? Math.max(0.55, 1 - (x - mx - 0.04) * 3.5) : 1), 0.025), "frontal");
    const en = sobre(tapaM, my - 0.03, 0);
    // (la Dio actual lleva el faro en el escudo: su tapa de manubrio solo cubre los relojes)
    if (en && !R.scooter?.faroEscudo) {
      pegar(caja(0.016, 0.06, an * 0.78, M.oscuro, V(), decor), en, V(1, 0, 0), 0.004);
      pegar(caja(0.008, 0.05, an * 0.7, M.luz, V(), decor), en, V(1, 0, 0), 0.012);
    }
  }

  await ceder();
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

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
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
    const zFiltro = esMaxi ? 0.05 : 0.13;
    caja(0.24, 0.1, 0.12, M.oscuro, V(xR + 0.35, Rr + 0.175, zFiltro), filtro);
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
    interno(instancias(cil(0.011, 0.02, 10), M.cromo, Array.from({ length: 6 }, (_, i) => {
      const a = (i / 6) * Math.PI * 2;
      return enDisco(poleaA.clone().add(V(Math.cos(a) * 0.04, Math.sin(a) * 0.04, 0.01)));
    }), correa));
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
    disco(0.012, 0.014, M.oscuro, V(E.x + 0.1 * s, E.y - 0.07 * s, -0.13 * s), aceite, 16); // visor del nivel de aceite (opaco: fuera de Rayos X nada se transparenta)
    tapaClutch.userData.base = true;
    const tapaMagneto = disco(0.07 * s, 0.03, M.motor, V(E.x - 0.07 * s, E.y + 0.0, 0.12 * s), aceite, 40);
    tapaMagneto.userData.base = true;
    disco(0.022, 0.03, M.oscuro, V(E.x - 0.08 * s, E.y - 0.09 * s, 0.1 * s), aceite, 6); // tapón de drenaje
    instancias(cil(0.005, 0.034, 6), M.metal, Array.from({ length: 8 }, (_, i) => {
      const a = (i / 8) * Math.PI * 2;
      return enDisco(V(E.x + 0.04 * s + Math.cos(a) * 0.075 * s, E.y - 0.02 + Math.sin(a) * 0.075 * s, -0.12 * s));
    }), aceite);
    // Cilindro y culata (motor)
    const inclinacion = tipo === "semi" ? -1.25 : -0.32;
    const base = V(E.x + 0.07 * s, E.y + 0.06 * s);
    const dirCil = V(-Math.sin(inclinacion), Math.cos(inclinacion));
    // (semi: cilindro casi acostado hacia adelante; más corto para que la culata y la bujía no toquen la llanta delantera)
    const alto = (tipo === "semi" ? 0.155 : 0.2) * s;
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
    const bujiaPunta = cabeza.clone().add(dirCil.clone().multiplyScalar(tipo === "semi" ? 0.035 : 0.06));
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
      for (let i = 0; i < 7; i++) caja(0.045, 0.006, 0.27, M.radiador, V(centroRad.x, centroRad.y - 0.09 + i * 0.03), rad, -0.2);
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
    // (en calidad baja, un eslabón de cada dos: a esa distancia se ve igual)
    const nEslabones = Math.round(curva.getLength() / (CALIDAD.nombre === "baja" ? 0.0254 : 0.0127));
    // Una caja por eslabón que abarca las dos placas (de lado se ve igual y es la mitad de triángulos)
    const matEslabones = [];
    const m4c = new THREE.Matrix4(), qc = new THREE.Quaternion();
    for (let i = 0; i < nEslabones; i++) {
      const u = i / nEslabones;
      const pt = curva.getPointAt(u), tg = curva.getTangentAt(u);
      qc.setFromAxisAngle(V(0, 0, 1), Math.atan2(tg.y, tg.x));
      m4c.compose(V(pt.x, pt.y, zCad), qc, V(1, i % 2 ? 1 : 0.85, 1));
      matEslabones.push(m4c.clone());
    }
    instancias(new THREE.BoxGeometry(0.0125, 0.0075, 0.0135), M.metal, matEslabones, cadena);
    // Corona con dientes y guardacadena sobre el tramo de arriba
    instancias(new THREE.BoxGeometry(0.008, 0.01, 0.007), M.metal, Array.from({ length: 36 }, (_, i) => {
      const a = (i / 36) * Math.PI * 2;
      return enCaja(V(corona.x + Math.cos(a) * (rC + 0.003), corona.y + Math.sin(a) * (rC + 0.003), zCad), a);
    }), cadena);
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
      const dep = ar.clone().add(V(-0.03, -0.01, abajo.z < 0 ? -0.03 : 0.03)); // (hacia afuera: hacia adentro tocaba la llanta)
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
    amortiguador(V(xR + 0.08, Rr + 0.05, 0.115), V(xR + 0.16, alturaAsiento - 0.14, 0.115)); // (a 0,1 el resorte rozaba la llanta)
  } else {
    amortiguador(V(P.x - 0.12, P.y + 0.02, 0), V(P.x + 0.02, alturaAsiento - 0.16, 0));
  }

  await ceder();
  // ----- Escape (lado derecho) -----
  if (scooter) {
    tubo(V(P.x + 0.2, Rr * 0.8, -0.05), V(xR + 0.15, Rr + 0.02, -0.14), 0.02, M.cromo, decor);
    const silenciador = tubo(V(xR + 0.3, Rr + 0.03, -0.15), V(xR - 0.02, Rr + 0.1, -0.15), 0.05, M.oscuro, decor);
    silenciador.userData.base = true;
  } else {
    const salida = V(Math.min(P.x + 0.32 * s, xF - Rf - 0.08), P.y - 0.03, -0.06); // (en las de motor grande quedaba pegada a la llanta)
    const finCodo = tipo === "enduro" ? V(P.x - 0.05, alturaAsiento - 0.15, -0.14) : V(P.x - 0.05, P.y - 0.02, -0.12);
    // Codo de escape curvo: sale de la culata, baja por delante del motor y pasa por debajo
    // (puerto de escape: frente de la culata del cilindro inclinado, ver "Motor")
    if (tipo !== "semi") {
      const culataEsc = V(Math.min(P.x + 0.2 * s + 0.04 + 0.215 * s, xF - Rf - 0.06), P.y + 0.05 + 0.25 * s, -0.02);
      // (el codo baja por delante del motor sin meterse en la llanta delantera)
      const codo = new THREE.CatmullRomCurve3([culataEsc, V(Math.min(culataEsc.x + 0.04, xF - Rf - 0.06), culataEsc.y - 0.12 * s, -0.065),
        V(salida.x + 0.03, salida.y - 0.05, -0.06), salida]);
      malla(new THREE.TubeGeometry(codo, 30, 0.019, 12), M.cromo, decor);
    }
    const formaEsc = R.escape?.forma;
    if (formaEsc === "bajo") {
      // Silenciador bajo el motor (Pulsar NS, Duke, MT-03, RC) (underbelly) en vez del lateral largo. Antes era un bloque oscuro bajo un
      // motor oscuro y parecía que no tuviera mofle: ahora el cuerpo es de acero con protector térmico perforado por
      // el lado derecho, el codo cromado llega a la vista y las dos puntas cromadas asoman delante de la llanta trasera.
      const Ez = V(P.x + 0.2 * s + 0.04, P.y + 0.05);
      // (más abajo que el motor y corrido hacia la derecha: centrado quedaba escondido detrás de la tapa del motor)
      const bajo = 0.045, zSil = -0.045;
      const xSil = Math.min(Ez.x + 0.14, xF - Rf - 0.03); // (la punta no llega a la llanta delantera en las de motor grande)
      const contornoSil = [[Ez.x - 0.16, Ez.y - 0.13 - bajo], [xSil - 0.04, Ez.y - 0.15 - bajo], [xSil, Ez.y - 0.11 - bajo],
        [Ez.x + 0.06, Ez.y - 0.07 - bajo], [Ez.x - 0.14, Ez.y - 0.06 - bajo]];
      const acero = M.metal; // (el mismo metal del resto: un material aparte era otra llamada de dibujo)
      const cajaSil = panelAhusado(contornoSil, 0.18, acero, () => 1, 0.02);
      cajaSil.position.z = zSil;
      cajaSil.userData.base = true;
      // Protector térmico de metal claro sobre la cara derecha, con ranuras oscuras
      const caraDer = zSil - 0.09 - 0.02 - 0.004; // cara derecha del cuerpo (mitad del ancho + bisel)
      perfil([[Ez.x - 0.12, Ez.y - 0.125 - bajo], [Ez.x + 0.08, Ez.y - 0.14 - bajo], [Ez.x + 0.1, Ez.y - 0.105 - bajo], [Ez.x - 0.1, Ez.y - 0.085 - bajo]],
        0.006, M.metalDoble, decor, caraDer, 0.004, true);
      instancias(new THREE.BoxGeometry(0.03, 0.006, 0.004), M.oscuro, [0, 1, 2, 3].map((k) =>
        enCaja(V(Ez.x - 0.07 + k * 0.045, Ez.y - 0.113 - bajo - k * 0.004, caraDer - 0.006), -0.08)), decor);
      // Codo cromado: de la salida del motor baja por el lado derecho hasta la boca del silenciador (a la vista)
      const bocaSil = V(Ez.x + 0.12, Ez.y - 0.11 - bajo, caraDer + 0.03);
      malla(new THREE.TubeGeometry(new THREE.CatmullRomCurve3([salida, V(salida.x + 0.01, salida.y - 0.05, -0.085),
        V(bocaSil.x + 0.03, bocaSil.y + 0.005, caraDer - 0.005), bocaSil]), 24, 0.021, 12), M.cromo, decor);
      // NS: dos puntas grandes y cromadas, una sobre otra, que salen hacia atrás y un poco hacia afuera.
      // Las demás: una lata corta que asoma por la derecha delante de la llanta trasera, subiendo un poco.
      if (!R.escape.puntas) {
        const rL = R.escape.lata || 0.032;
        const ini = V(Ez.x - 0.1, Ez.y - 0.1 - bajo, caraDer + 0.02 - rL * 0.4);
        const fin = V(P.x - 0.02 - rL * 1.5, P.y - 0.07 + rL, caraDer - rL * 0.6);
        tubo(ini, fin, rL, acero, decor, 18);
        const dir = fin.clone().sub(ini).normalize();
        tubo(fin, fin.clone().add(dir.clone().multiplyScalar(0.02)), rL * 0.75, M.oscuro, decor, 16);
        tubo(fin.clone().add(dir.clone().multiplyScalar(0.02)), fin.clone().add(dir.clone().multiplyScalar(0.024)), rL * 0.5, M.cromo, decor, 14);
      }
      for (const dy of R.escape.puntas ? [0.024, -0.02] : []) {
        const ini = V(Ez.x - 0.14, Ez.y - 0.1 - bajo + dy, caraDer + 0.035);
        const fin = V(P.x - 0.06, P.y - 0.08 + dy * 1.1, caraDer - 0.01);
        tubo(ini, fin, 0.019, M.cromo, decor, 18);
        const dir = fin.clone().sub(ini).normalize();
        tubo(fin, fin.clone().add(dir.clone().multiplyScalar(0.012)), 0.025, M.cromo, decor, 20);           // aro de la punta
        tubo(fin.clone().add(dir.clone().multiplyScalar(0.01)), fin.clone().add(dir.clone().multiplyScalar(0.013)), 0.016, M.oscuro, decor, 16); // boca
      }
      // Soporte de las puntas al chasis
      tubo(V(P.x - 0.02, P.y - 0.08, caraDer), V(P.x + 0.02, P.y + 0.02, -0.1), 0.006, M.oscuro, decor, 8);
    }
    if (formaEsc !== "bajo") {
    // Silenciador lateral: corto y subiendo (~20°, naked y commuter deportivas) o largo y casi horizontal (clásicas)
    const corto = formaEsc === "corto";
    const largo = corto ? 0.27 : tipo === "sport" ? 0.32 : 0.42;
    let finSil, iniSil;
    if (tipo === "enduro") {
      finSil = V(xR + 0.05, alturaAsiento - 0.08, -0.15);
      iniSil = finCodo.clone().lerp(finSil, 1 - largo / finCodo.distanceTo(finSil));
    } else {
      const a = THREE.MathUtils.degToRad(R.escape?.sube ?? 4);
      iniSil = V(xR + (corto ? 0.13 : 0.08) + largo * Math.cos(a), corto ? P.y + 0.0 : Rr + 0.11, -0.15);
      finSil = iniSil.clone().add(V(-largo * Math.cos(a), largo * Math.sin(a), 0));
      finCodo.x = Math.min(finCodo.x, iniSil.x + 0.05);
    }
    tubo(salida, finCodo, 0.02, M.cromo, decor);
    const rSil = corto ? 0.05 : tipo === "sport" ? 0.055 : 0.045;
    // El silenciador de fábrica va en su propio grupo: se esconde si la persona elige el escape deportivo
    escapeFabrica = new THREE.Group();
    raiz.add(escapeFabrica);
    escapeInfo = { finCodo, iniSil, finSil, rSil };
    tubo(iniSil, finSil, rSil, M.oscuro, escapeFabrica, 24);
    if (tipo !== "enduro") {
      // Abrazadera del silenciador al subchasis (no queda colgando solo del codo)
      const ab = iniSil.clone().lerp(finSil, 0.55);
      tubo(ab, V(ab.x + 0.02, Math.max(ab.y + 0.06, P.y + 0.19), -0.11), 0.007, M.oscuro, escapeFabrica, 8);
    }
    // Apache: dos cañones (el de arriba más delgado), como su silenciador doble
    if (R.escape?.doble) tubo(iniSil.clone().add(V(-0.03, rSil * 1.25, 0.005)), finSil.clone().add(V(0.0, rSil * 1.05, 0.005)), rSil * 0.62, M.oscuro, escapeFabrica, 18);
    tubo(finCodo, iniSil, 0.022, M.cromo, decor);
    // Punta cromada y protector térmico perforado
    const dirSil = new THREE.Vector3().subVectors(finSil, iniSil).normalize();
    tubo(finSil, finSil.clone().add(dirSil.clone().multiplyScalar(0.035)), rSil * 0.55, M.cromo, escapeFabrica, 20);
    const protectorSil = malla(dosCaras(new THREE.CylinderGeometry(rSil + 0.006, rSil + 0.006, iniSil.distanceTo(finSil) * 0.55, seg(24), 1, true, 0, Math.PI * 0.9)), M.metal, escapeFabrica);
    protectorSil.position.copy(iniSil.clone().lerp(finSil, 0.45));
    protectorSil.quaternion.setFromUnitVectors(V(0, 1, 0), dirSil);
    protectorSil.rotateY(Math.PI * 0.55);
    }
  }

  // ----- Carrocería específica: Yamaha NMAX (maxi-scooter) -----
  // Paneles curvos que se angostan hacia la nariz y la cola, pintura en dos tonos y detalles propios del modelo.
  function panelAhusado(puntos, ancho, mat, ahusar, bisel = 0.045, deformar = null, tosco = 1) {
    // Clave del panel: su contorno, medidas y el código de sus funciones de forma
    // (tosco > 1: aristas más largas en la subdivisión, para paneles que casi no se ven, como la quilla)
    const clave = `panel|${claveContorno(puntos)}|${ancho}|${bisel}|${ahusar}|${deformar || ""}${tosco === 1 ? "" : "|t" + tosco}`;
    const guardada = deCache(clave);
    if (guardada) return malla(guardada, mat, decor);
    // Base liviana (menos segmentos): la suavidad la dan la subdivisión de las tapas y las normales suavizadas.
    // (sin lisar aquí: abajo se vuelve a unir y suavizar todo, hacerlo dos veces era lo más lento del armado)
    const m = perfil(puntos, ancho, mat, decor, 0, bisel, true, seg(10, 6), 3, false);
    // Las tapas de una extrusión tienen pocos triángulos grandes: al angostarlas por vértice quedaban "facetadas"
    // (como papel doblado). Se subdividen antes de dar la forma y luego se suavizan las normales.
    let geo = m.geometry.index ? m.geometry.toNonIndexed() : m.geometry.clone();
    geo.deleteAttribute("uv");
    geo.deleteAttribute("normal");
    geo = medir("subdividir", () => subdividir(unirVertices(geo), CALIDAD.subdividir * tosco, 4));
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      pos.setZ(i, pos.getZ(i) * ahusar(pos.getX(i), pos.getY(i)));
      if (deformar) {
        const [x, y, z] = deformar(pos.getX(i), pos.getY(i), pos.getZ(i));
        pos.setXYZ(i, x, y, z);
      }
    }
    despejarLlantas(pos);
    pos.needsUpdate = true;
    medir("normales", () => { geo.computeVertexNormals(); suavizarNormales(geo, 3); });
    m.geometry.dispose();
    m.geometry = geo;
    aCache(clave, geo);
    return m;
  }
  // Ningún panel (quilla, protector, escudo, carenado, cola…) puede meterse en el volumen de una llanta: los vértices que
  // caen dentro se empujan hacia afuera, a 1,2 cm de la banda, como el borde de un guardabarros interno.
  // (los paneles se arman en las coordenadas de la moto, las mismas de los centros de las ruedas)
  function despejarLlantas(pos) {
    const ruedas = [[xF, Rf, anchoF], [xR, Rr, anchoR]];
    for (let i = 0; i < pos.count; i++) {
      const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
      for (const [cx, R, a] of ruedas) {
        if (Math.abs(z) > a * 0.55 + 0.01) continue;
        const dx = x - cx, dy = y - R, d = Math.hypot(dx, dy), lim = R + 0.012;
        if (d < lim && d > R * 0.6) { pos.setXY(i, cx + (dx * lim) / d, R + (dy * lim) / d); break; }
      }
    }
  }
  // Las tapas de la extrusión se triangulan en abanico (triángulos largos y finos): al curvarlas, sus normales
  // salen disparejas y la pintura se ve "arrugada" con cortes de luz raros. Promediar cada normal con las de sus
  // vecinas unas pocas veces deja el reflejo parejo sin cambiar la forma ni agregar triángulos.
  function suavizarNormales(geo, vueltas) {
    if (!geo.index) return;
    const idx = geo.index.array, n = geo.attributes.normal.array;
    for (let v = 0; v < vueltas; v++) {
      const acc = Float32Array.from(n);
      for (let t = 0; t < idx.length; t += 3) {
        const a = idx[t] * 3, b = idx[t + 1] * 3, c = idx[t + 2] * 3;
        for (let k = 0; k < 3; k++) {
          acc[a + k] += n[b + k] + n[c + k];
          acc[b + k] += n[a + k] + n[c + k];
          acc[c + k] += n[a + k] + n[b + k];
        }
      }
      for (let i = 0; i < n.length; i += 3) {
        const l = Math.hypot(acc[i], acc[i + 1], acc[i + 2]) || 1;
        n[i] = acc[i] / l; n[i + 1] = acc[i + 1] / l; n[i + 2] = acc[i + 2] / l;
      }
    }
    geo.attributes.normal.needsUpdate = true;
  }

  function carroceriaNmax(aerox = false) {
    const pintura = M.pintura;
    const negro = new THREE.MeshPhysicalMaterial({ color: 0x15181a, roughness: 0.45, metalness: 0.15, clearcoat: 0.6, clearcoatRoughness: 0.25 });
    const plastico = new THREE.MeshStandardMaterial({ color: 0x2b3033, roughness: 0.62, metalness: 0.05 });
    const vidrioOscuro = new THREE.MeshPhysicalMaterial({ color: 0x1b2226, transparent: true, opacity: 0.6, roughness: 0.04, clearcoat: 1, depthWrite: false });
    const ambar = M.ambar;
    M.resorte.color.set(0xd6a12c); // resortes dorados de los amortiguadores
    M.acento = negro; // el color de detalles también pinta los acabados negros
    const sube = (y) => y; // alturas en metros (NMAX: asiento 0,765 m)

    // Frontal (escudo) en el color de la moto: se angosta hacia adelante y hacia arriba
    // Escudo más inclinado (como la NMAX real) y con nariz en "V" vista desde arriba
    const puntosEscudo = aerox
      ? [[0.5, 0.42], [0.6, 0.47], [xF + 0.08, 0.56], [xF + 0.19, 0.63], [xF + 0.13, 0.72], [xF + 0.02, 0.85],
        [0.6, 0.92], [0.53, 0.91], [0.45, 0.82], [0.41, 0.66], [0.38, 0.47], [0.42, 0.42]]
      : [[0.5, 0.42], [0.6, 0.47], [xF + 0.05, 0.58], [xF + 0.13, 0.66], [xF + 0.1, 0.76], [xF + 0.03, 0.88],
        [0.6, 0.94], [0.53, 0.92], [0.45, 0.82], [0.41, 0.66], [0.38, 0.47], [0.42, 0.42]];
    const angostarEscudo = (x, y) => (x > 0.48 ? Math.max(0.45, 1 - (x - 0.48) * 1.6) : 1) * (y > 0.84 ? Math.max(0.55, 1 - (y - 0.84) * 2.2) : 1);
    const BISEL_ESCUDO = 0.045, PICO = aerox ? 0.1 : 0.06;
    const tPico = (x) => Math.min(1, Math.max(0, (x - 0.55) / 0.25));
    const narizV = (x, y, z) => {
      const zn = Math.min(1, Math.abs(z) / (0.2 * angostarEscudo(x, y)));
      return [x - PICO * tPico(x) * zn * zn, y, z];
    };
    const escudoM = zona(panelAhusado(puntosEscudo, 0.4, pintura, angostarEscudo, BISEL_ESCUDO, narizV), "frontal");
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
    const inclinacion = aerox ? -0.62 : -0.52;
    if (aerox) {
      // Aerox 2021+ (fotos en manual_despiece/yamaha_aerox155): dos faros grandes transparentes, uno a cada lado del escudo
      // a media altura, que se van hacia atrás siguiendo el borde; encima de cada uno una tira LED fina; la nariz en V
      // oscura al centro, entre los dos. La direccional va en la punta de afuera de cada faro.
      // (pegados con un rayo contra el escudo real y orientados por su normal: girados a ojo quedaban medio enterrados)
      for (const lado of [1, -1]) {
        const en = sobre(escudoM, 0.7, lado * 0.085);
        if (en) {
          pegar(caja(0.014, 0.06, 0.13, negro, V(), decor), en, V(1, 0, 0), 0.006).rotateX(lado * 0.45);
          pegar(caja(0.01, 0.046, 0.115, M.luz, V(), decor), en, V(1, 0, 0), 0.016).rotateX(lado * 0.45);
        }
        const d = sobre(escudoM, 0.755, lado * 0.1);
        if (d) pegar(caja(0.008, 0.01, 0.14, M.luz, V(), decor), d, V(1, 0, 0), 0.006).rotateX(lado * 0.5);
        // (a y 0.672 / z 0.15 el costado sobresalía 9 cm delante y la tapaba vista de frente)
        const a = sobre(escudoM, 0.69, lado * 0.165);
        if (a) pegar(caja(0.012, 0.022, 0.035, ambar, V(), decor), a, V(1, 0, 0), 0.007);
      }
      // Nariz en V oscura entre los faros, de la punta del escudo hacia el manubrio
      const yN = 0.66;
      caja(0.012, 0.16, 0.05, negro, V(frenteEscudo(yN, 0) + 0.002, yN, 0), decor).rotation.z = inclinacion;
    }
    for (const lado of aerox ? [] : [1, -1]) {
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
      const direccional = caja(0.014, 0.022, 0.05, ambar, V(frenteEscudo(yA, zA) + 0.004, yA, zA), decor);
      direccional.rotation.set(0, -lado * 0.55, inclinacion);
    }
    if (!aerox) caja(0.01, 0.012, 0.07, M.luz, V(frenteEscudo(0.72, 0) + 0.006, 0.72, 0), decor).rotation.z = -0.35; // luz de posición central

    // Parabrisas oscuro
    panelAhusado(aerox ? [[0.58, 0.935], [xF + 0.02, 0.87], [xF - 0.01, 0.91], [0.6, 0.99], [0.54, 0.985]]
      : [[0.58, 0.955], [xF + 0.03, 0.89], [xF - 0.01, 0.96], [0.6, 1.06], [0.54, 1.05]], 0.3, vidrioOscuro,
      (x, y) => Math.max(0.65, 1 - (y - 0.95) * 1.4), 0.008).userData.visorFabrica = true;

    // Cubre-manubrio negro y tablero
    caja(0.13, 0.05, aerox ? 0.16 : 0.42, negro, V(H.x - 0.01, H.y + 0.1, 0), decor).rotation.z = -0.15;
    const tablero = caja(0.06, 0.004, 0.16, M.tablero, V(H.x + 0.02, H.y + 0.128, 0), decor);
    tablero.rotation.z = -0.35;

    // Guardabarros delantero envolvente (negro)
    const guarda = malla(new THREE.TorusGeometry(Rf + 0.035, 0.016, 8, 32, Math.PI * (aerox ? 0.38 : 0.62)), negro, decor);
    guarda.position.set(xF, Rf, 0);
    guarda.rotation.z = Math.PI * (aerox ? 0.3 : 0.16);
    guarda.scale.z = aerox ? 3.6 : 4.5;

    // Piso plano con túnel central y faldón negro
    if (aerox) for (const lado of [1, -1]) caja(0.4, 0.03, 0.09, negro, V(0.16, 0.36, lado * 0.15), decor); // estribos a los lados del túnel
    else caja(0.42, 0.03, 0.34, negro, V(0.16, 0.365, 0), decor);
    if (aerox) {
      // Aerox: túnel central alto (pasa entre los pies) en el color de la moto, con tapa negra encima
      zona(perfil([[-0.06, 0.36], [-0.05, 0.64], [0.08, 0.67], [0.28, 0.64], [0.42, 0.55], [0.44, 0.36]], 0.21, pintura, decor, 0, 0.03, true), "lateral");
      perfil([[-0.02, 0.655], [0.1, 0.69], [0.3, 0.65], [0.38, 0.59], [0.26, 0.62], [0.08, 0.66]], 0.12, negro, decor, 0, 0.012);
    } else perfil([[0.0, 0.38], [0.04, 0.45], [0.26, 0.46], [0.32, 0.38]], 0.15, plastico, decor, 0, 0.02, true);
    panelAhusado([[-0.12, 0.37], [0.42, 0.37], [0.44, 0.3], [0.3, 0.22], [0.0, 0.2], [-0.16, 0.27]], 0.4, negro, () => 1, 0.018);

    // Carenado trasero en el color de la moto, angostándose hacia la cola
    zona(panelAhusado(aerox
      ? [[-0.06, 0.38], [-0.02, 0.64], [-0.1, 0.69], [-0.45, 0.74], [xR - 0.04, 0.83], [xR - 0.14, 0.95],
        [xR - 0.13, 0.9], [xR - 0.02, 0.7], [-0.55, 0.53], [-0.3, 0.44]]
      : [[-0.06, 0.38], [-0.02, 0.62], [-0.1, 0.68], [-0.45, 0.72], [xR - 0.13, 0.78], [xR - 0.23, 0.8],
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
    panelAhusado(aerox
      ? [[0.02, 0.68], [0.0, 0.74], [-0.1, 0.775], [-0.34, 0.77], [-0.4, 0.83], [-0.46, 0.86],
        [xR - 0.02, 0.885], [xR - 0.08, 0.865], [xR - 0.05, 0.81], [-0.45, 0.735], [-0.05, 0.685]]
      : [[0.02, 0.68], [0.0, 0.74], [-0.1, sube(0.775)], [-0.36, 0.77], [-0.42, 0.8], [-0.48, 0.82],
        [xR - 0.11, 0.835], [xR - 0.17, 0.805], [xR - 0.13, 0.765], [-0.45, 0.725], [-0.05, 0.685]], 0.3, M.asiento,
      (x) => (x > -0.1 ? 0.78 : x < -0.7 ? Math.max(0.6, 1 - (-0.7 - x) * 1.6) : 1), 0.03);

    // Parrilla trasera (agarradera)
    const parrilla = new THREE.CatmullRomCurve3([
      // Por fuera del asiento y del bisel del carenado (antes quedaba escondida dentro de ellos)
      V(-0.5, 0.82, 0.2), V(-0.72, 0.85, 0.2), V(xR - 0.17, 0.87, 0.13), V(xR - 0.2, 0.875, 0),
      V(xR - 0.17, 0.87, -0.13), V(-0.72, 0.85, -0.2), V(-0.5, 0.82, -0.2),
    ]);
    if (!aerox) malla(new THREE.TubeGeometry(parrilla, 60, 0.012, 10), negro, decor);
    else for (const lado of [1, -1]) {
      const agarradera = new THREE.CatmullRomCurve3([V(-0.46, 0.83, lado * 0.19), V(-0.58, 0.87, lado * 0.2), V(xR + 0.02, 0.89, lado * 0.17)]);
      malla(new THREE.TubeGeometry(agarradera, 16, 0.012, 8), negro, decor);
    }

    // Stop trasero en la punta de la cola
    const stop = aerox ? caja(0.02, 0.03, 0.12, M.stop, V(xR - 0.12, 0.89, 0), decor) : caja(0.02, 0.035, 0.17, M.stop, V(xR - 0.235, 0.765, 0), decor);
    stop.rotation.z = aerox ? 0.6 : 0.35;
    // NMAX: el stop envuelve la punta de la cola por los costados (foto trasera). Las direccionales de atrás van en
    // vástagos junto a la placa, como en las fotos (ver la placa más abajo).
    if (!aerox) for (const lado of [1, -1]) caja(0.06, 0.03, 0.014, M.stop, V(xR - 0.2, 0.775, lado * 0.088), decor).rotation.set(0, lado * 0.5, 0.35);

    // Tapa del escape plateada (protector térmico)
    // Media caña: se dibuja por ambas caras para que, visto desde atrás o por dentro, no parezca cortado
    const protector = malla(dosCaras(new THREE.CylinderGeometry(0.056, 0.056, 0.28, seg(24), 1, true, 0, Math.PI)), M.metal, decor);
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

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
  // ----- Carrocerías propias de enduro: Yamaha XTZ 125 y AKT TT 125 -----
  // Tanque angosto, aletas grandes a los lados (como tomas de aire), asiento largo y plano, tapas laterales tipo
  // porta número bajo el asiento y colín largo y levantado con su stop. El guardabarros delantero alto es el común.
  function carroceriaEnduro(modelo) {
    const aA = alturaAsiento;
    const xtz = modelo === "xtz";
    const tx = H.x - (xtz ? 0.22 : 0.2), ty = aA + (xtz ? 0.05 : 0.06);
    // Contornos por modelo (desde el tanque tx/ty y la pipa H): tanque, aleta, ribete oscuro de la aleta y colín.
    // XTZ: tanque redondeado y bajo; TT: más alto y cuadrado; XR 190L: aletas grandes que bajan hasta el frente del
    // motor (estilo CRF); DR 150: tanque ancho arriba y aleta con la mitad de abajo negra
    const E = {
      xtz: { ancho: 0.22, tapa: 0.1, cola: [0.22, 0.05],
        tanque: [[tx + 0.2, ty - 0.04], [tx + 0.18, ty + 0.07], [tx + 0.06, ty + 0.1], [tx - 0.12, ty + 0.07], [tx - 0.2, ty - 0.02], [tx - 0.1, ty - 0.09], [tx + 0.12, ty - 0.09]],
        aleta: [[tx + 0.21, ty + 0.03], [H.x + 0.0, H.y - 0.08], [H.x - 0.03, H.y - 0.24], [tx + 0.02, ty - 0.2], [tx - 0.04, ty - 0.06]],
        ribete: [[H.x - 0.02, H.y - 0.18], [H.x - 0.04, H.y - 0.25], [tx + 0.04, ty - 0.19], [tx + 0.09, ty - 0.14]] },
      tt: { ancho: 0.24, tapa: 0.12, cola: [0.18, 0.04],
        tanque: [[tx + 0.19, ty - 0.05], [tx + 0.19, ty + 0.09], [tx + 0.08, ty + 0.12], [tx - 0.12, ty + 0.1], [tx - 0.19, ty - 0.01], [tx - 0.1, ty - 0.1], [tx + 0.12, ty - 0.1]],
        aleta: [[tx + 0.2, ty + 0.06], [H.x + 0.02, H.y - 0.05], [H.x - 0.01, H.y - 0.3], [tx + 0.0, ty - 0.24], [tx - 0.06, ty - 0.04]],
        ribete: [[H.x - 0.0, H.y - 0.22], [H.x - 0.02, H.y - 0.31], [tx + 0.02, ty - 0.23], [tx + 0.08, ty - 0.17]] },
      xr: { ancho: 0.23, tapa: 0.1, cola: [0.25, 0.065],
        tanque: [[tx + 0.19, ty - 0.05], [tx + 0.18, ty + 0.075], [tx + 0.07, ty + 0.1], [tx - 0.12, ty + 0.075], [tx - 0.2, ty - 0.02], [tx - 0.1, ty - 0.1], [tx + 0.12, ty - 0.1]],
        aleta: [[tx + 0.21, ty + 0.05], [H.x + 0.03, H.y - 0.05], [H.x + 0.01, H.y - 0.33], [tx - 0.02, ty - 0.29], [tx - 0.09, ty - 0.06]],
        ribete: [[H.x + 0.0, H.y - 0.26], [H.x - 0.01, H.y - 0.34], [tx - 0.01, ty - 0.29], [tx + 0.06, ty - 0.22]] },
      dr: { ancho: 0.27, tapa: 0.13, cola: [0.21, 0.05],
        tanque: [[tx + 0.2, ty - 0.04], [tx + 0.2, ty + 0.1], [tx + 0.09, ty + 0.13], [tx - 0.12, ty + 0.1], [tx - 0.2, ty - 0.0], [tx - 0.1, ty - 0.1], [tx + 0.12, ty - 0.1]],
        aleta: [[tx + 0.22, ty + 0.07], [H.x + 0.02, H.y - 0.05], [H.x - 0.01, H.y - 0.3], [tx + 0.0, ty - 0.25], [tx - 0.06, ty - 0.03]],
        ribete: [[H.x + 0.0, H.y - 0.16], [H.x - 0.01, H.y - 0.3], [tx + 0.0, ty - 0.25], [tx - 0.05, ty - 0.1], [tx + 0.1, ty - 0.08]] },
    };
    const D = E[modelo] || E.tt; // (modelo desconocido: el de la TT)
    const oscuras = R.enduro?.tapas === "oscuro"; // tapas laterales y colín negros (DR 150)
    zona(panelAhusado(D.tanque, D.ancho, pintura, (x, y) => (x < tx - 0.04 ? Math.max(0.6, 1 - (tx - 0.04 - x) * 2) : 1) * (y < ty - 0.03 ? 0.75 : 1), 0.03), "tanque");
    disco(0.028, 0.012, M.oscuro, V(tx + 0.02, ty + D.tapa + 0.03, 0), decor, 20);
    disco(0.02, 0.016, M.cromo, V(tx + 0.02, ty + D.tapa + 0.036, 0), decor, 20);
    // Aletas laterales grandes, con un ribete oscuro abajo
    for (const lado of [1, -1]) {
      zona(perfil(D.aleta, 0.016, pintura, decor, lado * 0.128, 0.006, true), "tanque");
      perfil(D.ribete, 0.006, M.oscuro, decor, lado * 0.139, 0.003, true);
    }
    // Asiento largo y plano, de la parte de atrás del tanque hasta la cola
    panelAhusado([[tx - 0.08, ty + 0.02], [tx - 0.02, ty + 0.06], [xR + 0.04, aA + 0.05], [xR - 0.02, aA + 0.025],
      [xR + 0.0, aA - 0.02], [tx - 0.06, ty - 0.03]], 0.19, M.asiento, (x) => (x > tx - 0.12 ? 0.8 : 1), 0.025);
    // Tapas laterales tipo porta número (segundo tono) bajo el asiento
    zona(panelAhusado([[P.x + 0.05, aA - 0.02], [xR + 0.12, aA - 0.0], [xR + 0.2, aA - 0.11], [P.x + 0.0, aA - 0.17]],
      0.2, oscuras ? M.oscuro : pintura, () => 1, 0.02), "lateral", "cola");
    // Colín largo y levantado (guardabarros trasero de enduro) con su stop en la punta
    const [cl, ca] = D.cola;
    zona(panelAhusado([[xR + 0.16, aA - 0.04], [xR - 0.04, aA + 0.03], [xR - cl, aA + ca],
      [xR - cl + 0.01, aA + 0.015], [xR + 0.0, aA - 0.04], [xR + 0.12, aA - 0.09]], 0.16, oscuras ? M.oscuro : pintura,
    (x) => (x < xR ? Math.max(0.6, 1 - (xR - x) * 1.6) : 1), 0.015), "cola");
    const posStop = V(xR - cl + 0.02, aA + Math.max(0.03, ca - 0.02), 0);
    caja(0.022, 0.034, 0.08, M.oscuro, posStop.clone().add(V(0.008, 0, 0)), decor, 0.25);
    caja(0.012, 0.026, 0.07, M.stop, posStop, decor, 0.25);
  }

  // ----- Carrocería (color del usuario) -----
  const pintura = M.pintura;
  let pata = null;
  if (scooter && esMaxi) {
    carroceriaNmax(esAerox);
  } else if (scooter) {
    carroceriaScooter();
  } else if (tipo === "enduro" && (esXtz || esTt || R.enduro?.modelo)) {
    carroceriaEnduro(R.enduro?.modelo || (esXtz ? "xtz" : "tt"));
  } else if (fam === "semi") {
    carroceriaSemi();
  } else {
    carroceriaCalle();
  }
  if (!scooter) {
    // Guardabarros trasero (hugger) sobre la llanta; la placa y sus direccionales van más abajo, detrás de la llanta
    const hugger = malla(new THREE.TorusGeometry(Rr + 0.03, 0.01, 6, 24, Math.PI * 0.32), M.oscuro, decor);
    hugger.position.set(xR, Rr, 0);
    hugger.rotation.z = Math.PI * 0.42;
    hugger.scale.z = (anchoR / 2 + 0.012) / 0.01; // el tubo de 1 cm se ensancha hasta cubrir la llanta
    if (R.guardaTrasCromo) {
      // Clásica (GN): guardabarros trasero cromado largo que baja por detrás de la llanta
      const gt = malla(new THREE.TorusGeometry(Rr + 0.035, 0.009, 6, 24, Math.PI * 0.5), M.cromo, decor);
      gt.position.set(xR, Rr, 0);
      gt.rotation.z = Math.PI * 0.45;
      gt.scale.z = (anchoR / 2 + 0.02) / 0.009;
    }
    // Guardabarros delantero
    if (tipo === "enduro") {
      // Alto, de doble propósito: hoja larga unos 7 cm sobre la llanta, con la punta delantera levantada; pasa entre las
      // barras de la horquilla y se sujeta a ellas con dos platinas (antes quedaba metido en el chasís, sin verse)
      const yG = 2 * Rf + 0.075, xBarraG = xF - (yG - Rf) * Math.tan(rake);
      const matG = R.enduro?.guarda === "oscuro" ? M.oscuro : pintura;
      perfil([[-0.26, -0.035], [-0.02, 0.0], [0.2, 0.045], [0.235, 0.03], [0.21, 0.0], [-0.02, -0.03], [-0.25, -0.06]], 0.11, matG, decor, 0, 0.012)
        .position.set(xF, yG, 0);
      for (const lado of [1, -1]) tubo(V(xBarraG + 0.02, yG - 0.005, lado * 0.05), V(xBarraG, yG - 0.005, lado * zBarra), 0.008, M.oscuro, decor, 6);
    } else {
      // Cromado en las de trabajo (las que llevan parrilla) y en las semiautomáticas; negro en las naked; del color de
      // la moto en las commuter deportivas y las carenadas
      const guardaMat = R.guardaPintado ? pintura : (fam === "clasica" && R.parrilla) || fam === "semi" ? M.cromo : naked ? M.oscuro : pintura;
      const guarda = malla(new THREE.TorusGeometry(Rf + 0.025, 0.012, 6, 24, Math.PI * (naked ? 0.42 : 0.5)), guardaMat, decor);
      guarda.position.set(xF, Rf, 0);
      guarda.rotation.z = Math.PI * (naked ? 0.28 : 0.22);
      guarda.scale.z = 6;
      // Soportes del guardabarros a las botellas de la horquilla
      const Rg = Rf + 0.025, yS = Rf + Rg * 0.95, xG = xF - Rg * 0.3, xFork = xF - (yS - Rf) * Math.tan(rake);
      for (const lado of [1, -1]) tubo(V(xG, yS, lado * 0.06), V(xFork, yS, lado * zBarra), 0.006, M.oscuro, decor, 6);
    }
    if (specs.carenado) carenadoDeportivo();
  }

  // ----- Moto de calle (naked, clásica, commuter, carenada y enduro genérica) -----
  // Tanque, aletas, asiento, colín, tapas laterales y stop según los rasgos de la línea, medidos desde las anclas:
  // el tanque desde la pipa (H), el asiento y el colín desde el pivote (P), el eje trasero (xR) y la altura del asiento.
  function carroceriaCalle() {
    const aA = alturaAsiento;
    const T = { forma: "clasico", alto: tipo === "enduro" ? 0.09 : 0.11, ancho: tipo === "enduro" ? 0.26 : tipo === "sport" ? 0.34 : 0.32,
      largo: 0.25, nariz: 0.05, ...(R.tanque || {}) };
    if (fam === "carenada") Object.assign(T, { forma: "cuna", alto: 0.1, ancho: 0.34, nariz: 0.03 });
    const tx = H.x - (tipo === "enduro" ? 0.24 : 0.3), ty = aA + (tipo === "sport" ? 0.07 : 0.06);
    const a = T.alto, L = T.largo, n = T.nariz;
    // Contorno de perfil del tanque según su forma
    const contornoTanque = {
      // Cuña de naked: alto adelante, cae recto hacia el asiento
      cuna: [[tx + L + 0.03, ty - 0.04], [tx + L + 0.02, ty + a - 0.03], [tx + L * 0.6, ty + a], [tx - L * 0.35, ty + a - n],
        [tx - L * 0.75, ty + a - n - 0.03], [tx - L * 0.95, ty + 0.0], [tx - L * 0.6, ty - 0.06], [tx + L * 0.55, ty - 0.08]],
      // Gota redonda y larga (Boxer, GN)
      gota: [[tx + L - 0.01, ty - 0.04], [tx + L - 0.03, ty + a * 0.5], [tx + L * 0.5, ty + a], [tx - L * 0.15, ty + a],
        [tx - L * 0.7, ty + a * 0.5], [tx - L, ty - 0.03], [tx - L * 0.5, ty - 0.09], [tx + L * 0.5, ty - 0.09]],
      // Caja de esquinas suaves (Eco Deluxe)
      cuadrado: [[tx + L, ty - 0.04], [tx + L, ty + a * 0.7], [tx + L * 0.75, ty + a], [tx - L * 0.45, ty + a],
        [tx - L * 0.85, ty + a * 0.55], [tx - L, ty - 0.03], [tx - L * 0.5, ty - 0.09], [tx + L * 0.5, ty - 0.09]],
      // Commuter deportiva: cuña suave (las aletas laterales le dan el volumen)
      aletas: [[tx + L + 0.01, ty - 0.03], [tx + L, ty + a * 0.65], [tx + L * 0.4, ty + a], [tx - L * 0.2, ty + a * 0.92],
        [tx - L * 0.75, ty + a * 0.4], [tx - L, ty - 0.04], [tx - L * 0.5, ty - 0.1], [tx + L * 0.5, ty - 0.1]],
    }[T.forma] || [[tx + L, ty - 0.03], [tx + L - 0.01, ty + a * 0.55], [tx + L * 0.6, ty + a], [tx - 0.02, ty + a * 0.95],
      [tx - L * 0.68, ty + a * 0.45], [tx - L, ty - 0.04], [tx - L * 0.56, ty - a * 0.95], [tx + L * 0.48, ty - a * 0.9]];
    // Arista marcada a lo largo del costado (tanques angulosos)
    const anguloso = T.forma === "cuna" || T.forma === "aletas" || T.forma === "cuadrado";
    const arista = anguloso ? (x, y, z) => {
      const cerca = Math.max(0, 1 - Math.abs(y - (ty + a * 0.32)) / 0.05);
      return [x, y, z * (1 + 0.07 * cerca * cerca)];
    } : null;
    const tanque = panelAhusado(contornoTanque, T.ancho, pintura, (x, y) => {
      const atras = x < tx - 0.05 ? Math.max(0.55, 1 - (tx - 0.05 - x) * 2.2) : 1;
      const abajo = y < ty - 0.02 ? Math.max(0.6, 1 - (ty - 0.02 - y) * 3.2) : 1;
      const arriba = y > ty + a * 0.6 ? Math.max(0.7, 1 - (y - ty - a * 0.6) * 4) : 1;
      return atras * abajo * arriba;
    }, 0.035, arista);
    zona(tanque, "tanque");
    if (R.fuelles) {
      // Boxer: almohadillas de caucho para las rodillas a los lados del tanque y emblema cromado
      for (const lado of [1, -1]) {
        const zPad = (T.ancho / 2 + 0.035) * Math.max(0.55, 1 - 0.07 * 2.2);
        elipsoide(0.065, 0.04, 0.008, M.caucho, V(tx - 0.12, ty - 0.01, lado * (zPad + 0.002)), decor).rotation.y = lado * -0.18;
        caja(0.07, 0.012, 0.004, M.cromo, V(tx + 0.1, ty + 0.03, lado * (T.ancho / 2 + 0.03)), decor, 0.1);
      }
    }
    // Tapa de gasolina con aro, sobre lo más alto del tanque
    const xTapa = tx + L * 0.25, yTapa = ty + a + 0.03;
    disco(0.032, 0.012, M.oscuro, V(xTapa, yTapa, 0), decor, 24).rotation.set(0, 0, 0);
    disco(0.024, 0.016, M.cromo, V(xTapa, yTapa + 0.006, 0), decor, 24).rotation.set(0, 0, 0);
    // Aletas laterales
    if (naked) aletasNaked(tx, ty, T);
    else if (fam === "clasica" && (T.forma === "aletas" || T.aletas)) {
      // Commuter: aleta mediana pegada al tanque que baja hacia el motor (más alta en la NKD, más corta en la CR4)
      const ah = T.aletaAlto || 0.1;
      for (const lado of [1, -1]) {
        zona(perfil([[tx + L + 0.02, ty + 0.01], [tx + L * 0.25, ty + 0.03], [tx - L * 0.1, ty - ah * 0.45], [tx + L * 0.3, ty - ah],
          [H.x - 0.04, ty - ah * 0.8]], 0.014, pintura, decor, lado * (T.ancho / 2 - 0.004), 0.006), "tanque");
        perfil([[H.x - 0.05, ty - ah * 0.82], [tx + L * 0.32, ty - ah * 0.98], [tx + L * 0.2, ty - ah * 0.8], [H.x - 0.07, ty - ah * 0.65]],
          0.006, M.oscuro, decor, lado * (T.ancho / 2 + 0.006), 0.003);
      }
    } else if (tipo === "enduro") {
      for (const lado of [1, -1]) {
        perfil([[0, 0], [0.22, 0.06], [0.2, -0.16], [0.05, -0.2]], 0.02, pintura, decor, lado * 0.124, 0.008)
          .position.set(tx - 0.02, ty - 0.02, 0);
      }
    }

    // Asiento: más ancho donde se sienta el conductor y angosto hacia la cola; escalón al parrillero en las deportivas
    const inicioAsiento = tx - L + 0.05;
    const finAsiento = xR + 0.06;
    const escalon = R.asientoEscalonado ?? R.escalon ?? 0;
    const mitad = (inicioAsiento + finAsiento) / 2;
    const anchoAsiento = tipo === "enduro" ? 0.2 : 0.27;
    const angostarAsiento = (x) => (x > inicioAsiento + 0.14 ? Math.max(0.55, 1 - (x - inicioAsiento - 0.14) * 1.2) : 1)
      * (x < mitad - 0.05 ? Math.max(0.55, 1 - (mitad - 0.05 - x) * 1.4) : 1);
    if (R.asientoPartido) {
      // Asiento partido (RC): el del conductor termina antes del colín; el del parrillero es un cojín alto sobre el colín
      panelAhusado([[inicioAsiento, aA - 0.04], [inicioAsiento + 0.02, aA + 0.015], [inicioAsiento + 0.1, aA + 0.03], [mitad + 0.02, aA + 0.025],
        [mitad - 0.02, aA + 0.06], [mitad - 0.04, aA - 0.03]], anchoAsiento, M.asiento, angostarAsiento, 0.03);
      panelAhusado([[mitad - 0.06, aA + escalon - 0.01], [mitad - 0.07, aA + escalon + 0.03], [finAsiento + 0.06, aA + escalon + 0.045],
        [finAsiento + 0.03, aA + escalon + 0.005]], 0.2, M.asiento, () => 0.8, 0.02);
    } else if (R.asientoEscalonado) {
      // Escalonado clásico (GN): conductor hundido y parrillero en un escalón redondeado más alto
      panelAhusado([[inicioAsiento, aA - 0.04], [inicioAsiento + 0.02, aA + 0.015], [inicioAsiento + 0.1, aA + 0.03], [mitad + 0.02, aA + 0.0],
        [mitad - 0.06, aA + escalon * 0.4], [mitad - 0.12, aA + 0.03 + escalon], [finAsiento + 0.06, aA + 0.04 + escalon],
        [finAsiento + 0.0, aA + 0.015 + escalon], [finAsiento + 0.03, aA - 0.03]], anchoAsiento, M.asiento, angostarAsiento, 0.03);
    } else {
      panelAhusado([[inicioAsiento, aA - 0.04], [inicioAsiento + 0.02, aA + 0.015], [inicioAsiento + 0.1, aA + 0.035],
        [mitad, aA + 0.025], [mitad - 0.02, aA + 0.03 + escalon], [finAsiento + 0.1, aA + 0.05 + escalon],
        [finAsiento + 0.02, aA + 0.03 + escalon], [finAsiento + 0.04, aA - 0.03]], anchoAsiento, M.asiento, angostarAsiento, 0.03);
    }

    // Colín según su forma (rasgos.js): afilado/respingado (punta alta y corta), plano, largo o corto con guardabarros
    const C = R.colin || {};
    const formaColin = C.forma || "generico";
    let punta; // punta del colín: ahí va el stop
    let contornoColin;
    if (formaColin === "afilado" || formaColin === "respingado") {
      const tipX = xR + 0.1 - (C.largo ?? 0.2);
      const tipY = Math.max(aA + (C.alto ?? 0.12), aA + escalon + 0.03);
      const subeBajo = formaColin === "afilado" ? 0.3 : 0.15;
      contornoColin = [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA + escalon - 0.01], [tipX + 0.07, tipY - 0.005], [tipX, tipY - 0.012],
        [tipX + 0.03, tipY - 0.045], [xR + 0.1, aA - 0.1 + (C.alto ?? 0.12) * subeBajo], [P.x - 0.1, aA - 0.2], [P.x + 0.06, aA - 0.14]];
      punta = V(tipX + 0.015, tipY - 0.03);
    } else if (formaColin === "largo") {
      // Discover: tapa larga que sigue bajo todo el asiento hasta el tanque y una cola larga y baja
      contornoColin = [[inicioAsiento + 0.02, aA - 0.06], [finAsiento + 0.02, aA - 0.02], [xR - 0.1, aA + (C.alto ?? 0)], [xR - 0.14, aA - 0.03],
        [xR + 0.06, aA - 0.13], [P.x + 0.02, aA - 0.21], [inicioAsiento, aA - 0.17]];
      punta = V(xR - 0.11, aA - 0.025);
    } else if (formaColin === "corto") {
      // GN: colín corto que termina sobre el eje (atrás lo sigue el guardabarros cromado)
      contornoColin = [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA - 0.025 + escalon * 0.5], [xR + 0.0, aA - 0.03 + escalon * 0.5],
        [xR - 0.03, aA - 0.07], [xR + 0.1, aA - 0.13], [P.x - 0.1, aA - 0.19], [P.x + 0.06, aA - 0.14]];
      punta = V(xR - 0.03, aA - 0.07);
    } else if (formaColin === "plano") {
      contornoColin = [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA - 0.02], [xR - (C.largo ?? 0.1), aA - 0.01 + (C.alto ?? 0)],
        [xR - (C.largo ?? 0.1) - 0.03, aA - 0.04], [xR + 0.08, aA - 0.12], [P.x - 0.1, aA - 0.19], [P.x + 0.06, aA - 0.14]];
      punta = V(xR - (C.largo ?? 0.1) - 0.015, aA - 0.025);
    } else {
      contornoColin = [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA - 0.01 + escalon], [xR - 0.06, aA + escalon + 0.01],
        [xR - 0.1, aA + escalon - 0.025], [xR + 0.08, aA - 0.12], [P.x - 0.1, aA - 0.2], [P.x + 0.06, aA - 0.14]];
      punta = V(xR - 0.1, aA + escalon - 0.012);
    }
    const colin = panelAhusado(contornoColin, 0.22, pintura,
      (x) => (x < P.x - 0.1 ? Math.max(0.35, 1 - (P.x - 0.1 - x) * 1.6) : 1), 0.02,
      // (las afiladas, con arista a media altura como las naked reales)
      formaColin === "afilado" ? (x, y, z) => [x, y, z * (1 + 0.06 * Math.max(0, 1 - Math.abs(y - (aA - 0.05)) / 0.04))] : null);
    zona(colin, "lateral", "cola");
    if (C.partido) {
      // Gixxer: colín partido (franja negra a lo largo que lo separa en dos niveles, con el stop en dos)
      perfil([[finAsiento - 0.02, aA - 0.045], [punta.x + 0.03, punta.y - 0.0], [punta.x + 0.03, punta.y - 0.02], [finAsiento - 0.02, aA - 0.065]],
        0.215, M.oscuro, decor, 0, 0.012);
    }
    // Tapas laterales bajo el asiento
    if (R.fuelles) {
      // Boxer: tapa lateral ovalada con su emblema cromado
      for (const lado of [1, -1]) {
        const ovalo = Array.from({ length: 14 }, (_, k) => {
          const an = (k / 14) * Math.PI * 2;
          return [P.x + 0.07 + Math.cos(an) * 0.09, aA - 0.1 + Math.sin(an) * 0.05];
        });
        zona(perfil(ovalo, 0.014, pintura, decor, lado * 0.118, 0.006, true), "lateral");
        caja(0.05, 0.01, 0.004, M.cromo, V(P.x + 0.07, aA - 0.1, lado * 0.128), decor);
      }
    } else if (R.tapaRectangular) {
      // Eco Deluxe: tapa lateral grande y rectangular con franja cromada
      for (const lado of [1, -1]) {
        zona(perfil([[P.x + 0.17, aA - 0.05], [P.x - 0.06, aA - 0.05], [P.x - 0.04, aA - 0.17], [P.x + 0.15, aA - 0.17]], 0.012, pintura, decor,
          lado * 0.118, 0.006), "lateral");
        caja(0.12, 0.008, 0.004, M.cromo, V(P.x + 0.05, aA - 0.11, lado * 0.127), decor);
      }
    } else if (naked || fam === "carenada" || (fam === "clasica" && T.forma === "aletas")) {
      // Naked y commuter deportivas: tapa lateral negra angulosa entre el asiento y el basculante
      for (const lado of [1, -1]) {
        perfil([[P.x + 0.1, aA - 0.05], [P.x - 0.06, aA - 0.07], [P.x - 0.12, aA - 0.15], [P.x + 0.04, aA - 0.17]],
          0.012, M.oscuro, decor, lado * 0.112, 0.004, true);
      }
    }
    // Stop: carcasa negra con la mica roja encendida y una franja clara al centro (luz de placa)
    const giroStop = formaColin === "afilado" || formaColin === "respingado" ? 0.6 : formaColin === "corto" ? 1.1 : 0.5;
    const stopAparte = R.stop === "guardabarros" || R.stop === "redondo"; // (va sobre el guardabarros, ver la placa)
    if (!stopAparte) caja(0.03, 0.04, 0.125, M.oscuro, punta.clone().add(V(0.026, 0.004, 0)), decor).rotation.z = giroStop; // carcasa (la mica roja asoma por detrás)
    if (stopAparte) {
      // (la punta del colín queda solo con su remate oscuro)
      caja(0.02, 0.03, 0.1, M.oscuro, punta, decor).rotation.z = giroStop;
    } else if (R.stop === "led") {
      // MT-03 / Duke: franja LED fina en la punta del colín
      caja(0.01, 0.012, 0.12, M.stop, punta, decor).rotation.z = giroStop;
    } else if (formaFaro === "ns" || C.partido) {
      // Pulsar NS y Gixxer: stop partido en dos LED a cada lado de la punta del colín
      for (const lado of [1, -1]) {
        const led = caja(0.012, 0.022, 0.06, M.stop, punta.clone().add(V(0, 0, lado * 0.032)), decor);
        led.rotation.set(lado * 0.45, 0, giroStop);
      }
    } else {
      caja(0.012, 0.03, 0.11, M.stop, punta, decor).rotation.z = giroStop;
    }
    caja(0.004, 0.008, 0.05, M.luz, punta.clone().add(V(-0.007, -0.002, 0)), decor).rotation.z = giroStop;
  }

  // Aletas grandes de las naked: nacen bajo el tanque, bajan abrazando el radiador y terminan detrás de la horquilla.
  // Largo y caída según la línea (largas en la NS, anchas en la FZ, con tomas de aire en la MT-03); angulosas.
  // ----- Luces vestidas: cada lente encendida (faro, stop, direccionales, luz de placa) queda como una lámpara de
  // verdad: reflector metálico detrás, la fuente encendida más chica en el centro y la mica de vidrio por delante.
  // Se hace al final, sobre todas las lentes ya ubicadas, para que valga igual en las 25 carrocerías.
  function vestirLuces() {
    const centro = V((xF + xR) / 2, alturaAsiento * 0.75, 0);
    const lentes = decor.children.filter((m) => m.isMesh && !Object.keys(m.userData).length && [M.luz, M.stop, M.ambar].includes(m.material)
      && (m.geometry.type === "BoxGeometry" || m.geometry.type === "CylinderGeometry"));
    const ejes = [V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)];
    decor.updateMatrixWorld(true);
    const cuerpos = decor.children.filter((m) => m.isMesh && [M.pintura, M.pintura2, M.oscuro, M.asiento].includes(m.material));
    const rayoLuz = new THREE.Raycaster();
    for (const m of lentes) {
      const g = m.geometry;
      g.computeBoundingBox();
      const t = g.boundingBox.getSize(V());
      const tam = [t.x, t.y, t.z];
      const k = tam.indexOf(Math.min(...tam)); // eje delgado de la lente (hacia afuera)
      if (Math.min(...tam.filter((_, i) => i !== k)) < 0.012) continue; // (tiras muy finas: quedan como LED sueltos)
      const eje = ejes[k].clone().applyQuaternion(m.quaternion);
      if (eje.dot(m.position.clone().sub(centro)) < 0) eje.negate();
      // Si la lente quedó metida en la carrocería (el bisel de los paneles crece hacia afuera), se saca hasta la superficie
      // (rayo desde afuera hacia la lente: la primera cara que encuentra es la de afuera de la carrocería)
      rayoLuz.set(m.position.clone().add(eje.clone().multiplyScalar(0.12)), eje.clone().negate());
      const tapa = rayoLuz.intersectObjects(cuerpos, false)[0];
      const d = tapa ? tapa.point.clone().sub(m.position).dot(eje) : -1;
      if (d > -0.001 && d < 0.09) m.position.copy(tapa.point).add(eje.clone().multiplyScalar(tam[k] / 2 + 0.003));
      const capa = (mat, cara, grueso, desplazar) => {
        const c = malla(g.clone(), mat, decor);
        c.quaternion.copy(m.quaternion);
        const e = V(cara, cara, cara); e.setComponent(k, grueso / tam[k]);
        c.scale.copy(e);
        c.position.copy(m.position).add(eje.clone().multiplyScalar(desplazar));
        return c;
      };
      capa(M.metal, 1.06, 0.003, -tam[k] / 2 - 0.002);          // reflector
      // Faro: mica clara por delante y la fuente más chica, rodeada del reflector. Stop y direccionales: su lente de
      // color ya es la mica (una mica clara encima las desteñía)
      if (m.material === M.luz) {
        capa(M.vidrio, 1.08, 0.003, tam[k] / 2 + 0.003);
        const f = V(0.72, 0.72, 0.72); f.setComponent(k, 1);
        m.scale.multiply(f);
      }
    }
  }
  // Anclas de las luces para la escena (cono, halos, destellos), en coordenadas de la raíz: el CENTRO DE LA CARA de cada
  // lente (no el centro de la caja) y hacia dónde alumbra (normal del lente). Se calculan después de vestirLuces, con las
  // lentes ya sacadas a la superficie. anclas.lamparas trae una entrada por lente; faro/stop/direccional_* siguen siendo
  // Vector3 (el lente principal o el punto medio de los dos faros), como los usaba moto3d.js.
  function anclasLuces() {
    const ejes = [V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)];
    const centro = V((xF + xR) / 2, alturaAsiento * 0.75, 0), xMedio = (xF + xR) / 2;
    const lamparas = [];
    for (const m of decor.children) {
      if (!m.isMesh || ![M.luz, M.stop, M.ambar].includes(m.material)) continue;
      m.geometry.computeBoundingBox();
      const t = m.geometry.boundingBox.getSize(V()).multiply(m.scale), c = m.geometry.boundingBox.getCenter(V()).multiply(m.scale);
      const tam = [t.x, t.y, t.z], k = tam.indexOf(Math.min(...tam));
      const dir = ejes[k].clone().applyQuaternion(m.quaternion);
      const medio = m.position.clone().add(c.applyQuaternion(m.quaternion));
      if (dir.dot(medio.clone().sub(centro)) < 0) dir.negate();
      const otros = tam.filter((_, i) => i !== k);
      const pos = medio.clone().addScaledVector(dir, tam[k] / 2);
      let tipo = m.material === M.luz ? "faro" : m.material === M.stop ? "stop" : "direccional";
      if (tipo === "faro" && pos.x < xMedio) continue; // (luz de placa)
      if (tipo === "stop" && pos.x > xMedio) continue;
      const lado = tipo === "direccional" ? (pos.x > xMedio ? "d" : "t") + (pos.z > 0 ? "i" : "d")
        : pos.z > 0.02 ? "i" : pos.z < -0.02 ? "d" : "c";
      lamparas.push({ tipo, lado, pos, dir, ancho: Math.max(...otros), alto: Math.min(...otros), area: otros[0] * otros[1] });
    }
    // Principales: los lentes de más área de cada tipo (los faros dobles quedan los dos; las tiras finas de luz diurna no)
    // (faro: ≥ 80 % del lente mayor, así las tiras de luz diurna y las luces de posición no cuentan como faro)
    const principales = (tipo, filtro = () => true) => {
      const ls = lamparas.filter((l) => l.tipo === tipo && filtro(l));
      const max = Math.max(0, ...ls.map((l) => l.area));
      return ls.filter((l) => l.area >= max * (tipo === "faro" ? 0.8 : 0.5));
    };
    const medioDe = (ls) => (ls.length ? ls.reduce((a, l) => a.add(l.pos), V()).multiplyScalar(1 / ls.length) : null);
    const faros = principales("faro"), stops = principales("stop");
    for (const l of lamparas) l.principal = faros.includes(l) || stops.includes(l);
    const dir = (lado) => { const l = principales("direccional", (q) => q.lado === lado)[0]; if (l) l.principal = true; return l ? l.pos.clone() : null; };
    // Faros dobles (NMAX, Aerox, RS…): el punto medio cae entre los dos lentes y puede quedar dentro de la nariz. Si algo lo
    // tapa por delante, el ancla única pasa a la cara del lente principal (el de la izquierda si empatan); cada lente
    // tiene su propia ancla en "lamparas", que es lo que debe usarse con faros dobles.
    let faro = medioDe(faros);
    if (faro && faros.length > 1) {
      const d = faros.reduce((a, l) => a.add(l.dir), V()).normalize();
      decor.updateMatrixWorld(true);
      const r = new THREE.Raycaster(faro.clone().addScaledVector(d, 0.3), d.clone().negate(), 0, 0.3);
      const h = r.intersectObjects(decor.children.filter((m) => m.isMesh && !(m.material.transparent && m.material.opacity < 0.9)), false)[0];
      if (h && h.distance < 0.3 - 0.02) {
        const l = [...faros].sort((a, b) => b.area - a.area || b.pos.z - a.pos.z)[0];
        faro = l.pos.clone();
      }
    }
    const anclas = {
      faro, stop: medioDe(stops),
      direccional_di: dir("di"), direccional_dd: dir("dd"), direccional_ti: dir("ti"), direccional_td: dir("td"),
      lamparas,
    };
    for (const l of lamparas) delete l.area;
    return anclas;
  }
  // Primer punto de la carrocería por encima de (x, y, z): para colgar soportes del colín sin que queden en el aire
  function techoSobre(x, y, z, maximo = 0.5, otros = []) {
    const r = techoSobre.rayo || (techoSobre.rayo = new THREE.Raycaster());
    decor.updateMatrixWorld(true);
    r.set(V(x, y, z), V(0, 1, 0));
    r.far = maximo;
    const h = r.intersectObjects(decor.children.filter((m) => m.isMesh && (m.material === M.pintura || m.material === M.pintura2 || m.material === M.oscuro || otros.includes(m.material))), false)[0];
    return h ? h.point.y : null;
  }
  // Punto de la superficie de una malla visto desde adelante (rayo hacia atrás a esa altura y costado) y su normal:
  // así las luces quedan pegadas por fuera de la carrocería curva, sin quedar enterradas ni flotando
  // (el rayo se crea al primer uso: esta función se llama también desde secciones que van antes en el armado)
  function sobre(m, y, z) {
    const _rayo = sobre.rayo || (sobre.rayo = new THREE.Raycaster());
    m.updateMatrixWorld(true);
    _rayo.set(V(xF + 1, y, z), V(-1, 0, 0));
    const h = _rayo.intersectObject(m, false)[0];
    if (!h) return null;
    return { p: h.point, n: h.face.normal.clone().transformDirection(m.matrixWorld) };
  }
  // Pieza pegada sobre la superficie: su eje x (cajas) o y (discos) mirando hacia afuera, según la normal
  function pegar(pieza, en, eje = V(1, 0, 0), afuera = 0.004) {
    pieza.position.copy(en.p).add(en.n.clone().multiplyScalar(afuera));
    pieza.quaternion.setFromUnitVectors(eje, en.n);
    return pieza;
  }
  // Une la malla de un costado con la del otro (mismo material): queda una sola, en la primera
  function unirLados(a, b) {
    const g = mergeGeometries([a.geometry, b.geometry].map((x) => { const y = x.index ? x.toNonIndexed() : x; if (y.attributes.uv) y.deleteAttribute("uv"); return y; }));
    if (!g) return a;
    a.geometry.dispose(); b.geometry.dispose();
    a.geometry = g;
    b.parent?.remove(b);
    return a;
  }
  function aletasNaked(tx, ty, T) {
    const A = R.aleta || { largo: 0.2, baja: 0.16 };
    const radX = H.x - 0.12;
    const yBajo = ty - 0.1 - A.baja, xDel = H.x - 0.08 + A.largo * 0.5;
    const zAleta = Math.max(0.168, T.ancho / 2 - 0.01);
    // Cuña: borde de arriba bajo el tanque, punta adelante y abajo, borde de abajo que sube en diagonal hacia atrás
    const contornoAleta = [[tx - 0.02, ty - 0.01], [tx + T.largo - 0.02, ty - 0.02], [xDel + 0.05, yBajo + 0.13], [xDel + 0.03, yBajo + 0.02],
      [radX - 0.02, yBajo + 0.01], [tx - 0.01, ty - 0.11]];
    const yAlto = ty - 0.01;
    // Curvada: arriba se mete bajo el tanque y adelante se recoge hacia la horquilla
    const curvar = (m) => {
      const q = m.geometry.attributes.position;
      for (let i = 0; i < q.count; i++) {
        const t = Math.min(1, Math.max(0, (q.getY(i) - yBajo) / (yAlto - yBajo)));
        const adelante = Math.min(1, Math.max(0, (q.getX(i) - (H.x - 0.12)) / 0.16));
        q.setZ(i, q.getZ(i) * (1 - 0.2 * t * t) * (1 - 0.18 * adelante * adelante));
      }
      q.needsUpdate = true;
      m.geometry.computeVertexNormals();
      return m;
    };
    // Las dos aletas en una sola malla (una llamada de dibujo)
    const [izq, der] = [1, -1].map((lado) => curvar(perfil(contornoAleta, 0.014, pintura, decor, lado * zAleta, 0.006)));
    unirLados(izq, der);
    zona(izq, "tanque");
    for (const lado of [1, -1]) {
      // Punta inferior negra de contraste (sobre la misma curva, para que quede pegada a la aleta)
      curvar(perfil([[xDel + 0.045, yBajo + 0.1], [xDel + 0.025, yBajo + 0.025], [radX + 0.02, yBajo + 0.025], [xDel - 0.0, yBajo + 0.07]],
        0.006, M.oscuro, decor, lado * (zAleta + 0.009), 0.003));
      if (R.tomasAire) {
        // MT-03: toma de aire negra en la parte alta y delantera de la aleta
        curvar(perfil([[tx + T.largo - 0.03, ty - 0.03], [xDel + 0.035, yBajo + 0.14], [xDel - 0.02, yBajo + 0.11], [tx + T.largo - 0.1, ty - 0.06]],
          0.01, M.oscuro, decor, lado * (zAleta + 0.01), 0.003));
      }
    }
  }

  // ----- Semiautomática (Wave, Best, Crypton): sin tanque, con el hueco paso-a-través a la vista -----
  // Escudo de piernas estrecho y curvo que baja de la pipa al túnel, túnel bajo hasta el cuerpo trasero, asiento largo
  // y plano y cola redondeada.
  function carroceriaSemi() {
    const S = R.semi || { escudo: "curvo", asientoLargo: 0.6 };
    const aA = alturaAsiento;
    const curvo = S.escudo !== "anguloso";
    const escudo = curvo
      ? [[H.x + 0.035, H.y - 0.03], [H.x - 0.05, H.y + 0.0], [H.x - 0.09, H.y - 0.1], [P.x + 0.36, P.y + 0.12], [P.x + 0.32, P.y + 0.05],
        [P.x + 0.42, P.y + 0.0], [H.x - 0.02, H.y - 0.24]]
      : [[H.x + 0.04, H.y - 0.02], [H.x - 0.05, H.y + 0.0], [H.x - 0.1, H.y - 0.08], [H.x - 0.12, H.y - 0.2], [P.x + 0.35, P.y + 0.12],
        [P.x + 0.32, P.y + 0.05], [P.x + 0.43, P.y + 0.0], [H.x - 0.01, H.y - 0.28], [H.x + 0.02, H.y - 0.18]];
    const media = 0.13;
    zona(panelAhusado(escudo, media * 2, pintura, (x, y) => (y > H.y - 0.12 ? Math.max(0.6, 1 - (y - H.y + 0.12) * 2.2) : 1), 0.025,
      // Curvo en planta: los costados se van hacia atrás envolviendo las piernas
      (x, y, z) => [x - (curvo ? 0.05 : 0.03) * Math.min(1, (z / media) ** 2), y, z]), "frontal");
    // Túnel bajo (tapa de la espina del chasis) del escudo al cuerpo trasero: encima queda el hueco para pasar la pierna
    panelAhusado([[P.x + 0.4, P.y + 0.0], [P.x + 0.34, P.y + 0.1], [P.x + 0.14, P.y + 0.13], [P.x + 0.1, P.y + 0.05], [P.x + 0.3, P.y - 0.02]],
      0.15, pintura, () => 1, 0.02);
    // Cuerpo trasero redondeado bajo el asiento hasta la cola
    const ini = P.x + 0.16, largo = S.asientoLargo;
    zona(panelAhusado([[P.x + 0.13, P.y + 0.1], [ini + 0.01, aA - 0.06], [ini - largo - 0.02, aA - 0.035], [ini - largo - 0.06, aA - 0.08],
      [xR + 0.1, P.y + 0.2], [P.x - 0.05, P.y + 0.12]], 0.24, pintura,
    (x) => (x < P.x - 0.1 ? Math.max(0.7, 1 - (P.x - 0.1 - x) * 0.6) : 1), 0.025), "lateral", "cola");
    // Asiento largo y plano
    panelAhusado([[ini, aA - 0.05], [ini + 0.015, aA + 0.015], [ini - 0.08, aA + 0.035], [ini - largo + 0.05, aA + 0.035],
      [ini - largo, aA + 0.01], [ini - largo + 0.01, aA - 0.04]], 0.24, M.asiento, (x) => (x > ini - 0.1 ? 0.82 : 1), 0.025);
    // Stop en la punta de la cola, mirando atrás y abajo (más adentro lo tapaba el bisel del panel en 3/4)
    // (mirando atrás y un poco abajo, en la punta: más girado quedaba bajo la cola o detrás del porta placa)
    const punta = V(ini - largo - 0.078, aA - 0.078);
    caja(0.03, 0.045, 0.13, M.oscuro, punta.clone().add(V(0.022, 0.006, 0)), decor).rotation.z = 0.4;
    caja(0.012, 0.035, 0.11, M.stop, punta, decor).rotation.z = 0.4;
  }

  // ----- Scooter pequeña (Dio, Dynamic Pro): escudo inclinado como la dirección, piso bajo y plano, cuerpo trasero
  // redondeado (Dio) o anguloso (Dynamic) -----
  function carroceriaScooter() {
    const Sc = R.scooter || { estilo: "redonda" };
    const redonda = Sc.estilo !== "angulosa";
    const aA = alturaAsiento, yPiso = 0.3;
    // Línea de la horquilla: el frente del escudo va paralelo a ella, un poco por delante (~25°)
    const tanR = Math.tan(rake);
    const enHorquilla = (y, adelante) => xF - (y - Rf) * tanR + adelante;
    const yBajoF = 2 * Rf + 0.05;
    const F1 = [enHorquilla(yBajoF, 0.08), yBajoF], F2 = [enHorquilla(H.y - 0.04, 0.06), H.y - 0.04];
    const T1 = [enHorquilla(H.y + 0.01, 0.02), H.y + 0.01];
    const escudo = redonda
      ? [F1, F2, T1, [T1[0] - 0.13, T1[1] - 0.01], [T1[0] - 0.11, (T1[1] + yPiso) / 2], [0.3, yPiso + 0.07], [0.31, yPiso + 0.005],
        [(0.31 + F1[0]) / 2, (yPiso + F1[1]) / 2 - 0.01]]
      : [F1, F2, [F2[0] - 0.005, F2[1] + 0.005], T1, [T1[0] - 0.14, T1[1] - 0.005], [T1[0] - 0.14, T1[1] - 0.03], [T1[0] - 0.1, (T1[1] + yPiso) / 2],
        [0.3, yPiso + 0.06], [0.31, yPiso + 0.005], [(0.31 + F1[0]) / 2, (yPiso + F1[1]) / 2 - 0.005], [F1[0] - 0.005, F1[1] - 0.005]];
    const media = 0.18;
    const escudoM = zona(panelAhusado(escudo, media * 2, pintura,
      (x, y) => (x > F2[0] - 0.05 ? Math.max(0.5, 1 - (x - F2[0] + 0.05) * 2.4) : 1) * (y > H.y - 0.06 ? Math.max(0.6, 1 - (y - H.y + 0.06) * 2.5) : 1),
      0.03, (x, y, z) => [x - (redonda ? 0.05 : 0.025) * Math.min(1, (z / media) ** 2), y, z]), "frontal");
    // Escudo interior oscuro (donde van las rodillas)
    panelAhusado([[T1[0] - 0.14, T1[1] - 0.02], [T1[0] - 0.12, (T1[1] + yPiso) / 2], [0.28, yPiso + 0.06], [0.26, yPiso + 0.06],
      [T1[0] - 0.16, (T1[1] + yPiso) / 2], [T1[0] - 0.16, T1[1] - 0.03]], 0.3, M.oscuro, () => 1, 0.012);
    // Piso plano con tapetes de caucho y faldón negro
    caja(0.42, 0.035, 0.3, M.oscuro, V(0.1, yPiso, 0), decor);
    for (let i = 0; i < 6; i++) caja(0.014, 0.006, 0.22, M.caucho, V(-0.06 + i * 0.06, yPiso + 0.02, 0), decor);
    panelAhusado([[-0.12, yPiso], [0.42, yPiso], [0.44, yPiso - 0.05], [0.3, yPiso - 0.11], [0.0, yPiso - 0.12], [-0.16, yPiso - 0.06]],
      0.3, M.oscuro, () => 1, 0.018);
    // Frente del escudo a una altura (recta F1–F2) para pegar el faro y las direccionales
    const frenteEscudo = (y) => F1[0] + (F2[0] - F1[0]) * (y - F1[1]) / (F2[1] - F1[1]) + 0.03;
    const ambarEscudo = M.ambar;
    const giro = Math.atan2(F2[0] - F1[0], F2[1] - F1[1]);
    if (Sc.faroEscudo) {
      // Dio (fotos en manual_despiece/honda-dio-110): faro en V en el escudo, bajo la tapa del manubrio,
      // con las direccionales ámbar a cada lado, más arriba y hacia afuera
      const yF = H.y - 0.12;
      const en = sobre(escudoM, yF, 0);
      if (en) pegar(caja(0.018, 0.07, 0.15, M.oscuro, V(), decor), en, V(1, 0, 0), 0.004);
      for (const lado of [1, -1]) {
        const f = sobre(escudoM, yF - 0.008, lado * 0.035);
        if (f) pegar(caja(0.008, 0.045, 0.075, M.luz, V(), decor), f, V(1, 0, 0), 0.012).rotateX(-lado * 0.35);
      }
    } else if (!Sc.faroManubrio) {
      // Dynamic Pro (fotos en manual_despiece/akt-dynamic-pro-125): dos faros lado a lado en el escudo, sobre un marco negro
      const yF = H.y - 0.13;
      const en = sobre(escudoM, yF, 0);
      if (en) pegar(caja(0.02, 0.075, 0.17, M.oscuro, V(), decor), en, V(1, 0, 0), 0.004);
      for (const lado of [1, -1]) {
        const f = sobre(escudoM, yF, lado * 0.045);
        if (f) pegar(caja(0.008, 0.058, 0.068, M.luz, V(), decor), f, V(1, 0, 0), 0.014).rotateX(lado * 0.12);
      }
    }
    for (const lado of [1, -1]) {
      if (Sc.faroEscudo) {
        const a = sobre(escudoM, H.y - 0.07, lado * 0.095);
        if (a) pegar(caja(0.012, 0.04, 0.04, ambarEscudo, V(), decor), a, V(1, 0, 0), 0.007);
        continue;
      }
      const yA = redonda ? H.y - 0.02 : H.y - 0.21;
      caja(0.014, 0.025, 0.05, ambarEscudo, V(frenteEscudo(yA) - 0.01, yA, lado * (redonda ? 0.11 : 0.1)), decor, -giro);
    }
    // Cuerpo trasero: redondo y abultado (Dio) o anguloso con arista y cola en punta (Dynamic)
    const cuerpo = redonda
      ? [[0.02, yPiso + 0.01], [-0.03, 0.47], [-0.1, aA - 0.08], [-0.3, aA - 0.05], [xR + 0.06, aA - 0.045], [xR - 0.07, aA - 0.08],
        [xR - 0.05, aA - 0.15], [xR + 0.12, aA - 0.24], [P.x - 0.1, Rr + 0.2], [-0.18, yPiso + 0.05]]
      : [[0.02, yPiso + 0.01], [-0.04, 0.49], [-0.1, aA - 0.08], [-0.32, aA - 0.05], [xR + 0.02, aA - 0.02], [xR - 0.13, aA - 0.0],
        [xR - 0.12, aA - 0.035], [xR + 0.02, aA - 0.15], [xR + 0.16, aA - 0.24], [P.x - 0.1, Rr + 0.19], [-0.18, yPiso + 0.05]];
    zona(panelAhusado(cuerpo, redonda ? 0.27 : 0.3, pintura, (x) => (x < xR + 0.3 ? Math.max(0.5, 1 - (xR + 0.3 - x) * 1.4) : 1), redonda ? 0.045 : 0.035,
      redonda ? null : (x, y, z) => [x, y, z * (1 + 0.08 * Math.max(0, 1 - Math.abs(y - (aA - 0.12)) / 0.05))]), "lateral", "cola");
    // Asiento largo: redondeado en la Dio, con escalón al parrillero en la Dynamic
    if (redonda) {
      perfil([[-0.06, aA - 0.08], [-0.1, aA + 0.0], [-0.3, aA - 0.0], [xR + 0.02, aA + 0.015], [xR - 0.04, aA - 0.04]], 0.25, M.asiento, decor, 0, 0.025, true);
    } else {
      perfil([[-0.07, aA - 0.08], [-0.1, aA - 0.005], [-0.28, aA - 0.01], [-0.33, aA + 0.025], [xR - 0.04, aA + 0.035], [xR - 0.08, aA + 0.0],
        [xR - 0.06, aA - 0.04]], 0.25, M.asiento, decor, 0, 0.025, true);
    }
    // Stop: redondeado en la cola de la Dio; en punta y partido en la Dynamic
    if (redonda) caja(0.04, 0.045, 0.15, M.stop, V(xR - 0.095, aA - 0.12, 0), decor, 0.4);
    else for (const lado of [1, -1]) caja(0.02, 0.025, 0.07, M.stop, V(xR - 0.11, aA - 0.025, lado * 0.045), decor, 0.6).rotation.x = lado * 0.4;
    // Dynamic: franja lateral oscura a lo largo de la arista
    if (!redonda) {
      for (const lado of [1, -1]) {
        perfil([[-0.02, aA - 0.14], [-0.06, aA - 0.1], [xR + 0.05, aA - 0.08], [xR + 0.03, aA - 0.11], [-0.1, aA - 0.15]], 0.006, M.oscuro, decor,
          lado * 0.183, 0.003).userData.bajoCalca = true;
      }
    }
    // Parrilla trasera con patas que la atornillan al carenado
    const parrillaScooter = new THREE.CatmullRomCurve3([
      V(-0.28, aA + 0.03, 0.15), V(xR + 0.1, aA + 0.045, 0.15), V(xR - 0.06, aA + 0.05, 0.08),
      V(xR - 0.06, aA + 0.05, -0.08), V(xR + 0.1, aA + 0.045, -0.15), V(-0.28, aA + 0.03, -0.15),
    ]);
    malla(new THREE.TubeGeometry(parrillaScooter, 50, 0.011, 8), M.chasis, decor);
    for (const lado of [1, -1]) {
      for (const x of [-0.26, xR + 0.1]) tubo(V(x, aA + 0.035, lado * 0.15), V(x + 0.01, aA - 0.07, lado * 0.14), 0.008, M.chasis, decor, 8);
    }
    // Guardabarros delantero corto que sigue la llanta
    const formaGuarda = new THREE.Shape();
    formaGuarda.absarc(0, 0, Rf + 0.04, Math.PI * 0.22, Math.PI * 0.72, false);
    formaGuarda.absarc(0, 0, Rf + 0.025, Math.PI * 0.72, Math.PI * 0.22, true);
    const geoGuarda = new THREE.ExtrudeGeometry(formaGuarda, { depth: 0.1, bevelEnabled: true, bevelSize: 0.006, bevelThickness: 0.008, bevelSegments: 2, curveSegments: 16 });
    geoGuarda.translate(0, 0, -0.05);
    malla(geoGuarda, pintura, decor).position.set(xF, Rf, 0);
  }

  // ----- Carenado deportivo (RS 200, RC 200): cubre del 50 al 70 % del motor (medido desde el centro del motor),
  // cúpula alta (RS) o baja (RC), quilla bajo el motor y faros de su línea -----
  function carenadoDeportivo() {
    const C = R.carenado || { cupula: 0.2, cubre: 0.6 };
    const tanqueX = H.x - 0.3, tanqueY = alturaAsiento + 0.07;
    const Ex = P.x + 0.2 * s + 0.04, Ey = P.y + 0.05;
    // Motor de punta a punta: de la culata (adelante) a la parte de atrás del cárter, junto al pivote
    const xFrenteMotor = Ex + 0.2 * s, xAtrasMotor = P.x + 0.02;
    const xC = xFrenteMotor - C.cubre * (xFrenteMotor - xAtrasMotor); // borde trasero del costado
    // Cúpula baja (RC): lomo más bajo y nariz más larga, baja y afilada; alta (RS): más alta y redondeada
    const baja = Math.max(0, 0.2 - C.cupula), alto = (C.cupula - 0.2) * 0.6;
    const tanRake = Math.tan(rake);
    // Nariz por delante de la horquilla; el frente sube hacia atrás paralelo a la dirección
    const nariz = [H.x + 0.3 + baja * 0.5, H.y - 0.19 - baja * 0.5];
    const yBaseCupula = H.y + 0.05 + alto;
    const frenteCupula = [nariz[0] - (yBaseCupula - nariz[1]) * tanRake * 1.15, yBaseCupula];
    const angostar = (x, y) => (x > H.x ? Math.max(0.32, 1 - (x - H.x) * 2.8) : 1) * (y < P.y + 0.12 ? 0.85 : 1);
    // Parte de arriba en el color de la moto; abajo, la parte negra que sigue tapando el motor (dos tonos, como las reales)
    const puntosCarenado = [nariz, frenteCupula, [H.x - 0.04, yBaseCupula + 0.03], [tanqueX + 0.07, tanqueY - 0.07],
      [xC + 0.02, P.y + 0.22], [xC + 0.07, Ey + 0.08], [xFrenteMotor, Ey + 0.05], [H.x + 0.06, Ey + 0.11],
      [nariz[0] - 0.06, nariz[1] - 0.08 + baja * 0.3]];
    // Borde inferior del carenado negro: lo más bajo bajo el frente del motor y sube hacia atrás
    const puntosBajo = [[xC + 0.05, Ey + 0.12], [xC, Ey + 0.02], [xC + 0.05, Ey - 0.03], [xFrenteMotor + 0.03, Ey - 0.08 * s],
      [H.x + 0.04, Ey + 0.05], [H.x + 0.1, Ey + 0.15]];
    const xs = puntosCarenado.map((q) => q[0]), ys = puntosCarenado.map((q) => q[1]);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const bombeoEn = (x, y) => {
      const u = Math.min(1, Math.max(0, (x - x0) / (x1 - x0))), v = Math.min(1, Math.max(0, (y - y0) / (y1 - y0)));
      return 1 + (0.06 + C.cupula * 0.3) * Math.sin(Math.PI * u) * Math.sin(Math.PI * v); // RS más redondeada
    };
    const media = 0.155;
    const tNariz = (x) => Math.min(1, Math.max(0, (x - H.x + 0.08) / 0.36));
    // Nariz en V vista desde arriba (los costados se recogen hacia atrás) y costados apenas abombados
    const redondearNariz = (x, y, z) => {
      const zn = Math.min(1, Math.abs(z) / (media * angostar(x, y)));
      return [x - 0.07 * tNariz(x) * zn * zn, y, z * bombeoEn(x, y)];
    };
    const carenado = zona(panelAhusado(puntosCarenado, media * 2, pintura, angostar, 0.03, redondearNariz), "frontal");
    // (más angosto que el de arriba: queda metido por dentro en la unión y no se pelean las dos superficies)
    panelAhusado(puntosBajo, media * 1.72, M.oscuro, angostar, 0.03, (x, y, z) => [x, y, z * bombeoEn(x, y)], 2);
    // Rejillas de ventilación en los costados, apoyadas sobre la superficie
    const zCarenado = (x, y) => (media + 0.03) * angostar(x, y) * bombeoEn(x, y);
    for (const lado of [1, -1]) {
      for (let k = 0; k < 3; k++) {
        const x = H.x - 0.08 - k * 0.03, y = H.y - 0.17 - k * 0.045;
        caja(0.1, 0.012, 0.006, M.oscuro, V(x, y, lado * (zCarenado(x, y) + 0.001)), decor, 0.55).rotation.y = lado * 0.12;
      }
    }
    // Quilla negra bajo el motor
    if (C.quilla) {
      panelAhusado([[xC + 0.02, Ey - 0.07 * s], [xFrenteMotor + 0.04, P.y - 0.04], [xFrenteMotor, P.y - 0.12], [xAtrasMotor + 0.06, P.y - 0.1]], 0.26,
        M.oscuro, (x) => (x > xFrenteMotor - 0.02 ? 0.7 : 1), 0.02, null, 3);
    }
    // Cúpula inclinada hacia atrás siguiendo la dirección: alta en la RS, baja y tendida en la RC
    const h = C.cupula, inclina = tanRake * 1.3;
    const fc = frenteCupula;
    perfil([[fc[0] + 0.01, fc[1] - 0.01], [fc[0] - h * inclina, fc[1] + h], [fc[0] - h * inclina - 0.06, fc[1] + h - 0.02], [fc[0] - 0.09, fc[1] + 0.02]],
      0.22, M.vidrio, decor, 0, 0.01);
    // Faros pegados sobre la nariz (con un rayo contra la superficie real), mirando hacia afuera para que se vean en 3/4.
    // RS: dos proyectores redondos separados con cejas de luz diurna; RC: dos lentes rasgadas juntas.
    for (const lado of [1, -1]) {
      if (C.dobleFaro) {
        const en = sobre(carenado, nariz[1] + 0.06, lado * 0.045);
        if (en) {
          pegar(disco(0.032, 0.02, M.oscuro, V(), decor, 18), en, V(0, 1, 0), 0.006);
          pegar(disco(0.025, 0.006, M.luz, V(), decor, 18), en, V(0, 1, 0), 0.017);
        }
        const ceja = sobre(carenado, nariz[1] + 0.11, lado * 0.05);
        if (ceja) pegar(caja(0.006, 0.01, 0.06, M.luz, V(), decor), ceja).rotateX(lado * 0.35);
      } else {
        const en = sobre(carenado, nariz[1] + 0.045, lado * 0.03);
        if (en) {
          pegar(caja(0.012, 0.03, 0.05, M.oscuro, V(), decor), en, V(1, 0, 0), 0.004).rotateX(lado * 0.4);
          pegar(caja(0.006, 0.022, 0.044, M.luz, V(), decor), en, V(1, 0, 0), 0.011).rotateX(lado * 0.4);
        }
      }
    }
    // Direccionales delanteras integradas a los costados del carenado
    for (const lado of [1, -1]) {
      const d = sobre(carenado, H.y - 0.1, lado * 0.105);
      if (d) pegar(caja(0.012, 0.016, 0.04, M.ambar, V(), decor), d, V(1, 0, 0), 0.004);
    }
    // Toma de aire central bajo los faros
    const toma = sobre(carenado, nariz[1] - 0.005, 0);
    if (toma) pegar(caja(0.012, 0.024, 0.06, M.oscuro, V(), decor), toma);
  }

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
  // ----- Detalles que dan realismo -----
  // Tablero de instrumentos
  if (R.relojes && !scooter) {
    // Relojes redondos (clásicas y NKD): uno o dos tambores con aro y carátula, inclinados hacia el conductor
    const zs = R.relojes === "dos" ? [0.05, -0.05] : [0];
    const aroMat = R.direccionales?.cromo ? M.cromo : M.oscuro;
    for (const z of zs) {
      const c = V(H.x - 0.06, H.y + altoManubrio + 0.06, z), n = V(-Math.sin(0.6), Math.cos(0.6), 0);
      disco(0.043, 0.045, aroMat, c, decor, 20).rotation.z = 0.6;
      disco(0.036, 0.004, M.pantalla, c.clone().addScaledVector(n, 0.024), decor, 20).rotation.z = 0.6;
      // Soporte desde la tija superior (con manubrio alto, como la GN, los relojes quedaban sueltos en el aire)
      tubo(V(H.x, H.y + 0.02, z * 0.4), c.clone().addScaledVector(n, -0.02), 0.009, M.oscuro, decor);
    }
  } else {
  const tablero = caja(0.07, 0.05, 0.14, M.tablero, V(H.x - 0.07, H.y + altoManubrio + 0.05, 0), decor);
  tablero.rotation.z = -0.5;
  // la cara de arriba del tablero mira hacia (sen 0,5; cos 0,5): la pantalla va pegada a esa cara
  caja(0.052, 0.003, 0.11, M.pantalla, V(H.x - 0.07 + Math.sin(0.5) * 0.026, H.y + altoManubrio + 0.05 + Math.cos(0.5) * 0.026, 0), decor, -0.5);
  }
  // Lámpara de una direccional según su tipo (rasgos.direccionales): "redondas" = bombillo en copa redonda (cromada en
  // las clásicas), "led" = barrita fina, por defecto la cajita ámbar. "atras" = la mica mira hacia atrás.
  const tipoDir = R.direccionales?.tipo, tipoDirLinea = tipoDir, copaDir = R.direccionales?.cromo ? M.cromo : M.oscuro;
  function lamparaDir(punta, lado, atras, tipoDir = tipoDirLinea) {
    const s = atras ? -1 : 1;
    if (tipoDir === "redondas") {
      disco(0.021, 0.03, copaDir, punta.clone().add(V(-s * 0.004, 0, 0)), decor, 14).rotation.set(0, 0, Math.PI / 2);
      disco(0.019, 0.012, M.ambar, punta.clone().add(V(s * 0.014, 0, 0)), decor, 14).rotation.set(0, 0, Math.PI / 2);
    } else if (tipoDir === "led") {
      caja(0.012, 0.012, 0.045, M.oscuro, punta.clone().add(V(-s * 0.002, 0, lado * 0.01)), decor);
      caja(0.008, 0.008, 0.04, M.ambar, punta.clone().add(V(s * 0.006, 0, lado * 0.01)), decor);
    } else if (atras) {
      caja(0.03, 0.022, 0.03, M.oscuro, punta.clone().add(V(0.004, 0, 0)), decor); // carcasa
      caja(0.014, 0.024, 0.032, M.ambar, punta.clone().add(V(-0.016, 0, 0)), decor); // mica ámbar mirando atrás
    } else {
      caja(0.014, 0.022, 0.03, M.ambar, punta.clone().add(V(0.012, 0, lado * 0.008)), decor).rotation.y = -lado * 0.3;
    }
  }
  if (!scooter) {
    const ambar = M.ambar;
    for (const lado of [1, -1]) {
      // Direccional delantera en su tallo, a los lados del faro
      const base = V(H.x + 0.04, H.y - 0.12, lado * 0.09);
      const punta = base.clone().add(V(0.04, 0.0, lado * (tipoDir === "led" ? 0.045 : 0.06)));
      if (!specs.carenado) {
        tubo(base, punta, 0.006, M.oscuro, decor, 8);
        lamparaDir(punta, lado, false);
      }
    }
    // Agarradera del parrillero (motos de calle y enduro)
    if (R.agarradera === "partida") {
      // Naked: dos agarraderas cortas a los lados del colín, bajo el asiento del parrillero
      for (const lado of [1, -1]) {
        const ag = new THREE.CatmullRomCurve3([V(P.x - 0.2, alturaAsiento - 0.03, lado * 0.12), V(P.x - 0.26, alturaAsiento - 0.0, lado * 0.15),
          V(xR + 0.2, alturaAsiento + 0.01, lado * 0.15), V(xR + 0.15, alturaAsiento - 0.02, lado * 0.12)]);
        malla(new THREE.TubeGeometry(ag, 16, 0.009, 8), M.oscuro, decor);
      }
    } else if (R.agarradera === "tubo" || R.agarradera === "aluminio") {
      // Por encima del colín y por fuera del asiento del parrillero (antes quedaba medio enterrada en el costado),
      // con dos soportes que bajan hasta el colín a cada lado.
      const y = alturaAsiento + 0.025;
      // (el asiento tiene bisel: la agarradera va un poco más afuera para no quedar escondida dentro de él)
      const agarradera = new THREE.CatmullRomCurve3([V(P.x - 0.14, y - 0.01, 0.18), V(xR + 0.16, y + 0.01, 0.15),
        V(xR + 0.03, y + 0.02, 0.09), V(xR + 0.03, y + 0.02, -0.09), V(xR + 0.16, y + 0.01, -0.15), V(P.x - 0.14, y - 0.01, -0.18)]);
      const matAg = R.agarradera === "aluminio" ? M.metal : M.chasis;
      malla(new THREE.TubeGeometry(agarradera, 60, 0.0095, 10), matAg, decor);
      for (const lado of [1, -1]) {
        for (const [x, zz] of [[P.x - 0.14, 0.18], [xR + 0.2, 0.15]]) {
          tubo(V(x, y - 0.012, lado * zz), V(x, alturaAsiento - 0.05, lado * (zz - 0.04)), 0.008, matAg, decor, 8);
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
    // En la scooter baja por detrás del escudo y sale por debajo (antes cruzaba por fuera, sobre la pintura)
    const curvaFreno = new THREE.CatmullRomCurve3(scooter ? [
      V(H.x - 0.04, H.y + altoManubrio, anchoManubrio - 0.1), V(H.x - 0.08, H.y - 0.04, 0.05),
      V(H.x - 0.06, Rf + 0.2, zBarra * 0.6), V(xF - 0.03, Rf + 0.12, zBarra + 0.03), V(xF - 0.05, Rf + 0.08, anchoF * 0.55 + 0.04),
    ] : [
      V(H.x - 0.04, H.y + altoManubrio, anchoManubrio - 0.1), V(H.x + 0.05, H.y - 0.05, zBarra + 0.03),
      V(xF - 0.02, Rf + 0.22, zBarra + 0.03), V(xF - 0.05, Rf + 0.1, anchoF * 0.55 + 0.04),
    ]);
    malla(new THREE.TubeGeometry(curvaFreno, 48, 0.0045, 8), M.oscuro, decor);
  }
  await ceder();
  // ----- Calapiés (posapiés) -----
  // Platina plana entre dos puntos (el soporte que sostiene el calapié al chasis)
  function platina(a, b, ancho, grosor, mat) {
    const dir = new THREE.Vector3().subVectors(b, a);
    const m = malla(new THREE.BoxGeometry(ancho, dir.length(), grosor), mat, decor);
    m.position.copy(a).add(b).multiplyScalar(0.5);
    m.quaternion.setFromUnitVectors(V(0, 1, 0), dir.normalize());
    return m;
  }
  // Calapié completo: platina desde el chasis, horquilla con perno (eje del pliegue, a lo largo de la moto),
  // vástago metálico y goma con estrías y tapa en la punta. "dentado" = calapié de aluminio con dientes (deportivas).
  function calapie(pivote, lado, largo, { ancla = null, r = 0.011, dentado = false, matPlatina = M.chasis } = {}) {
    if (ancla) platina(ancla, pivote.clone().add(V(0, 0.012, -lado * 0.012)), 0.034, 0.008, matPlatina);
    // Horquilla: dos orejas a cada lado del vástago y el perno que las atraviesa
    for (const dx of [-1, 1]) caja(0.006, 0.03, 0.024, matPlatina, pivote.clone().add(V(dx * (r + 0.004), 0.004, 0)), decor);
    const perno = disco(0.005, 2 * r + 0.022, M.cromo, pivote.clone().add(V(0, 0.006, 0)), decor, 10);
    perno.rotation.set(0, 0, Math.PI / 2);
    for (const dx of [-1, 1]) {
      const cabeza = disco(0.0075, 0.004, M.cromo, pivote.clone().add(V(dx * (r + 0.009), 0.006, 0)), decor, 6);
      cabeza.rotation.set(0, 0, Math.PI / 2);
    }
    const punta = pivote.clone().add(V(-0.004, -0.004, lado * largo)); // cae un poquito hacia atrás y abajo
    const tramo = (t) => pivote.clone().lerp(punta, t);
    tubo(pivote, tramo(0.3), r * 0.75, M.metal, decor, 12);
    if (dentado) {
      // Aluminio: cuerpo pulido con dientes arriba para que la bota no se resbale
      tubo(tramo(0.25), punta, r, M.metal, decor, 14);
      const n = Math.round(largo / 0.014);
      for (let i = 0; i < n; i++) {
        const t = 0.3 + (0.66 * (i + 0.5)) / n;
        caja(0.024, 0.006, 0.004, M.motor, tramo(t).add(V(0, r * 0.9, 0)), decor);
      }
      disco(r * 1.05, 0.004, M.oscuro, punta, decor, 14);
    } else {
      // Goma con estrías (anillos) y tapa redondeada en la punta
      tubo(tramo(0.28), punta, r, M.caucho, decor, 14);
      const n = Math.round(largo / 0.013);
      for (let i = 0; i < n; i++) disco(r + 0.0022, 0.0035, M.caucho, tramo(0.32 + (0.62 * (i + 0.5)) / n), decor, 14);
      const tapa = malla(new THREE.SphereGeometry(r, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), M.caucho, decor);
      tapa.position.copy(punta);
      tapa.rotation.x = lado * Math.PI / 2;
    }
  }

  if (!scooter) {
    const deportiva = tipo === "sport";
    for (const lado of [1, -1]) {
      // Conductor: platina que baja del chasis al pivote, debajo del pivote de la tijera
      // (RC: estriberas retrasadas y altas, de deportiva de pista)
      const pie = R.estriberasAtras ? V(P.x - 0.03, P.y + 0.03, lado * 0.13) : V(P.x + 0.08, P.y - 0.04, lado * 0.13);
      calapie(pie, lado, 0.085,
        { ancla: V(pie.x - 0.06, pie.y + 0.11, lado * 0.1), r: 0.012, dentado: deportiva, matPlatina: deportiva ? M.metal : M.chasis });
      // Protector de talón (motos de 150 cc o más): lámina delante del pie, junto a la platina
      if (specs.cilindraje >= 150) {
        caja(0.07, 0.05, 0.004, deportiva ? M.metal : M.oscuro, V(P.x + 0.11, P.y + 0.01, lado * 0.118), decor, 0.5);
      }
      // Parrillero: cuelga del subchasis por fuera y por encima del basculante (no se mueve con la suspensión)
      // (la platina sube hasta lo primero que encuentre arriba —tapa lateral, colín o subchasis— para no quedar suelta)
      const anclaPar = V(P.x - 0.07, P.y + 0.19, lado * 0.115);
      const yArriba = techoSobre(anclaPar.x, anclaPar.y - 0.02, anclaPar.z, 0.3, [M.chasis]);
      if (yArriba != null) anclaPar.y = yArriba + 0.008;
      calapie(V(P.x - 0.16, P.y + 0.075, lado * 0.145), lado, 0.075, { ancla: anclaPar, r: 0.0105 });
    }
  } else {
    // Scooter: el conductor apoya en el piso; el parrillero tiene calapiés plegables que salen del costado del carenado
    // En la genérica va más arriba, sobre el costado rojo del carenado (abajo quedaba suelto junto al piso)
    const xPar = esMaxi ? -0.2 : -0.17, yPar = esMaxi ? 0.4 : 0.455, zPar = esMaxi ? 0.232 : 0.196;
    for (const lado of [1, -1]) {
      caja(0.06, 0.04, 0.012, M.oscuro, V(xPar, yPar + 0.006, lado * (zPar - 0.012)), decor); // base atornillada al carenado
      calapie(V(xPar, yPar, lado * zPar), lado, 0.065, { r: 0.0105, matPlatina: M.oscuro });
    }
  }
  // ----- Personalidad por tipo de moto -----
  if (!scooter) {
    const Em = V(P.x + 0.2 * s + 0.04, P.y + 0.05); // centro del motor (el mismo de la sección "Motor")
    if ((fam === "clasica" && R.parrilla) || fam === "semi") {
      // Defensa cromada delante del motor (muy común en las motos de trabajo en Colombia)
      // Nace y termina en el tubo bajante del chasis (antes la punta de abajo quedaba suelta al aire junto a la rueda)
      for (const lado of [1, -1]) {
        const A = tipo === "semi" ? V(H.x, H.y - 0.05, 0) : V(H.x, H.y - 0.12, lado * 0.035);
        const B = tipo === "semi" ? V(P.x + 0.25, P.y + 0.08, 0) : V(P.x + 0.37, P.y, lado * 0.07);
        const enBajante = (y) => A.clone().lerp(B, THREE.MathUtils.clamp((y - A.y) / (B.y - A.y), 0, 1));
        const arriba = enBajante(Em.y + 0.24), abajo = enBajante(Em.y - 0.04);
        const defensa = new THREE.CatmullRomCurve3([
          arriba, V(Em.x + 0.32 * s, Em.y + 0.15, lado * 0.22),
          V(Em.x + 0.33 * s, Em.y - 0.01, lado * 0.27), V(Em.x + 0.24 * s, Em.y - 0.09, lado * 0.17), abajo,
        ]);
        malla(new THREE.TubeGeometry(defensa, 36, 0.014, 12), M.cromo, decor);
        // Abrazaderas que la sujetan al chasis
        for (const p of [arriba, abajo]) caja(0.03, 0.03, 0.03, M.chasis, p, decor);
      }
    }
    if (naked) {
      // Chasis perimetral a la vista: dos largueros plateados (naranja en la Duke) que bajan de la tijera al pivote
      const chasisVisto = R.chasisColor ? new THREE.MeshStandardMaterial({ color: R.chasisColor, roughness: 0.35, metalness: 0.3 }) : M.metal;
      if (R.chasisColor) {
        // Duke: chasis multitubular (trellis) a la vista, con diagonales entre los largueros
        for (const lado of [1, -1]) {
          const z = lado * 0.12;
          for (const [a, b] of [[V(H.x - 0.16, H.y - 0.13, z), V(P.x + 0.32, P.y + 0.16, z)], [V(P.x + 0.32, P.y + 0.16, z), V(P.x + 0.2, P.y + 0.2, z)],
            [V(P.x + 0.32, P.y + 0.16, z), V(P.x + 0.06, P.y + 0.1, z)], [V(P.x + 0.06, P.y + 0.1, z), V(xR + 0.2, alturaAsiento - 0.09, z * 0.5)]]) {
            tubo(a, b, 0.011, chasisVisto, decor, 8);
          }
        }
      }
      for (const lado of [1, -1]) {
        const larguero = new THREE.CatmullRomCurve3([V(H.x - 0.03, H.y - 0.06, lado * 0.05), V(H.x - 0.16, H.y - 0.13, lado * 0.115),
          V(P.x + 0.2, P.y + 0.2, lado * 0.125), V(P.x + 0.04, P.y + 0.08, lado * 0.11), V(P.x, P.y, lado * 0.09)]);
        malla(new THREE.TubeGeometry(larguero, 40, 0.017, 10), chasisVisto, decor);
      }
      // Naked: quilla corta bajo el motor, en negro
      panelAhusado([[Em.x - 0.1 * s, Em.y - 0.12 * s], [Em.x + 0.2 * s, Em.y - 0.11 * s], [Em.x + 0.24 * s, Em.y - 0.03 * s],
        [Em.x + 0.16 * s, Em.y - 0.16 * s], [Em.x - 0.06 * s, Em.y - 0.17 * s]], 0.24, M.oscuro, (x) => (x > Em.x + 0.15 * s ? 0.75 : 1), 0.015);
    }
    if (R.parrilla) {
      // Parrilla metálica trasera detrás del asiento (motos de trabajo); pequeña en las semiautomáticas
      const pequena = R.parrilla === "pequena";
      const x0 = pequena ? P.x + 0.16 - (R.semi?.asientoLargo ?? 0.6) + 0.01 : xR + 0.06;
      const yP = alturaAsiento + (pequena ? 0.035 : 0.06), x1 = x0 - (pequena ? 0.13 : 0.21), zP = pequena ? 0.07 : 0.085;
      const marcoP = new THREE.CatmullRomCurve3([V(x0, yP, zP), V(x1 + 0.02, yP, zP), V(x1, yP, zP * 0.6), V(x1, yP, -zP * 0.6),
        V(x1 + 0.02, yP, -zP), V(x0, yP, -zP)]);
      malla(new THREE.TubeGeometry(marcoP, 40, 0.008, 8), M.chasis, decor);
      for (let k = 1; k <= 3; k++) tubo(V(x0 + (x1 - x0) * k / 4, yP, zP), V(x0 + (x1 - x0) * k / 4, yP, -zP), 0.006, M.chasis, decor, 6);
      for (const lado of [1, -1]) {
        tubo(V(x0, yP, lado * zP), V(x0 + 0.02, alturaAsiento - 0.02, lado * (zP - 0.01)), 0.008, M.chasis, decor, 8);
        tubo(V(x1 + 0.06, yP, lado * zP), V(x1 + 0.08, alturaAsiento - 0.03, lado * (zP - 0.02)), 0.008, M.chasis, decor, 8);
      }
    }
    if ((tipo === "calle" && specs.cilindraje <= 125) || tipo === "semi" || tipo === "enduro") {
      // Pedal de arranque (patada) al lado derecho, detrás del motor
      const ejeP = V(Em.x - 0.1 * s, Em.y + 0.02, -0.12 * s - 0.03);
      tubo(ejeP, V(Em.x - 0.22 * s, Em.y - 0.06, -0.12 * s - 0.04), 0.008, M.cromo, decor, 8);
      tubo(V(Em.x - 0.22 * s, Em.y - 0.06, -0.12 * s - 0.04), V(Em.x - 0.22 * s, Em.y - 0.06, -0.12 * s - 0.09), 0.009, M.caucho, decor, 8);
      disco(0.014, 0.02, M.oscuro, ejeP, decor, 12).rotation.set(0, 0, 0);
    }
    if (tipo === "enduro") {
      // Enduro: protector de cárter (cubre el motor por debajo); los cubremanos van más abajo, con los accesorios
      panelAhusado([[Em.x - 0.12 * s, Em.y - 0.15 * s], [Em.x + 0.18 * s, Em.y - 0.15 * s], [Em.x + 0.26 * s, Em.y - 0.04 * s],
        [Em.x + 0.24 * s, Em.y - 0.02 * s], [Em.x + 0.15 * s, Em.y - 0.12 * s], [Em.x - 0.1 * s, Em.y - 0.12 * s]], 0.2, M.metal,
      () => 1, 0.01);
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
  // (sube hasta tocar la cola o el colín de verdad: antes, con colines altos, los tubos quedaban colgando en el aire)
  const techoCola = techoSobre(arribaSoporte.x, yPlaca + 0.06, 0, 0.6);
  if (techoCola) arribaSoporte.y = techoCola + 0.01;
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
  caja(0.02, 0.014, 0.05, M.oscuro, V(xPlaca + 0.014, yPlaca + 0.054, 0), decor).rotation.z = inclinacion;
  {
    // (NMAX y Aerox: bombillos redondos en vástagos cortos junto a la placa, como en las fotos)
    const tipoTras = esMaxi ? "redondas" : tipoDir;
    for (const lado of [1, -1]) {
      const zD = tipoTras === "led" ? 0.13 : esMaxi ? 0.14 : 0.15;
      tubo(V(xPlaca + 0.03, yPlaca + 0.06, lado * 0.08), V(xPlaca + 0.02, yPlaca + 0.06, lado * zD), 0.006, M.oscuro, decor, 6);
      lamparaDir(V(xPlaca + 0.018, yPlaca + 0.06, lado * (zD + 0.012)), lado, true, tipoTras);
    }
    // Stop sobre el guardabarros, encima de la placa (clásicas y NKD): carcasa y mica mirando atrás; redondo en la GN
    if (R.stop === "guardabarros" || R.stop === "redondo") {
      const pS = V(xPlaca + 0.03, yPlaca + 0.105, 0);
      if (R.stop === "redondo") {
        disco(0.045, 0.04, M.cromo, pS.clone().add(V(0.012, 0, 0)), decor, 20).rotation.set(0, 0, Math.PI / 2);
        disco(0.04, 0.014, M.stop, pS.clone().add(V(-0.012, 0, 0)), decor, 20).rotation.set(0, 0, Math.PI / 2);
      } else {
        caja(0.05, 0.05, 0.12, M.oscuro, pS.clone().add(V(0.012, 0, 0)), decor);
        caja(0.014, 0.04, 0.11, M.stop, pS.clone().add(V(-0.018, 0, 0)), decor);
      }
      tubo(pS.clone().add(V(0.03, 0, 0)), V(arribaSoporte.x + 0.02, arribaSoporte.y - 0.01, 0), 0.01, M.oscuro, decor, 8); // soporte a la cola
    }
  }

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
  // Rendimiento: las piezas decorativas sueltas que comparten material (tornillos, soportes, cables, aletas…)
  // se unen en una sola malla por material. Menos mallas = menos llamadas de dibujo = anda mejor en celulares.
  // No se tocan las piezas con datos propios (carrocería para calcas, franjas, piezas internas, etc.).
  vestirLuces();
  const anclas = anclasLuces();
  medir("unir", () => unirDecorado(decor));
  // Lo mismo dentro de cada pieza de mantenimiento: la pieza se sigue reconociendo por su grupo (al tocarla,
  // al colorear su estado), así que unir sus mallas no cambia nada para el usuario.
  medir("unir", () => { for (const g of Object.values(piezas)) unirDecorado(g); });

  // Centra la moto en el origen para que gire sobre sí misma.
  const caja3 = new THREE.Box3().setFromObject(raiz);
  raiz.position.x = -(caja3.min.x + caja3.max.x) / 2;
  // Ejes para girar las ruedas en la animación de la portada: el rin, la llanta y los radios cuelgan de un pivote en el centro
  const ruedas = [[piezas.llanta_del, centroDel, Rf], [piezas.llanta_tras, centroTras, Rr]].map(([g, centro, R]) => {
    const pivote = new THREE.Group();
    pivote.position.copy(centro);
    g.add(pivote);
    for (const hijo of [...g.children]) if (hijo !== pivote) pivote.attach(hijo);
    g.userData.pivoteRueda = pivote;
    return { pivote, R };
  });
  // ----- Dos tonos: el colín y los costados traseros usan el segundo color de carrocería -----
  raiz.traverse((o) => {
    if (o.isMesh && o.material === M.pintura && o.userData.zonas?.includes("cola")) o.material = M.pintura2;
  });

  // ----- Accesorios (escondidos hasta que la persona los active al personalizar) -----
  // Se agregan después de centrar la moto para que, aun escondidos, no corran el centro de giro.
  const accesorios = {};
  // Visores y parabrisas de fábrica: con el parabrisas alto puesto se esconden (si no, quedan dos)
  const visoresFabrica = [];
  raiz.traverse((o) => {
    // (sin el visor del nivel de aceite, que es vidrio pero va dentro de su pieza)
    if (o.isMesh && (o.userData.visorFabrica || (o.material === M.vidrio && o.parent === decor))) visoresFabrica.push(o);
  });
  function accesorio(id, armar) {
    const g = new THREE.Group();
    g.userData.accesorio = id;
    g.visible = false;
    raiz.add(g);
    armar(g);
    unirDecorado(g);
    accesorios[id] = g;
  }
  // Anclas medidas sobre la moto ya armada (sirven igual para todas las carrocerías, sin números por modelo):
  // dónde termina el asiento y qué tan alto queda lo que hay detrás (colín, parrilla, agarraderas).
  raiz.updateMatrixWorld(true);
  const aLocal = new THREE.Matrix4().copy(raiz.matrixWorld).invert();
  function recorrerVertices(filtro, fn) {
    const v = new THREE.Vector3();
    raiz.traverseVisible((o) => {
      if (!o.isMesh || o.isInstancedMesh || !filtro(o)) return;
      const pos = o.geometry.attributes.position;
      const m = new THREE.Matrix4().multiplyMatrices(aLocal, o.matrixWorld);
      for (let i = 0; i < pos.count; i++) fn(v.fromBufferAttribute(pos, i).applyMatrix4(m));
    });
  }
  function anclaColin() {
    let finAsiento = Infinity;
    recorrerVertices((o) => o.material === M.asiento, (v) => { if (v.x < finAsiento) finAsiento = v.x; });
    if (!isFinite(finAsiento)) finAsiento = xR + 0.1; // (sin asiento reconocible: sobre el eje trasero)
    return finAsiento;
  }
  function techoEntre(x0, x1, medioAncho) {
    let alto = -Infinity;
    recorrerVertices((o) => o.material !== M.caucho, (v) => {
      if (v.x >= x0 && v.x <= x1 && Math.abs(v.z) <= medioAncho && v.y > 0.35 && v.y > alto) alto = v.y;
    });
    return isFinite(alto) ? alto : alturaAsiento;
  }
  accesorio("baul", (g) => {
    // Baúl trasero detrás del asiento del pasajero, apoyado sobre lo más alto del colín o la parrilla, con base
    // metálica y reflectivo rojo atrás. Más pequeño en las motos de 125 cc o menos.
    const k = specs.cilindraje <= 125 ? 0.85 : specs.cilindraje >= 250 ? 1.05 : 0.95;
    const frente = anclaColin() - 0.01;           // justo detrás de la punta del asiento (el bisel apenas la roza)
    const cx = frente - 0.17 * k;
    const b = techoEntre(cx - 0.18 * k, frente, 0.17) + 0.016;
    const P = (dx, dy) => [cx + dx * k, b + dy * k];
    perfil([P(0.15, 0), P(0.17, 0.15), P(0.11, 0.24), P(-0.12, 0.25), P(-0.18, 0.14), P(-0.16, 0)],
      0.36 * k, M.oscuro, g, 0, 0.022, true);
    caja(0.35 * k, 0.007, 0.41 * k, M.chasis, V(cx - 0.01 * k, b + 0.165 * k, 0), g); // junta de la tapa
    const refl = M.stop; // (reflectivo rojo: el mismo material del stop)
    caja(0.006, 0.03 * k, 0.22 * k, refl, V(cx - 0.197 * k, b + 0.12 * k, 0), g, 0.25);
    // Base de montaje (placa) y dos soportes que bajan hasta el colín
    caja(0.28 * k, 0.012, 0.2 * k, M.chasis, V(cx, b - 0.008, 0), g);
    for (const lado of [1, -1]) tubo(V(cx + 0.08 * k, b - 0.012, lado * 0.07 * k), V(cx + 0.1 * k, b - 0.05, lado * 0.06 * k), 0.006, M.chasis, g, 8);
  });
  // Cubremanos: un arco delante de cada puño (envuelve también la manigueta y el clutch), del largo del puño,
  // sujeto a la punta del manubrio y cerca de la abrazadera. Sigue la línea del manubrio de cada lado.
  function cubremanos(g, mat) {
    for (const lado of [1, -1]) {
      const punta = V(M1.x, M1.y, lado * anchoManubrio); // extremo del manubrio
      const cx = punta.x + 0.012, cy = punta.y + 0.004;
      // (arco ovalado: llega por delante hasta las palancas pero es bajo, como los cubremanos reales)
      const arco = (r, a) => [cx + r * Math.cos(a), cy + r * 0.66 * Math.sin(a)];
      const angulos = [];
      for (let a = -55; a <= 70; a += 9) angulos.push((a * Math.PI) / 180);
      const contorno = [...angulos.map((a) => arco(0.09, a)), ...angulos.slice().reverse().map((a) => arco(0.082, a))];
      perfil(contorno, 0.115, mat, g, lado * (anchoManubrio - 0.052), 0.004, false);
      // Sujeción en la punta y junto a la abrazadera
      const abajo = (r, z) => { const [x, y] = arco(r, (-25 * Math.PI) / 180); return V(x, y, z); };
      tubo(V(punta.x, punta.y, lado * (anchoManubrio + 0.012)), abajo(0.083, lado * (anchoManubrio + 0.004)), 0.006, M.oscuro, g, 8);
      tubo(V(punta.x + 0.01, punta.y, lado * (anchoManubrio - 0.115)), abajo(0.08, lado * (anchoManubrio - 0.106)), 0.005, M.oscuro, g, 8);
    }
  }
  if (tipo !== "enduro") accesorio("cubremanos", (g) => cubremanos(g, M.oscuro));
  if (tipo === "enduro") cubremanos(decor, pintura); // (de fábrica en las enduro, del color de la moto)
  accesorio("parabrisas", (g) => {
    // Parabrisas alto ahumado sobre el faro (o sobre el escudo en las scooter)
    const bx = H.x + (scooter ? 0.1 : 0.12), by = H.y + (scooter ? 0.08 : 0.0);
    perfil([[bx + 0.02, by], [bx - 0.05, by + 0.3], [bx - 0.11, by + 0.33], [bx - 0.07, by + 0.02]], scooter ? 0.34 : 0.3, M.vidrio, g, 0, 0.008, true);
    for (const lado of [1, -1]) tubo(V(bx - 0.08, by + 0.03, lado * 0.1), V(H.x - 0.03, H.y - 0.02, lado * 0.06), 0.006, M.oscuro, g, 8);
  });
  // (en las scooter quedaban metidas dentro del escudo: no se ofrecen)
  if (!scooter) accesorio("exploradoras", (g) => {
    // Dos faros auxiliares redondos con su soporte
    const y = scooter ? H.y - 0.33 : H.y - 0.22, x = scooter ? xF + 0.0 : H.x + 0.07, z = scooter ? 0.2 : 0.16;
    for (const lado of [1, -1]) {
      tubo(V(x - 0.06, y + 0.02, lado * (z - 0.07)), V(x - 0.005, y, lado * z), 0.006, M.oscuro, g, 8);
      disco(0.03, 0.045, M.oscuro, V(x, y, lado * z), g, 20).rotation.set(0, 0, Math.PI / 2);
      disco(0.024, 0.006, M.luz, V(x + 0.024, y, lado * z), g, 20).rotation.set(0, 0, Math.PI / 2);
      disco(0.032, 0.006, M.cromo, V(x + 0.02, y, lado * z), g, 20).rotation.set(0, 0, Math.PI / 2);
    }
  });
  if (!scooter) {
    accesorio("sliders", (g) => {
      // Sliders anticaída a los lados del motor
      for (const lado of [1, -1]) {
        tubo(V(P.x + 0.3, P.y + 0.2, lado * 0.1), V(P.x + 0.3, P.y + 0.2, lado * 0.2), 0.007, M.metal, g, 8);
        disco(0.022, 0.05, M.oscuro, V(P.x + 0.3, P.y + 0.2, lado * 0.2), g, 16);
        disco(0.012, 0.052, M.metal, V(P.x + 0.3, P.y + 0.2, lado * 0.2), g, 6);
      }
    });
  }

  if (escapeInfo) {
    accesorio("escape", (g) => {
      // Escape deportivo corto y levantado, de cuerpo hexagonal en titanio con punta oscura
      const { finCodo, iniSil } = escapeInfo;
      const ini = iniSil.clone().add(V(0.03, 0.01, 0)), fin = ini.clone().add(V(-0.26, 0.11, -0.01));
      tubo(finCodo, ini, 0.022, M.cromo, g);
      const titanio = new THREE.MeshPhysicalMaterial({ color: 0x8c96a6, metalness: 1, roughness: 0.28, iridescence: 0.5, iridescenceIOR: 1.5 });
      tubo(ini, fin, 0.058, titanio, g, 6).userData.conservar = true;
      const dir = fin.clone().sub(ini).normalize();
      tubo(fin, fin.clone().add(dir.clone().multiplyScalar(0.05)), 0.06, M.oscuro, g, 20);
      tubo(fin.clone().add(dir.clone().multiplyScalar(0.05)), fin.clone().add(dir.clone().multiplyScalar(0.065)), 0.032, M.cromo, g, 16);
      // Abrazadera al chasis
      const medio = ini.clone().lerp(fin, 0.5);
      tubo(medio, medio.clone().add(V(0.04, 0.09, 0.05)), 0.006, M.oscuro, g, 8);
    });
  }
  if (!scooter && tipo !== "enduro") {
    accesorio("protector", (g) => {
      // Protector de cárter en aluminio bajo el motor
      const Ex = P.x + 0.2 * s + 0.04, Ey = P.y + 0.05;
      const placa = panelAhusado([[Ex - 0.12 * s, Ey - 0.15 * s], [Ex + 0.18 * s, Ey - 0.15 * s], [Ex + 0.26 * s, Ey - 0.04 * s],
        [Ex + 0.24 * s, Ey - 0.02 * s], [Ex + 0.15 * s, Ey - 0.12 * s], [Ex - 0.1 * s, Ey - 0.12 * s]], 0.2, M.metal, () => 1, 0.01);
      g.attach(placa);
    });
  }
  accesorio("led", (g) => {
    // Luz LED bajo la moto: dos tiras que brillan y tiñen el piso con el color elegido (más vistosa de noche)
    const ledMat = new THREE.MeshStandardMaterial({ color: 0x22d3ee, emissive: 0x22d3ee, emissiveIntensity: 2.2 });
    const xa = P.x + 0.45, xb = P.x - 0.05, y = Math.max(0.12, P.y - 0.06);
    for (const lado of [1, -1]) caja(xa - xb, 0.008, 0.008, ledMat, V((xa + xb) / 2, y, lado * 0.08), g).userData.conservar = true;
    // La luz va siempre en la escena (apagada si no hay LED): si apareciera y desapareciera con el accesorio,
    // cambiaría el número de luces y se recompilarían los sombreadores de toda la moto.
    const resplandor = new THREE.PointLight(0x22d3ee, 0, 1.1, 1.5);
    resplandor.position.set((xa + xb) / 2, y - 0.03, 0);
    raiz.add(resplandor);
    g.userData.led = { material: ledMat, luz: resplandor };
  });

  return { raiz, piezas, M, ruedas, pata, placa, accesorios, visoresFabrica, espejos, escapeFabrica, anclas, rinFabrica, rinColor: R.rinColor ?? null };
}
