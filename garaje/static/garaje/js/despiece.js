// Despiece interactivo: láminas del catálogo con las piezas marcadas y coloreadas por estado.
(function () {
  const nodo = document.getElementById("datos-despiece");
  if (!nodo) return;
  const datos = JSON.parse(nodo.textContent);
  const laminas = datos.laminas;
  const $ = (id) => document.getElementById(id);
  const tabs = $("laminas-tabs");
  const img = $("lamina-img");
  const caja = $("lamina-imagen");
  const ficha = $("parte-ficha");
  const listaMant = $("partes-mant");
  const listaTodas = $("partes-todas");
  const ampliar = $("lamina-ampliar");
  const ETIQUETA = { ok: "Al día", pronto: "Pronto", vencido: "Toca ya", desconocido: "Sin registro" };
  let actual = null;
  let elegida = null;

  function texto(etiqueta, clase, contenido) {
    const el = document.createElement(etiqueta);
    if (clase) el.className = clase;
    if (contenido !== undefined) el.textContent = contenido;
    return el;
  }

  // Pestañas, una por lámina (las más urgentes primero)
  laminas.forEach((l) => {
    const b = texto("button", "lamina-tab");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.dataset.id = l.id;
    if (l.estado) b.appendChild(texto("span", `punto-mini punto-${l.estado}`));
    b.appendChild(document.createTextNode(l.nombre));
    b.addEventListener("click", () => mostrar(l));
    tabs.appendChild(b);
  });

  function mostrar(lamina, parteId) {
    actual = lamina;
    elegida = null;
    tabs.querySelectorAll(".lamina-tab").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.id == lamina.id)));
    $("lamina-titulo").textContent = `FIG. ${lamina.figura} · ${lamina.nombre}`;
    img.src = lamina.imagen;
    img.alt = `Despiece: ${lamina.nombre}`;
    img.width = lamina.ancho;
    img.height = lamina.alto;
    caja.querySelectorAll(".punto").forEach((p) => p.remove());

    listaMant.innerHTML = "";
    listaTodas.innerHTML = "";
    const vistas = new Set();
    lamina.partes.forEach((p) => {
      const punto = texto("button", `punto ${p.estado ? "punto-" + p.estado : "punto-neutro"}`, String(p.ref));
      punto.type = "button";
      punto.style.left = p.x * 100 + "%";
      punto.style.top = p.y * 100 + "%";
      punto.dataset.id = p.id;
      punto.setAttribute("aria-label", `${p.ref}: ${p.nombre}`);
      punto.addEventListener("click", () => elegir(p));
      caja.appendChild(punto);

      if (vistas.has(p.ref)) return; // el catálogo repite referencias (izquierda/derecha)
      vistas.add(p.ref);
      const li = texto("li");
      const b = texto("button", "parte-fila");
      b.type = "button";
      b.dataset.id = p.id;
      b.append(texto("span", "parte-ref", String(p.ref)), texto("span", "parte-nombre", p.nombre));
      if (p.estado) b.appendChild(texto("span", `estado estado-${p.estado}`, ETIQUETA[p.estado]));
      b.addEventListener("click", () => elegir(p, true));
      li.appendChild(b);
      (p.tarea ? listaMant : listaTodas).appendChild(li);
    });
    if (!listaMant.children.length) listaMant.appendChild(texto("li", "text-sm text-suave", "Esta lámina no tiene piezas del plan."));
    $("partes-todas-resumen").textContent = `Todas las piezas (${listaTodas.children.length})`;

    const inicial = lamina.partes.find((p) => p.id === parteId) ||
      lamina.partes.filter((p) => p.tarea).sort((a, b) => peso(b.estado) - peso(a.estado))[0];
    if (inicial) elegir(inicial); else ficha.innerHTML = '<p class="text-sm text-suave">Elige una pieza en el dibujo o en la lista.</p>';
  }

  function peso(estado) {
    return { vencido: 3, pronto: 2, desconocido: 1, ok: 0 }[estado] ?? -1;
  }

  function elegir(parte, centrar) {
    elegida = parte;
    caja.querySelectorAll(".punto").forEach((p) => p.classList.toggle("elegido", p.dataset.id == parte.id));
    document.querySelectorAll(".parte-fila").forEach((f) => f.classList.toggle("elegida", f.dataset.id == parte.id));
    ficha.innerHTML = "";
    const cabeza = texto("div", "flex items-start justify-between gap-3");
    const titulo = texto("div");
    titulo.append(texto("p", "titulo text-xl", parte.nombre), texto("p", "text-xs text-suave mt-0.5", `Ref. ${parte.ref} · ${parte.descripcion}`));
    cabeza.appendChild(titulo);
    if (parte.estado) cabeza.appendChild(texto("span", `estado estado-${parte.estado}`, ETIQUETA[parte.estado]));
    ficha.appendChild(cabeza);

    const codigo = texto("div", "codigo-repuesto mt-4");
    codigo.append(texto("span", "text-xs text-suave block", "Código de repuesto original"), texto("strong", "", parte.codigo));
    const copiar = texto("button", "boton-texto", "Copiar");
    copiar.type = "button";
    copiar.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(parte.codigo); copiar.textContent = "¡Copiado!"; }
      catch { copiar.textContent = "Selecciona y copia"; }
      setTimeout(() => { copiar.textContent = "Copiar"; }, 1800);
    });
    codigo.appendChild(copiar);
    ficha.appendChild(codigo);
    ficha.appendChild(texto("p", "text-xs text-suave mt-2", `Cantidad en la moto: ${parte.cantidad}`));

    if (parte.tarea) {
      const t = texto("div", "mt-4 pt-4 border-t border-white/10");
      t.append(texto("p", "font-semibold text-sm", parte.tarea.nombre), texto("p", "text-xs text-suave mt-1", parte.tarea.detalle));
      if (parte.tarea.servicio) {
        const a = texto("a", "btn btn-lava text-[.65rem] px-4 py-2 mt-3", "Talleres que lo hacen");
        a.href = `/?servicio=${parte.tarea.servicio}`;
        t.appendChild(a);
      }
      ficha.appendChild(t);
    }
    if (centrar) {
      const punto = caja.querySelector(`.punto[data-id="${parte.id}"]`);
      punto?.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
    }
  }

  ampliar.addEventListener("click", () => {
    const activo = ampliar.getAttribute("aria-pressed") !== "true";
    ampliar.setAttribute("aria-pressed", String(activo));
    ampliar.textContent = activo ? "Reducir" : "Ampliar";
    caja.classList.toggle("ampliada", activo);
    if (activo && elegida) elegir(elegida, true);
  });

  // Puente con el modelo 3D: "Ver despiece" desde la ficha de una pieza.
  window.TallerYaDespiece = {
    tiene: (pieza) => laminas.some((l) => l.pieza === pieza),
    mostrar(pieza) {
      const lamina = laminas.find((l) => l.pieza === pieza);
      if (!lamina) return;
      mostrar(lamina);
      document.getElementById("despiece").scrollIntoView({ behavior: "smooth", block: "start" });
    },
  };

  if (laminas.length) mostrar(laminas[0]);
})();
