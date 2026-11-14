// Paginación sencilla para listas largas: <ul data-paginar="5"> muestra 5 elementos y un botón "Ver más".
// Los filtros marcan con la clase "filtrado" lo que no aplica y llaman a TallerYaPaginar.refrescar(lista).
(function () {
  function preparar(lista) {
    if (lista._paginar) return lista._paginar;
    var tam = Number(lista.dataset.paginar) || 5;
    var pie = document.createElement("div");
    pie.className = "paginar-pie";
    var info = document.createElement("span");
    info.className = "paginar-info";
    var mas = document.createElement("button");
    mas.type = "button";
    mas.className = "paginar-boton";
    var menos = document.createElement("button");
    menos.type = "button";
    menos.className = "paginar-boton paginar-menos";
    menos.textContent = "Ver menos";
    pie.append(info, mas, menos);
    lista.after(pie);
    var estado = { tam: tam, mostrados: tam, pie: pie, info: info, mas: mas, menos: menos };
    mas.addEventListener("click", function () { estado.mostrados += tam; pintar(lista); });
    menos.addEventListener("click", function () {
      estado.mostrados = tam; pintar(lista);
      lista.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
    lista._paginar = estado;
    return estado;
  }

  function pintar(lista) {
    var e = preparar(lista);
    var items = Array.prototype.filter.call(lista.children, function (li) { return !li.classList.contains("filtrado"); });
    Array.prototype.forEach.call(lista.children, function (li) { li.classList.remove("paginado"); });
    items.forEach(function (li, i) { li.classList.toggle("paginado", i >= e.mostrados); });
    var total = items.length, vistos = Math.min(total, e.mostrados);
    e.pie.hidden = total <= e.tam;
    e.info.textContent = "Mostrando " + vistos + " de " + total;
    var faltan = total - vistos;
    e.mas.hidden = faltan <= 0;
    e.mas.textContent = "Ver " + Math.min(faltan, e.tam) + " más";
    e.menos.hidden = faltan > 0 || total <= e.tam;
  }

  window.TallerYaPaginar = {
    refrescar: function (lista) { var e = preparar(lista); e.mostrados = e.tam; pintar(lista); },
  };
  function iniciar() { document.querySelectorAll("[data-paginar]").forEach(pintar); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar); else iniciar();
})();

  // Filtros de listas paginadas (bitácora y lecturas): botones/selects con data-filtro dentro de [data-filtros-de="id de la lista"].
  (function () {
    function aplicar(lista, filtros) {
      var hoy = new Date();
      var visibles = 0;
      Array.prototype.forEach.call(lista.children, function (li) {
        var ok = true;
        Object.keys(filtros).forEach(function (k) {
          var v = filtros[k];
          if (!v) return;
          if (k === "dias") ok = ok && (hoy - new Date(li.dataset.fecha + "T00:00:00")) / 864e5 <= Number(v);
          else ok = ok && (li.dataset[k] || "").split(" ").indexOf(v) >= 0;
        });
        li.classList.toggle("filtrado", !ok);
        if (ok) visibles++;
      });
      var vacio = lista.parentElement.querySelector(".lista-vacia");
      if (vacio) vacio.hidden = visibles > 0;
      window.TallerYaPaginar && window.TallerYaPaginar.refrescar(lista);
    }
    function iniciarFiltros() { document.querySelectorAll("[data-filtros-de]").forEach(function (caja) {
      var lista = document.getElementById(caja.dataset.filtrosDe);
      if (!lista) return;
      var filtros = {};
      caja.querySelectorAll("button[data-filtro]").forEach(function (b) {
        b.addEventListener("click", function () {
          caja.querySelectorAll('button[data-filtro="' + b.dataset.filtro + '"]').forEach(function (o) { o.setAttribute("aria-pressed", String(o === b)); });
          filtros[b.dataset.filtro] = b.dataset.valor;
          aplicar(lista, filtros);
        });
      });
      caja.querySelectorAll("select[data-filtro]").forEach(function (s) {
        s.addEventListener("change", function () { filtros[s.dataset.filtro] = s.value; aplicar(lista, filtros); });
      });
    }); }
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciarFiltros); else iniciarFiltros();
  })();
