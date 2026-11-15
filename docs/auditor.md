# Instrucciones de la sesión Auditor

El Auditor revisa el despiece y sus guías, pero **no edita el código ni los datos**. Lo que encuentra lo manda en lotes a la sesión **"Planos y Esquema Piezas"**, que aplica los cambios. Después, el Auditor verifica cada lote aplicado y lo marca como verificado o lo devuelve.

El registro de todo vive en `AUDITORIA_DESPIECE.md`. Los hallazgos del filtro de fuentes van en `AUDITORIA_FUENTES.md`.

## Filtros

**El filtro 4 se suma a los filtros 1 a 3; no los reemplaza.** Todo lo anterior sigue vigente:
- los requisitos 1 a 10;
- los criterios de Planos (forma real, qué se cambia, primera palabra, nombres de empaques);
- los lotes pendientes;
- las decisiones que ya tomó el usuario, registradas en `AUDITORIA_DESPIECE.md`.

Reglas para combinarlos:
- Lo que está en curso se termina; el filtro 4 entra como trabajo adicional.
- Si una fuente externa contradice una decisión que ya tomó el usuario, no se cambia por cuenta propia: se le reporta al usuario con la fuente y él decide.
- Al verificar un lote del filtro 4, se corren también los chequeos anteriores, para que una corrección nueva no rompa algo ya verificado.

1. **Integridad de los datos:** láminas, piezas, enlaces al plan, nombres, conjuntos y sistemas. Son los filtros que ya se vienen haciendo (requisitos 1 a 10 y los criterios de Planos).
2. **Contraste con el catálogo:** cada código y lámina contra su PDF de `manual_despiece/`.
3. **Dibujos:** que los dibujos propios de `garaje/diagramas.py` se rendericen bien y sean coherentes (engranajes que engranan, sin piezas de cadena en scooters, etc.).
4. **Verificación con fuentes externas (nuevo):** ver abajo.

## Filtro 4: verificación con fuentes externas

El objetivo es que todo lo que TallerYa le dice al motociclista sobre una pieza sea correcto y se pueda respaldar con fuentes. Se revisa **todo el catálogo**: las 24 motos y todas sus piezas.

### Qué se verifica en cada pieza

**a. Concepto mecánico**
- ¿La pieza es lo que decimos que es? Se cruza el nombre en español, la descripción original del catálogo (en inglés o con el código del fabricante) y la lámina o sistema donde aparece.
- ¿Está en el sistema correcto? Ejemplo: que una leva de freno no quede en la transmisión.
- ¿Recibe la ficha que le corresponde? `ficha_para()` busca por coincidencia de texto y puede asignar una ficha equivocada.
- ¿Sirve igual en esa moto? Hay que distinguir scooter (CVT, sin cadena) de moto de cambios, carburador de inyección, disco de campana, y refrigeración por aire de refrigeración líquida.

**b. Contenido de la ficha** (`garaje/despiece_fichas.py`: `que_hace`, `cada_cuanto`, `senales`, `tips`, `dificultad`, más `como_revisar`, `si_no` y `al_comprar`)
- **Qué hace:** la función descrita es correcta y no exagera.
- **Cada cuánto (cambio estimado):** el intervalo coincide con el manual del fabricante de esa moto. Si es genérico, debe estar dentro del rango que dan fuentes confiables. Hay que señalar cuándo el intervalo depende de la moto y la ficha da una sola cifra.
- **Señales de falla:** son síntomas reales de esa pieza, no de otra.
- **Consejos:** son seguros y correctos. Cuidado especial con frenos, llantas, dirección, suspensión y sistema eléctrico. Un consejo que pueda causar un accidente o un daño es **crítico**.
- **Dificultad:** es realista. Lo que afecta la seguridad (frenos, dirección) no puede quedar como "Lo puedes hacer tú" sin advertencia.
- **Plan de mantenimiento:** si la pieza está enlazada a una tarea, el intervalo de la tarea (`TareaMantenimiento`) y el de la ficha no se contradicen.

**c. Diseño y representación**
- El dibujo del puesto (`diagramas.py`) se parece a la forma real de la pieza: silueta, partes visibles, proporciones y orientación.
- La pieza aparece en el dibujo correcto, sin una tapa dibujada como filtro ni una manguera dibujada como batería.
- La lámina tiene los componentes que debe y nada ajeno: número de piezas del conjunto, tornillería y rodamientos que faltan o sobran.
- Las marcas x/y del visor señalan la pieza correcta (muestreo por lámina).

### Cómo recorrer todas las piezas sin repetir trabajo

Son unas 7.500 piezas, pero se repiten mucho. Se trabaja por capas:

1. **Chequeo automático de todas las piezas (sin internet).** Un script recorre cada pieza de la base y registra su ficha asignada, su puesto de dibujo, su sistema y su tarea. Marca las combinaciones sospechosas: una ficha de otro sistema, una pieza de cadena en una scooter, una tarea en una pieza que no se cambia. Esto cubre el 100 % de las piezas.
2. **Verificación en internet por concepto.** Se verifica una vez cada ficha distinta (las unas 220 de `FICHAS` y sus extras), cada puesto de dibujo y cada tarea del plan. Lo verificado vale para todas las piezas que lo usan.
3. **Verificación por moto.** Para cada una de las 24 motos se cotejan los datos que cambian según el modelo: intervalos del manual de servicio o del propietario, capacidades (aceite, refrigerante), tipo de bujía, medidas de llantas, holguras (válvulas, cadena) y si es de cadena o CVT, carburador o inyección.

### Orden de prioridad (un lote por paso, para que Planos pueda empezar ya)

1. Piezas enlazadas al plan de mantenimiento (unas 608).
2. Seguridad: frenos, llantas y rines, dirección, suspensión.
3. Motor y transmisión: aceite, filtros, bujía, cadena y piñones, CVT, embrague, válvulas.
4. Sistema eléctrico y refrigeración.
5. Carrocería, tornillería, soportes y el resto.

### Fuentes

Orden de confianza:
1. **Fabricante:** manuales de servicio y del propietario, y sitios oficiales en Colombia (Incolmotos Yamaha, Fanalca Honda, Auteco para Bajaj, KTM y Kawasaki, AKT, Suzuki Motor de Colombia, Hero, TVS).
2. **Fabricantes de repuestos:** fichas técnicas y catálogos de NGK, Motul, DID, EBC, Michelin, Pirelli, Yuasa, etc.
3. **Fuentes técnicas reconocidas:** manuales de taller y sitios especializados de mecánica de motos.
4. **Foros y videos:** solo como apoyo, nunca como única fuente.

Reglas:
- Un intervalo o una cifra necesita **una fuente del fabricante o dos fuentes independientes**.
- Hay que anotar la **URL y la fecha de consulta** de cada fuente, igual que en `docs/datos/`.
- Si las fuentes no coinciden, se reportan las dos versiones y lo decide el usuario. No se elige una a escondidas.
- No se copia texto ni imágenes de manuales o sitios: se resume con palabras propias. Los planos y catálogos de terceros siguen **solo en local** (`manual_despiece/`, `despiece_local/`) y nunca se suben a internet ni al repositorio.
- No se envían datos de usuarios ni de la base a servicios externos: solo se busca por nombre de pieza, código de catálogo o modelo de moto.

### Cómo se reporta

En `AUDITORIA_FUENTES.md`, un apartado por lote con una tabla:

| Pieza o ficha | Moto(s) | Qué se revisó (a, b o c) | Dice hoy | Debería decir | Fuente(s) | Gravedad | Confianza |

- **Gravedad:** *crítico* (puede causar un accidente o un daño, o el concepto está mal), *importante* (dato incorrecto, como un intervalo o una función) o *menor* (redacción o precisión).
- **Confianza:** *alta* (fabricante o dos fuentes que coinciden), *media* (una sola fuente confiable) o *baja* (no se pudo confirmar).
- Cada lote termina con la **lista de cambios exactos para Planos**: archivo, clave de la ficha o del dibujo, texto actual y texto propuesto. Así Planos puede aplicarlos sin volver a investigar.
- Lo que el Auditor no pudo verificar se anota como abierto. No se da por bueno.

### Al terminar cada lote

1. Enviar el lote a "Planos y Esquema Piezas".
2. Cuando Planos avise que lo aplicó, verificarlo: correr el chequeo automático y revisar los dibujos que cambiaron.
3. Marcarlo como verificado en `AUDITORIA_FUENTES.md` y seguir con el siguiente.

Nada se sube con commit sin que el usuario lo pida.
