/* Chat de ayuda con Chispa (sin IA por ahora): temas en chips → preguntas → respuesta con acciones.
   Pide los datos a /ayuda/catalogo.json y /ayuda/preguntar/ solo al abrir. */
(function () {
  "use strict";
  var raiz = document.getElementById("chispa-chat");
  if (!raiz) return;
  var boton = raiz.querySelector(".cc-boton");
  var globito = raiz.querySelector(".cc-globito");
  var CERRADO = "tallerya-chispa-globito-cerrado";
  var panel, log, entrada, velo, catalogo, cargando, temporizador;

  function cerradoEnSesion() { try { return localStorage.getItem(CERRADO); } catch (e) { return null; } }

  // Globito «¿Te ayudo?»: sale al cargar y luego cada cierto tiempo. Tocarlo abre el chat;
  // tocar fuera o Esc lo cierra y no vuelve nunca (localStorage).
  function cerrarGlobito() {
    if (globito.hidden) return;
    globito.hidden = true;
    clearTimeout(temporizador);
    try { localStorage.setItem(CERRADO, "1"); } catch (e) { /* sin almacenamiento */ }
  }
  function mostrarGlobito() {
    if (cerradoEnSesion() || (panel && !panel.hidden) || escondida()) return;
    globito.hidden = false;
    setTimeout(function () { globito.hidden = true; }, 7000);
    temporizador = setTimeout(mostrarGlobito, 60000);
  }
  temporizador = setTimeout(mostrarGlobito, 150);
  globito.addEventListener("click", function () { globito.hidden = true; abrir(); });
  document.addEventListener("pointerdown", function (ev) {
    if (!globito.hidden && !raiz.contains(ev.target)) cerrarGlobito();
  });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") cerrarGlobito(); });

  // Saludo con el brazo: cada ~9 s y al pasar el cursor o enfocar a Chispa; si ya está saludando, no se corta ni se repite
  var saludando = false;
  function saludar() {
    if (saludando) return;
    saludando = true;
    raiz.classList.add("cc-saluda");
    setTimeout(function () { raiz.classList.remove("cc-saluda"); saludando = false; }, 2300);
  }
  setTimeout(function () { saludar(); setInterval(saludar, 9000); }, 1500);
  // Ráfaga de chispas por el electrodo, una por cada hover/foco
  var chispaTimer;
  function chispear() {
    raiz.classList.remove("cc-chispea");
    void raiz.offsetWidth; // reinicia la animación
    raiz.classList.add("cc-chispea");
    clearTimeout(chispaTimer);
    chispaTimer = setTimeout(function () { raiz.classList.remove("cc-chispea"); }, 650);
  }
  boton.addEventListener("mouseenter", function () { if (escondida()) return; saludar(); chispear(); });
  boton.addEventListener("focus", function () { if (!escondida() && boton.matches(":focus-visible")) { saludar(); chispear(); } });

  // Esconder a Chispa: se desliza al borde y solo asoma el visor; tocarla o pasar el cursor la saca de nuevo
  var ESCONDIDA = "tallerya-chispa-escondida";
  function escondida() { return raiz.classList.contains("cc-escondida"); }
  function esconder() {
    globito.hidden = true;
    raiz.classList.add("cc-escondida");
    boton.setAttribute("aria-label", "Mostrar a Chispa");
    try { localStorage.setItem(ESCONDIDA, "1"); } catch (e) { /* sin almacenamiento */ }
  }
  function mostrar() {
    raiz.classList.remove("cc-escondida");
    boton.setAttribute("aria-label", "Pregúntale a Chispa");
    try { localStorage.removeItem(ESCONDIDA); } catch (e) { /* sin almacenamiento */ }
    setTimeout(saludar, 300);
  }

  // Arrastrar a Chispa hacia el borde derecho para esconderla (mouse o dedo); si no pasa el umbral, vuelve a su sitio
  var arrastre = null, arrastro = false;
  boton.addEventListener("pointerdown", function (ev) {
    if (escondida() || ev.button > 0) return;
    arrastre = { x: ev.clientX, dx: 0, id: ev.pointerId };
  });
  boton.addEventListener("pointermove", function (ev) {
    if (!arrastre || ev.pointerId !== arrastre.id) return;
    arrastre.dx = Math.max(0, ev.clientX - arrastre.x);
    if (arrastre.dx > 6) {
      if (!raiz.classList.contains("cc-arrastrando")) { raiz.classList.add("cc-arrastrando"); try { boton.setPointerCapture(ev.pointerId); } catch (e) { /* */ } }
      raiz.style.transform = "translateX(" + arrastre.dx + "px)";
    }
  });
  function soltar() {
    if (!arrastre) return;
    var dx = arrastre.dx;
    arrastre = null;
    if (!raiz.classList.contains("cc-arrastrando")) return;
    arrastro = true;
    raiz.classList.remove("cc-arrastrando");
    raiz.style.transform = "";
    if (dx > 60) esconder();
  }
  boton.addEventListener("pointerup", soltar);
  boton.addEventListener("pointercancel", soltar);

  // Pista discreta la primera vez: «Arrástrame al borde para esconderme»
  var PISTA = "tallerya-chispa-pista-arrastre";
  var pista = raiz.querySelector(".cc-pista");
  function mostrarPista() {
    try { if (localStorage.getItem(PISTA)) return; localStorage.setItem(PISTA, "1"); } catch (e) { return; }
    if (escondida() || (panel && !panel.hidden)) return;
    globito.hidden = true;
    pista.hidden = false;
    setTimeout(function () { pista.hidden = true; }, 3500);
  }
  if (window.matchMedia && window.matchMedia("(hover: hover)").matches) boton.addEventListener("mouseenter", mostrarPista);
  else setTimeout(mostrarPista, 12000);
  try {
    if (localStorage.getItem(ESCONDIDA)) {
      raiz.style.transition = "none";
      esconder();
      void raiz.offsetWidth;
      raiz.style.transition = "";
    }
  } catch (e) { /* sin almacenamiento */ }

  // Copia de Chispa recortada desde el visor (cabecera y «escribiendo»)
  function carita() {
    var c = boton.querySelector("svg").cloneNode(true);
    c.removeAttribute("id");
    c.setAttribute("viewBox", "-32 -6 64 108");
    c.setAttribute("class", "chispa chispa-quieta chispa-a");
    return c;
  }

  function el(tag, clase, texto) {
    var e = document.createElement(tag);
    if (clase) e.className = clase;
    if (texto) e.textContent = texto;
    return e;
  }

  function construir() {
    velo = el("div", "cc-velo");
    velo.hidden = true;
    velo.addEventListener("click", cerrar);
    panel = el("section", "cc-panel");
    panel.id = "chispa-chat-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "true");
    panel.setAttribute("aria-labelledby", "chispa-chat-titulo");
    panel.hidden = true;

    var cabeza = el("div", "cc-cabeza");
    var cara = carita();
    cabeza.appendChild(cara);
    var titulo = el("h2", "cc-titulo", "Pregúntale a Chispa");
    titulo.id = "chispa-chat-titulo";
    titulo.appendChild(el("small", "", "Ayuda rápida de TallerYa"));
    cabeza.appendChild(titulo);
    var ocultar = el("button", "cc-panel-esconder");
    ocultar.type = "button";
    ocultar.setAttribute("aria-label", "Esconder a Chispa");
    ocultar.title = "Esconder a Chispa";
    ocultar.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><g class="cc-ojo-ic"><path d="M3 12s3.5-6 9-6 9 6 9 6-3.5 6-9 6-9-6-9-6z" fill="none" stroke="currentColor" stroke-width="1.7"/><circle cx="12" cy="12" r="2.6" fill="none" stroke="currentColor" stroke-width="1.7"/></g><path class="cc-raya" d="M4 20 L20 4" pathLength="1" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>';
    ocultar.addEventListener("click", function () { cerrar(); esconder(); });
    cabeza.appendChild(ocultar);
    var x = el("button", "cc-cerrar");
    x.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7 L17 17 M17 7 L7 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/></svg>';
    x.type = "button";
    x.setAttribute("aria-label", "Cerrar la ayuda");
    x.title = "Cerrar";
    x.addEventListener("click", cerrar);
    cabeza.appendChild(x);

    log = el("div", "cc-log");
    log.setAttribute("role", "log");
    log.setAttribute("aria-live", "polite");

    var form = el("form", "cc-form");
    form.setAttribute("role", "search");
    entrada = el("input");
    entrada.type = "search";
    entrada.placeholder = "Escribe tu pregunta…";
    entrada.setAttribute("aria-label", "Escribe tu pregunta");
    entrada.maxLength = 300;
    entrada.autocomplete = "off";
    var enviar = el("button", "cc-enviar", "Buscar");
    enviar.type = "submit";
    form.appendChild(entrada);
    form.appendChild(enviar);
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var q = entrada.value.trim();
      if (!q) return;
      entrada.value = "";
      preguntar({ q: q }, q);
    });

    panel.appendChild(cabeza);
    panel.appendChild(log);
    panel.appendChild(form);
    document.body.appendChild(velo);
    document.body.appendChild(panel);
    panel.addEventListener("keydown", teclas);
  }

  function teclas(ev) {
    if (ev.key === "Escape") { ev.preventDefault(); cerrar(); return; }
    if (ev.key !== "Tab") return;
    // mantener el foco dentro de la ventana
    var f = panel.querySelectorAll("button, a[href], input");
    if (!f.length) return;
    var primero = f[0], ultimo = f[f.length - 1];
    if (ev.shiftKey && document.activeElement === primero) { ev.preventDefault(); ultimo.focus(); }
    else if (!ev.shiftKey && document.activeElement === ultimo) { ev.preventDefault(); primero.focus(); }
  }

  function abrir() {
    if (!panel) construir();
    globito.hidden = true;
    panel.hidden = false;
    velo.hidden = false;
    raiz.classList.add("cc-abierto");
    boton.setAttribute("aria-expanded", "true");
    if (!catalogo && !cargando) iniciar();
    setTimeout(function () { entrada.focus({ preventScroll: true }); }, 30);
  }

  function cerrar() {
    if (!panel || panel.hidden) return;
    panel.hidden = true;
    velo.hidden = true;
    raiz.classList.remove("cc-abierto");
    boton.setAttribute("aria-expanded", "false");
    boton.focus();
  }

  function bajar() { log.scrollTop = log.scrollHeight; }

  function burbuja(clase, parrafos) {
    var m = el("div", "cc-msg " + clase);
    (Array.isArray(parrafos) ? parrafos : [parrafos]).forEach(function (t) { m.appendChild(el("p", "", t)); });
    log.appendChild(m);
    bajar();
    return m;
  }

  function chips(lista, alElegir) {
    var c = el("div", "cc-chips");
    lista.forEach(function (item) {
      var b = el("button", "cc-chip" + (item.volver ? " cc-chip-volver" : ""), item.texto);
      b.type = "button";
      b.addEventListener("click", function () { alElegir(item); });
      c.appendChild(b);
    });
    log.appendChild(c);
    bajar();
    return c;
  }

  function escribiendo() {
    var e = el("div", "cc-escribiendo");
    var cara = carita();
    e.appendChild(cara);
    e.appendChild(el("span", "", "Chispa está escribiendo…"));
    log.appendChild(e);
    bajar();
    return e;
  }

  function pedir(url) {
    return fetch(url, { headers: { Accept: "application/json" }, credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  function iniciar() {
    cargando = true;
    var e = escribiendo();
    pedir(raiz.dataset.catalogo).then(function (d) {
      catalogo = d;
      e.remove();
      burbuja("cc-bot", d.saludo);
      mostrarTemas();
    }).catch(function () {
      e.remove();
      burbuja("cc-bot", "Uy, no pude cargar la ayuda. Revisa tu conexión e inténtalo de nuevo.");
    }).then(function () { cargando = false; });
  }

  function mostrarTemas() {
    chips(catalogo.temas.map(function (t) { return { texto: t.titulo, tema: t }; }), function (item) {
      burbuja("cc-yo", item.tema.titulo);
      var lista = item.tema.preguntas.map(function (p) { return { texto: p.pregunta, id: p.id }; });
      lista.push({ texto: "← Otros temas", volver: true });
      chips(lista, elegirPregunta);
    });
  }

  function elegirPregunta(item) {
    if (item.volver) { mostrarTemas(); return; }
    preguntar({ id: item.id }, item.texto);
  }

  function preguntar(params, textoUsuario) {
    burbuja("cc-yo", textoUsuario);
    var e = escribiendo();
    var url = raiz.dataset.preguntar + "?" + new URLSearchParams(params).toString();
    var espera = new Promise(function (ok) { setTimeout(ok, 550); });
    Promise.all([pedir(url), espera]).then(function (res) {
      e.remove();
      responder(res[0]);
    }).catch(function () {
      e.remove();
      burbuja("cc-bot", "Uy, no pude traer la respuesta. Revisa tu conexión e inténtalo de nuevo.");
    });
  }

  function responder(r) {
    burbuja("cc-bot", r.respuesta);
    if (r.acciones && r.acciones.length) {
      var a = el("div", "cc-acciones");
      r.acciones.forEach(function (ac) {
        var l = el("a", "cc-accion", ac.texto);
        l.href = ac.url;
        a.appendChild(l);
      });
      log.appendChild(a);
    }
    var lista = (r.relacionadas || []).map(function (p) { return { texto: p.pregunta, id: p.id }; });
    lista.push({ texto: "← Otros temas", volver: true });
    chips(lista, elegirPregunta);
  }

  boton.addEventListener("click", function () {
    if (arrastro) { arrastro = false; return; }
    if (escondida()) { mostrar(); return; }
    if (panel && !panel.hidden) cerrar(); else abrir();
  });
})();
