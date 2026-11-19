---
name: fallas-modelo
description: Crea o amplía el archivo de «Tips y fallas frecuentes» de una línea de moto de TallerYa (garaje/fallas_frecuentes/<slug>.json), el que pinta la sección «Lo que más les pasa a las [modelo]» en la página de la moto. Úsala cuando pidan fallas frecuentes, daños típicos o tips de un modelo, agregar una moto nueva al piloto de fallas o revisar las fuentes de uno existente.
---

# Fallas frecuentes de un modelo

Para una sesión **limpia**: esta skill basta. Las rutas son relativas a la raíz del proyecto.
**Meta:** **≤ 10 min y ≤ 40 k tokens por modelo**: esqueleto, 2 búsquedas, edición y prueba. Calidad: cero ítems sin fuente y cero fallas del modelo inventadas.

## Reglas fijas
- **Menos y bien fundado:** se admite una falla como «del modelo» solo si una fuente concreta (URL) se la atribuye a **ese** modelo y no es el caso de un solo dueño. Si no, se queda como «del tipo» o no va.
- **Redacción:** «reportes frecuentes de dueños», nunca «defecto de fábrica».
  - De tú, claro, para el motero de Medellín: lluvia, lomas, trancón, parrillero.
  - Con tus palabras: nada copiado de la fuente.
- **Costos** (`costo`): solo con un dato en pesos colombianos y su fuente. Nada de rangos en dólares de otros países.
- **No se toca:** `garaje/fallas.py`, la plantilla `_fallas_frecuentes.html`, el CSS ni `generales.json`, salvo que la tarea lo pida. **Sin commit.**
- **Bandera:** `FALLAS_FRECUENTES_ACTIVO`, en `.env` local con valor 1; en producción viene apagada.

## Pasos
1. **Esqueleto** (alcance «tipo», con los datos del manual):
   ```
   venv/Scripts/python.exe manage.py esqueleto_fallas <slug>              # resumen
   venv/Scripts/python.exe manage.py esqueleto_fallas <slug> --escribir   # crea el archivo (--forzar lo rehace)
   venv/Scripts/python.exe manage.py esqueleto_fallas --faltantes --escribir
   ```
   - El slug es el mismo de `garaje/intervalos/` (`intervalos.slug_linea`, por ejemplo `yamaha_aerox_155`). Con un slug que no existe, el comando lista los válidos.
   - Arma las fallas según la línea en la BD:
     - cadena o CVT, y en enduro la cadena en trocha;
     - freno trasero de tambor o de disco;
     - válvulas, si el manual las trae;
     - recalentamiento si es de refrigeración líquida, o filtro con polvo si es enduro.
   - Los tips salen de las notas de `intervalos`.
2. **Fuentes del modelo** (máx. 2 búsquedas `standard`; delegables a un subagente `haiku`). Orden:
   1. el manual, que ya está resumido en `garaje/intervalos/<slug>.json` y no hace falta releer;
   2. guías de usados que listen fallas del modelo (`motoryk.com/bikes/<marca>/<modelo>/problems`) y foros o grupos de dueños: bikedekho/zigwheels/bikewale para motos indias, GridOto para scooters Yamaha;
   3. videos de mecánicos con resumen escrito.
   - Descartar: el caso de un solo dueño, otra variante del modelo (CT 125X ≠ CT 125), páginas que no abren (solo el extracto del buscador) y quejas de servicio del concesionario, que no son fallas de la moto.
3. **Editar el JSON**, sin volcarlo: leer solo las claves con Python.
   - Por cada falla con fuente:
     - si ya existe como «tipo», cambiar `alcance` a `"modelo"` y sumar la fuente;
     - si no existe, agregarla con todos los campos.
   - Fuentes: entrada `{"nombre", "url"}` en `fuentes`; `nombre` dice qué es (guía de usados, foro, mecánico).
   - Quitar de `nota` la frase del esqueleto si ya hay ítems del modelo; si no los hay, dejarla, porque explica el alcance.
   - Límites: **3 a 6 fallas** y **3 a 5 tips**.
4. **Conexiones de cada falla** (todas opcionales, pero úsalas):
   - `tareas`: claves de `TareaMantenimiento`: aceite, cadena-lubricar, kit-arrastre, correa-cvt, aceite-caja, filtro-aire, bujia, valvulas, pastillas-del/tras, bandas-del/tras, liquido-frenos, llanta-del/tras, suspension-del/tras, refrigerante, bateria;
   - `pieza`: sistema del despiece: aceite, motor, filtro_aire, bujia, cadena, correa, freno_del/tras, llanta_del/tras, suspension_del/tras, bateria, refrigeracion;
   - `diagnostico`: `{"s": síntoma, pregunta: valor}`, sacado de `garaje/diagnostico.py`:
     - ruido: donde (motor, arrastre, cvt, final, ruedas, frenar, huecos, escape) y tipo (tic, traqueteo, golpe);
     - vibracion: cuando;
     - no_prende: arranque (nada, gira, lento);
     - se_apaga: cuando (minimo, frio, andando, caliente) y radiador;
     - frena_mal: cual (del, tras, ambos) y como (esponjoso, poco, pegado, chilla);
     - inestable: como;
     - humo: color;
     - fuga: que (aceite, gasolina, refrigerante, frenos, barras, final);
     - sin_fuerza: como (patina, lenta, pesada);
     - electrico: que (debiles, una, descarga, tablero);
     - cambios: que (duro, salen, patina, arrastra, neutro);
     - cvt: que (tiembla, lenta, ruido, sola);
   - `taller`: nombre exacto de `talleres.Servicio`: Cambio de aceite, Frenos, Kit de arrastre, Llantas, Mantenimiento general, Sincronización, Sistema eléctrico, Suspensión;
   - `domicilio`: nombre exacto de `domicilio.TipoServicio`: Mantenimiento general, Cambio de aceite, Frenos, Sistema eléctrico, Batería y arranque, Llantas y despinche, Diagnóstico, Carburación, Inyección electrónica, Kit de arrastre, Suspensión.
   - Un nombre mal escrito no rompe nada: solo hace que el enlace no aparezca.
5. **Validar:** `venv/Scripts/python.exe manage.py test garaje.tests_fallas -v 1` (~3 s). Revisa todos los archivos: campos, gravedad, alcance, fuentes definidas y límites.
6. **Ver** (solo si cambió la plantilla o es el primer modelo de un tipo nuevo): preview `tallerya`, página de una moto de esa línea.
   - Para revisar texto y estructura, `get_page_text` o `javascript_tool`; como mucho una captura a `scale` 0.5.
   - Usa una cuenta de prueba propia: nunca entres con las cuentas reales de la base.
7. **Registrar** en la tabla de `informes_noche/fallas-frecuentes.md`: modelo, fallas del modelo, fallas del tipo y fuentes.

## Formato (resumen; el detalle está arriba de `garaje/fallas.py`)
```json
{"linea": "Yamaha Aerox 155", "tipo": "scooter", "revisado": "AAAA-MM-DD", "nota": "…",
 "fuentes": {"manual": {"nombre": "…", "url": ""}, "motoryk": {"nombre": "…", "url": "https://…"}},
 "fallas": [{"clave": "bateria-quieta", "titulo": "…", "sintoma": "…", "causa": "…",
             "gravedad": "molestia|cuidado|peligro", "que_hacer": "…", "alcance": "modelo|tipo",
             "tareas": ["bateria"], "pieza": "bateria", "diagnostico": {"s": "no_prende", "arranque": "lento"},
             "taller": "Sistema eléctrico", "domicilio": "Batería y arranque", "fuentes": ["motoryk"]}],
 "tips": [{"titulo": "…", "texto": "…", "fuentes": ["manual"]}]}
```
**Gravedad:**
- peligro: frenos, recalentamiento o lo que puede tumbarte;
- cuidado: si se deja, sale caro o te varas;
- molestia: lo demás.
