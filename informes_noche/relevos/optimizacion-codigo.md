# Relevo: Optimización de código (al 15-nov-2026)

## Hecho
- Commit 5c20531, subido a main: menos consultas SQL.
  - Nuevo `cuentas/backends.py` con select_related del perfil; todos los `login(..., backend=...)` lo indican.
  - Directorio de talleres ordenado y paginado en la base de datos.
  - Detalle de taller: 18 → 12 consultas. Detalle de moto: 27 → 19.
  - Redis opcional con `REDIS_URL`.
- `docs/auditor.md`: filtro 4, verificación con fuentes externas, que complementa los filtros 1 a 3.
- Despiece, sin commit:
  - `garaje/diagramas.py`: `_construir` memorizado con `_construir_guardado` (lru_cache más copias de cada Pieza). Lo aprobó Planos.
  - Armar en frío pasó de ~20 s a 3–5 s por moto, con el JSON idéntico.
  - `garaje/views.py`: `clave_base_despiece()` y `base_despiece()`; `_svg_guardado` usa `caches["despiece_svg"]`.
  - `manage.py precalentar_despiece`: idempotente, en tandas de 15 s (`--max-segundos 0` = todo); crea la tabla de caché.
  - `garaje/vista_tareas.py`: tarea "despiece" (se avisó a Garaje); `.github/workflows/despiece.yml` la llama tras cada push a main.
  - `config/settings.py`:
    - "despiece" = DatabaseCache (tabla `cache_despiece`, 100 entradas, CULL 3).
    - "despiece_svg" = FileBasedCache /tmp, 20.000 entradas.
    - En pruebas, ambas son LocMem.
    - Se avisó a Diseño General.
  - `build.sh`: `createcachetable` después de `migrate`.
  - Prueba nueva: `DespieceTests.test_precalentar_despiece_es_idempotente`.

## Pendiente
- Nada sube a git sin que el usuario lo pida.
- La suite completa da 3 fallas ajenas a este cambio. La de notificaciones (`NotificacionesTests.test_genera_avisos_...`) supone aceite NMAX cada 2.500 km, pero `garaje/intervalos/yamaha_nmax_155.json` dice 6.000. Le corresponde a quien lleva los intervalos.
- Despliegue no hecho: plan en memoria `despliegue-pendiente`. En GitHub faltan los secretos TALLERYA_URL y TAREAS_TOKEN.
- Scripts de medición en el scratchpad de la sesión (medir_despiece.py, perfil_despiece.py, comparar_despiece.py); se pierden con la sesión.

## Reglas
- Reportes y preguntas van a Auxiliares, en informes cortos.
- No tocar el `inicio` de `talleres/views.py` (Principal/Diseño General).
