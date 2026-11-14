// Construcción procedural de la moto a partir de su ficha técnica.
import * as THREE from "three";
import { mergeGeometries } from "three/addons/utils/BufferGeometryUtils.js";
import { V, medir, CALIDAD, seg, ceder } from "./comun.js";
import { cachePaneles } from "./cache.js";
import { materialLetrasLlanta } from "./texturas.js";
import { cascoCirculos, subdividir, unirVertices, unirDecorado } from "./geometria.js";

// =====================================================================
// Construcción procedural
// =====================================================================
export async function construirMoto(specs, colorPintura, linea = "") {
  const esNmax = /nmax/i.test(linea);
  // Rasgos propios de modelos populares en Medellín (sobre la base genérica de su tipo)
  const esBoxer = /boxer/i.test(linea);
  const esXtz = /xtz/i.test(linea);
  const esTt = /\btt\b/i.test(linea);
  const esGixxer = /gixxer/i.test(linea);
  const esNs = /pulsar\s*ns/i.test(linea);
  let escapeFabrica = null, escapeInfo = null; // silenciador de fábrica (se cambia por el deportivo)
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

  // Segundo tono de la carrocería (colín y costados traseros): igual al principal hasta que la persona elija otro
  M.pintura2 = M.pintura.clone();
  // Metal por ambas caras para las medias cañas (protectores de escape): por una sola cara se veían cortadas
  M.metalDoble = M.metal.clone();
  M.metalDoble.side = THREE.DoubleSide;
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
      if (!closed) geo = medir("tapas", () => conTapas(geo));
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
  function perfil(puntos, ancho, mat, padre, z = 0, bisel = 0.014, suave = false, curvas = 28, biselSeg = 6, lisar = true) {
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
    const m = malla(new THREE.SphereGeometry(1, seg(28), seg(18)), mat, padre);
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
    // Letras en el costado de la llanta (marca y medida), dibujadas en círculo sobre un anillo transparente
    const medida = `${Math.round(ancho * 1000 / 5) * 5}/${tipo === "scooter" ? 90 : 80}-${rin}`;
    const matLetras = materialLetrasLlanta(medida, (rinR + h * 0.5) / (rinR + h * 0.8), (h * 0.3) / (rinR + h * 0.8));
    for (const lado of [1, -1]) {
      const anillo = malla(new THREE.RingGeometry(rinR + h * 0.22, rinR + h * 0.8, seg(64)), matLetras, g);
      anillo.position.set(x, R, lado * ancho * 0.535);
      if (lado < 0) anillo.rotation.y = Math.PI;
      anillo.castShadow = false;
      anillo.userData.conservar = true; // lleva textura: no se une con otras piezas
    }
    g.add(labrado);
    disco(0.045, ancho * 0.9, M.metal, centro, g, 16);
    // Tres estilos de rin; solo se arma el que se ve (el de fábrica o el elegido). Los otros se arman la primera vez
    // que la persona los elige al personalizar: así el armado inicial hace un tercio del trabajo de los rines.
    g.userData.aro = aro;
    const armarRin = {
      radios(v) {
        instancias(cil(0.0035, 1, 5), M.cromo, Array.from({ length: 18 }, (_, i) => {
          const a = (i / 18) * Math.PI * 2;
          const lado = i % 2 ? 1 : -1;
          return enTubo(V(x, R, lado * ancho * 0.3), V(x + Math.cos(a) * rinR, R + Math.sin(a) * rinR, lado * 0.01));
        }), v);
      },
      aleacion(v) {
        // Maza robusta y 5 radios dobles curvos (como los rines de fábrica)
        disco(rinR * 0.3, ancho * 0.72, M.rin, centro, v, 28);
        for (let i = 0; i < 5; i++) {
          const a = (i / 5) * Math.PI * 2 + 0.3;
          for (const d of [-1, 1]) {
            const curva = new THREE.QuadraticBezierCurve3(
              V(x + Math.cos(a) * rinR * 0.26, R + Math.sin(a) * rinR * 0.26, 0),
              V(x + Math.cos(a + d * 0.16) * rinR * 0.62, R + Math.sin(a + d * 0.16) * rinR * 0.62, 0),
              V(x + Math.cos(a + d * 0.24) * rinR * 0.96, R + Math.sin(a + d * 0.24) * rinR * 0.96, 0),
            );
            const radio = malla(new THREE.TubeGeometry(curva, 14, 0.009, 8), M.rin, v);
            radio.scale.z = 1.8; // radio ovalado: más ancho que grueso
          }
        }
        tuercas(v);
      },
      estrella(v) {
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
    g.userData.armarRin(radios ? "radios" : "aleacion");
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
    const medio = eje.clone().lerp(pipa, 0.55);
    const rBotella = tipo === "enduro" ? 0.028 : 0.022;
    const dirBarra = new THREE.Vector3().subVectors(pipa, eje).normalize();
    tubo(eje.clone().add(dirBarra.clone().multiplyScalar(-0.03)), medio, rBotella, tipo === "sport" ? M.oscuro : M.metal, susDel);
    tubo(medio, pipa, tipo === "enduro" ? 0.022 : 0.017, M.cromo, susDel);
    // Retén con guardapolvo, tapa de la barra y punta donde se sujeta el eje
    tubo(medio, medio.clone().add(dirBarra.clone().multiplyScalar(0.025)), rBotella * 1.08, M.caucho, susDel, 20);
    if (esBoxer) {
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
  const altoManubrio = tipo === "sport" ? (specs.carenado ? 0.11 : 0.02) : tipo === "enduro" ? 0.12 : 0.08;
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
        const fin = V(H.x - 0.05, H.y + altoManubrio, lado * (anchoManubrio + 0.07));
        const brazo = fin.clone().add(V(-0.01, -0.02, lado * 0.05));
        tubo(fin, brazo, 0.007, M.oscuro, g);
        elipsoide(0.012, 0.034, 0.05, M.oscuro, brazo.clone().add(V(0, 0, lado * 0.03)), g).rotation.y = lado * 0.3;
        elipsoide(0.004, 0.029, 0.044, M.espejo, brazo.clone().add(V(-0.009, 0, lado * 0.03)), g).rotation.y = lado * 0.3;
      }
    }
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
      const drl = caja(0.01, 0.012, esNs ? 0.07 : 0.05, M.luz, V(fx + 0.07, fy + 0.04, lado * (esNs ? 0.05 : 0.045)), decor);
      drl.rotation.set(lado * 0.5, 0, -0.5);
      if (esNs) {
        // Pulsar NS: "ojos de lobo" (dos luces diurnas en ángulo a los lados del faro) con su marco negro
        const ojo = caja(0.012, 0.016, 0.06, M.luz, V(fx + 0.06, fy - 0.045, lado * 0.06), decor);
        ojo.rotation.set(-lado * 0.6, 0, -0.35);
        caja(0.008, 0.026, 0.07, M.oscuro, V(fx + 0.054, fy - 0.045, lado * 0.06), decor).rotation.set(-lado * 0.6, 0, -0.35);
      }
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
    disco(0.012, 0.014, M.vidrio, V(E.x + 0.1 * s, E.y - 0.07 * s, -0.13 * s), aceite, 16); // visor del nivel de aceite
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

  await ceder();
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
    if (esNs) {
      // Pulsar NS: silenciador bajo el motor (underbelly) en vez del lateral largo. Antes era un bloque oscuro bajo un
      // motor oscuro y parecía que no tuviera mofle: ahora el cuerpo es de acero con protector térmico perforado por
      // el lado derecho, el codo cromado llega a la vista y las dos puntas cromadas asoman delante de la llanta trasera.
      const Ez = V(P.x + 0.2 * s + 0.04, P.y + 0.05);
      // (más abajo que el motor y corrido hacia la derecha: centrado quedaba escondido detrás de la tapa del motor)
      const bajo = 0.045, zSil = -0.045;
      const contornoSil = [[Ez.x - 0.16, Ez.y - 0.13 - bajo], [Ez.x + 0.1, Ez.y - 0.15 - bajo], [Ez.x + 0.14, Ez.y - 0.11 - bajo],
        [Ez.x + 0.06, Ez.y - 0.07 - bajo], [Ez.x - 0.14, Ez.y - 0.06 - bajo]];
      const acero = new THREE.MeshPhysicalMaterial({ color: 0x9aa1a6, metalness: 0.85, roughness: 0.32, clearcoat: 0.4 });
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
      // Dos puntas grandes y cromadas, una sobre otra, que salen hacia atrás y un poco hacia afuera
      for (const dy of [0.024, -0.02]) {
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
    if (!esNs) {
    tubo(salida, finCodo, 0.02, M.cromo, decor);
    const largo = tipo === "sport" ? 0.32 : 0.42;
    const finSil = tipo === "enduro" ? V(xR + 0.05, alturaAsiento - 0.08, -0.15) : V(xR + 0.18, Rr + 0.14, -0.15);
    const iniSil = finCodo.clone().lerp(finSil, 1 - largo / finCodo.distanceTo(finSil));
    const rSil = tipo === "sport" ? 0.055 : 0.045;
    // El silenciador de fábrica va en su propio grupo: se esconde si la persona elige el escape deportivo
    escapeFabrica = new THREE.Group();
    raiz.add(escapeFabrica);
    escapeInfo = { finCodo, iniSil, finSil, rSil };
    tubo(iniSil, finSil, rSil, M.oscuro, escapeFabrica, 24);
    tubo(finCodo, iniSil, 0.022, M.cromo, decor);
    // Punta cromada y protector térmico perforado
    const dirSil = new THREE.Vector3().subVectors(finSil, iniSil).normalize();
    tubo(finSil, finSil.clone().add(dirSil.clone().multiplyScalar(0.035)), rSil * 0.55, M.cromo, escapeFabrica, 20);
    const protectorSil = malla(new THREE.CylinderGeometry(rSil + 0.006, rSil + 0.006, iniSil.distanceTo(finSil) * 0.55, 24, 1, true, 0, Math.PI * 0.9), M.metalDoble, escapeFabrica);
    protectorSil.position.copy(iniSil.clone().lerp(finSil, 0.45));
    protectorSil.quaternion.setFromUnitVectors(V(0, 1, 0), dirSil);
    protectorSil.rotateY(Math.PI * 0.55);
    }
  }

  // ----- Carrocería específica: Yamaha NMAX (maxi-scooter) -----
  // Paneles curvos que se angostan hacia la nariz y la cola, pintura en dos tonos y detalles propios del modelo.
  function panelAhusado(puntos, ancho, mat, ahusar, bisel = 0.045, deformar = null) {
    // Clave del panel: su contorno, medidas y el código de sus funciones de forma
    const clave = `panel|${claveContorno(puntos)}|${ancho}|${bisel}|${ahusar}|${deformar || ""}`;
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
    geo = medir("subdividir", () => subdividir(unirVertices(geo), CALIDAD.subdividir, 4));
    const pos = geo.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      pos.setZ(i, pos.getZ(i) * ahusar(pos.getX(i), pos.getY(i)));
      if (deformar) {
        const [x, y, z] = deformar(pos.getX(i), pos.getY(i), pos.getZ(i));
        pos.setXYZ(i, x, y, z);
      }
    }
    pos.needsUpdate = true;
    medir("normales", () => { geo.computeVertexNormals(); suavizarNormales(geo, 3); });
    m.geometry.dispose();
    m.geometry = geo;
    aCache(clave, geo);
    return m;
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
      (x, y) => Math.max(0.65, 1 - (y - 0.95) * 1.4), 0.008).userData.visorFabrica = true;

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
    // Media caña: se dibuja por ambas caras para que, visto desde atrás o por dentro, no parezca cortado
    const protector = malla(new THREE.CylinderGeometry(0.056, 0.056, 0.28, 24, 1, true, 0, Math.PI),
      new THREE.MeshStandardMaterial({ color: 0xc4c9cc, roughness: 0.22, metalness: 0.95, side: THREE.DoubleSide }), decor);
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
    const xtz = modelo === "xtz";
    const aA = alturaAsiento;
    const tx = H.x - (xtz ? 0.22 : 0.2), ty = aA + (xtz ? 0.05 : 0.06);
    // Tanque: XTZ redondeado y bajo; TT más alto y cuadrado
    zona(panelAhusado(xtz
      ? [[tx + 0.2, ty - 0.04], [tx + 0.18, ty + 0.07], [tx + 0.06, ty + 0.1], [tx - 0.12, ty + 0.07], [tx - 0.2, ty - 0.02], [tx - 0.1, ty - 0.09], [tx + 0.12, ty - 0.09]]
      : [[tx + 0.19, ty - 0.05], [tx + 0.19, ty + 0.09], [tx + 0.08, ty + 0.12], [tx - 0.12, ty + 0.1], [tx - 0.19, ty - 0.01], [tx - 0.1, ty - 0.1], [tx + 0.12, ty - 0.1]],
    xtz ? 0.22 : 0.24, pintura, (x, y) => (x < tx - 0.04 ? Math.max(0.6, 1 - (tx - 0.04 - x) * 2) : 1) * (y < ty - 0.03 ? 0.75 : 1), 0.03), "tanque");
    disco(0.028, 0.012, M.oscuro, V(tx + 0.02, ty + (xtz ? 0.1 : 0.12) + 0.03, 0), decor, 20);
    disco(0.02, 0.016, M.cromo, V(tx + 0.02, ty + (xtz ? 0.1 : 0.12) + 0.036, 0), decor, 20);
    // Aletas laterales grandes, con un ribete oscuro abajo
    for (const lado of [1, -1]) {
      const aleta = xtz
        ? [[tx + 0.21, ty + 0.03], [H.x + 0.0, H.y - 0.08], [H.x - 0.03, H.y - 0.24], [tx + 0.02, ty - 0.2], [tx - 0.04, ty - 0.06]]
        : [[tx + 0.2, ty + 0.06], [H.x + 0.02, H.y - 0.05], [H.x - 0.01, H.y - 0.3], [tx + 0.0, ty - 0.24], [tx - 0.06, ty - 0.04]];
      zona(perfil(aleta, 0.016, pintura, decor, lado * 0.128, 0.006, true), "tanque");
      perfil(xtz
        ? [[H.x - 0.02, H.y - 0.18], [H.x - 0.04, H.y - 0.25], [tx + 0.04, ty - 0.19], [tx + 0.09, ty - 0.14]]
        : [[H.x - 0.0, H.y - 0.22], [H.x - 0.02, H.y - 0.31], [tx + 0.02, ty - 0.23], [tx + 0.08, ty - 0.17]],
      0.006, M.oscuro, decor, lado * 0.139, 0.003, true);
    }
    // Asiento largo y plano, de la parte de atrás del tanque hasta la cola
    panelAhusado([[tx - 0.08, ty + 0.02], [tx - 0.02, ty + 0.06], [xR + 0.04, aA + 0.05], [xR - 0.02, aA + 0.025],
      [xR + 0.0, aA - 0.02], [tx - 0.06, ty - 0.03]], 0.19, M.asiento, (x) => (x > tx - 0.12 ? 0.8 : 1), 0.025);
    // Tapas laterales tipo porta número (segundo tono) bajo el asiento
    zona(panelAhusado([[P.x + 0.05, aA - 0.02], [xR + 0.12, aA - 0.0], [xR + 0.2, aA - 0.11], [P.x + 0.0, aA - 0.17]],
      0.2, pintura, () => 1, 0.02), "lateral", "cola");
    // Colín largo y levantado (guardabarros trasero de enduro) con su stop en la punta
    zona(panelAhusado([[xR + 0.16, aA - 0.04], [xR - 0.04, aA + 0.03], [xR - (xtz ? 0.22 : 0.18), aA + (xtz ? 0.05 : 0.04)],
      [xR - (xtz ? 0.21 : 0.17), aA + 0.015], [xR + 0.0, aA - 0.04], [xR + 0.12, aA - 0.09]], 0.16, pintura,
    (x) => (x < xR ? Math.max(0.6, 1 - (xR - x) * 1.6) : 1), 0.015), "cola");
    const posStop = V(xR - (xtz ? 0.2 : 0.16), aA + 0.03, 0);
    caja(0.022, 0.034, 0.08, M.oscuro, posStop.clone().add(V(0.008, 0, 0)), decor, 0.25);
    caja(0.012, 0.026, 0.07, M.stop, posStop, decor, 0.25);
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
    // Patas que la atornillan al carenado (antes flotaba sobre el asiento)
    for (const lado of [1, -1]) {
      for (const x of [-0.26, xR + 0.1]) {
        tubo(V(x, alturaAsiento + 0.025, lado * 0.152), V(x + 0.01, alturaAsiento - 0.07, lado * 0.14), 0.008, M.chasis, decor, 8);
      }
    }
    // guardabarros delantero
    // (antes era un toro estirado a lo ancho: de canto se veía como una cuchilla afilada)
    const formaGuarda = new THREE.Shape();
    formaGuarda.absarc(0, 0, Rf + 0.04, Math.PI * 0.2, Math.PI * 0.75, false);
    formaGuarda.absarc(0, 0, Rf + 0.025, Math.PI * 0.75, Math.PI * 0.2, true);
    const geoGuarda = new THREE.ExtrudeGeometry(formaGuarda, { depth: 0.09, bevelEnabled: true, bevelSize: 0.006, bevelThickness: 0.008, bevelSegments: 3, curveSegments: 24 });
    geoGuarda.translate(0, 0, -0.045);
    const guarda = malla(geoGuarda, pintura, decor);
    guarda.position.set(xF, Rf, 0);
  } else if (tipo === "enduro" && (esXtz || esTt)) {
    carroceriaEnduro(esXtz ? "xtz" : "tt");
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
      // Contorno del tanque según el modelo: Boxer en gota redonda y larga, NS anguloso y alto adelante,
      // Gixxer musculoso con la nariz levantada; los demás, el genérico
      const contornoTanque = esBoxer ? [
        [tx + 0.24, ty - 0.04], [tx + 0.22, ty + 0.05], [tx + 0.12, ty + 0.1], [tx - 0.04, ty + 0.1],
        [tx - 0.18, ty + 0.05], [tx - 0.25, ty - 0.03], [tx - 0.12, ty - 0.09], [tx + 0.12, ty - 0.09],
      ] : esNs ? [
        [tx + 0.27, ty - 0.01], [tx + 0.24, ty + 0.1], [tx + 0.1, ty + 0.135], [tx - 0.06, ty + 0.11],
        [tx - 0.2, ty + 0.04], [tx - 0.26, ty - 0.04], [tx - 0.12, ty - 0.1], [tx + 0.14, ty - 0.1],
      ] : esGixxer ? [
        [tx + 0.26, ty - 0.05], [tx + 0.26, ty + 0.07], [tx + 0.15, ty + 0.125], [tx - 0.04, ty + 0.11],
        [tx - 0.2, ty + 0.05], [tx - 0.25, ty - 0.03], [tx - 0.12, ty - 0.1], [tx + 0.14, ty - 0.1],
      ] : [
        [tx + 0.25, ty - 0.03], [tx + 0.24, ty + altoT * 0.55], [tx + 0.15, ty + altoT], [tx - 0.02, ty + altoT * 0.95],
        [tx - 0.17, ty + altoT * 0.45], [tx - 0.25, ty - 0.04], [tx - 0.14, ty - altoT * 0.95], [tx + 0.12, ty - altoT * 0.9],
      ];
      // NS: arista marcada a lo largo del costado del tanque (como su tanque de líneas rectas)
      const aristaNs = esNs ? (x, y, z) => {
        const cerca = Math.max(0, 1 - Math.abs(y - (ty + 0.035)) / 0.05);
        return [x, y, z * (1 + 0.07 * cerca * cerca)];
      } : null;
      const tanque = panelAhusado(contornoTanque, esGixxer ? 0.35 : anchoT, pintura, (x, y) => {
        const atras = x < tx - 0.05 ? Math.max(0.55, 1 - (tx - 0.05 - x) * 2.2) : 1;
        const abajo = y < ty - 0.02 ? Math.max(0.6, 1 - (ty - 0.02 - y) * 3.2) : 1;
        const arriba = y > ty + altoT * 0.6 ? Math.max(0.7, 1 - (y - ty - altoT * 0.6) * 4) : 1;
        return atras * abajo * arriba;
      }, 0.035, aristaNs);
      zona(tanque, "tanque");
      if (esBoxer) {
        // Boxer: almohadillas de caucho para las rodillas a los lados del tanque y emblema cromado
        for (const lado of [1, -1]) {
          const zPad = (anchoT / 2 + 0.035) * Math.max(0.55, 1 - 0.07 * 2.2);
          const pad = elipsoide(0.065, 0.04, 0.008, M.caucho, V(tx - 0.12, ty - 0.01, lado * (zPad + 0.002)), decor);
          pad.rotation.y = lado * -0.18;
          caja(0.07, 0.012, 0.004, M.cromo, V(tx + 0.1, ty + 0.03, lado * (anchoT / 2 + 0.03)), decor, 0.1);
        }
      }
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
            ? [[tx + 0.05, ty - 0.01], [tx + 0.22, ty - 0.02], [H.x + 0.02, radY + 0.16], [H.x + 0.04, radY + 0.04],
              [radX + 0.02, radY - 0.1], [radX - 0.1, radY - 0.06], [tx + 0.06, ty - 0.1]]
            : [[tx + 0.26, ty + 0.03], [tx + 0.12, ty + 0.06], [tx + 0.03, ty - 0.04], [tx + 0.08, ty - 0.1], [tx + 0.21, ty - 0.08]];
          const aleta = perfil(contornoAleta, 0.014, pintura, decor, lado * (grande ? 0.168 : anchoT / 2 - 0.01), 0.006, grande);
          if (grande) {
            // Inclinada: el borde de arriba se mete hacia el tanque (queda escondido bajo él) y el de abajo abraza el radiador
            const pos = aleta.geometry.attributes.position;
            // Curvada: arriba se mete bajo el tanque y adelante se recoge hacia la horquilla, abrazando tanque y radiador
            const yAlto = ty - 0.01, yBajo = radY - 0.09;
            const curvar = (malla) => {
              const q = malla.geometry.attributes.position;
              for (let i = 0; i < q.count; i++) {
                const t = Math.min(1, Math.max(0, (q.getY(i) - yBajo) / (yAlto - yBajo)));
                const adelante = Math.min(1, Math.max(0, (q.getX(i) - (H.x - 0.12)) / 0.16));
                q.setZ(i, q.getZ(i) * (1 - 0.2 * t * t) * (1 - 0.18 * adelante * adelante));
              }
              q.needsUpdate = true;
              malla.geometry.computeVertexNormals();
            };
            curvar(aleta);
            // Panel inferior negro de contraste en la punta de la aleta (como en las naked tipo NS 200)
            // (con la misma curva que la aleta, para que quede pegado sobre ella y no flotando)
            curvar(perfil([[H.x + 0.035, radY + 0.05], [radX + 0.025, radY - 0.085], [radX - 0.05, radY - 0.03], [H.x - 0.01, radY + 0.1]],
              0.006, M.oscuro, decor, lado * 0.177, 0.003, true));
          }
          zona(aleta, "tanque");
          // Ranura oscura de la aleta pequeña (en las grandes no: quedaba como una franja suelta entre aleta y tanque)
          if (!grande) {
            perfil([[tx + 0.2, ty - 0.06], [tx + 0.13, ty + 0.0], [tx + 0.08, ty - 0.03], [tx + 0.1, ty - 0.08]],
              0.008, M.oscuro, decor, lado * (anchoT / 2 + 0.002), 0.003);
          }
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
    const escalon = tipo === "sport" || esNs ? 0.05 : esGixxer ? 0.04 : 0; // asiento partido (deportivas, NS y Gixxer)
    // Asiento acolchado: más ancho donde se sienta el conductor, se angosta hacia la cola (escalón en las deportivas)
    const mitad = (inicioAsiento + finAsiento) / 2;
    const anchoAsiento = tipo === "enduro" ? 0.2 : 0.27;
    panelAhusado([[inicioAsiento, alturaAsiento - 0.04], [inicioAsiento + 0.02, alturaAsiento + 0.015], [inicioAsiento + 0.1, alturaAsiento + 0.035],
      [mitad, alturaAsiento + 0.025], [mitad - 0.02, alturaAsiento + 0.03 + escalon], [finAsiento + 0.1, alturaAsiento + 0.05 + escalon],
      [finAsiento + 0.02, alturaAsiento + 0.03 + escalon], [finAsiento + 0.04, alturaAsiento - 0.03]], anchoAsiento, M.asiento,
    (x, y) => (x > inicioAsiento + 0.14 ? Math.max(0.55, 1 - (x - inicioAsiento - 0.14) * 1.2) : 1)
      * (x < mitad - 0.05 ? Math.max(0.55, 1 - (mitad - 0.05 - x) * 1.4) : 1), 0.03);
    // Colín afilado que sube hacia atrás, con tapas laterales
    // Colín: NS afilado y levantado; Gixxer corto y respingado; Boxer largo y plano; los demás, el genérico
    const aA = alturaAsiento;
    const contornoColin = esNs ? [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA - 0.01 + escalon], [xR - 0.08, aA + escalon + 0.035],
      [xR - 0.15, aA + escalon + 0.015], [xR + 0.06, aA - 0.13], [P.x - 0.1, aA - 0.2], [P.x + 0.06, aA - 0.14]]
      : esGixxer ? [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA + escalon], [xR - 0.02, aA + escalon + 0.045],
        [xR - 0.08, aA + escalon + 0.025], [xR + 0.1, aA - 0.1], [P.x - 0.08, aA - 0.18], [P.x + 0.06, aA - 0.14]]
        : esBoxer ? [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA - 0.02], [xR - 0.1, aA - 0.01], [xR - 0.13, aA - 0.04],
          [xR + 0.08, aA - 0.12], [P.x - 0.1, aA - 0.19], [P.x + 0.06, aA - 0.14]]
          : [[P.x + 0.04, aA - 0.06], [finAsiento + 0.02, aA - 0.01 + escalon], [xR - 0.06, aA + escalon + 0.01],
            [xR - 0.1, aA + escalon - 0.025], [xR + 0.08, aA - 0.12], [P.x - 0.1, aA - 0.2], [P.x + 0.06, aA - 0.14]];
    zona(panelAhusado(contornoColin, tipo === "semi" ? 0.24 : 0.22, pintura,
    // En la semiautomática el colín sigue al panel de debajo del asiento (mismo ancho y poco angostamiento),
    // para que se vean como una sola pieza y no como un bulto aparte.
    (x) => (x < P.x - 0.1 ? Math.max(tipo === "semi" ? 0.7 : 0.35, 1 - (P.x - 0.1 - x) * (tipo === "semi" ? 0.6 : 1.6)) : 1), 0.02),
    "lateral", "cola");
    if (esBoxer) {
      // Boxer: tapa lateral ovalada bajo el asiento con su emblema cromado
      for (const lado of [1, -1]) {
        const ovalo = Array.from({ length: 14 }, (_, k) => {
          const a = (k / 14) * Math.PI * 2;
          return [P.x + 0.07 + Math.cos(a) * 0.09, alturaAsiento - 0.1 + Math.sin(a) * 0.05];
        });
        zona(perfil(ovalo, 0.014, pintura, decor, lado * 0.118, 0.006, true), "lateral");
        caja(0.05, 0.01, 0.004, M.cromo, V(P.x + 0.07, alturaAsiento - 0.1, lado * 0.128), decor);
      }
    } else if (esNs || esGixxer) {
      // NS y Gixxer: tapa lateral negra angulosa entre el asiento y el basculante
      for (const lado of [1, -1]) {
        perfil(esNs
          ? [[P.x + 0.1, alturaAsiento - 0.05], [P.x - 0.06, alturaAsiento - 0.07], [P.x - 0.12, alturaAsiento - 0.15], [P.x + 0.04, alturaAsiento - 0.17]]
          : [[P.x + 0.12, alturaAsiento - 0.06], [P.x - 0.04, alturaAsiento - 0.06], [P.x - 0.08, alturaAsiento - 0.14], [P.x + 0.08, alturaAsiento - 0.16]],
        0.012, M.oscuro, decor, lado * 0.112, 0.004, true);
      }
    }
    // Stop LED en la punta del colín
    // Stop: carcasa negra con la mica roja encendida y una franja clara al centro (luz de reversa/placa)
    const posStop = V(xR - 0.1, alturaAsiento + escalon - 0.012, 0);
    caja(0.03, 0.04, 0.125, M.oscuro, posStop.clone().add(V(0.012, 0.004, 0)), decor).rotation.z = 0.5;
    if (esNs) {
      // Pulsar NS: stop partido en dos LED en "V" a cada lado de la punta del colín
      for (const lado of [1, -1]) {
        const led = caja(0.012, 0.022, 0.06, M.stop, posStop.clone().add(V(0, 0, lado * 0.032)), decor);
        led.rotation.set(lado * 0.45, 0, 0.5);
      }
    } else {
      const stopLed = caja(0.012, 0.03, 0.11, M.stop, posStop, decor);
      stopLed.rotation.z = 0.5;
    }
    caja(0.004, 0.008, 0.05, M.luz, posStop.clone().add(V(-0.007, -0.002, 0)), decor).rotation.z = 0.5;
  }
  if (!scooter) {
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
      const tanqueX = H.x - 0.3, tanqueY = alturaAsiento + 0.07;
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
      // Rejillas de ventilación en los costados del carenado (tres ranuras oscuras inclinadas), apoyadas sobre la
      // superficie abombada (con una z fija quedaban medio enterradas o asomando como astillas)
      const zCarenado = (x, y) => {
        const u = Math.min(1, Math.max(0, (x - x0) / (x1 - x0))), v = Math.min(1, Math.max(0, (y - y0) / (y1 - y0)));
        return (0.18 + 0.03) * angostar(x, y) * (1 + 0.22 * Math.sin(Math.PI * u) * Math.sin(Math.PI * v));
      };
      for (const lado of [1, -1]) {
        for (let k = 0; k < 3; k++) {
          const x = H.x - 0.08 - k * 0.03, y = H.y - 0.17 - k * 0.045;
          const ranura = caja(0.1, 0.012, 0.006, M.oscuro, V(x, y, lado * (zCarenado(x, y) + 0.001)), decor, 0.55);
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

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
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
      for (let i = 0; i < n; i++) disco(r + 0.0022, 0.0035, M.labrado, tramo(0.32 + (0.62 * (i + 0.5)) / n), decor, 14);
      const tapa = malla(new THREE.SphereGeometry(r, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), M.caucho, decor);
      tapa.position.copy(punta);
      tapa.rotation.x = lado * Math.PI / 2;
    }
  }

  if (!scooter) {
    const deportiva = tipo === "sport";
    for (const lado of [1, -1]) {
      // Conductor: platina que baja del chasis al pivote, debajo del pivote de la tijera
      calapie(V(P.x + 0.08, P.y - 0.04, lado * 0.13), lado, 0.085,
        { ancla: V(P.x + 0.02, P.y + 0.07, lado * 0.1), r: 0.012, dentado: deportiva, matPlatina: deportiva ? M.metal : M.chasis });
      // Protector de talón (motos de 150 cc o más): lámina delante del pie, junto a la platina
      if (specs.cilindraje >= 150) {
        caja(0.07, 0.05, 0.004, deportiva ? M.metal : M.oscuro, V(P.x + 0.11, P.y + 0.01, lado * 0.118), decor, 0.5);
      }
      // Parrillero: cuelga del subchasis por fuera y por encima del basculante (no se mueve con la suspensión)
      calapie(V(P.x - 0.16, P.y + 0.075, lado * 0.145), lado, 0.075,
        { ancla: V(P.x - 0.07, P.y + 0.19, lado * 0.115), r: 0.0105 });
    }
  } else {
    // Scooter: el conductor apoya en el piso; el parrillero tiene calapiés plegables que salen del costado del carenado
    // En la genérica va más arriba, sobre el costado rojo del carenado (abajo quedaba suelto junto al piso)
    const xPar = esNmax ? -0.2 : -0.17, yPar = esNmax ? 0.4 : 0.455, zPar = esNmax ? 0.232 : 0.196;
    for (const lado of [1, -1]) {
      caja(0.06, 0.04, 0.012, M.oscuro, V(xPar, yPar + 0.006, lado * (zPar - 0.012)), decor); // base atornillada al carenado
      calapie(V(xPar, yPar, lado * zPar), lado, 0.065, { r: 0.0105, matPlatina: M.oscuro });
    }
  }
  // ----- Personalidad por tipo de moto -----
  if (!scooter) {
    const Em = V(P.x + 0.2 * s + 0.04, P.y + 0.05); // centro del motor (el mismo de la sección "Motor")
    if ((tipo === "calle" || tipo === "semi") && specs.cilindraje <= 125) {
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

  await ceder(); // (armado en pedazos: entre uno y otro el navegador atiende la página y no se congela)
  // Rendimiento: las piezas decorativas sueltas que comparten material (tornillos, soportes, cables, aletas…)
  // se unen en una sola malla por material. Menos mallas = menos llamadas de dibujo = anda mejor en celulares.
  // No se tocan las piezas con datos propios (carrocería para calcas, franjas, piezas internas, etc.).
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
  accesorio("baul", (g) => {
    // Baúl trasero sobre la parrilla, con base metálica y reflectivo rojo atrás
    const cx = scooter ? xR + 0.04 : xR - 0.04;
    const b = esNmax ? 0.9 : alturaAsiento + (scooter ? 0.07 : 0.075);
    perfil([[cx + 0.15, b], [cx + 0.17, b + 0.15], [cx + 0.11, b + 0.24], [cx - 0.12, b + 0.25], [cx - 0.18, b + 0.14],
      [cx - 0.16, b]], 0.36, M.oscuro, g, 0, 0.022, true);
    caja(0.35, 0.007, 0.41, M.chasis, V(cx - 0.01, b + 0.165, 0), g); // junta de la tapa
    const refl = new THREE.MeshStandardMaterial({ color: 0xc62828, emissive: 0x7a0c0c, emissiveIntensity: 0.35, roughness: 0.25 });
    caja(0.006, 0.03, 0.22, refl, V(cx - 0.197, b + 0.12, 0), g, 0.25);
    caja(0.26, 0.014, 0.2, M.chasis, V(cx, b - 0.004, 0), g);
  });
  if (tipo !== "enduro") {
    accesorio("cubremanos", (g) => {
      for (const lado of [1, -1]) {
        const cubre = elipsoide(0.075, 0.032, 0.022, M.oscuro, V(H.x + 0.035, H.y + altoManubrio + 0.005, lado * (anchoManubrio - 0.07)), g);
        cubre.rotation.y = -lado * 0.25;
      }
    });
  }
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
    const resplandor = new THREE.PointLight(0x22d3ee, 0.9, 1.1, 1.5);
    resplandor.position.set((xa + xb) / 2, y - 0.03, 0);
    g.add(resplandor);
    g.userData.led = { material: ledMat, luz: resplandor };
  });

  return { raiz, piezas, M, ruedas, pata, placa, accesorios, visoresFabrica, espejos, escapeFabrica, rinFabrica: radios ? "radios" : "aleacion" };
}
