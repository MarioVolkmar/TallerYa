# Informe nocturno: despiece y dibujos (sesión de planos)

Nada tiene commit: el informe y todos los cambios quedan en el árbol de trabajo para que los revises.

## Lo que hice

### 1. Nombres (lote del Auditor y un fallo grande)
- Corregí un fallo en unos 890 nombres: la abreviatura "del" se cambiaba por "delantero" también cuando era el artículo. Salían cosas como "Anillos delantero pistón" o "Piñón de tercera delantero eje secundario". Ahora se dice "del".
- Neumáticos AKT: "Neumati KTL INDIA…" ahora es "Neumático trasero" / "Neumático delantero".
- Otros nombres arreglados:

  | Antes | Ahora |
  |---|---|
  | Pieza de seguridad del aceite | Copa de bloqueo de aceite |
  | Pieza de deslizamiento | Bujes deslizantes de la barra |
  | Embudo para aire | Embudo de aire |
  | Emblema yamaha | Emblema Yamaha |
  | Tapa del neumático de la suspensión (el tubo de la barra) | Tapa de la barra de la suspensión |
  | Arandela anti - brinco | Arandela antibrinco |

- Revisión de los 8.364 nombres visibles: 0 con marca, código, signo raro o inglés.

### 2. Sistemas: la misma lista para todas las motos
- La clasificación pasó de despiece.js a un archivo nuevo, `garaje/despiece_sistemas.py`, que tiene una sola tabla. despiece.js ya solo pinta.
- Cadena: Motor · Lubricación · Admisión · Escape · Caja de cambios y clutch · Kit de arrastre · (Refrigeración) · Frenos · Ruedas · Suspensión · Eléctrico.
- Automáticas: igual, pero en lugar de caja y kit van "Transmisión CVT" y "Transmisión final".
- Refrigeración solo aparece en las motos refrigeradas por líquido.
- Un sistema sin láminas se muestra igual, con el aviso "Sin piezas en el catálogo".
- La lámina de aceite manda aunque use el dibujo del cárter. Por eso Lubricación ya aparece en Apache, Boxer, Discover y NS/RS 200.
- Las scooters (Dio, Dynamic Pro) ya no muestran "Kit de arrastre".
- Resultado: una lista por tipo de transmisión y refrigeración (4 variantes en total).
  - Lo comprobé en el visor con la Pulsar NS 200 y la NMAX, sin errores en consola.
  - Único vacío: el Escape de la GN 125, que no tiene datos de catálogo.

### 3. Láminas que faltaban
- FZ 25: Caja de cambios (fig. 12). El piñón de salida queda enlazado al kit de arrastre.
- Apache: Sistema eléctrico (fig. 23), con la batería enlazada a su tarea.
  - Su título no traía los dos puntos ("FIGURA N° 23 EQUIPO…"), así que el importador ahora acepta ese formato.
  - Revisé los otros catálogos Auteco, KTM y TVS: solo se agregaron figuras, ninguna se perdió.

### 4. Clutch: dibujo propio y láminas en 17 motos
- Dibujo nuevo, `clutch`, despiezado a lo largo del eje principal. Las piezas van en este orden:
  1. Arandela de empuje
  2. Canasta con el engranaje primario y sus cauchos
  3. Buje
  4. Centro estriado con su tuerca
  5. Discos alternados (fricción con orejas afuera, separadores de acero con dientes adentro)
  6. Plato de presión
  7. Resortes y tornillos
  8. Levantador (rodamiento y varilla)
- Cada pieza tiene su guía, escrita como la explicaría un mecánico.
- Lámina del clutch agregada en: CR4, NKD, TT, Boxer, Discover, NS 200, RS 200, Duke, RC, Gixxer FI, Crypton, FZ 25, MT-03, XTZ, Hero (E-6), CB 125F y XR 150L.
- Pasé el embrague del arranque a Eléctrico › Arranque.

### 5. Último detalle del Auditor
- **Lector Honda:** ya quita la letra de la columna de variante que se pegaba al inicio de la descripción ("A SWINGARM SUB ASSY." → "SWINGARM SUB ASSY.").
  - Los nombres "O RING", "C RING", "E RING" y "V BELT" se conservan.
  - Reimporté la CB 125F y la XR 150L, que eran las únicas con ese problema (10 piezas). Antes saqué el respaldo `respaldo_honda.json`.
- **Otros nombres:**

  | Antes | Ahora |
  |---|---|
  | Outer comp.clutch (Hero) | Canasta del clutch |
  | Sello para polvo (MT-03) | Guardapolvo de la dirección |
  | Rack, clutch release (Gixxer) | Cremallera del levantador del clutch |

- **"Campana delantera":** salía en 9 nombres que en realidad decían "campana del clutch" o "campana del piñón". Corregido.
- **Resultado:** solo quedan sin nombre en español los 2 códigos de la GN 125.

## Quedó pendiente
- **Best 125:** su clutch es centrífugo (de zapatas) y no ubiqué la figura. Hay que buscarla en el catálogo FD125.
- **Apache:** su clutch viene en la misma lámina que la tapa y el filtro (fig. 4). La dejé en Lubricación porque el filtro solo está ahí. Separarla pide partir la lámina en dos vistas.
- **GN 125:** no tiene datos de catálogo, ni escape ni clutch.
- **"sistema" forzado por lámina en los mapas:** no lo hice. Para guardarlo en la base de datos hace falta un campo nuevo y una migración.
- **Tarea "discos-clutch":** no la creé, la decides tú.

## Optimización
- La vista del despiece hace 7 consultas por moto, sin N+1. No hubo que cambiarla.
- despiece.js ya se carga solo en la ficha de la moto y con `defer`.

## Pruebas y respaldos
- `manage.py test garaje`: 78 OK. Incluye 3 pruebas nuevas, de sistemas y del clutch.
- Respaldos de la base de datos antes de reimportar (en el scratchpad de la sesión): `respaldo_0315.json` y `respaldo_clutch.json`.
- Borré una lámina que yo mismo había agregado por error esa noche: la Hero E-5, que es la tapa derecha del cárter y no el clutch. Está en el respaldo.

## Archivos tocados
- `garaje/despiece_sistemas.py` (nuevo)
- `garaje/views.py`
- `garaje/static/garaje/js/despiece.js`
- `talleres/static/talleres/css/tallerya.css`
- `garaje/diagramas.py`
- `garaje/despiece_guia_mecanica.py`
- `garaje/despiece_variantes.py`
- `garaje/management/commands/importar_despiece.py`
- `garaje/tests.py`
- `garaje/despiece_mapas/*.json`: 17 con clutch, más FZ 25 fig. 12 y Apache fig. 23
