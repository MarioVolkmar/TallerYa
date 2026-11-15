# Revisión de los esquemas del despiece (15-nov-2026)

Alcance: las 33 líneas (34 catálogos, con las dos versiones de la Gixxer), con más cuidado en las 8 nuevas. No se tocó el 3D ni Chispa. No hay commit.

## Qué se midió (con scripts sobre `_laminas_base`, sin pasar por la caché)
| Indicador | Antes | Después |
|---|---|---|
| Piezas con la explicación vacía "Es una pieza del conjunto que ves en el dibujo" | 272 | 27 (catálogo sin descripción: solo un código, como `DL1510` o `AK125 0023`) |
| Piezas principales con una explicación de tornillería vaga ("Es un componente eléctrico de…", "Es un piñón de…"), en AKT, Bajaj, Hero, Suzuki y TVS | 373 de 2.912 | 256 (casi todas son bujes y resortes pequeños, donde ese texto sí es correcto) |
| Números encimados (a menos de 3 % del ancho) | 0 | 0 |
| Tareas que abren otra pieza (`auditar_tareas_despiece`) | 0 | 0 |
| Pruebas `garaje.tests` y `garaje.tests_diagnostico` | — | 133 OK |

La fila de tornillería no cambió: las reglas nuevas solo mueven piezas principales que antes caían en "Otras piezas".

## Arreglos hechos
1. **Piezas que no se marcaban en el dibujo** (`diagramas.py`, bloque `_ANTES`/`_AL_FINAL`, después de `_RUEDAS`). Se agregaron reglas por nombre exacto de catálogo:
   - botellas (`CASE, R. BOTTOM` y la traducción errada "CAJA DE LA BATERIA DELANTERA INFERIOR" de la Hunk 150);
   - copa de bloqueo del aceite, bujes deslizantes, cilindro de la barra, `TUBE, INNER` (Suzuki);
   - pastillas (`PAD COMP`, "COJIN JUEGO"), caliper ("PRENZA"), bandas ("ZAPATA", "Kit Pastas Freno" en tambor);
   - rines (`WHEEL, FRONT/REAR`), poleas del variador (`FACE, DRIVE`), carburador completo, cuerpo de aceleración, CDI/TCI, llave de encendido, batería `YTX…`, cajas del filtro de aire y filtros (`FILTER,AIR CLNR`, `SPONGE,FILTER`).
   - Se revisaron todos los cambios de puesto (script `diff_puestos.py`) y se corrigieron 4 que iban mal: aguja del flotador, eje de la rueda, tapa de la caja del filtro y sello de la tapa.
2. **FZ 2.0, fig. 26 (rueda trasera con cadena y disco)**: usaba el dibujo de la rueda delantera. Ahora usa `rueda_trasera`, que muestra la corona y además la vista aparte del kit de arrastre. El cambio quedó en el mapa JSON y en la base local.
3. **Explicaciones nuevas** (`despiece_guia_mecanica.py`, dos bloques al final, solo claves nuevas):
   - piezas que no tenían guía propia: descompresor, paso de aceite, filtro centrífugo, arranque de pedal, cuña, contrapeso de balanceo, ajustador de guaya, tuerca de ajuste del freno, horquilla de la varilla, visor del líquido, pito, cargador USB, arrestallamas, motor de arranque, mecanismo del arranque, guaya y guaya del clutch, sensor de gasolina, tapa del tanque, tapón de inspección, piñón primario, eje balanceador, guía de válvula;
   - unas 80 "palabras de taller" en inglés y en español que llevan cada pieza a su guía.
   - `guia_mecanica` ahora también busca por el **nombre en español**. Suzuki, Hero y TVS traen la descripción en inglés, y antes por eso no se reconocían piezas como la bobina, las válvulas, el eje principal o los discos del clutch.
4. **Error de raíz en `views.guia_de`**: `tiene_guia_propia` daba "sí" a `CAM, BRAKE` por la ficha `CAM`, que es solo de la CVT, y la pieza se quedaba con el texto genérico. Ahora, si la ficha sale genérica, se usa la guía mecánica. Es un arreglo en la vista; el de raíz está en `despiece_fichas.py` (ver dudosos).
5. **Nombres** (`despiece_variantes.py`):
   - erratas del PDF: la ligadura "ti" (`NeumáƟ o` → Neumático, "Canas lla" → Canastilla, "Cor na" → Cortina), Flashaer, Piñó, Gurda polvo, Wasa, Componete, Tuerda, Prenza, Tesor, Meditor;
   - nombres claros por sistema: "Pistón horquilla delant" (`BUSH, INNER TUBE`) → Buje deslizante de la barra; "Neumático" (`TUBE, INNER` en la suspensión) → Barra cromada; "Templador" (`ADJUSTER` del carburador) → Ajustador de la guaya; `CAGE` → Canastilla; arnés, batería de gel, etc.
   - Una clave con "=" vale solo si la descripción es exactamente esa.

## El diagnóstico usa las mismas piezas
`vista_diagnostico` arma el esquema con `datos_despiece`: son las mismas láminas, números y guías del despiece, así que los arreglos de arriba también salen allá. Al buscar sus piezas candidatas se encontraron estos huecos (no los toqué, son de los patrones de `diagnostico.py`):
- Clutch (`clutch_patina`, `clutch_no_suelta`, `clutch_ajuste`): no encuentra piezas en Dynamic Pro, Hunk 125R, Best 125, Apache RTR 160 y GN 125. Hay que revisar si les falta la lámina del clutch o si es por los nombres.
- `bombillo` y `arranque_electrico`: sin piezas en 10 a 14 líneas. Los catálogos casi no traen bombillos ni relés.

## Dudoso (anotado, sin tocar)
- **`SPINDLE, TAPER`** (Yamaha). En `despiece_glosario.py:143` y en `despiece_fichas.py:782` dice "Eje de la dirección". En la FZ 2.0 aparece una vez en cada barra (refs. 11 y 30), así que es el cono del amortiguador, dentro de la barra. Ya corregí su nombre y su puesto en el dibujo, pero su ficha sigue explicando la dirección. Esa ficha es de la sesión de revisión mecánica: propongo que la cambie ella.
- **`tiene_guia_propia`** (`despiece_fichas.py`): debería ignorar las claves de `_SOLO_CVT` fuera de la CVT. Hoy lo cubre el arreglo en la vista.
- **Hunk 150, "AISLADOR DE LA BATERIA"** en la lámina de la culata: es una traducción errada; puede ser el aislante del carburador. Hay que verificarlo con su lámina.
- **Hunk 125R**: el catálogo no trae lámina del freno delantero ni batería, así que las tareas de pastillas, líquido de frenos y batería quedan sin pieza (`auditar_tareas_despiece`). Falta la lámina en el importador o la regla de "pieza de tarea".
- **Boxer CT 125, fig. 30** (rueda y freno delantero de tambor): usa el dibujo `freno_tambor`, que no tiene rin, y el rin cae en "Otras piezas". Hace falta un dibujo de rueda delantera con tambor.
- **Eco Deluxe**: en la lámina de la rueda trasera dice "Neumático delantero" (es la misma referencia 2.75×18 adelante y atrás).
- **`COLLAR, WHEEL`** (separadores de afuera de la rueda): su guía dice "separador entre las balineras", que es el de adentro.
- **Variantes con el mismo número** (piñón de salida de la Boxer: 7 filas; guardapolvo de la XR por marca): se listan por separado. Se podrían unir como alternos.
- 27 piezas con solo un código de catálogo (`DL1510`, `JA541021`, `55200-26F01`…): necesitan su nombre sacado del manual local.
- No comparé lámina por lámina contra los planos de fábrica. Revisé con scripts (puestos, números, guías) y miré un solo render: la rueda trasera de la FZ 2.0, que salió bien.

## Peso de los esquemas (medido)
- **SVG por lámina**: mediana de 91 KB; los más pesados son las carcasas (unos 235 KB, por ejemplo la cubierta del clutch de la Apache). Por línea suman de 1 a 2,6 MB, que comprimidos son de 210 a 560 KB. El visor carga una lámina a la vez y el servidor ya los comprime (`GZipMiddleware`), así que cada vista baja unos 50 KB.
- **JSON del despiece**: de 200 a 600 KB, que comprimidos son de 23 a 60 KB.
- Quitar la "L" repetida de los trazos y poner una sola vez `stroke-linejoin`/`stroke-linecap` ahorra un 14 % sin comprimir, pero solo un 3 % comprimido: no vale la pena.
- **Propuestas, sin perder calidad:**
  1. Los SVG llevan `?v=` con el hash: se puede cambiar `Cache-Control` de 1 día a `max-age=31536000, immutable`, y la segunda visita no los vuelve a bajar.
  2. Simplificar los puntos de las curvas (Ramer-Douglas-Peucker, tolerancia de unos 0,3 unidades del lienzo de 1000) solo en las carcasas, que son los SVG más pesados.
- **De la sesión de velocidad** (`velocidad-2.md`, punto 5): el primer armado del despiece tarda de 2 a 2,7 s.
  - `precalentar_despiece` ya cubre los 34 catálogos activos, y con eso también la vista pública del diagnóstico, que usa el mismo despiece completo. Trabaja por tandas de 15 s: con unos 2,5 s por catálogo, el cron necesita unas 6 llamadas seguidas después de cada despliegue.
  - Cada cambio de código cambia la clave de la caché (`_version_codigo_despiece`), así que **todo despliegue la deja fría**: conviene correr `precalentar_despiece --max-segundos 0` en `build.sh` o justo después del despliegue.
  - Se propone `Cache-Control: public, max-age=3600` en `despiece_publico`, que no tiene datos personales.

## Archivos tocados
`garaje/diagramas.py`, `garaje/despiece_guia_mecanica.py` (solo bloques al final y la firma de `guia_mecanica`), `garaje/despiece_variantes.py`, `garaje/views.py` (`guia_de` y una importación), `garaje/despiece_mapas/yamaha_fz20_b6u1.json`, y la base local (FZ 2.0, fig. 26). No se editó ninguna entrada existente de `despiece_fichas.py` ni de `despiece_glosario.py`.
Scripts de auditoría, para volver a correrlos: en el scratchpad de esta sesión (`auditar.py`, `vagas.py`, `diff_puestos.py`, `encimados.py`, `peso.py`, `render.py`).
