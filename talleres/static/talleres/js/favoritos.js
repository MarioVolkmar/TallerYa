// Corazón de favoritos: guarda o quita sin recargar la página (si falla, envía el formulario normal).
document.addEventListener("submit", async (e) => {
  const form = e.target.closest(".fav-form");
  if (!form) return;
  e.preventDefault();
  const boton = form.querySelector("button");
  try {
    const r = await fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" } });
    if (!r.ok) throw new Error(r.status);
    const { favorito } = await r.json();
    boton.classList.toggle("activo", favorito);
    boton.setAttribute("aria-pressed", favorito);
    boton.title = favorito ? "Quitar de favoritos" : "Guardar en favoritos";
    const texto = boton.querySelector(".fav-texto");
    if (texto) texto.textContent = favorito ? "En favoritos" : "Guardar";
    boton.classList.remove("late");
    void boton.offsetWidth;
    if (favorito) boton.classList.add("late");
  } catch (_) {
    form.submit();
  }
});
