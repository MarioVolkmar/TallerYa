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
  }

  // ---------- Pestañas ----------
  function pestana(cual) {
    ["pintura", "calcas"].forEach((n) => {
      $(`tab-${n}`).setAttribute("aria-selected", String(n === cual));
      $(`panel-${n}`).hidden = n !== cual;
    });
    if (cual !== "calcas") cancelarColocar();
    window.TallerYa3D?.resaltar(cual === "calcas" ? sel : -1);
  }
  const enCalcas = () => !$("panel-calcas").hidden;
  $("tab-pintura").addEventListener("click", () => pestana("pintura"));
  $("tab-calcas").addEventListener("click", () => pestana("calcas"));

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
      colores.forEach(([hex, nombre]) => {
        const b = el("button", "muestra-color");
        b.type = "button";
        b.style.background = hex;
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

  const filaPintura = filaDeColor($("p-color"), datos.colores, () => cfg.color, (c) => { cfg.color = c; });
  const filaRines = filaDeColor($("p-secundario"), datos.secundarios, () => cfg.color_secundario, (c) => { cfg.color_secundario = c; });
  function pintarColores() {
    filaPintura.pintar();
    filaRines.pintar();
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
      img.src = window.TallerYa3D.miniatura(clave, "#f2611d", "");
      img.alt = "";
      b.append(img, el("span", "", nombre.replace(" de carreras", "")));
      b.setAttribute("aria-pressed", String(colocando === clave));
      b.disabled = lleno;
      if (lleno) b.title = "Llegaste al máximo de 4 calcas";
      b.addEventListener("click", () => {
        if (cfg.calcas.length >= MAX_CALCAS) return;
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
      img.src = window.TallerYa3D.miniatura(c.diseno, c.color, c.texto);
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
    if (ficha && c) ficha.querySelector("img").src = window.TallerYa3D.miniatura(c.diseno, c.color, c.texto);
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
        });
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
      alElegir(i) { pestana("calcas"); elegir(i); },
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
    cajon.hidden = !si;
    abrir.setAttribute("aria-expanded", String(si));
    if (si) {
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

  function iniciar(inicial) {
    cfg = copiar(inicial);
    guardado = copiar(inicial);
    sel = cfg.calcas.length ? 0 : -1;
    conectar3D();
    pintarColores();
    repintarCalcas();
    $("p-guardar").disabled = true;
    $("p-deshacer").disabled = true;
    $("p-atras").disabled = true;
    window.TallerYa3D.resaltar(-1);
    abrir.hidden = false;
    if (location.hash === "#personalizar") mostrarCajon(true);
  }

  // Para revisar desde la consola: __personalizar.cfg()
  window.__personalizar = { cfg: () => copiar(cfg) };

  if (window.TallerYa3DInicial) iniciar(window.TallerYa3DInicial);
  else document.addEventListener("moto3d-listo", (e) => iniciar(e.detail), { once: true });
})();
