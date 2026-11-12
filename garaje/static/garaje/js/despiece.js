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

  let actual = null;
  let elegida = null;
  let filtro = "mant";

  function el(etiqueta, clase, texto) {
    const n = document.createElement(etiqueta);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  // ---------------- Sistemas ----------------
  const sistemas = $("sistemas");
  laminas.forEach((l) => {
    const mant = l.partes.filter((p) => p.tarea);
    const b = el("button", "sistema");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.dataset.id = l.id;
    b.appendChild(el("span", `punto-mini punto-${l.estado || "neutro"}`));
    const textos = el("span", "sistema-texto");
    textos.appendChild(el("span", "sistema-nombre", l.nombre));
    const meta = l.estado && l.estado !== "ok" ? ETIQUETA[l.estado] : `${mant.length || "Sin"} de mantenimiento`;
    textos.appendChild(el("span", "sistema-meta", meta));
    b.appendChild(textos);
    b.addEventListener("click", () => mostrar(l));
    sistemas.appendChild(b);
  });

  // ---------------- Plano con zoom y desplazamiento ----------------
  const vista = { s: 1, x: 0, y: 0, base: { w: 0, h: 0 } };
  const ZOOM_MAX = 5;

  function medir() {
    if (!actual) return;
    const { clientWidth: w, clientHeight: h } = plano;
    const aspecto = actual.ancho / actual.alto;
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
    // Acerca y centra la pieza elegida.
    const s = Math.max(vista.s, 2.2);
    vista.s = s;
    vista.x = plano.clientWidth / 2 - parte.x * vista.base.w * s;
    vista.y = plano.clientHeight / 2 - parte.y * vista.base.h * s;
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
    plano.setPointerCapture?.(e.pointerId);
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
    if (Math.hypot(dx, dy) > 4) movido = true;
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
    actual = lamina;
    sistemas.querySelectorAll(".sistema").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.id == lamina.id)));
    sistemas.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: "nearest", inline: "nearest" });
    $("lamina-titulo").textContent = lamina.nombre;
    const mant = lamina.partes.filter((p) => p.tarea);
    const pendientes = mant.filter((p) => p.estado === "vencido" || p.estado === "pronto").length;
    $("lamina-resumen").textContent = `FIG. ${lamina.figura} · ${lamina.partes.length} piezas · ${mant.length} de mantenimiento` +
      (pendientes ? ` · ${pendientes} por atender` : "");

    img.src = lamina.imagen;
    img.alt = `Despiece: ${lamina.nombre}`;
    escena.querySelectorAll(".punto").forEach((p) => p.remove());
    lamina.partes.forEach((p) => {
      const punto = el("button", `punto ${p.estado ? "punto-" + p.estado : "punto-neutro"}`, String(p.ref));
      punto.type = "button";
      punto.style.left = p.x * 100 + "%";
      punto.style.top = p.y * 100 + "%";
      punto.dataset.id = p.id;
      punto.dataset.nombre = p.nombre;
      punto.dataset.mant = p.tarea ? "1" : "";
      punto.setAttribute("aria-label", `${p.ref}: ${p.nombre}`);
      punto.addEventListener("click", (e) => {
        if (movido) { e.preventDefault(); return; }
        elegir(p);
      });
      escena.appendChild(punto);
    });
    aplicarFiltro();
    buscar.value = "";
    pintarLista();
    reiniciar(false);

    const inicial = lamina.partes.find((p) => p.id === parteId) ||
      mant.slice().sort((a, b) => peso(b.estado) - peso(a.estado))[0] || lamina.partes[0];
    elegir(inicial);
  }

  function aplicarFiltro() {
    escena.classList.toggle("solo-mant", filtro === "mant" && actual?.partes.some((p) => p.tarea));
  }
  document.querySelectorAll("[data-filtro]").forEach((b) => {
    b.addEventListener("click", () => {
      filtro = b.dataset.filtro;
      document.querySelectorAll("[data-filtro]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      aplicarFiltro();
    });
  });

  // ---------------- Lista y búsqueda ----------------
  function pintarLista() {
    const q = buscar.value.trim().toLowerCase();
    lista.innerHTML = "";
    const vistas = new Set();
    const ordenadas = actual.partes.slice().sort((a, b) => (b.tarea ? 1 : 0) - (a.tarea ? 1 : 0) || peso(b.estado) - peso(a.estado) || a.ref - b.ref);
    let hayMant = false;
    let separador = false;
    for (const p of ordenadas) {
      if (vistas.has(p.ref)) continue; // el catálogo repite referencias (lado derecho e izquierdo)
      if (q && !`${p.nombre} ${p.descripcion} ${p.codigo} ${p.ref}`.toLowerCase().includes(q)) continue;
      vistas.add(p.ref);
      if (p.tarea) hayMant = true;
      if (!p.tarea && hayMant && !separador) {
        lista.appendChild(el("li", "partes-separador", "Otras piezas"));
        separador = true;
      }
      const li = el("li");
      const b = el("button", "parte-fila");
      b.type = "button";
      b.dataset.id = p.id;
      b.append(el("span", "parte-ref", String(p.ref)), el("span", "parte-nombre", p.nombre));
      if (p.estado) b.appendChild(el("span", `punto-mini punto-${p.estado}`));
      b.addEventListener("click", () => { elegir(p); enfocar(p); });
      li.appendChild(b);
      lista.appendChild(li);
    }
    if (!lista.children.length) lista.appendChild(el("li", "text-sm text-suave px-2 py-3", "No encontramos esa pieza en este sistema."));
    marcarElegida();
  }
  buscar.addEventListener("input", pintarLista);

  // ---------------- Ficha de la pieza ----------------
  function marcarElegida() {
    if (!elegida) return;
    escena.querySelectorAll(".punto").forEach((p) => p.classList.toggle("elegido", p.dataset.id == elegida.id));
    lista.querySelectorAll(".parte-fila").forEach((f) => f.classList.toggle("elegida", f.dataset.id == elegida.id));
  }

  function elegir(parte) {
    if (!parte) return;
    elegida = parte;
    marcarElegida();
    ficha.innerHTML = "";

    const cabeza = el("div", "flex items-start justify-between gap-3");
    const titulo = el("div", "min-w-0");
    titulo.append(el("p", "text-xs text-suave", `Pieza ${parte.ref} del dibujo`), el("p", "titulo text-2xl leading-tight mt-1", parte.nombre));
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
    }

    const codigo = el("div", "codigo-repuesto");
    const izq = el("div");
    izq.append(el("span", "codigo-etiqueta", "Código de repuesto original"), el("strong", "", parte.codigo));
    if (parte.cantidad > 1) izq.appendChild(el("span", "codigo-etiqueta", `Lleva ${parte.cantidad} unidades`));
    const copiar = el("button", "codigo-copiar", "Copiar");
    copiar.type = "button";
    copiar.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(parte.codigo); copiar.textContent = "¡Copiado!"; }
      catch { copiar.textContent = "No se pudo"; }
      setTimeout(() => { copiar.textContent = "Copiar"; }, 1800);
    });
    codigo.append(izq, copiar);
    ficha.appendChild(codigo);

    const acciones = el("div", "flex flex-wrap gap-2 mt-4");
    const mensaje = `Hola, necesito el repuesto ${parte.codigo} (${parte.nombre}) para mi ${datos.moto}. ¿Lo tienen?`;
    const wa = el("a", "btn btn-whatsapp text-[.65rem] px-4 py-2.5", "Pedir este repuesto");
    wa.href = `https://wa.me/?text=${encodeURIComponent(mensaje)}`;
    wa.target = "_blank";
    wa.rel = "noopener";
    acciones.appendChild(wa);
    if (parte.tarea?.servicio) {
      const talleres = el("a", "btn btn-borde text-[.65rem] px-4 py-2.5", "Talleres que lo hacen");
      talleres.href = `/?servicio=${parte.tarea.servicio}`;
      acciones.appendChild(talleres);
    }
    ficha.appendChild(acciones);
  }

  // ---------------- Puente con el modelo 3D ----------------
  window.TallerYaDespiece = {
    tiene: (pieza) => laminas.some((l) => l.pieza === pieza),
    mostrar(pieza) {
      const lamina = laminas.find((l) => l.pieza === pieza);
      if (!lamina) return;
      mostrar(lamina);
      $("despiece").scrollIntoView({ behavior: reducido ? "auto" : "smooth", block: "start" });
    },
  };

  if (laminas.length) mostrar(laminas[0]);
})();
