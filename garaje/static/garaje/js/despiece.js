// Despiece interactivo: sistemas de la moto, plano con zoom y piezas coloreadas por estado.
(function () {
  const nodo = document.getElementById("datos-despiece");
  if (!nodo) return;
  const datos = JSON.parse(nodo.textContent);
  const laminas = datos.laminas;
  const $ = (id) => document.getElementById(id);
  const plano = $("plano");
  const escena = $("plano-escena");
  const img = $("plano-img");
  const ficha = $("parte-ficha");
  const lista = $("partes-lista");
  const buscar = $("buscar-pieza");
  const reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const ETIQUETA = { ok: "Al día", pronto: "Pronto", vencido: "Toca ya", desconocido: "Sin registro" };
  const PESO = { vencido: 3, pronto: 2, desconocido: 1, ok: 0 };
  const peso = (e) => PESO[e] ?? -1;

  const NS = "http://www.w3.org/2000/svg";
  let actual = null;
  let elegida = null;
  let filtro = "mant";
  // Se abre siempre el dibujo propio de TallerYa; el plano del catálogo (solo en local) va en su propia pestaña.
  let fuente = "dibujo";

  const usaOriginal = () => fuente === "original" && actual && actual.original;
  const coords = (p) => (usaOriginal() ? [p.xo, p.yo] : [p.x, p.y]);
  const enDibujo = (p) => { const [x, y] = coords(p); return x !== null && x !== undefined && y !== null && y !== undefined; };
  const dimensiones = () => (usaOriginal() ? [actual.ancho_original, actual.alto_original] : [actual.ancho, actual.alto]);

  function el(etiqueta, clase, texto) {
    const n = document.createElement(etiqueta);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  // ---------------- Sistemas ----------------
  // Funcionan como acordeón (también en celular): el sistema abierto despliega debajo su lista de piezas.
  const sistemas = $("sistemas");
  const cajaPartes = $("caja-partes");
  const panelDerecho = cajaPartes.parentElement;
  const escritorio = window.matchMedia("(min-width: 1024px)");
  let desplegado = true;
  // Los sistemas se agrupan por temática, en este orden.
  const TEMAS = [
    ["Frenos", ["freno_del", "freno_tras"]],
    ["Llantas", ["llanta_del", "llanta_tras"]],
    ["Motor", ["motor", "bujia", "filtro_aire"]],
    ["Aceite", ["aceite"]],
    ["Refrigeración", ["refrigeracion"]],
    ["Transmisión", ["correa", "cadena"]],
    ["Suspensión y dirección", ["suspension_del", "suspension_tras"]],
    ["Eléctrico", ["bateria"]],
  ];
  const temaDe = (l) => TEMAS.findIndex(([, piezas]) => piezas.includes(l.pieza));
  const ordenadas = laminas.map((l, i) => ({ l, i, t: temaDe(l) < 0 ? TEMAS.length : temaDe(l) }))
    .sort((a, b) => a.t - b.t || a.i - b.i);
  let temaActual = null;
  let cuerpoTema = sistemas;
  const grupoFamilia = new Map();
  // La familia toma el color del peor estado de sus sistemas (pista de "Toca ya" aunque esté plegada).
  function pintarFamilias() {
    sistemas.querySelectorAll(".sistemas-familia").forEach((f) => {
      const estados = laminas.filter((l) => grupoFamilia.get(l.id) === f).map((l) => l.estado);
      const peor = estados.sort((a, b) => peso(b) - peso(a))[0];
      f.dataset.estado = peor || "ok";
      const cuenta = (e) => estados.filter((x) => x === e).length;
      const AVISO = { vencido: "con mantenimiento pendiente", pronto: "que les falta poco", desconocido: "sin registro", ok: "al día" };
      const n = cuenta(peor || "ok") || estados.length;
      f.querySelector(".sistemas-tema").title = `${n} sistema${n > 1 ? "s" : ""} ${AVISO[peor || "ok"]}`;
    });
  }
  ordenadas.forEach(({ l, t }) => {
    if (t !== temaActual) {
      // Cada familia (Frenos, Llantas…) se pliega y despliega con su título.
      temaActual = t;
      const cuantos = ordenadas.filter((o) => o.t === t).length;
      const familia = el("div", "sistemas-familia");
      const titulo = el("button", "sistemas-tema");
      titulo.type = "button";
      titulo.setAttribute("aria-expanded", "true");
      titulo.append(el("span", "", t < TEMAS.length ? TEMAS[t][0] : "Otros"), el("em", "", String(cuantos)), el("i", "sistemas-tema-flecha"));
      cuerpoTema = el("div", "sistemas-familia-cuerpo");
      titulo.addEventListener("click", () => {
        const plegada = familia.classList.toggle("plegada");
        titulo.setAttribute("aria-expanded", String(!plegada));
      });
      familia.append(titulo, cuerpoTema);
      sistemas.appendChild(familia);
    }
    grupoFamilia.set(l.id, cuerpoTema.parentElement);
    const mant = l.partes.filter((p) => p.tarea);
    const grupo = el("div", "sistema-grupo");
    const b = el("button", "sistema");
    b.type = "button";
    b.dataset.id = l.id;
    b.setAttribute("aria-controls", `sistema-panel-${l.id}`);
    b.appendChild(el("span", `punto-mini punto-${l.estado || "neutro"}`));
    const textos = el("span", "sistema-texto");
    textos.appendChild(el("span", "sistema-nombre", l.nombre));
    const meta = l.estado && l.estado !== "ok" ? ETIQUETA[l.estado] : `${mant.length || "Sin"} de mantenimiento`;
    textos.appendChild(el("span", "sistema-meta", meta));
    b.appendChild(textos);
    const flecha = el("span", "sistema-flecha");
    flecha.setAttribute("aria-hidden", "true");
    b.appendChild(flecha);
    b.addEventListener("click", () => {
      if (actual === l) { desplegado = !desplegado; ubicarLista(); return; }
      desplegado = true;
      mostrar(l);
    });
    const panel = el("div", "sistema-panel");
    panel.id = `sistema-panel-${l.id}`;
    panel.hidden = true;
    grupo.append(b, panel);
    cuerpoTema.appendChild(grupo);
  });

  pintarFamilias();

  function ubicarLista() {
    sistemas.querySelectorAll(".sistema-grupo").forEach((g) => {
      const b = g.querySelector(".sistema");
      const abierto = desplegado && actual && b.dataset.id == actual.id;
      b.setAttribute("aria-expanded", String(Boolean(abierto)));
      const panel = g.querySelector(".sistema-panel");
      panel.hidden = !abierto;
      if (abierto && cajaPartes.parentElement !== panel) panel.appendChild(cajaPartes);
    });
    cajaPartes.hidden = !desplegado;
  }
  escritorio.addEventListener("change", ubicarLista);

  // ---------------- Plano con zoom y desplazamiento ----------------
  const vista = { s: 1, x: 0, y: 0, base: { w: 0, h: 0 } };
  const ZOOM_MAX = 5;

  function medir() {
    if (!actual) return;
    const { clientWidth: w, clientHeight: h } = plano;
    const [ancho, alto] = dimensiones();
    const aspecto = ancho / alto;
    const bw = Math.min(w, h * aspecto);
    vista.base = { w: bw, h: bw / aspecto };
    escena.style.width = vista.base.w + "px";
    escena.style.height = vista.base.h + "px";
  }

  function limitar() {
    const { clientWidth: w, clientHeight: h } = plano;
    const ew = vista.base.w * vista.s;
    const eh = vista.base.h * vista.s;
    vista.x = ew <= w ? (w - ew) / 2 : Math.min(40, Math.max(w - ew - 40, vista.x));
    vista.y = eh <= h ? (h - eh) / 2 : Math.min(40, Math.max(h - eh - 40, vista.y));
  }

  function aplicar(animar) {
    limitar();
    escena.style.transition = animar && !reducido ? "transform .3s ease" : "none";
    escena.style.transform = `translate(${vista.x}px, ${vista.y}px) scale(${vista.s})`;
    escena.style.setProperty("--inv", 1 / vista.s);
    plano.classList.toggle("acercado", vista.s > 1.01);
  }

  function zoomEn(nuevo, px, py, animar) {
    nuevo = Math.min(ZOOM_MAX, Math.max(1, nuevo));
    vista.x = px - (px - vista.x) * (nuevo / vista.s);
    vista.y = py - (py - vista.y) * (nuevo / vista.s);
    vista.s = nuevo;
    aplicar(animar);
  }

  function centro() {
    return [plano.clientWidth / 2, plano.clientHeight / 2];
  }

  function reiniciar(animar) {
    vista.s = 1;
    medir();
    aplicar(animar);
  }

  function enfocar(parte) {
    // Acerca y centra la pieza elegida (si aparece en el dibujo).
    if (!enDibujo(parte)) return;
    const [px, py] = coords(parte);
    const s = Math.max(vista.s, 2.2);
    vista.s = s;
    vista.x = plano.clientWidth / 2 - px * vista.base.w * s;
    vista.y = plano.clientHeight / 2 - py * vista.base.h * s;
    aplicar(true);
  }

  document.querySelectorAll("[data-zoom]").forEach((b) => {
    b.addEventListener("click", () => {
      const [cx, cy] = centro();
      if (b.dataset.zoom === "mas") zoomEn(vista.s * 1.5, cx, cy, true);
      else if (b.dataset.zoom === "menos") zoomEn(vista.s / 1.5, cx, cy, true);
      else reiniciar(true);
    });
  });

  plano.addEventListener("wheel", (e) => {
    const r = plano.getBoundingClientRect();
    const factor = e.deltaY < 0 ? 1.18 : 1 / 1.18;
    if (factor < 1 && vista.s <= 1) return; // deja hacer scroll a la página
    e.preventDefault();
    zoomEn(vista.s * factor, e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });

  plano.addEventListener("dblclick", (e) => {
    if (e.target.closest(".punto")) return;
    const r = plano.getBoundingClientRect();
    zoomEn(vista.s * 2, e.clientX - r.left, e.clientY - r.top, true);
  });

  plano.addEventListener("keydown", (e) => {
    const [cx, cy] = centro();
    const paso = 60;
    const acciones = {
      "+": () => zoomEn(vista.s * 1.5, cx, cy, true), "=": () => zoomEn(vista.s * 1.5, cx, cy, true),
      "-": () => zoomEn(vista.s / 1.5, cx, cy, true), "0": () => reiniciar(true),
      ArrowLeft: () => { vista.x += paso; aplicar(true); }, ArrowRight: () => { vista.x -= paso; aplicar(true); },
      ArrowUp: () => { vista.y += paso; aplicar(true); }, ArrowDown: () => { vista.y -= paso; aplicar(true); },
    };
    if (acciones[e.key]) { e.preventDefault(); acciones[e.key](); }
  });

  // Arrastrar con un dedo/mouse y pellizcar con dos dedos.
  const punteros = new Map();
  let arrastre = null;
  let movido = false;
  plano.addEventListener("pointerdown", (e) => {
    if (e.target.closest(".plano-zoom")) return;
    punteros.set(e.pointerId, { x: e.clientX, y: e.clientY });
    movido = false;
    arrastre = { x: e.clientX, y: e.clientY, vx: vista.x, vy: vista.y, dist: null, s: vista.s };
  });
  plano.addEventListener("pointermove", (e) => {
    if (!punteros.has(e.pointerId) || !arrastre) return;
    punteros.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const r = plano.getBoundingClientRect();
    if (punteros.size === 2) {
      const [a, b] = [...punteros.values()];
      const dist = Math.hypot(a.x - b.x, a.y - b.y);
      if (arrastre.dist === null) arrastre.dist = dist / vista.s;
      movido = true;
      zoomEn(dist / arrastre.dist, (a.x + b.x) / 2 - r.left, (a.y + b.y) / 2 - r.top);
      return;
    }
    const dx = e.clientX - arrastre.x;
    const dy = e.clientY - arrastre.y;
    if (!movido && Math.hypot(dx, dy) > 4) {
      movido = true;
      // Solo al empezar a arrastrar capturamos el puntero, para seguir moviendo aunque salga del plano.
      try { plano.setPointerCapture(e.pointerId); } catch (_) { /* navegadores sin soporte */ }
    }
    if (movido && vista.s > 1) {
      vista.x = arrastre.vx + dx;
      vista.y = arrastre.vy + dy;
      aplicar(false);
    }
  });
  const soltar = (e) => {
    punteros.delete(e.pointerId);
    if (punteros.size === 0) arrastre = null;
    else if (arrastre) { arrastre.dist = null; const p = [...punteros.values()][0]; Object.assign(arrastre, { x: p.x, y: p.y, vx: vista.x, vy: vista.y }); }
  };
  plano.addEventListener("pointerup", soltar);
  plano.addEventListener("pointercancel", soltar);
  new ResizeObserver(() => { medir(); aplicar(false); }).observe(plano);

  // ---------------- Lámina ----------------
  function mostrar(lamina, parteId) {
    if (actual) cerrarGuia();
    actual = lamina;
    sistemas.querySelectorAll(".sistema").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.id == lamina.id)));
    // Si el sistema elegido está en una familia plegada, se despliega.
    const familiaElegida = sistemas.querySelector(`.sistema[data-id="${lamina.id}"]`)?.closest(".sistemas-familia");
    if (familiaElegida?.classList.contains("plegada")) {
      familiaElegida.classList.remove("plegada");
      familiaElegida.querySelector(".sistemas-tema").setAttribute("aria-expanded", "true");
    }
    ubicarLista();
    // Solo desliza la fila de sistemas (en celular es horizontal); nunca mueve la página.
    // Antes se usaba scrollIntoView y, al cargar, la página bajaba sola hasta el despiece.
    const elegido = sistemas.querySelector('[aria-selected="true"]');
    if (elegido && sistemas.scrollWidth > sistemas.clientWidth) {
      sistemas.scrollTo({ left: Math.max(0, elegido.offsetLeft - sistemas.offsetLeft - 8), behavior: "auto" });
    }
    $("lamina-titulo").textContent = lamina.nombre;
    const mant = lamina.partes.filter((p) => p.tarea);
    const pendientes = mant.filter((p) => p.estado === "vencido" || p.estado === "pronto").length;
    const origen = usaOriginal() || !lamina.dibujo_propio ? `Plano original · FIG. ${lamina.figura}` : "Dibujo TallerYa";
    const selector = $("fuente-dibujo");
    selector.hidden = !lamina.original;
    selector.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.fuente === (usaOriginal() ? "original" : "dibujo"))));
    $("lamina-resumen").textContent = `${origen} · ${lamina.partes.length} piezas · ${mant.length} de mantenimiento` +
      (pendientes ? ` · ${pendientes} por atender` : "");

    dibujarPlano();
    aplicarFiltro();
    buscar.value = "";
    pintarLista();
    reiniciar(false);

    const inicial = lamina.partes.find((p) => p.id === parteId) ||
      mant.slice().sort((a, b) => peso(b.estado) - peso(a.estado))[0] || lamina.partes[0];
    elegir(inicial);
  }

  function dibujarPlano() {
    const lamina = actual;
    img.src = usaOriginal() ? lamina.original : lamina.imagen;
    img.alt = `Despiece: ${lamina.nombre}`;
    escena.querySelectorAll(".punto").forEach((p) => p.remove());
    dibujarLineas();
    lamina.partes.filter(enDibujo).forEach((p) => {
      const [px, py] = coords(p);
      const punto = el("button", `punto ${p.estado ? "punto-" + p.estado : "punto-neutro"}`, String(p.ref));
      punto.type = "button";
      punto.style.left = px * 100 + "%";
      punto.style.top = py * 100 + "%";
      punto.dataset.id = p.id;
      punto.dataset.nombre = p.nombre;
      punto.dataset.mant = p.tarea ? "1" : "";
      punto.setAttribute("aria-label", `${p.ref}: ${p.nombre}` + (p.cantidad > 1 ? `, ${p.cantidad} unidades` : ""));
      // El nombre que aparece al pasar el mouse no se sale del recuadro: cerca de un borde se corre hacia adentro
      const ubicarEtiqueta = () => {
        const r = punto.getBoundingClientRect(), c = plano.getBoundingClientRect();
        punto.dataset.lado = r.left - c.left < 130 ? "izq" : c.right - r.right < 130 ? "der" : "";
        punto.classList.toggle("etiqueta-abajo", r.top - c.top < 56);
      };
      punto.addEventListener("pointerenter", ubicarEtiqueta);
      punto.addEventListener("focus", ubicarEtiqueta);
      // Piezas que van varias veces (tornillos, rodamientos...): la cantidad junto al número
      if (p.cantidad > 1) punto.appendChild(el("span", "punto-cantidad", `×${p.cantidad}`));
      punto.addEventListener("click", (e) => {
        if (movido) { e.preventDefault(); return; }
        if (elegida && elegida.id === p.id) abrirGuia(p); // segundo toque: abre la guía
        else elegir(p);
      });
      escena.appendChild(punto);
    });
    marcarElegida();
  }

  function aplicarFiltro() {
    escena.classList.toggle("solo-mant", filtro === "mant" && actual?.partes.some((p) => p.tarea));
  }
  document.querySelectorAll('[data-filtro="mant"], [data-filtro="todas"]').forEach((b) => {
    b.addEventListener("click", () => {
      filtro = b.dataset.filtro;
      document.querySelectorAll('[data-filtro="mant"], [data-filtro="todas"]').forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      aplicarFiltro();
    });
  });

  // Pestañas "Dibujo TallerYa" / "Plano original" (el plano solo aparece si existe en local).
  document.querySelectorAll("[data-fuente]").forEach((b) => {
    b.addEventListener("click", () => {
      fuente = b.dataset.fuente;
      document.querySelectorAll("[data-fuente]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      const resumen = $("lamina-resumen");
      resumen.textContent = resumen.textContent.replace(/^[^·]*(· FIG\. \d+ )?/, usaOriginal() ? `Plano original · FIG. ${actual.figura} ` : "Dibujo TallerYa ");
      dibujarPlano();
      aplicarFiltro();
      reiniciar(false);
      if (elegida) elegir(elegida);
    });
  });

  // ---------------- Lista y búsqueda ----------------
  // "Otras piezas" (sin mantenimiento) va plegado; se abre al tocarlo, al buscar o al elegir una de ellas.
  let otrasAbiertas = false;
  function pintarOtras() {
    const abiertas = otrasAbiertas || Boolean(buscar.value.trim());
    lista.classList.toggle("otras-plegadas", !abiertas);
    const t = lista.querySelector(".partes-separador button");
    if (t) t.setAttribute("aria-expanded", String(abiertas));
  }
  function pintarLista() {
    const q = buscar.value.trim().toLowerCase();
    // Solo números: busca por el número de la pieza en el dibujo ("3" encuentra 3, 30, 31…, pero no 13).
    const porNumero = /^\d+$/.test(q);
    const coincide = (p) => !q || (porNumero ? String(p.ref).startsWith(q)
      : `${p.nombre} ${p.descripcion} ${p.codigo}`.toLowerCase().includes(q));
    lista.innerHTML = "";
    const vistas = new Set();
    const ordenadas = actual.partes.slice().sort((a, b) => (b.tarea ? 1 : 0) - (a.tarea ? 1 : 0) || peso(b.estado) - peso(a.estado) || a.ref - b.ref);
    let hayMant = false;
    let separador = false;
    for (const p of ordenadas) {
      if (vistas.has(p.ref)) continue; // el catálogo repite referencias (lado derecho e izquierdo)
      if (!coincide(p)) continue;
      vistas.add(p.ref);
      if (p.tarea) hayMant = true;
      if (!p.tarea && hayMant && !separador) {
        const sep = el("li", "partes-separador");
        const t = el("button");
        t.type = "button";
        const cuantas = new Set(ordenadas.filter((o) => !o.tarea && coincide(o)).map((o) => o.ref)).size;
        t.append(el("span", "", "Otras piezas"), el("em", "", String(cuantas)), el("i", "partes-flecha"));
        t.addEventListener("click", () => { otrasAbiertas = !otrasAbiertas; pintarOtras(); });
        sep.appendChild(t);
        lista.appendChild(sep);
        separador = true;
      }
      const li = el("li", separador ? "parte-otra" : "");
      const b = el("button", "parte-fila");
      b.type = "button";
      b.dataset.id = p.id;
      b.append(el("span", "parte-ref", String(p.ref)), el("span", "parte-nombre", p.nombre));
      if (p.cantidad > 1) b.appendChild(el("span", "parte-cantidad", `×${p.cantidad}`));
      if (!enDibujo(p)) b.appendChild(el("span", "parte-sin-dibujo", "solo en lista"));
      if (p.estado) b.appendChild(el("span", `punto-mini punto-${p.estado}`));
      b.addEventListener("click", () => { elegir(p); enfocar(p); });
      li.appendChild(b);
      lista.appendChild(li);
    }
    if (!lista.children.length) lista.appendChild(el("li", "text-sm text-suave px-2 py-3", "No encontramos esa pieza en este sistema."));
    pintarOtras();
    marcarElegida();
  }
  const limpiar = $("buscar-limpiar");
  buscar.addEventListener("input", () => { limpiar.hidden = !buscar.value; pintarLista(); });
  limpiar.addEventListener("click", () => { buscar.value = ""; limpiar.hidden = true; pintarLista(); buscar.focus(); });

  // ---------------- Ficha de la pieza ----------------
  // Líneas finas de cada número (afuera del dibujo) a su pieza, como en los planos de las marcas
  function dibujarLineas() {
    let capa = escena.querySelector(".plano-lineas");
    if (!capa) {
      capa = document.createElementNS(NS, "svg");
      capa.setAttribute("class", "plano-lineas");
      capa.setAttribute("viewBox", "0 0 1000 1000");
      capa.setAttribute("preserveAspectRatio", "none");
      capa.setAttribute("aria-hidden", "true");
      escena.insertBefore(capa, img.nextSibling);
    }
    capa.innerHTML = "";
    if (usaOriginal() || !actual) return;
    const vistos = new Set();
    actual.partes.forEach((p) => {
      if (!p.ancla || p.x === null || p.x === undefined) return;
      const clave = `${p.x},${p.y}`;
      if (vistos.has(clave)) return;
      vistos.add(clave);
      const linea = document.createElementNS(NS, "line");
      Object.entries({ x1: p.ancla[0] * 1000, y1: p.ancla[1] * 1000, x2: p.x * 1000, y2: p.y * 1000 }).forEach(([k, v]) => linea.setAttribute(k, v));
      linea.dataset.id = p.id;
      if (p.tarea) linea.classList.add("de-mant");
      const punta = document.createElementNS(NS, "circle");
      Object.entries({ cx: p.ancla[0] * 1000, cy: p.ancla[1] * 1000, r: 3.2 }).forEach(([k, v]) => punta.setAttribute(k, v));
      punta.dataset.id = p.id;
      capa.append(linea, punta);
    });
  }

  // Pieza que solo tiene número en la franja de abajo: muestra en el dibujo dónde va (anillo + línea punteada)
  function marcarDestino(parte) {
    let capa = escena.querySelector(".plano-destino");
    if (!capa) {
      capa = document.createElementNS(NS, "svg");
      capa.setAttribute("class", "plano-destino");
      capa.setAttribute("viewBox", "0 0 1000 1000");
      capa.setAttribute("preserveAspectRatio", "none");
      capa.setAttribute("aria-hidden", "true");
      escena.insertBefore(capa, img.nextSibling);   // encima del dibujo, debajo de los números
    }
    capa.innerHTML = "";
    const [x, y] = coords(parte);
    if (usaOriginal() || !parte.destino || !parte.destino.length || x === null || x === undefined) return;
    // Solo el punto y un anillo que late en cada lugar (máximo tres), sin línea hasta el número
    parte.destino.forEach(([dx, dy]) => {
      const anillo = document.createElementNS(NS, "circle");
      Object.entries({ cx: dx * 1000, cy: dy * 1000, r: 26 }).forEach(([k, v]) => anillo.setAttribute(k, v));
      const centro = document.createElementNS(NS, "circle");
      Object.entries({ cx: dx * 1000, cy: dy * 1000, r: 6, class: "plano-destino-centro" }).forEach(([k, v]) => centro.setAttribute(k, v));
      capa.append(anillo, centro);
    });
  }

  function marcarElegida() {
    if (!elegida) return;
    if (!elegida.tarea && !otrasAbiertas && lista.querySelector(".partes-separador")) { otrasAbiertas = true; pintarOtras(); }
    escena.querySelectorAll(".punto").forEach((p) => p.classList.toggle("elegido", p.dataset.id == elegida.id));
    escena.querySelectorAll(".plano-lineas [data-id]").forEach((l) => l.classList.toggle("elegida", l.dataset.id == elegida.id));
    marcarDestino(elegida);
    lista.querySelectorAll(".parte-fila").forEach((f) => f.classList.toggle("elegida", f.dataset.id == elegida.id));
  }

  // ---------------- Registrar que se hizo el mantenimiento (sin recargar) ----------------
  function cookie(nombre) {
    const m = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`));
    return m ? decodeURIComponent(m[1]) : "";
  }
  function formularioRegistro(parte) {
    const r = datos.registro;
    const caja = el("details", "registro-pieza");
    const resumen = el("summary", "registro-pieza-titulo",
      parte.estado === "desconocido" ? "Registrar cuándo se hizo" : "Ya le hice este mantenimiento");
    caja.appendChild(resumen);
    const form = el("form", "registro-pieza-form");
    form.noValidate = true;
    form.innerHTML = `
      <fieldset class="registro-cuando registro-pieza-ancho">
        <legend class="campo-label">¿Cuándo lo hiciste?</legend>
        <label class="opcion"><input type="radio" name="cuando" value="hoy" checked> Hoy, con ${r.km.toLocaleString("es-CO")} km</label>
        <label class="opcion"><input type="radio" name="cuando" value="otro"> En otra fecha o kilometraje</label>
      </fieldset>
      <div class="registro-otro registro-pieza-ancho" hidden>
        <label class="campo-label">Kilometraje
          <input type="number" name="km" class="campo" inputmode="numeric" min="0" max="${r.km}" value="${r.km}" required></label>
        <label class="campo-label">Fecha
          <input type="date" name="fecha" class="campo" max="${r.hoy}" value="${r.hoy}" required></label>
      </div>
      <label class="campo-label registro-pieza-ancho">Taller (opcional)
        <select name="taller" class="campo"><option value="">Lo hice yo / sin taller</option></select></label>
      <label class="campo-label registro-pieza-ancho" data-otro hidden>Nombre del taller (opcional)
        <input type="text" name="taller_otro" maxlength="80" class="campo" placeholder="Ej: Motos El Paisa"></label>
      <p class="registro-pieza-aviso registro-pieza-ancho" aria-live="polite"></p>
      <button class="btn btn-lava text-xs py-3 registro-pieza-ancho">Registrar mantenimiento</button>`;
    const select = form.querySelector("select");
    r.talleres.forEach(([id, nombre]) => { const o = el("option", "", nombre); o.value = id; select.appendChild(o); });
    const otro = el("option", "", "Otro taller (fuera de TallerYa)");
    otro.value = "otro";
    select.appendChild(otro);
    select.addEventListener("change", () => { form.querySelector("[data-otro]").hidden = select.value !== "otro"; });
    caja.appendChild(form);
    const aviso = form.querySelector(".registro-pieza-aviso");
    const km = form.querySelector('[name="km"]');
    const boton = form.querySelector("button");
    const revisar = () => {
      const v = Number(km.value);
      const malo = km.value === "" || !Number.isInteger(v) || v < 0 || v > r.km;
      aviso.className = "registro-pieza-aviso registro-pieza-ancho" + (malo ? " error-km" : "");
      aviso.textContent = !malo ? "" : v > r.km
        ? `No puede ser mayor que el kilometraje actual (${r.km.toLocaleString("es-CO")} km).`
        : "Escribe el kilometraje en números enteros.";
      boton.disabled = malo;
      return !malo;
    };
    km.addEventListener("input", revisar);
    // "Hoy" usa el kilometraje actual y la fecha de hoy; "otra" muestra los campos para cambiarlos.
    const otroMomento = form.querySelector(".registro-otro");
    const fecha = form.querySelector('[name="fecha"]');
    form.querySelectorAll('[name="cuando"]').forEach((radio) => radio.addEventListener("change", () => {
      const otra = form.querySelector('[name="cuando"]:checked').value === "otro";
      otroMomento.hidden = !otra;
      if (!otra) {
        km.value = r.km;
        fecha.value = r.hoy;
        fecha.dispatchEvent(new Event("change"));
      }
      revisar();
    }));
    caja.addEventListener("toggle", () => { if (caja.open) window.TallerYaControles?.mejorarTodo(form); }, { once: true });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!revisar()) return;
      boton.disabled = true;
      aviso.className = "registro-pieza-aviso registro-pieza-ancho";
      aviso.textContent = "Guardando…";
      const cuerpo = new FormData(form);
      cuerpo.append("tarea", parte.tarea.id);
      try {
        const resp = await fetch(r.url, {
          method: "POST", body: cuerpo,
          headers: { "X-Requested-With": "fetch", "X-CSRFToken": cookie("csrftoken") },
        });
        const res = await resp.json();
        if (!resp.ok || !res.ok) throw new Error(res.error || "No se pudo registrar. Intenta de nuevo.");
        actualizarTarea(res.tarea);
        elegir(parte); // vuelve a pintar la ficha con el estado nuevo
        const ok = el("p", "registro-pieza-listo", `✓ ${res.mensaje} `);
        const ver = el("a", "km-cambios", "Ver el plan actualizado");
        ver.href = location.pathname + "#plan";
        ver.addEventListener("click", (ev) => { ev.preventDefault(); location.hash = "plan"; location.reload(); });
        ok.appendChild(ver);
        ficha.querySelector(".parte-tarea")?.after(ok);
      } catch (err) {
        aviso.className = "registro-pieza-aviso registro-pieza-ancho error-km";
        aviso.textContent = err.message;
        boton.disabled = false;
      }
    });
    return caja;
  }

  // Aplica el nuevo estado de una tarea a todas sus piezas, a los números del dibujo y al sistema.
  function actualizarTarea(t) {
    if (!t) return;
    laminas.forEach((l) => {
      let toca = false;
      l.partes.forEach((p) => {
        if (p.tarea && p.tarea.id === t.id) {
          toca = true;
          p.estado = t.estado;
          Object.assign(p.tarea, { etiqueta: t.etiqueta, detalle: t.detalle, porcentaje: t.porcentaje });
        }
      });
      if (!toca) return;
      const peor = l.partes.filter((p) => p.estado).sort((a, b) => peso(b.estado) - peso(a.estado))[0];
      l.estado = peor ? peor.estado : null;
      const b = sistemas.querySelector(`.sistema[data-id="${l.id}"]`);
      if (b) {
        b.querySelector(".punto-mini").className = `punto-mini punto-${l.estado || "neutro"}`;
        const mant = l.partes.filter((p) => p.tarea).length;
        b.querySelector(".sistema-meta").textContent = l.estado && l.estado !== "ok" ? ETIQUETA[l.estado] : `${mant || "Sin"} de mantenimiento`;
      }
      pintarFamilias();
    });
    dibujarPlano();
    pintarLista();
  }

  function elegir(parte) {
    if (!parte) return;
    elegida = parte;
    marcarElegida();
    ficha.innerHTML = "";

    const cabeza = el("div", "flex items-start justify-between gap-3");
    const titulo = el("div", "min-w-0");
    const ref = el("p", "guia-ref guia-ref-ficha");
    ref.append(el("span", "guia-ref-texto", "Pieza N.º"), el("strong", "guia-ref-num", String(parte.ref)));
    titulo.append(ref, el("p", "titulo text-2xl leading-tight mt-1", parte.nombre));
    cabeza.appendChild(titulo);
    if (parte.estado) cabeza.appendChild(el("span", `estado estado-${parte.estado} shrink-0`, ETIQUETA[parte.estado]));
    ficha.appendChild(cabeza);
    ficha.appendChild(el("p", "text-xs text-suave mt-1", `En el catálogo: ${parte.descripcion}`));

    if (parte.ayuda) ficha.appendChild(el("p", "parte-ayuda", parte.ayuda));

    if (parte.tarea) {
      const t = el("div", "parte-tarea");
      const fila = el("div", "flex items-center justify-between gap-2");
      fila.append(el("p", "font-semibold text-sm", parte.tarea.nombre));
      t.appendChild(fila);
      if (parte.tarea.porcentaje !== null && parte.tarea.porcentaje !== undefined) {
        const barra = el("div", `barra barra-${parte.estado} mt-2`);
        const relleno = el("span");
        relleno.style.width = parte.tarea.porcentaje + "%";
        barra.appendChild(relleno);
        t.appendChild(barra);
      }
      t.appendChild(el("p", "text-xs text-suave mt-2", parte.tarea.detalle));
      ficha.appendChild(t);
      if (datos.registro) ficha.appendChild(formularioRegistro(parte));
    }

    const codigo = el("div", "codigo-repuesto");
    const izq = el("div");
    izq.append(el("span", "codigo-etiqueta", "Código de repuesto original"), el("strong", "", parte.codigo));
    if (parte.cantidad > 1) izq.appendChild(el("span", "codigo-etiqueta", `Lleva ${parte.cantidad} unidades`));
    // Otras referencias de la misma pieza (otra versión de la moto, o según el año del modelo)
    if (parte.alternos && parte.alternos.length) {
      izq.appendChild(el("span", "codigo-etiqueta", "Otras referencias: " + parte.alternos.map((r) => `${r.codigo} (${r.nota})`).join(" · ")));
    }
    const copiar = el("button", "codigo-copiar", "Copiar");
    copiar.type = "button";
    copiar.addEventListener("click", async () => {
      // Se fija el ancho actual para que el aviso no agrande el botón ni descuadre la caja.
      copiar.style.width = copiar.offsetWidth + "px";
      try { await navigator.clipboard.writeText(parte.codigo); copiar.textContent = "¡Listo!"; }
      catch { copiar.textContent = "Error"; }
      setTimeout(() => { copiar.textContent = "Copiar"; copiar.style.width = ""; }, 1800);
    });
    codigo.append(izq, copiar);
    ficha.appendChild(codigo);

    // Dos acciones del mismo tamaño, una al lado de la otra: ver la guía y pedir el repuesto.
    const acciones = el("div", "ficha-pieza-acciones");
    const guiaBtn = el("button", "btn btn-lava text-xs py-3", "Ver guía");
    guiaBtn.type = "button";
    guiaBtn.addEventListener("click", () => abrirGuia(parte));
    const mensaje = `Hola, necesito el repuesto ${parte.codigo} (${parte.nombre}) para mi ${datos.moto}. ¿Lo tienen?`;
    const wa = el("a", "btn btn-whatsapp text-xs py-3", "Pedir repuesto");
    wa.href = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
    wa.target = "_blank";
    wa.rel = "noopener";
    acciones.append(guiaBtn, wa);
    ficha.appendChild(acciones);
  }

  // ---------------- Guía de la pieza (ventana centrada en la pantalla) ----------------
  const guia = $("guia");
  let origenGuia = null;

  function partesNavegables() {
    const vistas = new Set();
    return actual.partes.slice()
      .sort((a, b) => (b.tarea ? 1 : 0) - (a.tarea ? 1 : 0) || peso(b.estado) - peso(a.estado) || a.ref - b.ref)
      .filter((p) => (vistas.has(p.ref) ? false : vistas.add(p.ref)));
  }

  function seccion(titulo, icono) {
    const s = el("section", "guia-seccion");
    const h = el("h4", "guia-subtitulo");
    h.append(el("span", "guia-icono", icono), document.createTextNode(titulo));
    s.appendChild(h);
    return s;
  }

  function listaGuia(items, clase) {
    const ul = el("ul", `guia-lista ${clase}`);
    items.forEach((t) => ul.appendChild(el("li", "", t)));
    return ul;
  }

  function abrirGuia(parte) {
    if (!parte || !parte.guia) return;
    if (guia.hidden) origenGuia = document.activeElement;
    elegir(parte);
    const g = parte.guia;
    guia.innerHTML = "";

    // Barra superior: volver y navegar entre piezas
    const barra = el("div", "guia-barra");
    const volver = el("button", "guia-volver", "← Volver al dibujo");
    volver.type = "button";
    volver.addEventListener("click", cerrarGuia);
    barra.appendChild(volver);
    const nav = el("div", "guia-nav");
    const contador = (n, total) => {
      const span = el("span", "guia-contador");
      span.setAttribute("aria-label", `Pieza ${n} de ${total}`);
      span.append(el("strong", "", String(n)), el("span", "", `/ ${total}`));
      return span;
    };
    const orden = partesNavegables();
    const i = orden.findIndex((p) => p.ref === parte.ref);
    const CHEVRON = { "‹": "m15 18-6-6 6-6", "›": "m9 18 6-6-6-6" };
    const flecha = (texto, destino, etiqueta) => {
      const b = el("button", "guia-flecha");
      b.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${CHEVRON[texto]}"/></svg>`;
      b.type = "button";
      b.setAttribute("aria-label", etiqueta);
      b.disabled = !destino;
      if (destino) b.addEventListener("click", () => abrirGuia(destino));
      return b;
    };
    nav.append(flecha("‹", orden[i - 1], "Pieza anterior"), contador(i + 1, orden.length),
      flecha("›", orden[i + 1], "Pieza siguiente"));
    barra.appendChild(nav);
    guia.appendChild(barra);

    // Encabezado
    const cabeza = el("header", "guia-cabeza");
    const etiquetas = el("div", "flex flex-wrap items-center gap-2");
    const ref = el("span", "guia-ref");
    ref.append(el("span", "guia-ref-texto", "Pieza N.º"), el("strong", "guia-ref-num", String(parte.ref)));
    etiquetas.appendChild(ref);
    if (parte.estado) etiquetas.appendChild(el("span", `estado estado-${parte.estado}`, ETIQUETA[parte.estado]));
    cabeza.appendChild(etiquetas);
    const titulo = el("h3", "titulo text-3xl md:text-4xl leading-tight mt-3", parte.nombre);
    titulo.tabIndex = -1;
    cabeza.appendChild(titulo);
    cabeza.appendChild(el("p", "text-xs text-suave mt-1", `${parte.descripcion} · Código ${parte.codigo}`));
    // La pieza sola y en grande (dibujo propio de TallerYa) para reconocerla en la moto
    if (parte.dibujo) {
      const figura = el("figure", "guia-dibujo");
      const img = el("img");
      img.src = parte.dibujo;
      img.alt = `Dibujo de la pieza: ${parte.nombre}`;
      img.loading = "lazy";
      figura.append(img, el("figcaption", "", "Dibujo TallerYa de la pieza"));
      // Texto a la izquierda y la pieza a la derecha (en celular, una debajo de la otra)
      const texto = el("div", "guia-cabeza-texto");
      texto.append(...cabeza.childNodes);
      cabeza.append(texto, figura);
      cabeza.classList.add("con-dibujo");
    }
    guia.appendChild(cabeza);

    const cuerpo = el("div", "guia-cuerpo");

    const queHace = seccion("¿Qué hace?", "◎");
    queHace.appendChild(el("p", "guia-texto", g.que_hace));
    if (g.contexto) queHace.appendChild(el("p", "guia-contexto", g.contexto));
    cuerpo.appendChild(queHace);

    const cada = seccion("¿Cada cuánto?", "↻");
    if (parte.tarea) {
      const plan = el("div", "guia-plan");
      plan.appendChild(el("p", "guia-intervalo", parte.tarea.intervalo || parte.tarea.nombre));
      if (parte.tarea.porcentaje !== null && parte.tarea.porcentaje !== undefined) {
        const barraEstado = el("div", `barra barra-${parte.estado} mt-2`);
        const relleno = el("span");
        relleno.style.width = parte.tarea.porcentaje + "%";
        barraEstado.appendChild(relleno);
        plan.appendChild(barraEstado);
      }
      plan.appendChild(el("p", "text-sm mt-2", `${parte.tarea.nombre}: ${parte.tarea.detalle}`));
      cada.appendChild(plan);
      cada.appendChild(el("p", "guia-texto mt-3", g.cada_cuanto));
    } else {
      cada.appendChild(el("p", "guia-texto", g.cada_cuanto));
    }
    cuerpo.appendChild(cada);

    if (g.como_revisar && g.como_revisar.length) {
      const revisar = seccion("Cómo revisarla tú mismo", "◉");
      revisar.appendChild(listaGuia(g.como_revisar, "guia-pasos"));
      cuerpo.appendChild(revisar);
    }

    const senales = seccion("Señales de que algo anda mal", "!");
    senales.appendChild(listaGuia(g.senales, "guia-alertas"));
    cuerpo.appendChild(senales);

    if (g.si_no) {
      const consecuencia = seccion("Si no la atiendes", "⚠");
      consecuencia.classList.add("guia-advertencia");
      consecuencia.appendChild(el("p", "guia-texto", g.si_no));
      cuerpo.appendChild(consecuencia);
    }

    const consejos = seccion("Consejos", "✓");
    consejos.appendChild(listaGuia(g.tips, "guia-consejos"));
    cuerpo.appendChild(consejos);

    if (g.al_comprar && g.al_comprar.length) {
      const compra = seccion("Al comprar el repuesto", "$");
      compra.appendChild(listaGuia(g.al_comprar, "guia-compra"));
      compra.appendChild(el("p", "guia-contexto", `Código para pedirlo: ${parte.codigo}`));
      cuerpo.appendChild(compra);
    }

    const dificultad = seccion("¿Lo hago yo?", "⚒");
    const nivel = { facil: 1, media: 2, taller: 3 }[g.dificultad] || 3;
    const medidor = el("div", "guia-dificultad");
    const niveles = el("span", "guia-niveles");
    niveles.setAttribute("aria-hidden", "true");
    for (let n = 1; n <= 3; n++) niveles.appendChild(el("span", n <= nivel ? `lleno nivel-${nivel}` : ""));
    medidor.append(niveles, el("span", "font-semibold", g.dificultad_texto));
    dificultad.appendChild(medidor);
    cuerpo.appendChild(dificultad);
    guia.appendChild(cuerpo);

    // Acciones
    const acciones = el("div", "guia-acciones");
    const mensaje = `Hola, necesito el repuesto ${parte.codigo} (${parte.nombre}) para mi ${datos.moto}. ¿Lo tienen?`;
    const wa = el("a", "btn btn-whatsapp text-xs px-5 py-3", "Pedir este repuesto");
    wa.href = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
    wa.target = "_blank";
    wa.rel = "noopener";
    acciones.appendChild(wa);
    if (parte.tarea && parte.tarea.servicio) {
      const talleres = el("a", "btn btn-borde text-xs px-5 py-3", "Talleres que lo hacen");
      talleres.href = `/?servicio=${parte.tarea.servicio}`;
      acciones.appendChild(talleres);
    }
    if (parte.tarea && parte.tarea.ancla) {
      const hecho = el("button", "btn btn-borde text-xs px-5 py-3", "Ya lo hice: registrar");
      hecho.type = "button";
      hecho.addEventListener("click", () => {
        const tarea = document.getElementById(parte.tarea.ancla);
        if (!tarea) return;
        cerrarGuia();
        if (window.TallerYaPlan) { window.TallerYaPlan.registrar(tarea.dataset.tareaId); return; }
        const detalles = tarea.querySelector("details");
        if (detalles) detalles.open = true;
        tarea.classList.add("resaltada");
        tarea.scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "center" });
      });
      acciones.appendChild(hecho);
    }
    guia.appendChild(acciones);
    guia.appendChild(el("p", "text-xs text-suave mt-4",
      "Los intervalos son orientativos. Sigue también el manual de tu moto y el criterio de tu mecánico."));

    guia.hidden = false;
    guia.scrollTop = 0;
    document.documentElement.classList.add("guia-abierta");
    titulo.focus({ preventScroll: true });
  }

  document.addEventListener("click", (e) => {
    if (!guia || guia.hidden) return;
    if (!guia.contains(e.target) && !e.target.closest("button")) cerrarGuia();
  });

  function cerrarGuia() {
    if (!guia || guia.hidden) return;
    guia.hidden = true;
    document.documentElement.classList.remove("guia-abierta");
    const destino = (elegida && escena.querySelector(`.punto[data-id="${elegida.id}"]`)) || origenGuia;
    origenGuia = null;
    if (destino && destino.focus) destino.focus({ preventScroll: true });
  }

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && guia && !guia.hidden) cerrarGuia();
  });

  // ---------------- Puente con el modelo 3D ----------------
  window.TallerYaDespiece = {
    tiene: (pieza) => laminas.some((l) => l.pieza === pieza),
    mostrar(pieza) {
      const lamina = laminas.find((l) => l.pieza === pieza);
      if (!lamina) return;
      window.TallerYaSecciones?.abrir("despiece");
      mostrar(lamina);
      $("despiece").scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "start" });
    },
  };

  if (laminas.length) mostrar(laminas[0]);
  // Al entrar a la moto, las familias de sistemas empiezan cerradas (se abren al tocarlas o al elegir un sistema).
  sistemas.querySelectorAll(".sistemas-familia").forEach((f) => {
    f.classList.add("plegada");
    f.querySelector(".sistemas-tema").setAttribute("aria-expanded", "false");
  });
})();
