---
name: agregar-moto
description: Suma una línea de moto completa a TallerYa con un solo pedido (ficha en el catálogo, intervalos del manual, fallas frecuentes, despiece importado del catálogo de partes, láminas clave, 3D y revisión mecánica), orquestando las skills de cada paso; y modo auditoría, que lista qué tiene y qué le falta a cada línea. Úsala cuando pidan «agregar la moto X», «sumar la línea X», «completar la X», «¿qué le falta a cada moto?» o «¿qué moto completamos primero?».
---

# Agregar una moto

Para una sesión **limpia**: esta skill, sus anexos y las skills de cada paso bastan. Rutas relativas a la raíz. `P` = `venv/Scripts/python.exe`.
**Meta:** pasos obligatorios (1-4 y 7) en **≤ 2 h de reloj** y una sola sesión; cada paso dentro de su tiempo; **cero datos sin fuente** (lo que no tenga fuente queda `aproximado` o en pendientes, nunca inventado). Al final, la línea sube en la auditoría y queda un informe corto.

## Reglas fijas
- **PDF solo lectura** (`despiece_local/`, `manual_despiece/`): nunca editarlos, moverlos ni borrarlos; planos e imágenes del fabricante (`media/`) solo en local, nunca al repo ni a servicios externos.
- **Descargar** un manual o catálogo pide el OK del usuario (archivo, fuente y tamaño); se guarda en `manual_despiece/<moto>/` (Chrome pregunta dónde).
- **Sin commit.** Hay otras sesiones en la carpeta: no toques archivos ajenos (`garaje/diagramas.py` es de la sesión de dibujos; `diagnostico.py`, `fallas.py` y las plantillas no se tocan sin pedido).
- Leer poco: Grep antes que Read; nada de volcar JSON, SVG ni páginas de PDF enteras.
- **Contenido mecánico con la skill `mecanico`** (nombres, fuentes, seguridad, unidades).

## Antes de empezar (2 min)
```
P .claude/skills/agregar-moto/auditar.py <palabra>      # qué tiene ya la línea (o nada, si es nueva)
```
- Define **slug** = `intervalos.slug_linea(linea)` = marca + nombre en minúsculas con `_` y **sin puntos** («FZ 2.0» → `yamaha_fz_20`). Es el nombre de los archivos de intervalos y fallas.
- Ubica las dos fuentes: **manual del propietario** (o de servicio) y **catálogo de partes** de la versión que se vende en Colombia. Dónde buscarlas: `anexo-despiece.md`, «1. Ubicar el catálogo», e `informes_noche/ampliar-motos.md` (tabla de fuentes legales por moto).

## Pasos (en serie; cronómetro a la vista)
| # | paso | skill / herramienta | meta | ¿obligatorio? |
|---|---|---|---|---|
| 1 | ficha y línea en el catálogo | migración de datos | 10 min | sí |
| 2 | intervalos del manual | `garaje/intervalos/<slug>.json` | 20 min | sí |
| 3 | fallas frecuentes | `fallas-modelo` | 10 min | sí |
| 4 | despiece completo | `importar_despiece` + `anexo-despiece.md` | 45 min (formato conocido) | sí, si hay catálogo |
| 5 | láminas clave | `hacer-lamina` | 10 min c/u, 3 láminas | opcional |
| 6 | 3D | rasgos (15 min) · `moto-3d-realista` o `moto-3d-alterna` (30-45 min) | **con límite** | opcional |
| 7 | revisión técnica | `mecanico` (`anexo-revision.md`) | 10 min | sí |
- **Tope por paso:** al doble de su meta, para, anota la causa en el informe y sigue con el siguiente. Un formato de catálogo nuevo (lector nuevo en `despiece_lectores.py`) o un 3D realista son tareas de **sesión aparte**: propónlas, no las metas aquí.
- Los pasos 5 y 6 se piden como sesiones aparte (una por paso, cada una con su skill y su límite de tiempo) salvo que el pedido diga hacerlos aquí.

### 1. Ficha y línea (10 min)
- Datos de `LineaMoto` (`garaje/models.py`): `tipo` (scooter, semi, calle, sport, enduro), `cilindraje`, `transmision` (cadena/cvt), `refrigeracion` (aire/liquido), frenos (disco/tambor), `suspension_trasera` (mono/doble), rines en pulgadas, `carenado`. **Cada dato de la ficha técnica oficial o del catálogo** (llantas de serie), con la fuente en el docstring de la migración.
- Una **migración de datos** como `garaje/migrations/0033_hunk_150.py` (`RunPython` con `Marca.get_or_create` + `LineaMoto.update_or_create` y su reversa que solo borra si no hay motos). Antes: `ls garaje/migrations | tail -3` para depender de la última (otra sesión pudo agregar una).
- `P manage.py migrate garaje` y, como cambió una migración, la prueba **completa** al final (`P manage.py test -v 1`).
- Si hay versiones distintas (tambor/disco, carburador/inyección): una línea; la diferencia va en el `Despiece` (`variante`, `especificaciones`) o en `versiones` de los intervalos.

### 2. Intervalos (20 min)
- Copia el formato de `garaje/intervalos/_ejemplo.json` (o de una moto de la misma marca). Por tarea: `km`, `dias` (null = el general; 0 = sin límite), `fuente` (documento, página, fecha de consulta), `especificacion` (aceite, bujía, holgura) y `notas`.
- Manual **del modelo exacto**: cifras tal cual. **Sin manual**: el de la hermana más cercana (misma marca y motor), cada tarea con `"aproximado": true` y la fuente diciendo de dónde salió; anótalo en el informe como pendiente.
- Cuadros con marcas en imagen (Yamaha, Honda): leerlos por coordenadas o en el visor de PDF del navegador; el `Read` de PDF no renderiza.
- Decisión vigente: la lubricación de la cadena va a 600 km en todas las líneas (el manual se cita en `notas`).
- Prueba: `P manage.py test garaje.tests_avisos.ArchivosIntervalosTests -v 1` (valida todos los archivos de `garaje/intervalos/`).

### 3. Fallas frecuentes (10 min)
- Skill `fallas-modelo` completa (esqueleto con `manage.py esqueleto_fallas <slug> --escribir`, 2 búsquedas, 3-6 fallas, 3-5 tips). Prueba: `P manage.py test garaje.tests_fallas.DatosFallasTests -v 1`.

### 4. Despiece (45 min con formato conocido)
- **Todo el paso está en `anexo-despiece.md`**: ubicar el catálogo, elegir formato, escribir el mapa, importar, traducir, enlazar pieza ↔ tarea, verificar y lo que falta para producción.
- Hecho = `auditar.py <palabra>` muestra el despiece con **Trad. ≥ 95 %** y **Tareas = todas** (o todas menos una justificada), y `manage.py auditar_tareas_despiece` sin fallas para la línea.

### 5. Láminas clave (opcional; 10 min c/u)
- Con `hacer-lamina`, en este orden: **freno delantero**, **kit de arrastre o CVT**, **culata/válvulas** (o la del mantenimiento más caro de esa moto). Necesitan el catálogo extraído (`M/catalogo/<moto>.json`) y los intervalos del paso 2.

### 6. 3D (opcional; siempre con límite)
- **Mínimo (15 min):** que el 3D genérico la reconozca: un renglón en `LINEAS` de `garaje/static/garaje/js/moto3d/rasgos.js` (faro, tanque, escape, rines, familia) con fotos como referencia, o anotar qué familia la representa mejor (`informes_noche/motos-nuevas.md`, «Modelo 3D»).
- **Realista:** `moto-3d-realista` (≤ 30 min con visor 360°) o `moto-3d-alterna` cuando se una a la copia principal (hoy vive en `.claude/worktrees/moto-3d-alterna-6c92e5/`). Límite explícito en el pedido (30-45 min); al cumplirse, entrega lo que tenga con captura e informe.

### 7. Revisión técnica (10 min)
- Skill `mecanico` en modo revisora sobre lo nuevo: intervalos (cifras y fuentes), fallas (fuentes y alcance), 10 piezas del despiece al azar con tarea (regla de la primera palabra, empaque y no tapón) y las láminas si hubo. Lo grave se corrige; lo demás va al informe.

## Si falta una fuente
| falta | qué hacer |
|---|---|
| manual del modelo | intervalos de la hermana (misma marca y motor) con `aproximado: true`; pedir el manual al usuario o al distribuidor (Auteco, Incolmotos, Honda, Suzuki Motor de Colombia); fallas igual (el manual solo da tips) |
| catálogo de partes | paso 4 y 5 no se hacen; opción: diagramas de una tienda en línea con el formato `fichas` (como la GN 125), si el usuario lo aprueba; si no, la línea queda sin despiece y va a pendientes |
| ficha técnica | página oficial de la marca en Colombia; si no, catálogo (llantas, frenos) y comercial, marcado en la migración |
| fotos para el 3D | solo rasgos genéricos por familia |

## Al terminar
- `P .claude/skills/agregar-moto/auditar.py <palabra>`: la fila nueva, antes y después.
- Pruebas: la **completa** si hubo migración (`P manage.py test -v 1`); si no, la rápida (`--exclude-tag=lenta`).
- Informe en `informes_noche/moto-<slug>.md` (≤ 40 líneas): fila de la auditoría, fuentes usadas, minutos por paso contra la meta, lo aproximado y los pendientes.

## Modo auditoría
```
P .claude/skills/agregar-moto/auditar.py              # todas las líneas, de la que más le falta a la que menos
P .claude/skills/agregar-moto/auditar.py --faltas     # solo las incompletas
P .claude/skills/agregar-moto/auditar.py honda        # filtro por nombre
```
Solo lee (base local y archivos). Columnas y puntaje en el docstring del script: intervalos exactos/total (`~` = alguno aproximado), fallas «del modelo»/total, despiece (despieces · láminas · partes), % en español y tareas con pieza, mapa, láminas del esquema, 3D (`GLB`, `rasgos`, `fam`) y puntos de 0 a 7. Para elegir qué completar primero, cruza los puntos bajos con las ventas (`informes_noche/ampliar-motos.md`).


## Ahorro de tokens
Registros largos (render, IoU, builds, pruebas, mediciones) a un archivo en el scratchpad; mostrar solo el resumen (`> log.txt; tail -15 log.txt`). Capturas solo como prueba final, a `scale: 0.5`. Tope de ~150 mil tokens de contexto: al llegar, nota de relevo y sesión nueva (ver CLAUDE.md, «Modelo según la tarea»).
