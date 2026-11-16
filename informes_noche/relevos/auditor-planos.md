# Relevo — Auditor de Planos (filtro 4 + diagnóstico guiado)

## Hecho
- Filtro 4 (docs/auditor.md): capa 1 (todas las piezas), capa 2 (por concepto) y capa 3 (intervalos) completas. Tandas 1–5 de arreglos aplicadas por Planos y verificadas. Registro: `AUDITORIA_FUENTES.md` (+ criterios en `AUDITORIA_DESPIECE.md`).
- Capa 3: 25/25 líneas con `garaje/intervalos/<slug>.json` (fuente por cifra, `aproximado` cuando no es exacta; null = plan general, 0 = sin límite). Gixxer con `versiones` por año. Valida `manage.py test garaje.tests_avisos.ArchivosIntervalosTests` (OK).
- Fuente única: la guía de pieza con tarea toma el texto de `intervalo_para(...)`; 0 conflictos en 9.446 piezas.
- Diagnóstico guiado `/diagnostico/` (archivos propios): esquema completo numerado con sospechosas resaltadas, lista al lado, guía real de despiece.js como emergente (`TallerYaDespiece.abrirGuia`), buscador de motos (combobox), enlace "¿Te varaste?", 7 arreglos de seguridad del auditor mecánico. Gratis para todos (lo de Plus se canceló). Pruebas `garaje.tests_diagnostico` OK.

## Pendiente (menor)
- Planos: Discover "Batería de gel" muestra cifras propias en vez del intervalo único. Al aplicarlo: volcado nuevo (`capa1_volcado.py`, ~10 min, en segundo plano) y `criterios_planos.py 3`.
- Sin pieza (aceptado abierto): batería de la Boxer, barras delanteras de la Dynamic Pro.
- Sugerido: versionar estáticos en base.html (caché del navegador del CSS).
- Nada en commit; solo si el usuario lo pide.

## Archivos clave
- `garaje/diagnostico.py`, `garaje/vista_diagnostico.py`, `garaje/templates/garaje/diagnostico.html`, `_visor_despiece_oculto.html`, `_diag_esquema*.html`
- `garaje/static/garaje/js/diagnostico.js`, `diag_buscador.js`; bloques `.diag-*`/`.dg-*` al final de `tallerya.css`
- `garaje/intervalos.py` + `garaje/intervalos/*.json`
- Scripts (scratchpad, pueden borrarse): capa1_volcado/analisis, criterios_planos, cuadro_casillas (Yamaha √), honda_cuadro, bajaj_cuadro, tanda3/4_intervalos.

## Reglas
- No edita código ni datos del despiece: arreglos en tandas a "Planos y Esquema Piezas". Reportes al usuario solo vía Auxiliares (3–5 líneas).
- `manual_despiece/` y planos de terceros solo en local; no copiar texto de manuales (algunos AKT traen marca de agua con datos personales).
