# Relevo: fig. 8 NMAX «Admisión y filtro de aire» (16-nov-2026)
`M` = `informes_noche/piloto-esquema/motor`. Sin commit.
- Hecho: `M/datos/nmax-fig8.json` (fuente), `M/datos/nmax-fig8-arte.js`, `M/admision.html`, `M/prueba-nmax-fig8.html`, captura `M/nmax-fig8-1280.jpg`. Validador OK, medir sin bloqueantes (4,55 medible; con ojo 4,61). Métricas en `M/metricas.json` (creación 13 min).
- Motor: tipos `manguera`, `abrazadera`, `caja`, `ducto`, `placa` en `piezas-comunes.js`, reconocidos en `mas_controles.py` y propuestos por `esqueleto_v2.py`. Detalle en `cambios.md`.
- Para la revisión mecánica: unión 22 (grieta = aire sin filtrar, no aire falso: ya corregido), orden del desarme (inyector antes que el cuerpo), `sujeta`, torques «sin dato».
- Para ux-piloto: criterio 6 en 3 (9 piezas < 24 px a 360: 2, 4, 6, 7, 11, 21, 26, 27, 37). La captura de medir_lamina sale con el grupo «Caja» seleccionado.
- Pendiente: unión 22 dibujada lisa (real corrugada); 3D solo en 16, 33 y 19.

## Después de la revisión (16-nov-2026, 06:41)
- Correcciones mecánicas hechas (los 5 puntos de revision-mecanica-fig8.md) y preguntas 14a, 14b y 10a en el validador (`revisar_tecnologia`).
- Ajustes UX del motor en `esquema.js`: toque mínimo automático con racimos, píldoras de tornillería que se esconden al salir y desarme de ≤ 4,8 s. Medido: freno 4,72, CVT 4,63, bomba-freno 4,72 y admisión 4,72; todas sin bloqueantes. Detalle en `cambios.md`.
- Pendiente: la CVT conserva 5 piezas < 24 px (18 resorte grande de alambre fino, 19, 3, 33 y 5). En admisión, los círculos de los tornillos de la tapa (25) recortan a la 21 y la 27: si molesta, el recorte podría dar prioridad a las piezas enteras sobre los racimos.
- Para ux-piloto: volver a medir las 4 con `medir_lamina.py`.
