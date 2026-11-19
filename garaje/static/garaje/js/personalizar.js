// Cajón "Personaliza tu moto": pintura, rines y calcas que se pegan tocando la moto, con vista previa en vivo.
(function () {
  const nodo = document.getElementById("datos-personalizacion");
  if (!nodo) return;
  const datos = JSON.parse(nodo.textContent);
  const $ = (id) => document.getElementById(id);
  const MAX_CALCAS = 4;
  const CON_TEXTO = { numero: 3, texto: 14 };
  const COLORES_CALCA = [["#ffffff", "Blanco"], ["#14181a", "Negro"], ["#f2611d", "Naranja"], ["#e3a72f", "Amarillo"],
    ["#c62828", "Rojo"], ["#1f4fa8", "Azul"], ["#c0c4c8", "Plata"]];

  const cajon = $("personalizar");
  const abrir = $("abrir-personalizar");
  let cfg = null;
  let guardado = null;
  let sel = -1;          // calca que se está editando
  let colocando = null;  // diseño esperando el toque sobre la moto
  let imagenPendiente = ""; // imagen propia elegida, esperando el toque sobre la moto
  const MAX_IMAGEN = 190000; // caracteres del data URL (~140 KB): el servidor rechaza más
  const ICONO_SUBIR = "data:image/svg+xml," + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 32"><g fill="none" stroke="#f2611d" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><rect x="20" y="4" width="24" height="24" rx="4"/><path d="M32 22V11M27 15l5-5 5 5"/></g></svg>');
  const miniaturaDe = (c) => (c.diseno === "imagen" ? c.imagen : window.TallerYa3D.miniatura(c.diseno, c.color, c.texto));
  // Reduce la imagen a 256 px como máximo (PNG para conservar la transparencia; JPEG si así queda muy pesada)
  function reducirImagen(archivo) {
    return new Promise((resolver, fallar) => {
      const img = new Image();
      img.onload = () => {
        const k = Math.min(1, 256 / Math.max(img.width, img.height));
        const c = document.createElement("canvas");
        c.width = Math.max(1, Math.round(img.width * k));
        c.height = Math.max(1, Math.round(img.height * k));
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(img.src);
        let url = c.toDataURL("image/png");
        if (url.length > MAX_IMAGEN) url = c.toDataURL("image/jpeg", 0.85);
        if (url.length > MAX_IMAGEN) url = c.toDataURL("image/jpeg", 0.6);
        if (url.length > MAX_IMAGEN) fallar(new Error("La imagen es muy pesada. Prueba con otra más sencilla."));
        else resolver(url);
      };
      img.onerror = () => fallar(new Error("No pudimos leer esa imagen. Usa un PNG o JPG."));
      img.src = URL.createObjectURL(archivo);
    });
  }
  const selectorImagen = Object.assign(document.createElement("input"), { type: "file", accept: "image/png,image/jpeg,image/webp", hidden: true });
  document.body.appendChild(selectorImagen);
  selectorImagen.addEventListener("change", async () => {
    const archivo = selectorImagen.files[0];
    selectorImagen.value = "";
    if (!archivo) return;
    try {
      imagenPendiente = await reducirImagen(archivo);
    } catch (e) {
      $("p-estado").textContent = e.message;
      return;
    }
    colocando = "imagen";
    window.TallerYa3D.verMoto();
    window.TallerYa3D.colocar("imagen");
    $("visor-colocar").hidden = false;
    pintarCatalogo();
  });

  const copiar = (o) => JSON.parse(JSON.stringify(o));
  function el(etiqueta, clase, texto) {
    const n = document.createElement(etiqueta);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }
  const claridad = (hex) => {
    const n = parseInt(hex.slice(1), 16);
    return (0.299 * (n >> 16) + 0.587 * ((n >> 8) & 255) + 0.114 * (n & 255)) / 255;
  };

  // ---------- Historial: "Atrás" quita el último cambio; "Deshacer todo" vuelve a lo guardado ----------
  const historial = [];
  function guardarPaso() {
    const foto = JSON.stringify(cfg);
    if (historial[historial.length - 1] !== foto) historial.push(foto);
    if (historial.length > 50) historial.shift();
  }
  // Un arrastre (color, tamaño, giro) o una palabra escrita cuenta como un solo paso.
  function gesto(campo, alCambiar) {
    let activo = false;
    campo.addEventListener("input", (e) => {
      if (!activo) { guardarPaso(); activo = true; }
      alCambiar(e);
    });
    campo.addEventListener("change", () => { activo = false; });
  }

  let pendiente = false;
  function aplicar() {
    if (!window.TallerYa3D) return;
    if (!pendiente) {
      pendiente = true;
      requestAnimationFrame(() => { pendiente = false; window.TallerYa3D.aplicar(cfg); });
    }
    const cambios = JSON.stringify(cfg) !== JSON.stringify(guardado);
    $("p-estado").textContent = cambios ? "Tienes cambios sin guardar." : "";
    $("p-estado").classList.toggle("sin-guardar", cambios);
    $("p-guardar").disabled = !cambios;
    $("p-deshacer").disabled = !cambios;
    $("p-atras").disabled = historial.length === 0;
    document.querySelectorAll("#personalizar [data-quitar]").forEach((b) => { b.hidden = !cfg.estilo?.[b.dataset.quitar]; });
  }

  // ---------- Pestañas ----------
  function pestana(cual) {
    ["pintura", "estilo", "calcas"].forEach((n) => {
      $(`tab-${n}`).setAttribute("aria-selected", String(n === cual));
      $(`panel-${n}`).hidden = n !== cual;
    });
    if (cual !== "calcas") cancelarColocar();
    window.TallerYa3D?.resaltar(enCalcas() ? sel : -1);
  }
  // (las calcas propias solo se editan con su subpestaña "Personalizadas" a la vista)
  const enCalcas = () => !$("panel-calcas").hidden && !$("sub-panel-propias").hidden;
  $("tab-pintura").addEventListener("click", () => pestana("pintura"));
  $("tab-calcas").addEventListener("click", () => pestana("calcas"));
  $("tab-estilo").addEventListener("click", () => pestana("estilo"));

  // ---------- Calcas: subpestañas "De fábrica" y "Personalizadas" ----------
  function subpestana(cual) {
    [["fabrica", "sub-fabrica"], ["propias", "sub-propias"]].forEach(([n, id]) => {
      $(id).setAttribute("aria-selected", String(n === cual));
      $(id).setAttribute("aria-pressed", String(n === cual));
      $(`sub-panel-${n}`).hidden = n !== cual;
    });
    if (cual !== "propias") cancelarColocar();
    window.TallerYa3D?.resaltar(enCalcas() ? sel : -1);
  }
  $("sub-fabrica").addEventListener("click", () => subpestana("fabrica"));
  $("sub-propias").addEventListener("click", () => subpestana("propias"));

  // De fábrica: cada calca de serie se quita o se vuelve a poner; lo quitado se guarda en estilo.sin_fabrica
  function ponerQuitadas(lista) {
    if (lista.length) estilo().sin_fabrica = [...new Set(lista)].sort();
    else if (cfg.estilo) delete cfg.estilo.sin_fabrica;
  }
  function pintarFabrica() {
    const lista = window.TallerYa3D?.calcasFabrica?.() || [];
    const caja = $("p-fabrica");
    caja.innerHTML = "";
    const quitadas = new Set(cfg.estilo?.sin_fabrica || []);
    $("p-fabrica-restaurar").hidden = !lista.length;
    $("p-fabrica-restaurar").disabled = !lista.some((c) => quitadas.has(c.id));
    if (!lista.length) { caja.append(el("p", "cajon-ayuda", "Esta moto no trae calcas de fábrica.")); return; }
    for (const c of lista) {
      const fila = el("div", "calca-fabrica-fila");
      fila.style.cssText = "display:flex;align-items:center;justify-content:space-between;gap:.5rem";
      const etiqueta = el("label", "calca-interruptor");
      const casilla = el("input");
      casilla.type = "checkbox";
      casilla.checked = !quitadas.has(c.id);
      casilla.addEventListener("change", () => {
        guardarPaso();
        const resto = (cfg.estilo?.sin_fabrica || []).filter((id) => id !== c.id);
        ponerQuitadas(casilla.checked ? resto : [...resto, c.id]);
        pintarFabrica();
        aplicar();
      });
      etiqueta.append(casilla, el("span", "", c.nombre));
      const color = el("button", "boton-suave text-xs", "Color");
      color.type = "button";
      color.setAttribute("aria-pressed", String(selFab === c.id));
      color.setAttribute("aria-label", `Cambiar el color: ${c.nombre}`);
      color.addEventListener("click", () => { selFab = selFab === c.id ? null : c.id; pintarFabrica(); });
      fila.append(etiqueta, color);
      caja.append(fila);
    }
    pintarEditorFabrica(lista);
  }
  // Editor de color de una calca de fábrica: principal y secundario (estilo.color_fabrica) y "Color original"
  let selFab = null;
  const fabActual = () => (window.TallerYa3D?.calcasFabrica?.() || []).find((c) => c.id === selFab);
  const colorFab = (slot) => cfg.estilo?.color_fabrica?.[selFab]?.[slot] || fabActual()?.original[slot] || "#ffffff";
  function ponerColorFab(slot, hex) {
    const todos = estilo().color_fabrica ??= {};
    const propio = (todos[selFab] ??= {});
    if (hex.toLowerCase() === (fabActual()?.original[slot] || "").toLowerCase()) delete propio[slot]; else propio[slot] = hex.toLowerCase();
    if (!Object.keys(propio).length) delete todos[selFab];
    if (!Object.keys(todos).length) delete cfg.estilo.color_fabrica;
    $("p-fab-original").disabled = !cfg.estilo?.color_fabrica?.[selFab];
  }
  let filaFab1 = null, filaFab2 = null; // (se crean al abrir el editor: filaDeColor usa variables de más abajo)
  function pintarEditorFabrica(lista) {
    const c = lista.find((x) => x.id === selFab);
    $("p-fab-editor").hidden = !c;
    if (!c) return;
    $("p-fab-nombre").textContent = c.nombre;
    $("p-fab-original").disabled = !cfg.estilo?.color_fabrica?.[selFab];
    filaFab1 ??= filaDeColor($("p-fab-color1"), COLORES_CALCA, () => colorFab("p"), (hex) => ponerColorFab("p", hex));
    filaFab2 ??= filaDeColor($("p-fab-color2"), COLORES_CALCA, () => colorFab("s"), (hex) => ponerColorFab("s", hex));
    filaFab1.pintar();
    filaFab2.pintar();
  }
  $("p-fab-original").addEventListener("click", () => {
    if (!cfg.estilo?.color_fabrica?.[selFab]) return;
    guardarPaso();
    delete cfg.estilo.color_fabrica[selFab];
    if (!Object.keys(cfg.estilo.color_fabrica).length) delete cfg.estilo.color_fabrica;
    pintarFabrica();
    aplicar();
  });
  $("p-fabrica-restaurar").addEventListener("click", () => {
    guardarPaso();
    ponerQuitadas([]);
    pintarFabrica();
    aplicar();
  });

  // ---------- Colores: muestras con un botón arcoíris al final que abre un selector propio ----------
  function hsvAHex({ h, s, v }) {
    const f = (n) => { const k = (n + h / 60) % 6; return v - v * s * Math.max(Math.min(k, 4 - k, 1), 0); };
    return "#" + [f(5), f(3), f(1)].map((x) => Math.round(x * 255).toString(16).padStart(2, "0")).join("");
  }
  function hexAHsv(hex) {
    const n = parseInt(hex.slice(1), 16);
    const r = (n >> 16) / 255, g = ((n >> 8) & 255) / 255, b = (n & 255) / 255;
    const max = Math.max(r, g, b), d = max - Math.min(r, g, b);
    let h = 0;
    if (d) h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return { h: (h * 60 + 360) % 360, s: max ? d / max : 0, v: max };
  }

  let serieColor = 0;
  function filaDeColor(contenedor, colores, obtener, poner) {
    const id = `selector-color-${++serieColor}`;
    const panel = el("div", "selector-color");
    panel.id = id;
    panel.hidden = true;
    const sv = el("div", "selector-sv");
    sv.tabIndex = 0;
    sv.setAttribute("role", "slider");
    sv.setAttribute("aria-label", "Saturación y brillo");
    const perilla = el("span", "selector-sv-perilla");
    sv.appendChild(perilla);
    const tono = el("input", "selector-tono");
    Object.assign(tono, { type: "range", min: "0", max: "360", step: "1" });
    tono.setAttribute("aria-label", "Tono");
    const etiquetaHex = el("label", "selector-hex");
    const campoHex = el("input");
    Object.assign(campoHex, { type: "text", maxLength: 7, spellcheck: false, autocomplete: "off", placeholder: "#F2611D" });
    etiquetaHex.append(el("span", "", "Código"), campoHex);
    const error = el("p", "campo-error", "Usa el formato #RRGGBB, por ejemplo #F2611D.");
    error.hidden = true;
    panel.append(sv, tono, etiquetaHex, error);
    contenedor.after(panel);

    const hsv = { h: 20, s: 0.9, v: 0.95 };
    let arcoiris = null;

    function marcarTodo() {
      const actual = obtener().toLowerCase();
      let enLista = false;
      contenedor.querySelectorAll(".muestra-color:not(.muestra-propia)").forEach((b) => {
        const si = b.dataset.color === actual;
        if (si) enLista = true;
        b.setAttribute("aria-pressed", String(si));
      });
      // Si el color no es de la lista, el botón arcoíris lo muestra en el centro y queda marcado.
      arcoiris.setAttribute("aria-pressed", String(!enLista));
      arcoiris.style.setProperty("--propio", enLista ? "var(--c-tarjeta, #20272a)" : actual);
    }
    function pintarSelector() {
      sv.style.setProperty("--tono", hsv.h);
      perilla.style.left = `${hsv.s * 100}%`;
      perilla.style.top = `${(1 - hsv.v) * 100}%`;
      sv.setAttribute("aria-valuetext", `Saturación ${Math.round(hsv.s * 100)}%, brillo ${Math.round(hsv.v * 100)}%`);
      tono.value = String(Math.round(hsv.h));
    }
    function sincronizar() {
      Object.assign(hsv, hexAHsv(obtener()));
      pintarSelector();
      campoHex.value = obtener().toUpperCase();
      error.hidden = true;
    }
    function desdeSelector() {
      poner(hsvAHex(hsv));
      pintarSelector();
      campoHex.value = obtener().toUpperCase();
      marcarTodo();
      aplicar();
    }
    function pintar() {
      contenedor.innerHTML = "";
      colores.forEach(([hex, nombre, fondo]) => {
        const b = el("button", "muestra-color");
        b.type = "button";
        b.style.background = fondo || hex; // ("De fábrica" guarda un valor y se pinta con el color que da en este modelo)
        b.dataset.color = hex.toLowerCase();
        b.title = nombre;
        b.setAttribute("aria-label", nombre);
        b.addEventListener("click", () => { guardarPaso(); poner(hex); sincronizar(); marcarTodo(); aplicar(); });
        contenedor.appendChild(b);
      });
      arcoiris = el("button", "muestra-color muestra-propia");
      arcoiris.type = "button";
      arcoiris.title = "Crear mi propio color";
      arcoiris.setAttribute("aria-label", "Crear mi propio color");
      arcoiris.setAttribute("aria-controls", id);
      arcoiris.setAttribute("aria-expanded", String(!panel.hidden));
      arcoiris.addEventListener("click", () => {
        panel.hidden = !panel.hidden;
        arcoiris.setAttribute("aria-expanded", String(!panel.hidden));
        if (!panel.hidden) sincronizar();
      });
      contenedor.appendChild(arcoiris);
      marcarTodo();
      sincronizar();
    }

    let arrastre = false;
    function moverSV(e) {
      const r = sv.getBoundingClientRect();
      hsv.s = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
      hsv.v = 1 - Math.min(1, Math.max(0, (e.clientY - r.top) / r.height));
      desdeSelector();
    }
    sv.addEventListener("pointerdown", (e) => { guardarPaso(); arrastre = true; sv.setPointerCapture(e.pointerId); moverSV(e); });
    sv.addEventListener("pointermove", (e) => { if (arrastre) moverSV(e); });
    sv.addEventListener("pointerup", () => { arrastre = false; });
    sv.addEventListener("keydown", (e) => {
      const paso = e.shiftKey ? 0.1 : 0.02;
      const mov = { ArrowLeft: ["s", -paso], ArrowRight: ["s", paso], ArrowUp: ["v", paso], ArrowDown: ["v", -paso] }[e.key];
      if (!mov) return;
      e.preventDefault();
      guardarPaso();
      hsv[mov[0]] = Math.min(1, Math.max(0, hsv[mov[0]] + mov[1]));
      desdeSelector();
    });
    gesto(tono, () => { hsv.h = Number(tono.value); desdeSelector(); });
    campoHex.addEventListener("input", () => { error.hidden = true; });
    campoHex.addEventListener("change", () => {
      let v = campoHex.value.trim();
      if (!v.startsWith("#")) v = `#${v}`;
      if (!/^#[0-9a-f]{6}$/i.test(v)) { error.hidden = false; return; }
      guardarPaso();
      poner(v.toLowerCase());
      sincronizar();
      marcarTodo();
      aplicar();
    });
    return { pintar, cerrar() { panel.hidden = true; arcoiris?.setAttribute("aria-expanded", "false"); } };
  }

  const filaPintura = filaDeColor($("p-color"), datos.colores, () => cfg.color, (c) => { cfg.color = c; refrescarAcabados(); });
  const coloresRines = [...datos.secundarios];
  const filaRines = filaDeColor($("p-secundario"), coloresRines, () => cfg.color_secundario, (c) => { cfg.color_secundario = c; });
  // Muestras "De fábrica" según el modelo que muestra el visor y su estilo de rin (se arman al conectar el 3D y al
  // cambiar de rin). Rines: el secundario de serie es la muestra "De fábrica", pintada como se ven los rines de serie
  // con ese estilo (naranja en la Duke, aro plateado en los de radios…), y el negro es otra muestra (#15181a). Así un
  // color elegido —negro incluido— nunca es el de serie y se conserva en cualquier estilo de rin.
  function coloresDeFabrica() {
    const op = window.TallerYa3D?.opciones?.(estilo()) || {};
    const serie = (op.secundarioFabrica || "#1c2022").toLowerCase();
    coloresRines.splice(0, coloresRines.length, [serie, "De fábrica", op.colorRinFabrica || serie], ["#15181a", "Negro"],
      ...datos.secundarios.filter(([hex]) => hex.toLowerCase() !== serie));
    if (chasisFabrica) COLORES_CHASIS.shift();
    chasisFabrica = op.colorChasisFabrica || null;
    if (chasisFabrica) COLORES_CHASIS.unshift([chasisFabrica, "De fábrica"]);
  }
  // ---------- Estilo: acabado, segundo tono, chasis, asiento, rines y accesorios ----------
  const ACABADOS = [["brillante", "Brillante"], ["mate", "Mate"], ["satinado", "Satinado"], ["metalizado", "Metalizado"], ["perlado", "Perlado"]];
  const NOMBRE_RIN = { radios: "Radios", aleacion: "Aleación", estrella: "Deportivo" };
  const RINES = [["fabrica", "De fábrica"], ["radios", "Radios"], ["aleacion", "Aleación"], ["estrella", "Deportivo"]];
  const ACCESORIOS = { baul: "Baúl", cubremanos: "Cubremanos", parabrisas: "Parabrisas alto", exploradoras: "Exploradoras", sliders: "Sliders",
    escape: "Escape deportivo", protector: "Protector de motor", led: "Luz LED" };
  const ESPEJOS = [["fabrica", "De fábrica"], ["redondos", "Redondos"], ["puntas", "En la punta"]];
  const COLORES_LED = [["#22d3ee", "Cian"], ["#a855f7", "Morado"], ["#ef4444", "Rojo"], ["#22c55e", "Verde"], ["#3b82f6", "Azul"],
    ["#f59e0b", "Ámbar"], ["#f4f4f2", "Blanco"]];
  // Íconos de línea (24×24) para las tarjetas
  const svg = (trazos) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${trazos}</svg>`;
  const rayos = (n, curvo) => Array.from({ length: n }, (_, k) => {
    const a = (k / n) * Math.PI * 2, x = 12 + Math.cos(a) * 8.2, y = 12 + Math.sin(a) * 8.2;
    if (!curvo) return `<path d="M12 12L${x.toFixed(1)} ${y.toFixed(1)}"/>`;
    const b = a + 0.5, cx = 12 + Math.cos(b) * 5, cy = 12 + Math.sin(b) * 5;
    return `<path d="M${(12 + Math.cos(a) * 2.6).toFixed(1)} ${(12 + Math.sin(a) * 2.6).toFixed(1)}Q${cx.toFixed(1)} ${cy.toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)}"/>`;
  }).join("");
  const ICONO_RIN = {
    radios: svg(`<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="1.6"/>${rayos(16, false).replaceAll("<path", '<path stroke-width=".8"')}`),
    aleacion: svg(`<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="2.6"/>${rayos(5, true).replaceAll("<path", '<path stroke-width="2.4"')}`),
    estrella: svg(`<circle cx="12" cy="12" r="9.5"/><circle cx="12" cy="12" r="2.2"/>${rayos(7, false).replaceAll("<path", '<path stroke-width="2.2"')}`),
  };
  const ICONO_ACCESORIO = {
    baul: svg('<rect x="4" y="7" width="16" height="12" rx="3"/><path d="M4 12h16M10 15h4"/>'),
    cubremanos: svg('<path d="M4 15c0-5 4-8 9-8h3a4 4 0 0 1 0 8H8"/><path d="M8 11h7"/>'),
    parabrisas: svg('<path d="M7 20 5 6c3-2 11-2 14 0l-2 14"/><path d="M8 9c2.5-.8 5.5-.8 8 0"/>'),
    exploradoras: svg('<circle cx="7" cy="13" r="3.2"/><circle cx="17" cy="13" r="3.2"/><path d="M7 6v2M17 6v2M3.5 9.5l1.4 1M20.5 9.5l-1.4 1"/>'),
    sliders: svg('<path d="M3 12h7"/><rect x="10" y="7" width="6" height="10" rx="2"/><path d="M16 9.5h3a2.5 2.5 0 0 1 0 5h-3"/>'),
    escape: svg('<path d="M3 16h5l3-3"/><path d="m10 14 8-6 3 3-8 6z"/><path d="M19.5 9.5l1.5-1.5"/>'),
    protector: svg('<path d="M3 9h18l-2 6H5z"/><path d="M7 12h10"/><circle cx="12" cy="6" r="2"/>'),
    led: svg('<path d="M3 15h18"/><path d="M6 19l1-2M12 20v-2M18 19l-1-2"/><path d="M5 11a7 7 0 0 1 14 0"/>'),
  };
  const COLORES_CHASIS = [["#23282b", "Negro"], ["#b8bec2", "Plata"], ["#f4f4f2", "Blanco"], ["#c62828", "Rojo"], ["#f2611d", "Naranja"],
    ["#e3a72f", "Dorado"], ["#1f4fa8", "Azul"], ["#2f6b3a", "Verde"]];
  const COLORES_ASIENTO = [["#161819", "Negro"], ["#4a4f52", "Gris"], ["#5a3b24", "Café"], ["#b59a74", "Beige"], ["#7a1f1a", "Vino"],
    ["#1d2f55", "Azul"], ["#c62828", "Rojo"]];
  const estilo = () => (cfg.estilo ??= {});
  const filaTono = filaDeColor($("p-color2"), datos.colores, () => estilo().color2 || cfg.color, (c) => { estilo().color2 = c; });
  // Chasis: si la moto lo trae a la vista (naked), la primera muestra es "De fábrica" (su color de serie) y es la que
  // queda marcada mientras no se elija otro; elegirla quita el color propio. Ver coloresDeFabrica().
  let chasisFabrica = null;
  const filaChasis = filaDeColor($("p-chasis"), COLORES_CHASIS, () => estilo().chasis || chasisFabrica || "#23282b",
    (c) => { if (c === chasisFabrica) delete estilo().chasis; else estilo().chasis = c; });
  const filaAsiento = filaDeColor($("p-asiento"), COLORES_ASIENTO, () => estilo().asiento || "#161819", (c) => { estilo().asiento = c; });
  const filaLed = filaDeColor($("p-led"), COLORES_LED, () => estilo().led || "#22d3ee", (c) => { estilo().led = c; });
  // Íconos de los retrovisores (vistos de frente, con el manubrio)
  const ICONO_ESPEJOS = {
    // Vistos desde el puesto del conductor: manubrio con sus puños y la luna de cada espejo rellena
    fabrica: svg('<path d="M5 18h14"/><path d="M3 18h2M19 18h2" stroke-width="3"/><path d="M8 18 6 11M16 18l2-7"/>'
      + '<path d="M2.5 9.2c0-1.6 1.6-2.7 3.5-2.7s3.5 1.1 3.5 2.4-1.6 2.3-3.5 2.3-3.5-.6-3.5-2z" fill="currentColor" fill-opacity=".3"/>'
      + '<path d="M21.5 9.2c0-1.6-1.6-2.7-3.5-2.7s-3.5 1.1-3.5 2.4 1.6 2.3 3.5 2.3 3.5-.6 3.5-2z" fill="currentColor" fill-opacity=".3"/>'),
    redondos: svg('<path d="M5 19h14"/><path d="M3 19h2M19 19h2" stroke-width="3"/><path d="M7.5 19V9.5M16.5 19V9.5"/>'
      + '<circle cx="7.5" cy="6.5" r="3" fill="currentColor" fill-opacity=".3"/><circle cx="16.5" cy="6.5" r="3" fill="currentColor" fill-opacity=".3"/>'),
    puntas: svg('<path d="M6 10h12"/><path d="M4 10h2M18 10h2" stroke-width="3"/><path d="M3.5 10.5v2M20.5 10.5v2"/>'
      + '<rect x="1" y="12.5" width="5" height="6.5" rx="2.4" fill="currentColor" fill-opacity=".3"/>'
      + '<rect x="18" y="12.5" width="5" height="6.5" rx="2.4" fill="currentColor" fill-opacity=".3"/>'),
  };

  document.querySelectorAll("#personalizar [data-quitar]").forEach((b) => b.addEventListener("click", () => {
    guardarPaso();
    delete estilo()[b.dataset.quitar];
    pintarColores();
    aplicar();
  }));
  // Dos tonos: al prenderlo propone un color que contraste (negro o blanco) y muestra la paleta
  $("p-dos-tonos").addEventListener("change", (e) => {
    guardarPaso();
    if (e.target.checked) estilo().color2 = claridad(cfg.color) > 0.5 ? "#14181a" : "#f4f4f2";
    else delete estilo().color2;
    pintarColores();
    aplicar();
  });
  $("p-mas-colores").addEventListener("click", () => {
    const abrir = $("p-caja-zonas").hidden;
    $("p-caja-zonas").hidden = !abrir;
    $("p-mas-colores").setAttribute("aria-expanded", String(abrir));
  });

  // Tarjetas: [valor, nombre, contenido visual (HTML), detalle opcional]
  function tarjetas(contenedor, opciones, activo, alElegir, multiple = false) {
    contenedor.replaceChildren(...opciones.map(([valor, nombre, visual, detalle]) => {
      const b = el("button", "tarjeta-opcion");
      b.type = "button";
      b.dataset.valor = valor;
      if (multiple) b.setAttribute("aria-pressed", String(activo(valor)));
      else { b.setAttribute("role", "radio"); b.setAttribute("aria-checked", String(activo(valor))); }
      b.innerHTML = `<span class="tarjeta-visual">${visual}</span><span class="tarjeta-nombre"></span>${detalle ? '<span class="tarjeta-detalle"></span>' : ""}`
        + (multiple ? '<span class="tarjeta-marca" aria-hidden="true"></span>' : "");
      b.querySelector(".tarjeta-nombre").textContent = nombre;
      if (detalle) b.querySelector(".tarjeta-detalle").textContent = detalle;
      b.addEventListener("click", () => { guardarPaso(); alElegir(valor); pintarEstilo(); aplicar(); });
      return b;
    }));
  }
  // Esfera de muestra de cada acabado, dibujada por el visor 3D con el material real
  const vistaAcabado = (acabado, color) => window.TallerYa3D?.vistaAcabado?.(acabado, color) || "";
  // Las esferas se dibujan solo cuando hacen falta (cajón abierto o por abrirse): la primera vez el visor crea un
  // segundo renderizador y compila los sombreadores del material físico de cada acabado, y eso, hecho al cargar la
  // página con el cajón cerrado, la congelaba de 3 a 6 s en la primera visita (y atrasaba el esquema del despiece).
  // Se dibuja una esfera por cuadro para no trabar la página de un solo golpe.
  let acabadosQuieren = false;
  let refrescoAcabados = 0;
  const VACIA = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==";
  function refrescarAcabados() {
    // Al arrastrar el selector de color llegan muchos cambios seguidos: se redibuja una vez por cuadro
    cancelAnimationFrame(refrescoAcabados);
    if (!acabadosQuieren) return;
    const pendientes = [...document.querySelectorAll("#p-acabado img[data-acabado]")];
    const siguiente = () => {
      const img = pendientes.shift();
      if (!img) return;
      const url = vistaAcabado(img.dataset.acabado, cfg.color);
      if (url) img.src = url;
      refrescoAcabados = requestAnimationFrame(siguiente);
    };
    refrescoAcabados = requestAnimationFrame(siguiente);
  }
  function quererAcabados() {
    if (acabadosQuieren) return;
    acabadosQuieren = true;
    refrescarAcabados();
  }
  function pintarEstilo() {
    const op = window.TallerYa3D?.opciones?.() || { accesorios: Object.keys(ACCESORIOS), rinFabrica: "aleacion" };
    const fondo = cfg.color;
    tarjetas($("p-acabado"), ACABADOS.map(([v, n]) => [v, n, `<img class="muestra-acabado" alt="" data-acabado="${v}" src="${VACIA}">`]),
      (v) => (estilo().acabado || "brillante") === v,
      (v) => { if (v === "brillante") delete estilo().acabado; else estilo().acabado = v; });
    refrescarAcabados();
    tarjetas($("p-rin"), RINES.map(([v, n]) => [v, n, ICONO_RIN[v === "fabrica" ? op.rinFabrica : v],
      v === "fabrica" ? NOMBRE_RIN[op.rinFabrica] : ""]),
      (v) => (estilo().rin || "fabrica") === v,
      (v) => {
        if (v === "fabrica") delete estilo().rin; else estilo().rin = v;
        // (la muestra "De fábrica" de Rines y detalles cambia con el estilo: radios de serie = aro plateado)
        coloresDeFabrica();
        filaRines.pintar();
      });
    tarjetas($("p-accesorios"), op.accesorios.map((id) => [id, ACCESORIOS[id] || id, ICONO_ACCESORIO[id] || ""]),
      (v) => (estilo().accesorios || []).includes(v),
      (v) => {
        const lista = new Set(estilo().accesorios || []);
        if (lista.has(v)) lista.delete(v); else lista.add(v);
        if (lista.size) estilo().accesorios = [...lista].sort(); else delete estilo().accesorios;
      }, true);
    tarjetas($("p-espejos"), ESPEJOS.map(([v, n]) => [v, n, ICONO_ESPEJOS[v]]),
      (v) => (estilo().espejos || "fabrica") === v,
      (v) => { if (v === "fabrica") delete estilo().espejos; else estilo().espejos = v; });
    // El color del LED solo aparece con la luz LED puesta
    $("p-caja-led").hidden = !(estilo().accesorios || []).includes("led");
    const dos = Boolean(estilo().color2);
    $("p-dos-tonos").checked = dos;
    $("p-caja-tono").hidden = !dos;
    // Si ya tiene chasis o asiento propios, el desplegable arranca abierto
    if (estilo().chasis || estilo().asiento) { $("p-caja-zonas").hidden = false; $("p-mas-colores").setAttribute("aria-expanded", "true"); }
  }

  function pintarColores() {
    coloresDeFabrica(); // (también al deshacer: el estilo de rin pudo cambiar)
    filaPintura.pintar();
    filaRines.pintar();
    filaTono.pintar();
    filaChasis.pintar();
    filaAsiento.pintar();
    filaLed.pintar();
    pintarEstilo();
  }

  // ---------- Calcas: catálogo y colocación con un toque ----------
  function pintarCatalogo() {
    const cont = $("p-catalogo");
    cont.innerHTML = "";
    const lleno = cfg.calcas.length >= MAX_CALCAS;
    $("p-contador").textContent = `${cfg.calcas.length}/${MAX_CALCAS}`;
    $("p-contador").classList.toggle("lleno", lleno);
    $("p-limite").hidden = !lleno;
    cont.classList.toggle("lleno", lleno);
    Object.entries(datos.disenos).forEach(([clave, nombre]) => {
      const b = el("button", "calca-opcion");
      b.type = "button";
      const img = el("img");
      img.src = clave === "imagen" ? ICONO_SUBIR : window.TallerYa3D.miniatura(clave, "#f2611d", "");
      img.alt = "";
      b.append(img, el("span", "", nombre.replace(" de carreras", "")));
      b.setAttribute("aria-pressed", String(colocando === clave));
      b.disabled = lleno;
      if (lleno) b.title = "Llegaste al máximo de 4 calcas";
      b.addEventListener("click", () => {
        if (cfg.calcas.length >= MAX_CALCAS) return;
        // Imagen propia: primero se elige el archivo; al cargar queda lista para tocar la moto
        if (clave === "imagen" && colocando !== "imagen") { selectorImagen.click(); return; }
        colocando = colocando === clave ? null : clave;
        window.TallerYa3D.verMoto();
        window.TallerYa3D.colocar(colocando);
        $("visor-colocar").hidden = !colocando;
        pintarCatalogo();
      });
      cont.appendChild(b);
    });
  }
  function cancelarColocar() {
    if (!colocando) return;
    colocando = null;
    window.TallerYa3D?.colocar(null);
    $("visor-colocar").hidden = true;
    pintarCatalogo();
  }

  function elegir(i) {
    sel = i;
    pintarPuestas();
    pintarEditor();
    window.TallerYa3D.resaltar(enCalcas() ? sel : -1);
  }

  function pintarPuestas() {
    const cont = $("p-puestas");
    cont.innerHTML = "";
    cfg.calcas.forEach((c, i) => {
      const b = el("button", "calca-ficha");
      b.type = "button";
      b.setAttribute("role", "option");
      b.setAttribute("aria-selected", String(i === sel));
      const img = el("img");
      img.src = miniaturaDe(c);
      img.alt = "";
      b.append(img, el("span", "", datos.disenos[c.diseno].replace(" de carreras", "")));
      b.addEventListener("click", () => elegir(i));
      cont.appendChild(b);
    });
  }

  // ---------- Editor de la calca elegida ----------
  const ed = { tamano: $("p-ed-tamano"), giro: $("p-ed-giro"), texto: $("p-ed-texto"), ambos: $("p-ed-ambos") };
  const actual = () => cfg.calcas[sel];
  const filaCalca = filaDeColor($("p-ed-color"), COLORES_CALCA, () => actual()?.color || "#ffffff",
    (hex) => { actual().color = hex; refrescarMiniatura(); });
  function refrescarMiniatura() {
    const ficha = $("p-puestas").children[sel];
    const c = actual();
    if (ficha && c) ficha.querySelector("img").src = miniaturaDe(c);
  }
  function pintarEditor() {
    const c = actual();
    $("p-editor").hidden = !c;
    if (!c) return;
    $("p-ed-nombre").textContent = datos.disenos[c.diseno];
    ed.tamano.value = String(c.tamano);
    $("p-ed-tamano-v").textContent = `${Math.round(c.tamano * 100)}%`;
    ed.giro.value = String(c.giro || 0);
    $("p-ed-giro-v").textContent = `${Math.round(c.giro || 0)}°`;
    ed.ambos.checked = Boolean(c.ambos);
    const conTexto = CON_TEXTO[c.diseno];
    $("p-ed-texto-caja").hidden = !conTexto;
    if (conTexto) {
      $("p-ed-texto-etq").textContent = c.diseno === "numero" ? "Número" : "Texto";
      ed.texto.maxLength = conTexto;
      ed.texto.placeholder = c.diseno === "numero" ? "27" : "Tu nombre o frase";
      ed.texto.value = c.texto || "";
    }
    filaCalca.pintar();
  }
  gesto(ed.tamano, () => {
    actual().tamano = Number(ed.tamano.value);
    $("p-ed-tamano-v").textContent = `${Math.round(actual().tamano * 100)}%`;
    aplicar();
  });
  gesto(ed.giro, () => {
    actual().giro = Number(ed.giro.value);
    $("p-ed-giro-v").textContent = `${actual().giro}°`;
    aplicar();
  });
  gesto(ed.texto, () => { actual().texto = ed.texto.value; refrescarMiniatura(); aplicar(); });
  ed.ambos.addEventListener("change", () => { guardarPaso(); actual().ambos = ed.ambos.checked; aplicar(); });
  $("p-ed-quitar").addEventListener("click", () => {
    guardarPaso();
    cfg.calcas.splice(sel, 1);
    sel = cfg.calcas.length - 1;
    repintarCalcas();
    aplicar();
  });

  function repintarCalcas() {
    if (sel >= cfg.calcas.length) sel = cfg.calcas.length - 1;
    pintarCatalogo();
    pintarPuestas();
    pintarEditor();
    window.TallerYa3D.resaltar(enCalcas() ? sel : -1);
  }

  // ---------- Lo que pasa en el modelo 3D ----------
  function conectar3D() {
    window.TallerYa3D.escuchar({
      alColocar(diseno, sitio) {
        guardarPaso();
        const lateral = Math.abs(sitio.normal[2]) > 0.6; // en un costado: por defecto en ambos lados
        cfg.calcas.push({
          diseno, color: claridad(cfg.color) > 0.55 ? "#14181a" : "#ffffff", tamano: 1, giro: 0,
          ambos: lateral, texto: "", punto: sitio.punto, normal: sitio.normal,
          ...(diseno === "imagen" ? { imagen: imagenPendiente } : {}),
        });
        imagenPendiente = "";
        colocando = null;
        $("visor-colocar").hidden = true;
        sel = cfg.calcas.length - 1;
        repintarCalcas();
        aplicar();
        $("p-editor").scrollIntoView({ block: "nearest", behavior: "smooth" });
      },
      alFallar() {
        $("p-estado").textContent = "Toca una parte pintada de la carrocería.";
        $("p-estado").classList.add("sin-guardar");
      },
      alElegir(i) { prepararCajon(); pestana("calcas"); elegir(i); },
      alEmpezarArrastre() { guardarPaso(); },
      alMover(i, sitio) {
        Object.assign(cfg.calcas[i], { punto: sitio.punto, normal: sitio.normal });
        aplicar();
      },
      alSoltar() { aplicar(); },
    });
  }

  // ---------- Guardar, Atrás y Deshacer todo ----------
  function cookie(nombre) {
    const m = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`));
    return m ? decodeURIComponent(m[1]) : "";
  }
  $("p-guardar").addEventListener("click", async () => {
    $("p-guardar").disabled = true;
    $("p-estado").textContent = "Guardando…";
    try {
      const r = await fetch(datos.url, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": cookie("csrftoken") },
        body: JSON.stringify(cfg),
      });
      const respuesta = await r.json();
      if (!r.ok || !respuesta.ok) throw new Error(respuesta.error || "No se pudo guardar.");
      guardado = copiar(cfg);
      historial.length = 0; // lo guardado es el nuevo punto de partida: ya no se puede volver atrás
      aplicar();
      mostrarCajon(false);
      avisarGuardado();
    } catch (e) {
      $("p-estado").textContent = e.message;
      $("p-guardar").disabled = false;
    }
  });

  function repintarTodo() {
    pintarColores();
    repintarCalcas();
    pintarFabrica();
    aplicar();
  }
  function atras() {
    if (!historial.length) return;
    cfg = JSON.parse(historial.pop());
    repintarTodo();
    $("p-estado").textContent = historial.length ? "Cambio deshecho." : "Cambio deshecho. No hay más cambios atrás.";
  }
  $("p-atras").addEventListener("click", atras);
  $("p-deshacer").addEventListener("click", () => {
    guardarPaso();
    cfg = copiar(guardado);
    repintarTodo();
    $("p-estado").textContent = "La moto volvió a como estaba.";
  });

  // Confirmación breve en el botón "Personalizar" al cerrar (guardado o con los cambios descartados).
  let textoBoton = null;
  function avisarEnBoton(texto, clase) {
    textoBoton ??= abrir.innerHTML;
    abrir.classList.remove("guardado", "descartado");
    abrir.classList.add(clase);
    abrir.textContent = texto;
    clearTimeout(avisarEnBoton.reloj);
    avisarEnBoton.reloj = setTimeout(() => { abrir.innerHTML = textoBoton; abrir.classList.remove(clase); }, 2600);
  }
  const avisarGuardado = () => avisarEnBoton("✓ Diseño guardado", "guardado");

  // Cerrar sin guardar deshace todo lo que no se guardó: la moto vuelve a como estaba.
  function descartarSinGuardar() {
    if (JSON.stringify(cfg) === JSON.stringify(guardado)) return;
    cfg = copiar(guardado);
    historial.length = 0;
    sel = cfg.calcas.length ? 0 : -1;
    repintarTodo();
    $("p-estado").textContent = "";
    avisarEnBoton("Cambios sin guardar descartados", "descartado");
  }

  // ---------- Abrir y cerrar el cajón ----------
  function mostrarCajon(si) {
    if (si) prepararCajon();
    cajon.hidden = !si;
    abrir.setAttribute("aria-expanded", String(si));
    if (si) {
      quererAcabados();
      window.TallerYa3D?.verMoto();
      const visor = $("visor");
      const r = visor.getBoundingClientRect();
      if (r.top < 0 || r.bottom > window.innerHeight * (window.innerWidth < 768 ? 0.42 : 1)) {
        visor.scrollIntoView({ block: "start", behavior: "smooth" });
      }
      $("cerrar-personalizar").focus();
    } else {
      cancelarColocar();
      descartarSinGuardar();
      abrir.focus();
    }
    window.TallerYa3D?.resaltar(si && enCalcas() ? sel : -1);
  }
  abrir.addEventListener("click", () => mostrarCajon(cajon.hidden));
  $("cerrar-personalizar").addEventListener("click", () => mostrarCajon(false));
  document.addEventListener("keydown", (e) => {
    if (cajon.hidden) return;
    if (e.key === "Escape") { if (colocando) cancelarColocar(); else mostrarCajon(false); return; }
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === "z") {
      if (e.target.matches?.('input[type="text"]')) return; // ahí Ctrl+Z deshace lo escrito
      e.preventDefault();
      atras();
    }
  });

  let cajonListo = true; // (hasta que llegue la configuración no hay nada que armar)
  function prepararCajon() {
    if (cajonListo) return;
    cajonListo = true;
    pintarColores();
    repintarCalcas();
    pintarFabrica();
    if (cajon.hidden) window.TallerYa3D.resaltar(-1);
  }

  function iniciar(inicial) {
    cfg = copiar(inicial);
    guardado = copiar(inicial);
    sel = cfg.calcas.length ? 0 : -1;
    conectar3D();
    // El contenido del cajón (filas de color, catálogo de calcas, calcas de fábrica) no se arma aquí: los colores
    // guardados ya los pinta el visor, y armarlo al cargar (las miniaturas de calcas esperan a la tarjeta gráfica,
    // ocupada compilando el 3D) congelaba la página de 2 a 10 s en un celular. Se arma al acercarse al botón,
    // al abrir el cajón o cuando la página queda libre.
    cajonListo = false;
    $("p-guardar").disabled = true;
    $("p-deshacer").disabled = true;
    $("p-atras").disabled = true;
    window.TallerYa3D.resaltar(-1);
    abrir.hidden = false;
    // Quien se acerca al botón probablemente va a abrir el cajón: las esferas empiezan a dibujarse desde ya
    const precalentarCajon = () => { prepararCajon(); quererAcabados(); };
    ["pointerenter", "focus", "touchstart"].forEach((ev) => abrir.addEventListener(ev, precalentarCajon, { once: true, passive: true }));
    // Si nadie se acerca, se arma igual cuando la página quede libre (y la tarjeta gráfica ya terminó con el 3D)
    const enReposo = (fn, ms) => (window.requestIdleCallback ? requestIdleCallback(fn, { timeout: ms }) : setTimeout(fn, 200));
    setTimeout(() => enReposo(prepararCajon, 4000), 3000);
    if (location.hash === "#personalizar") mostrarCajon(true);
  }

  // Para revisar desde la consola: __personalizar.cfg()
  window.__personalizar = { cfg: () => copiar(cfg) };

  if (window.TallerYa3DInicial) iniciar(window.TallerYa3DInicial);
  else document.addEventListener("moto3d-listo", (e) => iniciar(e.detail), { once: true });
})();
