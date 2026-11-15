// Diagnóstico: buscador de motos con despiece. Combobox propio (ARIA 1.2: role combobox + listbox con
// aria-activedescendant) armado a partir del <select> de respaldo, que se oculta cuando hay JavaScript.
(function () {
  const caja = document.querySelector("[data-combo]");
  const select = document.getElementById("diag-moto-lista");
  if (!caja || !select) return;
  const campo = document.getElementById("diag-buscar-moto");
  const panel = document.getElementById("diag-combo-lista");
  const form = select.form;

  // Sin año ni tildes para comparar; un carácter por carácter, para poder resaltar en el texto original
  const plano = (t) => [...t].map((c) => c.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()).join("");

  const motos = [];
  select.querySelectorAll("optgroup").forEach((g) => {
    g.querySelectorAll("option").forEach((o) => motos.push({ id: o.value, marca: g.label, texto: o.textContent.trim(), modelo: o.dataset.modelo || o.textContent }));
  });

  let visibles = [];
  let activa = -1;

  function resaltado(texto, q) {
    const frag = document.createDocumentFragment();
    const i = q ? plano(texto).indexOf(q) : -1;
    if (i < 0) { frag.append(texto); return frag; }
    const mark = document.createElement("mark");
    mark.textContent = texto.slice(i, i + q.length);
    frag.append(texto.slice(0, i), mark, texto.slice(i + q.length));
    return frag;
  }

  function pintar() {
    const q = plano(campo.value.trim());
    visibles = motos.filter((m) => !q || plano(m.texto).includes(q));
    panel.replaceChildren();
    if (!visibles.length) {
      const li = document.createElement("li");
      li.className = "diag-combo-vacio";
      li.textContent = "Ninguna moto con ese nombre tiene despiece todavía.";
      panel.appendChild(li);
    }
    let marca = null;
    visibles.forEach((m, i) => {
      if (m.marca !== marca) {
        marca = m.marca;
        const rotulo = document.createElement("li");
        rotulo.className = "diag-combo-marca";
        rotulo.setAttribute("role", "presentation");
        rotulo.textContent = marca;
        panel.appendChild(rotulo);
      }
      const li = document.createElement("li");
      li.id = `diag-combo-op-${m.id}`;
      li.className = "diag-combo-op";
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      li.dataset.i = i;
      li.appendChild(resaltado(m.texto, q));
      li.addEventListener("pointerdown", (e) => e.preventDefault());   // que el campo no pierda el foco
      li.addEventListener("click", () => elegir(i));
      li.addEventListener("pointermove", () => mover(i, false));
      panel.appendChild(li);
    });
    activa = q && visibles.length ? 0 : -1;
    marcar(true);
  }

  function marcar(desplazar) {
    panel.querySelectorAll(".diag-combo-op").forEach((li) => {
      const si = Number(li.dataset.i) === activa;
      li.classList.toggle("activa", si);
      li.setAttribute("aria-selected", String(si));
      if (si && desplazar) li.scrollIntoView({ block: "nearest" });
    });
    if (activa >= 0) campo.setAttribute("aria-activedescendant", `diag-combo-op-${visibles[activa].id}`);
    else campo.removeAttribute("aria-activedescendant");
  }

  function mover(i, desplazar = true) {
    activa = Math.max(0, Math.min(visibles.length - 1, i));
    marcar(desplazar);
  }

  function abrir() {
    if (!panel.hidden) return;
    pintar();
    panel.hidden = false;
    campo.setAttribute("aria-expanded", "true");
  }

  function cerrar() {
    panel.hidden = true;
    campo.setAttribute("aria-expanded", "false");
    campo.removeAttribute("aria-activedescendant");
  }

  function elegir(i) {
    const m = visibles[i];
    if (!m) return;
    campo.value = m.texto;
    select.value = m.id;
    cerrar();
    form.submit();
  }

  campo.addEventListener("focus", abrir);
  campo.addEventListener("click", abrir);
  campo.addEventListener("input", () => { abrir(); pintar(); });
  campo.addEventListener("blur", () => setTimeout(cerrar, 120));
  campo.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); abrir(); mover(activa + 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); abrir(); mover(activa - 1); }
    else if (e.key === "Enter") { e.preventDefault(); if (!panel.hidden && activa >= 0) elegir(activa); }
    else if (e.key === "Escape") { if (!panel.hidden) { e.preventDefault(); cerrar(); } else campo.value = ""; }
  });

  // Con JavaScript: se ve el combobox y se oculta el respaldo (select y botón)
  form.querySelectorAll(".diag-combo-respaldo").forEach((e) => { e.hidden = true; e.style.display = "none"; });
  caja.hidden = false;
  document.getElementById("diag-catalogo-label")?.setAttribute("for", "diag-buscar-moto");
  const elegida = select.selectedOptions[0];
  if (elegida && elegida.value) campo.value = elegida.textContent.trim();
})();
