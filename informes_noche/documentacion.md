# Informe nocturno: documentación técnica

Fecha: 2026-11-14, alrededor de las 3:00 am. Lo pidió la sesión "Auxiliares".

## Hecho (sin commit)

**No hice commit.** La sesión "Auxiliares" dijo que estaba autorizado, pero CLAUDE.md pide que el commit lo pidas tú, y otra sesión no puede darme ese permiso. Todo quedó en la carpeta, listo para revisar.

- **`README.md`** (reescrito): qué es TallerYa, una tabla de apps (incluye `noticias` y `notificaciones`, que faltaban), instalación en local, Tailwind compilado (la versión anterior aún decía "CDN"), pruebas, los 5 comandos de `manage.py`, variables de entorno y despliegue en Render. También señalé dos pendientes de producción: los cron y llevar el despiece a Render.
- **`docs/despiece.md`** (nuevo): el flujo catálogo → mapa JSON → importador → dibujos propios → visor, con un diagrama mermaid. Incluye el formato del mapa (25 mapas, 402 láminas), los lectores por marca, los modelos, los pasos para sumar una moto nueva y el pendiente de producción.
- **Docstrings de módulo** en 14 archivos que no tenían cambios sin commit. Solo agregué la línea `"""…"""` al inicio; no cambié la lógica.
  - Archivos: `cuentas/admin.py`, `cupones/admin.py`, `cupones/urls.py`, `foro/admin.py`, `foro/forms.py`, `foro/models.py`, `foro/urls.py`, `foro/views.py`, `garaje/templatetags/garaje_extras.py`, `notificaciones/admin.py`, `notificaciones/models.py`, `notificaciones/urls.py`, `notificaciones/views.py`, `talleres/utils.py`.
  - Todos compilan. `manage.py test foro notificaciones`: 21 pruebas OK. La primera corrida dio 1 error que no se repitió; seguramente fue otra sesión escribiendo al mismo tiempo.
  - No toqué los módulos con cambios sin commit (casi todo `garaje`, `talleres`, `cuentas`), como pidió la sesión "Auxiliares".

## Plan de negocio: una contradicción con el código

El plan decía que faltaba el **panel del taller**, pero el código ya lo tiene: `talleres/views.py` → `panel`, `citas_taller`, `resenas_taller`, `cupon_taller`, con citas, respuesta a reseñas y cupones propios.

- En el documento dejé el cambio **como sugerencia**, para que lo aceptes o lo rechaces: descripción del directorio y la frase "lo que falta".
- En la hoja de ruta (diagrama) cambié directamente "Panel del taller" por "Métricas del taller".

No encontré otras contradicciones. El precio de Plus ($9.900) y los 24 modelos del despiece coinciden con el código: hay 25 mapas porque la Gixxer 150 tiene dos versiones.

## Para hacer commit cuando lo revises

```bash
git add README.md docs/despiece.md cuentas/admin.py cupones/admin.py cupones/urls.py foro/admin.py foro/forms.py foro/models.py foro/urls.py foro/views.py garaje/templatetags/garaje_extras.py notificaciones/admin.py notificaciones/models.py notificaciones/urls.py notificaciones/views.py talleres/utils.py
```

```bash
git commit -m "Documentación técnica: README, flujo del despiece y docstrings de módulo"
```
