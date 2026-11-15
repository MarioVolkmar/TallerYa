/* Foro: responder en hilo, colapsar respuestas y autocompletar @menciones (accesible con teclado y lector de pantalla). */
(function () {
  "use strict";
  var script = document.currentScript;
  var URL_SUGERIR = script && script.dataset.sugerir;
  var PREGUNTA = script && script.dataset.pregunta;

  /* ---------- Responder a un mensaje: el formulario se abre ahí mismo ---------- */
  function cerrarForm(slot) {
    var boton = document.querySelector('.fo-responder[aria-controls="' + slot.id + '"]');
    slot.innerHTML = "";
    if (boton) boton.setAttribute("aria-expanded", "false");
    return boton;
  }

  function abrirForm(boton) {
    var pk = boton.dataset.responder, slot = document.getElementById("responder-" + pk);
    var plantilla = document.getElementById("fo-plantilla-hilo");
    if (!slot || !plantilla) return false;
    if (slot.querySelector("form")) {  // segundo toque: cerrar (si no hay nada escrito)
      var t = slot.querySelector("textarea");
      if (!t.value.trim()) cerrarForm(slot); else t.focus();
      return true;
    }
    document.querySelectorAll(".fo-responder-slot").forEach(function (otro) {
      var ta = otro.querySelector("textarea");
      if (otro !== slot && ta && !ta.value.trim()) cerrarForm(otro);
    });
    var form = plantilla.content.firstElementChild.cloneNode(true);
    form.querySelector('[name="padre"]').value = pk;
    var ta = form.querySelector("textarea"), id = "cuerpo-hilo-" + pk;
    ta.id = id;
    form.querySelector("label").setAttribute("for", id);
    form.querySelector("[data-nombre]").textContent = boton.dataset.nombre || "";
    form.querySelector(".fo-cancelar").setAttribute("href", "#r" + pk);
    slot.appendChild(form);
    boton.setAttribute("aria-expanded", "true");
    ta.focus();
    return true;
  }

  document.addEventListener("click", function (e) {
    var boton = e.target.closest(".fo-responder");
    if (boton && abrirForm(boton)) { e.preventDefault(); return; }
    var cancelar = e.target.closest(".fo-cancelar");
    if (cancelar) {
      var slot = cancelar.closest(".fo-responder-slot");
      if (slot) { e.preventDefault(); var b = cerrarForm(slot); if (b) b.focus(); }
      return;
    }
    var colapsar = e.target.closest(".fo-colapsar");
    if (colapsar) {
      var hilo = document.getElementById(colapsar.getAttribute("aria-controls"));
      var abierto = colapsar.getAttribute("aria-expanded") === "true";
      hilo.hidden = abierto;
      colapsar.setAttribute("aria-expanded", String(!abierto));
      colapsar.textContent = textoColapsar(colapsar.dataset.n, !abierto);
    }
  });

  function textoColapsar(n, abierto) {
    var s = n === "1" ? "respuesta" : "respuestas";
    return (abierto ? "Ocultar " : "Ver ") + n + " " + s;
  }
  document.querySelectorAll(".fo-colapsar").forEach(function (b) { b.hidden = false; });

  // Si se llega con #rID a una respuesta escondida en un hilo colapsado, se abre.
  function revelar() {
    var el = location.hash && document.getElementById(location.hash.slice(1));
    while (el && (el = el.parentElement)) {
      if (el.classList.contains("fo-hilo") && el.hidden) {
        var b = document.querySelector('.fo-colapsar[aria-controls="' + el.id + '"]');
        if (b) b.click();
      }
    }
  }
  window.addEventListener("hashchange", revelar);


  /* ---------- Aviso discreto ---------- */
  var avisoT = null;
  function avisar(texto) {
    var a = document.querySelector(".fo-aviso");
    if (!a) return;
    a.textContent = texto;
    a.hidden = false;
    clearTimeout(avisoT);
    avisoT = setTimeout(function () { a.hidden = true; }, 3500);
  }

  /* ---------- Menús desplegables (⋯ y selector de reacciones): se cierran al tocar fuera o con Escape ---------- */
  function cerrarMenus(excepto) {
    document.querySelectorAll(".fo-menu[open], .fo-reaccionar[open]").forEach(function (d) { if (d !== excepto) d.open = false; });
  }
  document.addEventListener("click", function (e) { cerrarMenus(e.target.closest(".fo-menu, .fo-reaccionar")); });
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    var abierto = document.querySelector(".fo-menu[open], .fo-reaccionar[open]");
    if (abierto) { abierto.open = false; abierto.querySelector("summary").focus(); }
  });

  // El selector de reacciones flota sobre el botón (o debajo si no hay espacio arriba) sin salirse de la pantalla.
  var MARGEN = 16;
  document.addEventListener("toggle", function (e) {
    var d = e.target;
    if (!d.classList || !d.classList.contains("fo-reaccionar") || !d.open) return;
    var sel = d.querySelector(".fo-selector"), boton = d.querySelector("summary").getBoundingClientRect();
    sel.classList.remove("fo-abajo");
    sel.style.left = "0px"; sel.style.transform = "none";
    var ancho = sel.offsetWidth, vw = document.documentElement.clientWidth;
    var izq = boton.left + boton.width / 2 - ancho / 2;
    izq = Math.max(MARGEN, Math.min(izq, vw - MARGEN - ancho));
    sel.style.left = (izq - boton.left) + "px";
    if (sel.getBoundingClientRect().top < 72) sel.classList.add("fo-abajo");  // la cabecera fija tapa lo de arriba
  }, true);

  /* ---------- Reacciones sin recargar (respaldo: el formulario POST normal) ---------- */
  document.addEventListener("submit", function (e) {
    var form = e.target.closest(".fo-reacciones-form");
    if (!form || !e.submitter) return;
    e.preventDefault();
    var datos = new FormData(form);
    datos.set("reaccion", e.submitter.value);
    fetch(form.action, { method: "POST", body: datos, headers: { "X-Requested-With": "fetch" } })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (!d.ok) { avisar(d.mensaje || "No se pudo guardar la reacción."); return; }
        var fila = form.closest("[data-reacciones]"), clave = fila.dataset.reacciones;
        fila.outerHTML = d.html;
        var nueva = document.querySelector('[data-reacciones="' + clave + '"] .fo-reaccionar summary');
        if (nueva) nueva.focus();
      })
      .catch(function () {
        var oculto = document.createElement("input");
        oculto.type = "hidden"; oculto.name = "reaccion"; oculto.value = e.submitter.value;
        form.appendChild(oculto); form.submit();
      });
  });

  /* ---------- Copiar enlace ---------- */
  document.addEventListener("click", function (e) {
    var a = e.target.closest("[data-copiar]");
    if (!a || !navigator.clipboard) return;
    e.preventDefault();
    navigator.clipboard.writeText(a.href).then(function () { avisar("Enlace copiado"); }, function () { location.href = a.href; });
    var menu = a.closest(".fo-menu"); if (menu) menu.open = false;
  });

  /* ---------- Reportar: diálogo con motivos ---------- */
  var dialogo = document.getElementById("reporte"), origen = null;
  if (dialogo && dialogo.showModal) {
    var formR = dialogo.querySelector("form"), detalle = formR.querySelector("[name=motivo]");
    function validarOtro() {
      var otro = formR.querySelector("[name=motivo_tipo]:checked");
      detalle.setCustomValidity(otro && otro.value === "otro" && !detalle.value.trim() ? "Cuéntanos el motivo." : "");
    }
    formR.addEventListener("change", validarOtro);
    detalle.addEventListener("input", validarOtro);
    document.addEventListener("click", function (e) {
      var a = e.target.closest("[data-reportar]");
      if (a) {
        e.preventDefault();
        origen = a;
        formR.reset();
        formR.action = a.dataset.reportar;
        var menu = a.closest(".fo-menu"); if (menu) menu.open = false;
        dialogo.showModal();
        return;
      }
      if (e.target.closest("#reporte [data-cerrar]")) { e.preventDefault(); dialogo.close(); }
    });
    dialogo.addEventListener("close", function () { if (origen) { var m = origen.closest(".fo-menu"); if (m) m.querySelector("summary").focus(); } });
    formR.addEventListener("submit", function (e) {
      validarOtro();
      if (!formR.checkValidity()) return;
      e.preventDefault();
      fetch(formR.action, { method: "POST", body: new FormData(formR), headers: { "X-Requested-With": "fetch" } })
        .then(function (r) { return r.json(); })
        .then(function (d) {
          dialogo.close();
          avisar(d.mensaje);
          if (origen) {
            var span = document.createElement("span");
            span.className = "fo-menu-op fo-menu-inactivo"; span.textContent = "Ya lo reportaste";
            origen.replaceWith(span); origen = null;
          }
          if (d.oculta) setTimeout(function () { location.reload(); }, 1200);
        })
        .catch(function () { formR.submit(); });
    });
  }
  /* ---------- Autocompletado de @menciones ---------- */
  if (!URL_SUGERIR) return;
  var RE_TOKEN = /(^|[^\w@])@([\p{L}\p{N}]{0,30})$/u;
  var cache = {}, temporizador = null, n = 0;
  var estado = document.createElement("div");
  estado.className = "sr-only fo-sr";
  estado.setAttribute("role", "status");
  estado.setAttribute("aria-live", "polite");
  document.body.appendChild(estado);

  function preparar(ta) {
    if (ta.dataset.mencionesListo) return;
    ta.dataset.mencionesListo = "1";
    var lista = document.createElement("ul");
    lista.id = "fo-sugerencias-" + (++n);
    lista.className = "fo-sugerencias";
    lista.setAttribute("role", "listbox");
    lista.setAttribute("aria-label", "Personas para mencionar");
    lista.hidden = true;
    ta.insertAdjacentElement("afterend", lista);
    ta.setAttribute("aria-autocomplete", "list");
    ta.setAttribute("aria-controls", lista.id);
    ta.setAttribute("aria-expanded", "false");
    ta._lista = lista;
  }

  function token(ta) {
    var antes = ta.value.slice(0, ta.selectionStart);
    var m = antes.match(RE_TOKEN);
    return m ? { q: m[2], inicio: antes.length - m[2].length - 1 } : null;
  }

  function cerrar(ta) {
    if (!ta._lista) return;
    ta._lista.hidden = true;
    ta._lista.innerHTML = "";
    ta.setAttribute("aria-expanded", "false");
    ta.removeAttribute("aria-activedescendant");
  }

  function mostrar(ta, usuarios) {
    var lista = ta._lista;
    lista.innerHTML = "";
    if (!usuarios.length) { cerrar(ta); estado.textContent = "Sin coincidencias"; return; }
    usuarios.forEach(function (u, i) {
      var li = document.createElement("li");
      li.id = lista.id + "-" + i;
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", i === 0 ? "true" : "false");
      li.dataset.alias = u.alias;
      li.innerHTML = "<strong></strong>" + (u.detalle ? " <small></small>" : "");
      li.querySelector("strong").textContent = u.nombre;
      if (u.detalle) li.querySelector("small").textContent = u.detalle;
      lista.appendChild(li);
    });
    lista.hidden = false;
    ta.setAttribute("aria-expanded", "true");
    ta.setAttribute("aria-activedescendant", lista.id + "-0");
    estado.textContent = usuarios.length + (usuarios.length === 1 ? " sugerencia" : " sugerencias") +
      ". Flechas para elegir, Enter para mencionar, Escape para cerrar.";
  }

  function buscar(ta) {
    var t = token(ta);
    if (!t) { cerrar(ta); return; }
    var clave = t.q.toLowerCase();
    if (cache[clave]) { mostrar(ta, cache[clave]); return; }
    clearTimeout(temporizador);
    temporizador = setTimeout(function () {
      fetch(URL_SUGERIR + "?q=" + encodeURIComponent(t.q) + "&pregunta=" + encodeURIComponent(PREGUNTA || ""),
            { headers: { "X-Requested-With": "fetch" } })
        .then(function (r) { return r.ok ? r.json() : { usuarios: [] }; })
        .then(function (d) {
          cache[clave] = d.usuarios;
          var actual = token(ta);
          if (actual && actual.q.toLowerCase() === clave && document.activeElement === ta) mostrar(ta, d.usuarios);
        })
        .catch(function () { cerrar(ta); });
    }, 150);
  }

  function elegir(ta, li) {
    var t = token(ta);
    if (!t || !li) return;
    var texto = "@" + li.dataset.alias + " ";
    ta.value = ta.value.slice(0, t.inicio) + texto + ta.value.slice(ta.selectionStart);
    var pos = t.inicio + texto.length;
    ta.setSelectionRange(pos, pos);
    estado.textContent = li.querySelector("strong").textContent + " mencionado";
    cerrar(ta);
    ta.focus();
  }

  function mover(ta, paso) {
    var ops = Array.prototype.slice.call(ta._lista.children), i = ops.findIndex(function (o) {
      return o.getAttribute("aria-selected") === "true";
    });
    if (i >= 0) ops[i].setAttribute("aria-selected", "false");
    i = (i + paso + ops.length) % ops.length;
    ops[i].setAttribute("aria-selected", "true");
    ops[i].scrollIntoView({ block: "nearest" });
    ta.setAttribute("aria-activedescendant", ops[i].id);
  }

  document.addEventListener("focusin", function (e) {
    if (e.target.matches("textarea[data-menciones]")) preparar(e.target);
  });
  document.addEventListener("input", function (e) {
    if (e.target._lista) buscar(e.target);
  });
  document.addEventListener("keydown", function (e) {
    var ta = e.target;
    if (!ta._lista || ta._lista.hidden) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); mover(ta, e.key === "ArrowDown" ? 1 : -1); }
    else if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      elegir(ta, ta._lista.querySelector('[aria-selected="true"]'));
    } else if (e.key === "Escape") { e.preventDefault(); cerrar(ta); }
  });
  document.addEventListener("mousedown", function (e) {
    var li = e.target.closest(".fo-sugerencias [role=option]");
    if (!li) return;
    e.preventDefault();  // que el textarea no pierda el foco
    var ta = li.parentElement.previousElementSibling;
    elegir(ta, li);
  });
  document.addEventListener("focusout", function (e) {
    var ta = e.target;
    if (ta._lista) setTimeout(function () { if (document.activeElement !== ta) cerrar(ta); }, 100);
  });
})();
