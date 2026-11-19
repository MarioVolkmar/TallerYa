# Pruebas más rápidas (19-nov-2026)

## Resumen
- **Arranque de la suite: ~35 s → ~8 s.** Era el costo de aplicar 111 migraciones en cada corrida (el 85 % del tiempo se iba en que Django reconstruye el estado de los modelos en cada migración). Ahora la base migrada se guarda una vez como plantilla y las siguientes corridas la copian.
- **Las pruebas en sí no tienen un cuello de botella único**: el ~70 % del tiempo es renderizar páginas de verdad (plantillas, ~20 consultas y sesión por petición, 1.844 peticiones en la suite rápida). Recortarlo sin perder cobertura exige hacer la app más rápida, no las pruebas.
- **La meta de <45 s no se pudo comprobar**: durante toda la medición la CPU estuvo al 100 % por otras sesiones (generador 3D, varios runserver, otra suite de `domiciliarios` con 6 procesos). Con esa carga los tiempos variaron de 75 s a 186 s para la misma suite. Estimado con la máquina libre: ~8 s de arranque + 130 s de CPU repartidos en 4 núcleos ≈ **40-50 s**.
- Todo pasa, en paralelo y con `--parallel 1`: rápida 777 pruebas OK, completa 823 OK.

## Antes y después

| | Antes | Después |
|---|---|---|
| Arranque (crear la base + clonar), en serie | ~38 s | ~11-14 s (de ellos ~5 s son imports y ~3 s chequeos de Django) |
| Arranque de la suite rápida en paralelo | ~35 s | ~8 s |
| Suite rápida en paralelo, mismo tipo de carga | 82 s (6 procesos) | 75 s (4 procesos); la mejor corrida del encargo: 98 s antes |
| Suite rápida, suma de pruebas en serie | 138,7 s (778) | 132,6 s (777) |
| Una clase focalizada (15 pruebas) | 36 s | 16 s |
| Pruebas rápida / completa | 778 / 823 | 777 / 823 (una pasó a `lenta`, sigue en la completa) |

Medido bajo carga: los números absolutos están inflados; la comparación vale porque antes y después se midieron en las mismas condiciones.

### Top de pruebas (serie, antes → después)
| Prueba | Antes | Después | Qué se hizo |
|---|---|---|---|
| talleres ComandoCargarDemoTests (demo completo ×2) | 3,94 s | completa | `@tag("lenta")` |
| config IdorTests.otro_motero | 3,74 s | 2,54 s | 2 peticiones por ruta en vez de 3 (el GET con datos ya dice si la ruta existe) |
| config IdorTests.otro_taller | 2,41 s | 1,59 s | ídem |
| notificaciones PushTests.no_envia_a_quien_no_activo | 2,13 s | 2,86 s | sin cambio: es la importación de `pywebpush` (una vez por proceso) |
| domicilio demo / ilustraciones (3 pruebas) | 1,2-1,9 s | 1,2-1,5 s | sin cambio: generan las imágenes del demo, que es lo que prueban |
| talleres PanelTallerTests y 8 subclases (60 pruebas) | setUp 3,4 s en total | — | datos a `setUpTestData` |
| cupones tests_transacciones Base (22 pruebas) | setUp 1,8 s en total | — | datos a `setUpTestData` |

Top de clases después: IdorTests 6,0 s · DiagnosticoEnForoTests 3,7 s · ArreglosRevisionTests 3,5 s (las tres hacen muchas peticiones a propósito).

## Por qué la plantilla y no las otras opciones
- **Squash de migraciones**: hay 28 migraciones con `RunPython` que siembran catálogos (líneas, rines, tareas) y otras sesiones están agregando migraciones ahora mismo. Hacer squash es invasivo y arriesgado para producción.
- **Sin migraciones (`MIGRATION_MODULES` / syncdb)**: hay que reproducir a mano todo lo que siembran esas 28 migraciones (fixtures que se desactualizan) y se deja de probar que las migraciones corren.
- **Plantilla (lo elegido)**: la base sale de las migraciones reales, con los mismos datos sembrados, y solo cambia cómo se obtiene. La clave es un hash de todos los archivos `migrations/*.py` de las apps instaladas, la versión de Django y `MIGRATION_MODULES`: si alguien toca o agrega una migración, se migra de nuevo y se guarda otra plantilla. No toca producción ni `settings.py`.
  - Vive en `%TEMP%/tallerya_pruebas/` (fuera del repo, no hace falta tocar `.gitignore`). Se escribe a un temporal y se renombra, así que sirve con varias sesiones y worktrees a la vez (cada combinación de migraciones tiene su archivo); las que no se usan en 7 días se borran.
  - Si la plantilla falta o no se puede leer, migra como antes. `PRUEBAS_SIN_PLANTILLA=1` obliga a migrar.
- **Número de procesos**: 6 → un proceso por núcleo físico (4 en esta máquina de 8 hilos). Medido: 4 procesos 58 s de pruebas y 72 s en total; 6 procesos 62 s y 82 s; 8 procesos 59 s y 84 s. Cada proceso extra cuesta ~5 s de CPU para arrancar (spawn de Windows) y no aporta, porque la CPU ya estaba llena.
- Probé las sesiones en caché en vez de en la base solo para pruebas: sin diferencia medible, así que lo revertí.

## Archivos tocados
- `config/test_runner.py`: plantilla de la base y número de procesos.
- `config/tests_seguridad.py`: IdorTests con una petición menos por ruta (misma cobertura).
- `talleres/tests_demo.py`: `ComandoCargarDemoTests` con `@tag("lenta")`.
- `talleres/tests.py`, `cupones/tests_transacciones.py`: `setUpTestData`.
- `CLAUDE.md`, sección «Pruebas».

## Qué más daría velocidad (no hecho, es código de la app)
- `notificaciones.servicios.contexto` y `cuentas.backends.get_user` suman ~14 % del tiempo de cada página (avisos y la carga del usuario en cada visita); también se nota en producción.
- ~49 `{% url %}` por página (sobre todo en el menú de `base.html`).
- Medir de nuevo con la máquina libre para confirmar los <45 s.
