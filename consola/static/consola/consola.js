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
    if (si) { boton.dataset.texto = boton.textContent; boton.setAttribute("aria-busy", "true"); boton.disabled = true; boton.textContent = "Guardando…"; }
    else { boton.removeAttribute("aria-busy"); boton.disabled = false; if (boton.dataset.texto) boton.textContent = boton.dataset.texto; }
  }

  raiz.addEventListener("submit", async (ev) => {
    const form = ev.target;
    if (!form.matches("form[data-accion]")) return;
    ev.preventDefault();
    if (!form.reportValidity()) return;
    if (form.dataset.confirmar && !(await confirmar(form.dataset.confirmar))) return;
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

  // ---------- Filtros: elegir en un desplegable filtra de una vez (conserva la búsqueda escrita; la URL lo refleja) ----------
  raiz.querySelectorAll("form.cs-filtros select").forEach((sel) => sel.addEventListener("change", () => {
    const ayuda = sel.closest("label").querySelector("[data-ayuda-rol]");
    if (ayuda) ayuda.hidden = sel.value !== "sin_perfil";
    sel.form.requestSubmit();
  }));
  // URL limpia (?seccion=usuarios&rol=motero): los campos vacíos no viajan
  raiz.querySelectorAll("form.cs-filtros").forEach((f) => f.addEventListener("submit", () => {
    f.querySelectorAll("[name]").forEach((c) => { if (!c.value) c.disabled = true; });
  }));
  window.addEventListener("pageshow", () => raiz.querySelectorAll("form.cs-filtros [disabled]").forEach((c) => { c.disabled = false; }));

  // ---------- Navegación, rol y tema ----------
  const movil = raiz.querySelector("[data-navegar]");
  if (movil) movil.addEventListener("change", () => { location.href = "?seccion=" + encodeURIComponent(movil.value); });

  const rol = raiz.querySelector("[data-rol]");
  const soloTaller = raiz.querySelector("[data-solo-taller]");
  if (rol && soloTaller) rol.addEventListener("change", () => { soloTaller.hidden = rol.value !== "taller"; });

  // Tema: hay un botón en la barra lateral y otro en el desplegable del celular; el texto visible dice a qué tema pasa
  raiz.querySelectorAll("[data-tema]").forEach((b) => b.addEventListener("click", () => {
    const nuevo = document.documentElement.dataset.consolaTema === "claro" ? "oscuro" : "claro";
    document.documentElement.dataset.consolaTema = nuevo;
    try { localStorage.setItem("consola-tema", nuevo); } catch (e) { /* */ }
  }));
})();
