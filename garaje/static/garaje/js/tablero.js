// Tablero de la moto: actualizar el kilometraje sin recargar la página.
// Valida mientras escribes (no deja enviar un número menor al último) y hace rodar el odómetro.
(function () {
  const form = document.getElementById("form-km");
  const odometro = document.getElementById("odometro");
  if (!form || !odometro) return;
  const campo = form.querySelector('input[name="km"]');
  const boton = form.querySelector("button");
  const aviso = document.getElementById("km-aviso");
  const textoBase = aviso.textContent;
  const MAX_SALTO = 50000;
  const reducido = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let actual = Number(odometro.dataset.km);
  const miles = (n) => n.toLocaleString("es-CO");

  function decir(texto, clase) {
    aviso.className = "km-aviso" + (clase ? " " + clase : "");
    aviso.textContent = texto;
  }

  // ---- Validación en vivo ----
  function revisar() {
    const valor = campo.value.trim();
    if (valor === "") { boton.disabled = true; decir(textoBase); return false; }
    const km = Number(valor);
    if (!Number.isInteger(km) || km < 0) { boton.disabled = true; decir("Escribe solo números enteros.", "error-km"); return false; }
    if (km < actual) { boton.disabled = true; decir(`Debe ser ${miles(actual)} km o más: es lo último que registraste.`, "error-km"); return false; }
    if (km - actual > MAX_SALTO) { boton.disabled = true; decir("Ese salto es muy grande. Revisa el número.", "error-km"); return false; }
    boton.disabled = false;
    decir(km === actual ? "Es el mismo kilometraje; lo guardamos como lectura de hoy." : `Vas a sumar ${miles(km - actual)} km.`);
    return true;
  }
  campo.addEventListener("input", revisar);
  revisar();

  // ---- Odómetro que rueda ----
  function pintarOdometro(valor) {
    const digitos = odometro.querySelectorAll(".odometro-digito");
    const texto = String(Math.round(valor)).padStart(digitos.length, "0").slice(-digitos.length);
    let relleno = true;
    digitos.forEach((d, i) => {
      if (texto[i] !== "0" || i === digitos.length - 1) relleno = false;
      d.textContent = texto[i];
      d.classList.toggle("relleno", relleno);
    });
  }
  function rodar(desde, hasta) {
    if (reducido) { pintarOdometro(hasta); return; }
    let inicio = null;
    const paso = (ts) => {
      inicio = inicio || ts;
      const p = Math.min(1, (ts - inicio) / 1200);
      pintarOdometro(desde + (hasta - desde) * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(paso);
    };
    requestAnimationFrame(paso);
  }

  // ---- Lo que cambia con el nuevo kilometraje ----
  function actualizarAceite(a) {
    const t = document.getElementById("tacometro");
    if (!t || !a) return;
    t.className = `tacometro tacometro-${a.estado}`;
    t.querySelector(".tacometro-valor").style.strokeDasharray = `${a.pct} 100`;
    t.querySelector(".tacometro-aguja").style.transform = `rotate(${a.giro}deg)`;
    t.querySelector(".tacometro-dato").textContent = a.dato;
    t.querySelector(".tacometro-detalle").textContent = a.detalle;
  }
  function actualizarLeyenda(conteos) {
    Object.entries(conteos || {}).forEach(([estado, n]) => {
      const li = document.querySelector(`.leyenda-3d-lista [data-grupo="${estado}"]`);
      if (!li) return;
      li.querySelector("strong").textContent = n;
      li.classList.toggle("vacio", n === 0);
    });
  }
  function cookie(nombre) {
    const m = document.cookie.match(new RegExp(`(?:^|; )${nombre}=([^;]*)`));
    return m ? decodeURIComponent(m[1]) : "";
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!revisar()) return;
    boton.disabled = true;
    decir("Guardando…");
    try {
      const r = await fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "fetch", "X-CSRFToken": cookie("csrftoken") },
        body: new FormData(form),
      });
      const datos = await r.json();
      if (!r.ok || !datos.ok) throw new Error(datos.error || "No se pudo guardar. Intenta de nuevo.");
      rodar(actual, datos.km);
      actual = datos.km;
      odometro.dataset.km = actual;
      odometro.setAttribute("aria-label", `${actual} kilómetros`);
      campo.value = "";
      campo.placeholder = `Último: ${actual}`;
      campo.min = actual;
      boton.disabled = true;
      const porDia = document.getElementById("km-por-dia");
      if (porDia && datos.km_por_dia) porDia.textContent = `≈ ${datos.km_por_dia} km al día`;
      actualizarAceite(datos.aceite);
      actualizarLeyenda(datos.conteos);
      decir(datos.mensaje, "listo");
      if (datos.cambiaron && datos.cambiaron.length) {
        // El modelo 3D y el plan de abajo se calculan al cargar: ofrecemos verlos actualizados.
        aviso.append(` Cambió: ${datos.cambiaron.join(", ")}.`);
        const ver = document.createElement("a");
        ver.href = location.pathname;
        ver.className = "km-cambios";
        ver.textContent = "Ver el plan actualizado";
        aviso.append(" ", ver);
      }
    } catch (err) {
      decir(err.message, "error-km");
      boton.disabled = false;
    }
  });
})();
