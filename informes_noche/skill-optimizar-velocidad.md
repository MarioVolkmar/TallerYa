# Skill `optimizar-velocidad` y auditoría de carga — 19-nov-2026

Skill nueva en `.claude/skills/optimizar-velocidad/` (respaldo en `~/.claude/skills_respaldo/tallerya/`). No se tocó código
de la página. Sin commit. Únicos cambios fuera de la skill: una línea en `CLAUDE.md` y el preview `tallerya-medir`
(127.0.0.1:8024, `--noreload`) en `.claude/launch.json`.

**Contenido:** `SKILL.md` (flujo medir → presupuesto → priorizar → aplicar → volver a medir, más el autocontrol),
`anexo-presupuesto.md` (metas, topes y línea base), `anexo-tecnicas.md` (servidor, página, esquema y 3D),
`anexo-medicion.md`, y los scripts `medir.js` (para `javascript_tool`), `medir_chrome.py` (Chrome sin ventana: cuenta como
pestaña visible, GPU real, perfil «celular de referencia» 375 px, CPU ×4 y 4G), `servidor.py` (ms y consultas por URL),
`pesos.py` (KB brotli y gzip como en producción), `traza.py` (qué llena las tareas largas) y `sesion.py`.

## Auditoría (solo medición)
Servidor `tallerya-medir`, carga fría, moto 3 con la cuenta del dueño (sesión creada por shell). «375/4G» = celular de
referencia; «375» = solo el ancho, sin freno (comparable con `velocidad-detalle-moto.md`).

| Medida | Página | 1366 | 375 | 375/4G | Meta / tope | |
|---|---|---|---|---|---|---|
| LCP | portada | — ¹ | — | 2,8 | 2,5 / 4 | ✗ meta |
| LCP | talleres | 1,2 | — | 2,9 | 2,5 / 4 | ✗ meta |
| LCP | mecánicos | 1,8 | — | 4,6 | 2,5 / 4 | ✗ tope |
| LCP | moto 3 | 10,8 | 3,2 | 21,0 | 2,5 / 4 | ✗ tope |
| Esquema visible | moto 3 | 4,1 | 4,4 | 20,0 | 3 / 6 | ✗ tope |
| 3D listo | moto 3 | 11,8 | 7,1 | 37,3 | 4 (×4: 12) / 8 (×4: 20) | ✗ tope |
| 3D listo, tibia | moto 3 | 5,7 | 2,8 | 30,8 | 2,5 / 4 | ✗ |
| Tarea larga máx. | portada · talleres · mecánicos · moto | 0,25 · 0,16 · 0,17 · 5,6 | — · — · — · 2,1 | 5,0 · 2,8 · 1,5 · 4,3 | 0,5 / 1 | ✗ |
| CSS (br) | todas | 80-81 KB | | | 40 / 60 | ✗ tope |
| JS (br) | moto 3 · resto | 283 · 14 KB | | | 250 / 350 · 50 | ✗ meta |
| JSON despiece · SVG (br) | moto 3 | 32 · 35 KB | | | 30-40 / 40-60 | ✓ |
| Servidor | portada · talleres · mecánicos · moto · despiece.json | 141 · 127 · 93 · 338 · 87 ms | | | 150 / 300 | moto ✗ |
| Consultas | ídem | 15 · 12 · 11 · 39 (1 repetida) · 13 | | | 20 / 35 | moto ✗ |

¹ La portada no registra LCP en escritorio (probable texto con animación de opacidad); FCP en 375/4G: 2,8 s.

## Mejoras priorizadas (impacto en el celular ÷ esfuerzo)
1. **`personalizar.js` hace 4,8 s de trabajo (CPU ×4) al recibir `moto3d-listo`** (`iniciar()`: `conectar3D`, `pintarColores`,
   `repintarCalcas`, `pintarFabrica`). Es la tarea larga más grande del detalle y retrasa el esquema y los toques. Diferir
   todo menos el botón a `requestIdleCallback` o al abrir el cajón. **S**. (Archivo del 3D/Personalizar: proponer a esa sesión.)
2. **Esperas de GPU en `moto3d.js`, en frío:** entre `boceto` y `compilaAsync` pasan **6,0 s** en 1366 (tibio 0,15 s);
   `pedazoMasLargo` 6,9 s y una `GPUTask` de 4,1 s en la traza. `compileAsync` sin `render` ni consultas de estado antes de
   que termine, menos variantes de material y sombras con un solo programa (`anexo-tecnicas.md`, 3D). **M**. Sesión del 3D.
3. **Portada: una tarea de 4,3 s (CPU ×4) que es casi todo Layout (3,0 s) + estilos (0,8 s) con solo 974 nodos.** Sospechosos:
   `tallerya.css` (469 KB bruto, 4.600 reglas, 27 `:has()`, `backdrop-filter`) y las fuentes de Google (7 pesos). En
   talleres, `controles.js` evalúa 0,8 s con Layout dentro. Partir el CSS por sección y medir con `traza.py` qué regla pesa. **M**.
4. **CSS de 80 KB br en todas las páginas** (tope 60): base común + hojas por sección (garaje, foro, consola, domicilio). Baja
   FCP/LCP de todas. **M-L** (pasar luego `revisar-ux` por todas las páginas). Sesión de CSS y plantillas.
5. **Con CPU ×4 el módulo 3D arranca a los 13,6 s** (18 s en tibio): el hilo está ocupado antes (tareas largas suman 18,8 s).
   Tras 1-3, volver a medir; si sigue, cargar `moto3d.js` por IntersectionObserver o después del primer pintado del esquema. **S** tras medir.
6. **`three.module.min.js` completo (132 KB br)**: el `build_js` de producción minifica pero no recorta three; un bundle con
   solo lo usado (esbuild con tree-shaking) bajaría ~40-60 KB. **M**.
7. **`icon-192.png` se pide dos veces** (manifiesto + `<img>` del aviso «Instalar», oculto): `loading="lazy"` en esa `<img>`
   de `base.html`. **S**, 20 KB por primera visita.
8. **Detalle de moto: 39 consultas y 338 ms** (`reglapicoplaca` ×2 y las duplicadas que ya anotó `velocidad-detalle-moto.md`).
   **S**, en archivos de otras sesiones.
9. SVG del esquema: `feDropShadow` sobre todo el grupo (rasterizado caro en celular). Sesión de dibujos. **S**.

## Notas
- Las cifras 375/4G son pesimistas en red (runserver entrega sin comprimir; en producción son ≈ 30 % de esos KB), pero el
  freno de CPU es el que más pesa y ese sí es real.
- El 3D por defecto es el procedural: `nmax155.glb` (400 KB) solo carga con `?modelo3d=glb`.
- Mediciones en el scratchpad de esta sesión (temporales).
