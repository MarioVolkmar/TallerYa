// Consola de administración: un solo patrón para todas las acciones (confirmar → ocupado → éxito/error con aviso).
// Sin JS los formularios igual funcionan: el servidor responde con mensaje y redirección.
(function () {
  "use strict";
  const raiz = document.getElementById("consola");
  if (!raiz) return;
  const CLAVE_AVISO = "consola-aviso";

  // ---------- Avisos (toasts) ----------
  function avisar(texto, tipo) {
    const caja = document.getElementById("cs-toasts");
    const t = document.createElement("div");
    t.className = "cs-toast" + (tipo === "error" ? " cs-toast-error" : "");
    t.setAttribute("role", tipo === "error" ? "alert" : "status");
    t.textContent = texto;
    caja.appendChild(t);
    setTimeout(() => t.remove(), tipo === "error" ? 9000 : 5000);
  }
  try {
    const guardado = sessionStorage.getItem(CLAVE_AVISO);
    if (guardado) { sessionStorage.removeItem(CLAVE_AVISO); const a = JSON.parse(guardado); avisar(a.texto, a.tipo); }
  } catch (e) { /* sin almacenamiento: no pasa nada */ }

  function recargarConAviso(texto, destino) {
    try { sessionStorage.setItem(CLAVE_AVISO, JSON.stringify({ texto, tipo: "ok" })); } catch (e) { /* */ }
    if (destino) location.href = destino; else location.reload();
  }

  // ---------- Confirmación reutilizable ----------
  function confirmar(texto) {
    const d = document.getElementById("cs-confirmar");
    if (!d || !d.showModal) return Promise.resolve(window.confirm(texto));
    d.querySelector("[data-texto]").textContent = texto;
    d.returnValue = "";
    d.showModal();
    d.querySelector("[value=no]").focus();
    return esperarCierre(d).then((valor) => valor === "si");
  }

  // Pide un motivo (rechazar, ocultar, eliminar): resuelve con el texto, o null si cancela.
  function pedirMotivo(titulo, aviso) {
    const d = document.getElementById("cs-motivo");
    if (!d || !d.showModal) { const t = window.prompt(titulo); return Promise.resolve(t && t.trim().length >= 4 ? t.trim() : null); }
    const campo = d.querySelector("input"), error = d.querySelector("[data-error]"), texto = d.querySelector("[data-texto]");
    d.querySelector("h2").textContent = titulo;
    texto.hidden = !aviso; texto.textContent = aviso || "";
    campo.value = ""; error.hidden = true; d.returnValue = "";
    const si = d.querySelector("[data-si]");
    return new Promise((ok) => {
      const alClic = (ev) => {
        const b = ev.target.closest("button[value]");
        if (!b) return;
        ev.preventDefault();
        if (b.value === "si" && campo.value.trim().length < 4) { error.hidden = false; campo.focus(); return; }
        d.removeEventListener("click", alClic);
        const valor = b.value === "si" ? campo.value.trim() : null;
        if (d.open) d.close();
        ok(valor);
      };
      d.addEventListener("click", alClic);
      campo.onkeydown = (ev) => { if (ev.key === "Enter") { ev.preventDefault(); si.click(); } };
      d.addEventListener("cancel", () => { d.removeEventListener("click", alClic); ok(null); }, { once: true });
      d.showModal(); campo.focus();
    });
  }

  // Resuelve con el valor del botón pulsado (o "" con Escape). No depende solo del evento "close",
  // que algunos navegadores retrasan cuando la pestaña no está visible.
  function esperarCierre(d) {
    return new Promise((ok) => {
      let listo = false;
      const fin = (valor) => {
        if (listo) return;
        listo = true;
        d.removeEventListener("click", alClic);
        if (d.open) d.close(valor);
        ok(valor);
      };
      const alClic = (ev) => {
        const b = ev.target.closest("button[value]");
        if (b) { ev.preventDefault(); fin(b.value); }
      };
      d.addEventListener("click", alClic);
      d.addEventListener("cancel", () => fin(""), { once: true });
      d.addEventListener("close", () => fin(d.returnValue), { once: true });
    });
  }

  function mostrarClave(mensaje, clave) {
    const d = document.getElementById("cs-resultado");
    d.querySelector("[data-texto]").textContent = mensaje;
    d.querySelector("[data-clave]").textContent = clave;
    d.querySelector("[data-copiar]").onclick = () => navigator.clipboard && navigator.clipboard.writeText(clave)
      .then(() => avisar("Contraseña copiada."));
    d.showModal();
    return esperarCierre(d);
  }

  // ---------- Acciones ----------
  function ocupado(boton, si) {
    if (!boton) return;
    if (si) { boton._html = boton.innerHTML; boton.setAttribute("aria-busy", "true"); boton.disabled = true; boton.textContent = "Guardando…"; }
    else { boton.removeAttribute("aria-busy"); boton.disabled = false; if (boton._html != null) boton.innerHTML = boton._html; }
  }

  raiz.addEventListener("submit", async (ev) => {
    const form = ev.target;
    if (!form.matches("form[data-accion]")) return;
    ev.preventDefault();
    if (!form.reportValidity()) return;
    if (form.dataset.motivo) {
      const motivo = await pedirMotivo(form.dataset.motivo, form.dataset.confirmar);
      if (motivo === null) return;
      let campo = form.querySelector("input[name=motivo]");
      if (!campo) { campo = document.createElement("input"); campo.type = "hidden"; campo.name = "motivo"; form.appendChild(campo); }
      campo.value = motivo;
    } else if (form.dataset.confirmar && !(await confirmar(form.dataset.confirmar))) return;
    const boton = form.querySelector("button:not([type=button])");
    ocupado(boton, true);
    try {
      const r = await fetch(form.action, {
        method: "POST", body: new FormData(form), credentials: "same-origin",
        headers: { "X-Requested-With": "fetch", "X-CSRFToken": raiz.dataset.csrf },
      });
      const datos = await r.json().catch(() => ({ ok: false, error: "El servidor no respondió como se esperaba." }));
      if (!datos.ok) { ocupado(boton, false); avisar(datos.error || "No se pudo completar.", "error"); return; }
      if (datos.contrasena) { await mostrarClave(datos.mensaje, datos.contrasena); location.reload(); return; }
      recargarConAviso(datos.mensaje, datos.redirigir);
    } catch (e) {
      ocupado(boton, false);
      avisar("Sin conexión. Intenta de nuevo.", "error");
    }
  });

  // ---------- Filtros: elegir en un desplegable filtra de una vez (delegado: sigue vivo al cambiar el contenido) ----------
  raiz.addEventListener("change", (ev) => {
    const el = ev.target;
    if (el.matches("form.cs-filtros select")) {
      const ayuda = el.closest("label").querySelector("[data-ayuda-rol]");
      if (ayuda) ayuda.hidden = el.value !== "sin_perfil";
      el.form.requestSubmit();
    } else if (el.matches("[data-navegar]")) {
      navegar("?seccion=" + encodeURIComponent(el.value));
    } else if (el.matches("[data-rol]")) {
      const soloTaller = raiz.querySelector("[data-solo-taller]");
      if (soloTaller) soloTaller.hidden = el.value !== "taller";
      const soloAdmin = raiz.querySelector("[data-solo-admin]");
      if (soloAdmin) {
        soloAdmin.hidden = el.value !== "admin";
        const c = soloAdmin.querySelector("input"); if (c && soloAdmin.hidden) c.checked = false;
      }
    }
  });
  // Filtros por GET: URL limpia (los campos vacíos no viajan) y sin recargar la página
  raiz.addEventListener("submit", (ev) => {
    const f = ev.target;
    if (!f.matches("form.cs-filtros, form.cs-movil")) return;
    ev.preventDefault();
    const q = new URLSearchParams();
    new FormData(f).forEach((v, k) => { if (v !== "" && typeof v === "string") q.append(k, v); });
    navegar("?" + q.toString());
  });

  // ---------- Navegación sin recargar: pide la página, cambia solo el contenido y la URL (atrás funciona) ----------
  const principal = raiz.querySelector(".cs-principal");
  let pedido = null;
  function mismaPagina(a) {
    if (a.target && a.target !== "_self") return false;
    if (a.hasAttribute("download") || a.hasAttribute("data-completo")) return false;
    const u = new URL(a.href, location.href);
    return u.origin === location.origin && u.pathname === location.pathname && u.search !== "";
  }
  async function navegar(destino, opciones) {
    const empujar = !(opciones && opciones.sinHistorial);
    const url = new URL(destino, location.href);
    if (pedido) pedido.abort();
    pedido = new AbortController();
    principal.setAttribute("aria-busy", "true");
    try {
      const r = await fetch(url.href, { credentials: "same-origin", signal: pedido.signal,
        headers: { "X-Requested-With": "fetch" } });
      const final = new URL(r.url);
      if (!r.ok || final.pathname !== location.pathname) throw new Error("respuesta no válida");
      const doc = new DOMParser().parseFromString(await r.text(), "text/html");
      const nuevo = doc.querySelector(".cs-principal");
      if (!nuevo || !doc.getElementById("consola")) throw new Error("sin contenido");
      principal.innerHTML = nuevo.innerHTML;
      if (window.TallerYaControles) window.TallerYaControles.mejorarTodo(principal); // desplegables propios en el contenido nuevo
      const nav = raiz.querySelector(".cs-nav"), navN = doc.querySelector(".cs-nav");
      if (nav && navN) nav.innerHTML = navN.innerHTML;
      for (const q of [".cs-movil", ".cs-hoja-lista"]) {  // «Estás en» y la hoja de secciones del celular
        const viejo = raiz.querySelector(q), nuevoQ = doc.querySelector(q);
        if (viejo && nuevoQ) viejo.innerHTML = nuevoQ.innerHTML;
      }
      const hoja = document.getElementById("cs-secciones");
      if (hoja && hoja.open) hoja.close();
      document.title = doc.title;
      if (empujar) history.pushState({ consola: true }, "", final.pathname + final.search + url.hash);
      const ancla = url.hash && document.getElementById(url.hash.slice(1));
      if (ancla) ancla.scrollIntoView(); else window.scrollTo(0, 0);
      const h1 = principal.querySelector("h1");
      if (h1) { h1.setAttribute("tabindex", "-1"); h1.focus({ preventScroll: true }); }
    } catch (e) {
      if (e.name === "AbortError") return;
      location.href = url.href; // si algo falla, recarga normal
      return;
    } finally {
      principal.removeAttribute("aria-busy");
    }
  }
  // Hoja de secciones (celular)
  raiz.addEventListener("click", (ev) => {
    const hoja = document.getElementById("cs-secciones");
    if (!hoja) return;
    if (ev.target.closest("[data-abrir-secciones]")) { if (hoja.showModal) hoja.showModal(); }
    else if (ev.target.closest("[data-cerrar-secciones]") || ev.target === hoja) hoja.close();
    else if (ev.target.closest(".cs-hoja-item") && !ev.target.closest(".cs-hoja-item[aria-current=page]")) { /* navegar() la cierra */ }
    else if (ev.target.closest(".cs-hoja-item")) hoja.close();
  });
  raiz.addEventListener("click", (ev) => {
    if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    const a = ev.target.closest("a[href]");
    if (!a || !mismaPagina(a)) return;
    ev.preventDefault();
    if (sucio && !a.closest(".cs-principal form") && !confirm("¿Descartar lo que escribiste?")) return;
    sucio = false;
    navegar(a.href);
  });
  // Formularios de alta y edición (Nuevo proveedor, + Categoría, alta de taller): si hay algo escrito, se pregunta
  // antes de salir a otra sección; al guardar no.
  let sucio = false;
  raiz.addEventListener("input", (ev) => { if (ev.target.closest(".cs-principal form[method=post]")) sucio = true; });
  raiz.addEventListener("submit", () => { sucio = false; }, true);
  window.addEventListener("popstate", () => navegar(location.href, { sinHistorial: true }));
  history.replaceState({ consola: true }, "", location.href);

  // Tema: hay un botón en la barra lateral y otro en el desplegable del celular; el texto visible dice a qué tema pasa
  raiz.addEventListener("click", (ev) => {  // delegado: el botón del celular se vuelve a pintar al navegar
    if (!ev.target.closest("[data-tema]")) return;
    const nuevo = document.documentElement.dataset.consolaTema === "claro" ? "oscuro" : "claro";
    document.documentElement.dataset.consolaTema = nuevo;
    try { localStorage.setItem("consola-tema", nuevo); } catch (e) { /* */ }
  });

  // ---------- Menú «⋯» de acciones por fila ----------
  function cerrarMenus(salvo, devolverFoco) {
    raiz.querySelectorAll("details[data-menu][open]").forEach((m) => {
      if (m === salvo) return;
      m.open = false;
      if (devolverFoco) m.querySelector("summary").focus();
    });
  }
  raiz.addEventListener("toggle", (ev) => {
    const m = ev.target;
    if (!m.matches || !m.matches("details[data-menu]") || !m.open) return;
    cerrarMenus(m);
    // La lista va fija a la pantalla (la caja de la tabla desplaza y recortaría un menú absoluto).
    const lista = m.querySelector(".cs-menu-lista");
    const colocar = () => {
      const sb = m.querySelector("summary").getBoundingClientRect();
      lista.style.position = "fixed"; lista.style.maxHeight = ""; lista.style.top = "0px"; lista.style.right = "auto";
      const w = lista.offsetWidth, h = lista.offsetHeight;
      let left = Math.min(Math.max(8, sb.right - w), window.innerWidth - w - 8);
      let top = sb.bottom + 4;
      if (top + h > window.innerHeight - 8) top = Math.max(8, sb.top - h - 4);
      lista.style.left = left + "px"; lista.style.top = top + "px";
    };
    colocar();
    m._colocar = colocar;
    const primero = lista.querySelector("button, input, a, [tabindex]");
    if (primero && document.activeElement === m.querySelector("summary") && ev.isTrusted && m._teclado) primero.focus();
  }, true);
  raiz.addEventListener("keydown", (ev) => {
    const m = ev.target.closest && ev.target.closest("details[data-menu]");
    if (!m) return;
    if (ev.key === "Escape" && m.open) { ev.preventDefault(); m.open = false; m.querySelector("summary").focus(); return; }
    const items = [...m.querySelectorAll(".cs-menu-lista button, .cs-menu-lista input, .cs-menu-lista a")];
    if (ev.target.matches("summary")) { m._teclado = ev.key === "Enter" || ev.key === " " || ev.key === "ArrowDown"; if (ev.key === "ArrowDown" && !m.open) { ev.preventDefault(); m.open = true; } if (m.open && ev.key === "ArrowDown" && items[0]) { ev.preventDefault(); items[0].focus(); } return; }
    const i = items.indexOf(ev.target);
    if (ev.key === "ArrowDown" && i > -1) { ev.preventDefault(); items[(i + 1) % items.length].focus(); }
    if (ev.key === "ArrowUp" && i > -1) { ev.preventDefault(); (i === 0 ? m.querySelector("summary") : items[i - 1]).focus(); }
    if (ev.key === "Tab" && !ev.shiftKey && i === items.length - 1) m.open = false;
  });
  document.addEventListener("click", (ev) => { if (!ev.target.closest("details[data-menu]")) cerrarMenus(null); });
  // Al desplazar o cambiar el tamaño, el menú abierto se cierra (queda fijo y se desalinearía).
  window.addEventListener("resize", () => cerrarMenus(null));
  window.addEventListener("scroll", () => cerrarMenus(null), true);
})();
