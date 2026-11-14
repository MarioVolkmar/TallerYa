// Menús desplegables y calendario con el estilo de TallerYa.
// Mejora progresiva: el <select> y el <input type="date"> originales siguen en el formulario
// (y son los que se envían); aquí solo se dibuja una interfaz propia encima.
// Para dejar un campo nativo, agrégale data-nativo.
(function () {
  "use strict";
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const DIAS = ["L", "M", "M", "J", "V", "S", "D"];
  let abierto = null; // { cerrar() } del control desplegado ahora

  function el(etiqueta, clase, texto) {
    const n = document.createElement(etiqueta);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }
  function avisar(campo) {
    campo.dispatchEvent(new Event("input", { bubbles: true }));
    campo.dispatchEvent(new Event("change", { bubbles: true }));
  }
  // El panel se abre hacia arriba si no cabe debajo.
  function ubicar(panel, ancla) {
    panel.classList.remove("hacia-arriba", "hacia-izquierda");
    const r = ancla.getBoundingClientRect();
    const alto = panel.offsetHeight;
    if (r.bottom + alto + 12 > window.innerHeight && r.top > alto + 12) panel.classList.add("hacia-arriba");
    if (panel.getBoundingClientRect().right > document.documentElement.clientWidth - 8) panel.classList.add("hacia-izquierda");
  }
  function esconderNativo(campo) {
    campo.classList.add("control-nativo");
    campo.tabIndex = -1;
    campo.setAttribute("aria-hidden", "true");
  }
  // Los clics dentro del panel no deben "re-activar" la etiqueta <label> que envuelve el campo.
  function aislar(panel) {
    panel.addEventListener("click", (e) => e.preventDefault());
    panel.addEventListener("mousedown", (e) => e.preventDefault()); // no robar el foco del botón
  }
  document.addEventListener("pointerdown", (e) => {
    if (abierto && !abierto.raiz.contains(e.target)) abierto.cerrar();
  });
  // En el celular la barra del navegador cambia el alto al hacer scroll: solo se cierra si cambia el ancho.
  let anchoVentana = window.innerWidth;
  window.addEventListener("resize", () => {
    if (window.innerWidth !== anchoVentana) abierto?.cerrar();
    anchoVentana = window.innerWidth;
  });

  // ------------------------------------------------------------------ Menús
  let serie = 0;
  function mejorarSelect(select) {
    if (select.multiple || select.dataset.nativo !== undefined || select.dataset.mejorado) return;
    select.dataset.mejorado = "1";
    const id = `selector-${++serie}`;
    const raiz = el("div", "selector");
    select.parentNode.insertBefore(raiz, select);
    const boton = el("button", "campo selector-boton");
    boton.type = "button";
    boton.setAttribute("aria-haspopup", "listbox");
    boton.setAttribute("aria-expanded", "false");
    boton.setAttribute("aria-controls", id);
    for (const c of select.classList) if (c.startsWith("!")) boton.classList.add(c); // p. ej. !mt-0
    const texto = el("span", "selector-texto");
    boton.appendChild(texto);
    const lista = el("ul", "selector-lista");
    lista.id = id;
    lista.setAttribute("role", "listbox");
    lista.tabIndex = -1;
    lista.hidden = true;
    aislar(lista);
    raiz.append(boton, select, lista);
    esconderNativo(select);

    let activa = -1;
    let opciones = [];

    function pintarTexto() {
      const op = select.options[select.selectedIndex];
      texto.textContent = op ? op.textContent : "";
      boton.classList.toggle("vacio", !op || op.value === "");
    }
    function construir() {
      lista.innerHTML = "";
      opciones = [];
      const agregar = (op) => {
        const li = el("li", "selector-opcion", op.textContent);
        li.setAttribute("role", "option");
        li.id = `${id}-${opciones.length}`;
        li.setAttribute("aria-selected", String(op.selected));
        if (op.disabled) li.setAttribute("aria-disabled", "true");
        if (op.value === "") li.classList.add("selector-vacia");
        const i = opciones.length;
        li.addEventListener("click", () => { if (!op.disabled) elegir(i); });
        li.addEventListener("mousemove", () => marcar(i, false));
        opciones.push({ op, li });
        return li;
      };
      for (const hijo of select.children) {
        if (hijo.tagName === "OPTGROUP") {
          const g = el("li", "selector-grupo", hijo.label);
          g.setAttribute("role", "presentation");
          lista.appendChild(g);
          for (const op of hijo.children) lista.appendChild(agregar(op));
        } else {
          lista.appendChild(agregar(hijo));
        }
      }
    }
    function marcar(i, desplazar = true) {
      if (opciones[activa]) opciones[activa].li.classList.remove("activa");
      activa = i;
      const o = opciones[i];
      if (!o) return;
      o.li.classList.add("activa");
      boton.setAttribute("aria-activedescendant", o.li.id);
      if (desplazar) o.li.scrollIntoView({ block: "nearest" });
    }
    function mover(paso) {
      let i = activa;
      for (let n = 0; n < opciones.length; n++) {
        i = Math.min(opciones.length - 1, Math.max(0, i + paso));
        if (!opciones[i].op.disabled) break;
      }
      marcar(i);
    }
    function abrir() {
      if (abierto && abierto.raiz !== raiz) abierto.cerrar();
      construir();
      lista.hidden = false;
      boton.setAttribute("aria-expanded", "true");
      raiz.classList.add("abierto");
      ubicar(lista, boton);
      marcar(Math.max(0, opciones.findIndex((o) => o.op.selected)));
      abierto = { raiz, cerrar };
    }
    function cerrar() {
      lista.hidden = true;
      boton.setAttribute("aria-expanded", "false");
      boton.removeAttribute("aria-activedescendant");
      raiz.classList.remove("abierto");
      if (abierto && abierto.raiz === raiz) abierto = null;
    }
    function elegir(i) {
      const { op } = opciones[i];
      const cambio = select.value !== op.value;
      select.value = op.value;
      pintarTexto();
      cerrar();
      boton.focus();
      if (cambio) avisar(select);
    }

    let busqueda = "";
    let reloj = null;
    boton.addEventListener("click", () => (lista.hidden ? abrir() : cerrar()));
    boton.addEventListener("keydown", (e) => {
      const cerradoAhora = lista.hidden;
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key) && cerradoAhora) { e.preventDefault(); abrir(); return; }
      if (cerradoAhora) return;
      if (e.key === "ArrowDown") { e.preventDefault(); mover(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); mover(-1); }
      else if (e.key === "Home") { e.preventDefault(); marcar(0); }
      else if (e.key === "End") { e.preventDefault(); marcar(opciones.length - 1); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); if (activa >= 0) elegir(activa); }
      else if (e.key === "Escape") { e.preventDefault(); cerrar(); }
      else if (e.key === "Tab") cerrar();
      else if (e.key.length === 1) {
        // Escribir salta a la opción que empieza por esas letras.
        busqueda += e.key.toLowerCase();
        clearTimeout(reloj);
        reloj = setTimeout(() => { busqueda = ""; }, 600);
        const i = opciones.findIndex((o) => o.op.textContent.trim().toLowerCase().startsWith(busqueda));
        if (i >= 0) marcar(i);
      }
    });
    // Si el valor cambia desde otro lado (código o "reset" del formulario), se actualiza el texto.
    select.addEventListener("change", pintarTexto);
    select.form?.addEventListener("reset", () => setTimeout(pintarTexto));
    pintarTexto();
  }

  // --------------------------------------------------------------- Calendario
  const iso = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  const desdeIso = (s) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || "");
    return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
  };
  const legible = (d) => `${d.getDate()} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`;
  const corta = (d) => `${d.getDate()} ${MESES[d.getMonth()].slice(0, 3)} ${d.getFullYear()}`; // cabe en campos angostos

  function mejorarFecha(input) {
    if (input.dataset.nativo !== undefined || input.dataset.mejorado) return;
    input.dataset.mejorado = "1";
    const raiz = el("div", "selector fecha");
    input.parentNode.insertBefore(raiz, input);
    const boton = el("button", "campo selector-boton fecha-boton");
    boton.type = "button";
    boton.setAttribute("aria-haspopup", "dialog");
    boton.setAttribute("aria-expanded", "false");
    for (const c of input.classList) if (c.startsWith("!")) boton.classList.add(c);
    boton.innerHTML = '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>';
    const texto = el("span", "selector-texto");
    boton.appendChild(texto);
    const panel = el("div", "calendario");
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Elige una fecha");
    panel.hidden = true;
    aislar(panel);
    raiz.append(boton, input, panel);
    esconderNativo(input);
    input.type = "date"; // se conserva el tipo para que el valor sea AAAA-MM-DD

    let vista = null;  // primer día del mes que se muestra
    let foco = null;   // día resaltado con el teclado
    const limite = () => ({ min: desdeIso(input.min), max: desdeIso(input.max) });
    const fuera = (d) => { const { min, max } = limite(); return (min && d < min) || (max && d > max); };

    function pintarTexto() {
      const d = desdeIso(input.value);
      texto.textContent = d ? corta(d) : "Elige una fecha";
      boton.setAttribute("aria-label", d ? `Fecha: ${legible(d)}. Cambiar` : "Elegir una fecha");
      boton.classList.toggle("vacio", !d);
    }

    const cabeza = el("div", "calendario-cabeza");
    const botonNav = (etq, simbolo, accion) => {
      const b = el("button", "calendario-nav", simbolo);
      b.type = "button";
      b.setAttribute("aria-label", etq);
      b.addEventListener("click", accion);
      return b;
    };
    const titulo = el("p", "calendario-titulo");
    titulo.setAttribute("aria-live", "polite");
    cabeza.append(
      botonNav("Año anterior", "«", () => cambiarMes(-12)),
      botonNav("Mes anterior", "‹", () => cambiarMes(-1)),
      titulo,
      botonNav("Mes siguiente", "›", () => cambiarMes(1)),
      botonNav("Año siguiente", "»", () => cambiarMes(12)),
    );
    const semana = el("div", "calendario-semana");
    DIAS.forEach((d) => semana.appendChild(el("span", "", d)));
    const rejilla = el("div", "calendario-dias");
    rejilla.setAttribute("role", "grid");
    const pie = el("div", "calendario-pie");
    const hoyBtn = el("button", "calendario-accion", "Hoy");
    hoyBtn.type = "button";
    hoyBtn.addEventListener("click", () => { const h = new Date(); h.setHours(0, 0, 0, 0); if (!fuera(h)) elegir(h); });
    const borrarBtn = el("button", "calendario-accion", "Borrar");
    borrarBtn.type = "button";
    borrarBtn.addEventListener("click", () => {
      const cambio = input.value !== "";
      input.value = "";
      pintarTexto();
      cerrar();
      boton.focus();
      if (cambio) avisar(input);
    });
    pie.append(hoyBtn, borrarBtn);
    panel.append(cabeza, semana, rejilla, pie);

    function cambiarMes(n) {
      vista = new Date(vista.getFullYear(), vista.getMonth() + n, 1);
      const ultimo = new Date(vista.getFullYear(), vista.getMonth() + 1, 0).getDate();
      foco = new Date(vista.getFullYear(), vista.getMonth(), Math.min(foco.getDate(), ultimo));
      pintarMes();
    }
    function pintarMes() {
      titulo.textContent = `${MESES[vista.getMonth()]} ${vista.getFullYear()}`;
      rejilla.innerHTML = "";
      const elegida = desdeIso(input.value);
      const hoy = iso(new Date());
      const vacios = (vista.getDay() + 6) % 7; // la semana empieza el lunes
      for (let i = 0; i < vacios; i++) rejilla.appendChild(el("span"));
      const dias = new Date(vista.getFullYear(), vista.getMonth() + 1, 0).getDate();
      for (let n = 1; n <= dias; n++) {
        const d = new Date(vista.getFullYear(), vista.getMonth(), n);
        const b = el("button", "calendario-dia", String(n));
        b.type = "button";
        b.tabIndex = -1;
        b.dataset.fecha = iso(d);
        b.setAttribute("aria-label", legible(d));
        if (iso(d) === hoy) b.classList.add("hoy");
        if (elegida && iso(d) === iso(elegida)) b.setAttribute("aria-pressed", "true");
        if (foco && iso(d) === iso(foco)) b.classList.add("foco");
        if (fuera(d)) b.disabled = true;
        b.addEventListener("click", () => elegir(d));
        rejilla.appendChild(b);
      }
      borrarBtn.hidden = input.required;
    }
    function abrir() {
      if (abierto && abierto.raiz !== raiz) abierto.cerrar();
      const base = desdeIso(input.value) || new Date();
      base.setHours(0, 0, 0, 0);
      foco = base;
      vista = new Date(base.getFullYear(), base.getMonth(), 1);
      pintarMes();
      panel.hidden = false;
      boton.setAttribute("aria-expanded", "true");
      raiz.classList.add("abierto");
      ubicar(panel, boton);
      abierto = { raiz, cerrar };
    }
    function cerrar() {
      panel.hidden = true;
      boton.setAttribute("aria-expanded", "false");
      raiz.classList.remove("abierto");
      if (abierto && abierto.raiz === raiz) abierto = null;
    }
    function elegir(d) {
      if (fuera(d)) return;
      const cambio = input.value !== iso(d);
      input.value = iso(d);
      pintarTexto();
      cerrar();
      boton.focus();
      if (cambio) avisar(input);
    }
    function moverFoco(dias) {
      foco = new Date(foco.getFullYear(), foco.getMonth(), foco.getDate() + dias);
      if (foco.getMonth() !== vista.getMonth() || foco.getFullYear() !== vista.getFullYear()) {
        vista = new Date(foco.getFullYear(), foco.getMonth(), 1);
      }
      pintarMes();
    }

    boton.addEventListener("click", () => (panel.hidden ? abrir() : cerrar()));
    boton.addEventListener("keydown", (e) => {
      if (panel.hidden) {
        if (["ArrowDown", "Enter", " "].includes(e.key)) { e.preventDefault(); abrir(); }
        return;
      }
      const pasos = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
      if (pasos[e.key]) { e.preventDefault(); moverFoco(pasos[e.key]); }
      else if (e.key === "PageUp") { e.preventDefault(); cambiarMes(e.shiftKey ? -12 : -1); }
      else if (e.key === "PageDown") { e.preventDefault(); cambiarMes(e.shiftKey ? 12 : 1); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); elegir(foco); }
      else if (e.key === "Escape") { e.preventDefault(); cerrar(); }
      else if (e.key === "Tab") cerrar();
    });
    input.addEventListener("change", pintarTexto);
    input.form?.addEventListener("reset", () => setTimeout(pintarTexto));
    pintarTexto();
  }

  // En pantallas táctiles el selector nativo del celular es más cómodo (lista grande, con scroll),
  // así que los <select> se quedan nativos; conservan el estilo .campo.
  const tactil = window.matchMedia("(pointer: coarse)").matches;
  function mejorarTodo(raiz = document) {
    if (!tactil) raiz.querySelectorAll("select.campo").forEach(mejorarSelect);
    raiz.querySelectorAll('input[type="date"].campo').forEach(mejorarFecha);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", () => mejorarTodo());
  else mejorarTodo();
  window.TallerYaControles = { mejorarTodo };
})();

// Menú del celular (<details>): se cierra al tocar fuera, con Escape o al elegir un enlace,
// y no reaparece abierto al volver atrás en el navegador.
(function () {
  "use strict";
  const menu = document.querySelector(".menu-movil");
  if (!menu) return;
  const cerrar = () => { menu.open = false; };
  document.addEventListener("pointerdown", (e) => { if (menu.open && !menu.contains(e.target)) cerrar(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && menu.open) { cerrar(); menu.querySelector("summary").focus(); } });
  menu.addEventListener("click", (e) => { if (e.target.closest(".menu-panel a")) cerrar(); });
  window.addEventListener("pageshow", cerrar);
})();
