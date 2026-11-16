# Relevo: revisión en celular y despliegue (15 nov. 2026)

**Estado: las dos tareas están terminadas, sin commit.** Al retomar se revisó también el diagnóstico nuevo en celular: OK y sin cambios.

## Lo que se hizo
- **Celular:** se revisaron 21 páginas a 360 y 390 px, con y sin sesión, más el menú, la campana, el diálogo de registro y la guía de pieza.
  - Se corrigieron 2 desbordes reales: Talleres (`.dir-cuerpo`) y la lista de Hoja de vida en el detalle de moto (`.hv-mini`).
  - Los chips de filtro de la página Hoja de vida ya no se salen de la pantalla.
  - Unos 20 botones pasaron a medir al menos 40 px.
  - Detalle por página en `informes_noche/celular.md`.
- **Despliegue:** la lista por prioridad, con costos, está en `informes_noche/despliegue.md`.

## Archivos tocados
- `talleres/static/talleres/css/tallerya.css`: dos líneas editadas (`.dir-cuerpo`, `.hv-mini`), `min-height` en `.boton-seccion` y un bloque `@media (max-width: 640px)` al final.
- `.env.example`: variables de producción agregadas al final, todas comentadas (no cambia nada en local).
- Nuevos: `informes_noche/celular.md`, `informes_noche/despliegue.md` y este archivo.
- `render.yaml`, `settings.py`, plantillas y vistas no se tocaron.

## Lo que falta (decisión del usuario o de otras sesiones)
- Botón día/noche de la portada (`.portada-noche`, 35 px): la portada es de la sesión «Proyecto tallerYa».
- Cambios sugeridos en `render.yaml`, sin aplicar:
  - planes pagos;
  - `CARGAR_DEMO=0`;
  - disco persistente para `media/` y `privado/`;
  - `SITIO_URL`, el correo y Google con `sync: false`;
  - `--timeout 60` en gunicorn.
- Decidir cómo llevar los datos del despiece a producción sin publicar imágenes de catálogos de fábrica.
- Decidir si `informes_noche/` va al `.gitignore`.
- El navegador del panel quedó con la sesión de la cuenta demo (antes tenía la del taller demo).
- Pruebas: no se corrieron. Solo cambió CSS y texto, y según `CLAUDE.md` no hacen falta.
