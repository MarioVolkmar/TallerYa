# Auditoría del despiece (noviembre de 2026)

Esta auditoría la hizo la sesión **Auditor**, por encargo de "Auxiliares". Los cambios los aplicó la sesión **"Planos y Esquema Piezas"** en 4 tandas y el Auditor los verificó al terminar cada una. No hay nada en commit.

## Qué se revisó
- **Base de datos:** los 23 despieces, con 353 láminas, 7.498 piezas y 608 piezas enlazadas al plan de mantenimiento al cierre. Al empezar eran 352 láminas, 7.450 piezas y 751 enlaces.
- **Código y datos:** los mapas `garaje/despiece_mapas/*.json`, los lectores e importador, el glosario y el traductor, y los dibujos de `diagramas.py`. Los 27 dibujos se renderizaron y se revisaron a ojo; en los de engranajes se hizo además el cálculo de que engranen.
- **Contraste con los catálogos PDF:** se buscó cada código de la base en el texto de su PDF y se cotejó una muestra de 2 láminas por moto. Hay 22 motos con PDF; la GN 125 no tiene.
- **Imágenes:** se revisaron en hojas de contacto.

## Corregido y verificado

### Todas las motos
- **Enlaces falsos a tareas:** había 173. Venían de reglas que atrapaban herrajes: "Capuchón bujía", "Eje piñón salida", "Porta sprocket", "BAND, BATTERY", "Soporte radiador", "Resorte válvula" y otros. Ahora una regla solo enlaza si la pieza empieza por el patrón o si no empieza por una palabra de herraje (`tarea_para` en el importador).
- **Nuevo modo `--reenlazar` del importador:** recalcula tarea, nombre y ayuda sin borrar las marcas x/y (las 347 de la NMAX siguen intactas).
- **Traducciones que cambiaban el sentido:** "CAM, BRAKE" salía como "Rampa del variador" y ahora es "Leva del freno". "ROD, CONNECTING" salía como "Varilla amortiguadora" y ahora es "Biela". "SLIDER, CHAIN" era "Deslizador del variador", "CUSHION ASSY" era un "caucho" y "CYLINDER ASSY, FRONT MASTER" era "Cilindro".
- **Nombres:** se quitaron los códigos de modelo (cgr, ttr, nkd…) y se desarrollaron las abreviaturas (camp, carcaza, empaq, inf…). Ya no queda ninguna pieza sin nombre, salvo 2 de la GN 125 cuya descripción es solo un código.
- **Cadenilla de la MT-03 (fig. 4):** "DAMPER, CHAIN 1/2" ahora se llama "Guía de la cadenilla".
- **Caja de cambios (dibujo):** los engranajes no engranaban (ejes a 165 con pares que suman 90). Ahora los ejes van a 90 y cada eje tiene sus dos rodamientos.
- **Transmisión final de scooter (dibujo):** al eje primario le faltaba el rodamiento de la tapa.

### Honda (CB 125F, Dio 110, XR 150L)
- **Piezas ajenas en las láminas:** las páginas de boletín "PARTS CATALOGUE NEWS" metían piezas de otros sistemas. Por ejemplo, la culata de la CB 125F traía pistones, la manigueta del clutch y un reflector. Ahora esas páginas se saltan.
- **Filas basura:** se quitaron 39 filas cuya descripción era un código de modelo o de color ("2TU", "CO", "7ID,8ID") y 70 filas duplicadas.
- **Recorte de imágenes (también en Hero):** quedó solo el dibujo, sin la tabla F.R.T., el encabezado de partes, el panel lateral ni el pie de página.

### AKT (CR4, Dynamic Pro, NKD, TT)
- **Filas que no se leían:** el lector descartaba 219 de 1.776. Ahora lee 1.774; las 2 que faltan son duplicados.

### Auteco (Boxer, KTM Duke y RC)
- **Boxer:** había unas 50 filas con descripción "- - -"; ahora heredan la descripción de su variante.
- **KTM:** el año se guardaba como cantidad (por ejemplo, 2014 piezas); corregido.

### Suzuki (Best, Gixxer)
- **Nivel de las piezas:** se quitó el punto inicial de 95 descripciones y ese punto pasó a indicar el nivel de la pieza.

### Scooters (Dio, Dynamic Pro, NMAX)
- **Dibujos de cadena:** la rueda trasera y el amortiguador ya no muestran cadena, corona ni templadores, gracias a la bandera "s" del perfil. Los títulos también se ajustaron.
- **Nombres de la NMAX fig. 13:** la transmisión final es un reductor de dos etapas, sin marchas, así que se quitaron los ordinales inventados. "Piñón de primera" pasó a "Engranaje conducido del eje de salida".
- **Aceite de la caja:** en la NMAX se importó la fig. 10 (cárter) y se enlazó el tornillo de llenado. También se enlazó el control del nivel de aceite del motor en las tres scooters.

### Reglas agregadas
- Depósito de líquido de frenos de la Dynamic Pro.
- Unishock de la TT.
- Diafragma de la Best.
- Elemento filtrante y 14 llantas de la Boxer.

## Gixxer 150: catálogo nuevo (verificado)
- **Catálogo:** GSX150FRLAM0, Gixxer SF FI ABS 2020, con disco trasero. Se guardó en `manual_despiece/suzuki-gixxer-150-sf-abs/`.
- **Datos:** 405 filas, todas coinciden con el PDF. El lector Suzuki ahora entiende las refs con sufijo ("1-1"), las descripciones partidas en dos líneas y las filas escritas en una sola línea.
- **Tareas con su pieza:**
  - pastillas delanteras y traseras;
  - líquido de frenos en las dos bombas;
  - llantas, kit de arrastre, bujía, filtros, amortiguador y batería (fig. 21).
- **Catálogo anterior:** el de tambor (GSX150L6) quedó desactivado, sin borrar. `Despiece.para` elige el nuevo para cualquier año.
- **Efecto en otras motos:** al arreglar el lector se recuperaron filas en CB125F (343), XR150L (308), Hero y Best, y todas siguen coincidiendo con su PDF.

## Requisito 9: integridad de conjuntos (verificado)
- **Escape:** 22 de 23 despieces activos tienen su lámina de escape. La GN 125 no tiene datos.
  - El sensor de oxígeno solo sale en motos de inyección, y el escape de una pieza se dibuja sin unión. Se verificó en la imagen del visor de la CB 125F y la XTZ.
  - La Boxer ya tiene su fig. 19: el lector exigía "N°" en el título y ahora es opcional.
- **Basculante:** las motos que no tenían su lámina ya la tienen, y ninguna lámina de basculante queda sin dibujo propio.
- **Tensores:** el dibujo lleva el taco con índice, el tornillo, la platina, la contratuerca y las marcas. Hay 32 enlaces a la tarea de cadena, y todas las motos de cadena tienen al menos uno.
- **Corregido:** el guardacadena "CASE, CHAIN" quedó enlazado como tensor en Crypton, MT-03 y XTZ. Venía de una regla "CABRECADENA" mal sugerida por el Auditor: el catálogo Yamaha bilingüe llama así al guardacadena. Se quitó la regla y la pieza ahora se llama "Guardacadena". La tarea de cadena tiene 29 enlaces y ninguno es un guardacadena.

### Diagnóstico inicial del requisito 9
El usuario pidió que cada conjunto se vea completo: el escape entero, los tensores de cadena y el basculante en la suspensión trasera. Este es el diagnóstico; la tanda está enviada y todavía no está verificada.
- **Escape:** el dibujo base ya trae el conjunto completo: empaque, brida, tubo, catalizador, empaque de unión, abrazadera, silenciador, protector y soporte. Lo que falta:
  - **Láminas de escape:** 11 despieces no tienen la suya aunque el catálogo sí la trae (las 4 AKT, Boxer, Hero, CB125F, Dio, XR150L, Best y la GN125, que está por confirmar).
  - **Sensor de oxígeno:** se dibuja también en motos de carburador. Debe salir solo en motos de inyección.
  - **Unión tubo–silenciador:** se dibuja aunque el escape sea de una sola pieza ("MUFFLER COMP."). Si no existe, no debe dibujarse.
- **Basculante:**
  - Faltan sus láminas en Duke, RC, Apache, Best y FZ25. La FZ25 no tenía ninguna lámina de suspensión trasera.
  - Seis láminas de basculante muestran el plano del catálogo en vez del dibujo propio (TT, Hero, CB125F, XR150L, GN125 y Gixxer).
  - Bieletas: ninguna moto de la flota las tiene, así que no hace falta dibujarlas.
- **Tensores:**
  - En el dibujo son un bloque y un tornillo, sin contratuerca ni marcas de alineación. Se pidió dibujar el bloque, el tornillo de ajuste, la placa, la contratuerca y las marcas.
  - No están enlazados a la tarea de cadena en ninguna moto. Se pidió enlazarlos a "cadena-lubricar", que incluye revisar la tensión.
- **Script:** `conjuntos.py` (en la misma carpeta que los demás).

## Nombres (ampliación del requisito 6, en curso)
La regla: el nombre visible dice qué es la pieza y, si hace falta, su posición. Las marcas, las medidas, las palabras en inglés, los códigos y las abreviaturas van a la guía, no al nombre.
- **Revisión:** se revisaron los 7.701 nombres visibles de los 24 despieces activos con `nombres.py`.
- **Casos dudosos:**
  - 53 nombres con marcas, por ejemplo "Llanta mrf revz", "Bujía NGK", "Cadena did" o "Batería kontrol";
  - llantas sin la posición limpia;
  - 19 con códigos o guiones del catálogo, como "Kit-arbol" o "Rin mrs-steel";
  - 4 filas de color de Honda que siguen rotas ("A * *sheen silver metallic");
  - unos 40 con signos o restos del catálogo ("#", "Rp", "(llega × unidad");
  - unos pocos en inglés, como "Collar de rueda" o "Cubierta para polvo".
- **Aceptado como español de taller en Colombia:** clutch, kit, pin seguro, sprocket y balinera. Los ordinales de los piñones de la caja ("Piñón de segunda") son la pieza misma y se mantienen.
- **Estado:** verificado en 7.946 nombres visibles.
  - Quedan 0 marcas (salvo "Emblema Yamaha", que es la pieza misma), 0 códigos, 0 signos y 0 filas de color de Honda.
  - Las llantas, los rines y los neumáticos se llaman solo "… delantera/trasera" o van sin lado. Las marcas pasaron a la guía, en el dato "Marca/referencia".
  - Se devolvieron 4 nombres menores: neumáticos "KTL INDIA" de la TT, "PIECE, OIL LOCK", "PIECE SET, SLIDE" y "Embudo para aire".

## Sistemas (requisito 10, en curso)
La regla: todas las motos muestran los mismos sistemas, en el mismo orden y con los mismos nombres. La única diferencia es la transmisión: de cadena o automática.
- **Situación hoy:**
  - La agrupación está en `despiece.js` (`FAMILIAS` y `clasificar`). Un sistema solo aparece si alguna lámina cae en él, así que los que faltan se ocultan.
  - Hay 7 listas distintas entre las 20 motos de cadena y 2 entre las 3 scooters.
- **Faltantes:**
  - Escape, en 11 motos.
  - Lubricación, en 5 (Apache, Boxer, Discover, NS 200 y RS 200). Sus láminas de aceite usan el dibujo del cárter, que manda sobre la pieza.
  - Eléctrico, en la Apache: falta la lámina.
  - Caja de cambios, en la FZ 25: falta la lámina.
  - Clutch, en las 20 motos de cadena: no hay lámina del paquete de clutch ni dibujo propio.
- **Sobrantes:** "Kit de arrastre" en Dio y Dynamic Pro, porque `_vistas` parte la rueda de tambor también en scooters.
- **Lista base acordada:**
  - De cadena: Motor · Lubricación · Admisión · Escape · Caja de cambios y clutch · Kit de arrastre · Refrigeración (solo si es líquida) · Frenos · Ruedas · Suspensión · Eléctrico.
  - Automáticas: Transmisión CVT y Transmisión final en lugar de la caja y el kit.
  - Ajuste mecánico frente a la propuesta: el clutch va con la caja de cambios, porque comparten eje y cárter.
- **Solución pedida:** una tabla única en Python que use el visor. Los sistemas sin piezas se muestran con el aviso "Sin piezas en el catálogo", nunca se ocultan.
- **Estado: verificado (14 de noviembre, 03:20).** Script: `sistemas2.py`.
  - **Tabla única:** `garaje/despiece_sistemas.py` tiene `SISTEMAS`, `sistema_de` y `sistemas_de`. El visor solo pinta.
  - **Una lista por tipo:** queda exactamente una por tipo de moto (cadena o automática, por aire o líquida).
  - **Sistemas vacíos:** el único es el Escape de la GN 125, que se muestra con "Sin piezas en el catálogo".
  - **Correcciones:** Lubricación y Eléctrico aparecen en todas las motos, y las scooters ya no muestran "Kit de arrastre".
  - **Láminas nuevas:** caja de cambios de la FZ 25 (fig. 12) y sistema eléctrico de la Apache (fig. 23).
- **Clutch:**
  - **Dibujo nuevo `clutch`:** canasta con su engranaje, centro, discos de fricción y separadores alternados, plato, resortes y levantador. Tiene sentido mecánico.
  - **Láminas:** 17 motos de cadena tienen la suya, con todas las piezas ubicadas en el dibujo.
  - **Sin lámina de clutch:** la Best 125 (su clutch es centrífugo y no se encontró la figura), la Apache (el clutch viene en la fig. 4, junto con la tapa y el filtro de aceite, y se dejó en Lubricación) y la GN 125 (no tiene catálogo).
- **Nombres, de paso:** unos 890 nombres usaban "delantero" donde iba el artículo "del" ("Anillos delantero pistón"). Ya está corregido.

## Trabajo nocturno (14 de noviembre)
- **Reglas** (pedidas por "Auxiliares"): solo cambios reversibles, sin push, sin despliegue y sin borrar datos. Respaldo con dumpdata antes de cada reimportación.
- **Commits:** el Auditor no los autorizó, porque CLAUDE.md exige que los pida el usuario. Se pidió a "Planos y Esquema Piezas" que deje los cambios sin commit y anote qué archivos tocó cada tanda.
- **Resultado de la noche:** **nada tiene commit.** El informe de "Planos y Esquema Piezas" está en `informes_noche/planos.md`. Archivos tocados en el requisito 10:
  - nuevo: `despiece_sistemas.py`;
  - modificados: `views.py`, `despiece.js`, `tallerya.css`, `diagramas.py`, `despiece_guia_mecanica.py`, `despiece_variantes.py`, `importar_despiece.py`, `tests.py` y 19 mapas.
  - Las pruebas de garaje dan 78 OK. Los respaldos con dumpdata quedaron en el scratchpad de "Planos y Esquema Piezas" (`respaldo_0315.json`, `respaldo_clutch.json`).
- **Datos borrados:** se borró la lámina E-5 de la Hero, que "Planos y Esquema Piezas" había agregado esa misma noche por error (era la tapa del cárter, no el clutch).
- **Detalle final (verificado a las 03:26):** en Honda, algunas descripciones conservaban la letra de la variante al inicio ("A SWINGARM SUB ASSY.", "C WHEEL SUB ASSY.").
  - El lector ya las quita y la CB 125F y la XR 150L se reimportaron. Antes se respaldaron en `respaldo_honda.json`.
  - Ninguna descripción empieza ya con esa letra. Solo quedan sin nombre los 2 códigos de la GN 125.
  - Archivos tocados: `despiece_lectores.py`, `despiece_variantes.py` y `despiece_glosario.py`.
- **Cierre del ciclo (03:26):** los requisitos 1 a 10 están verificados.
  - Todo coincide con su PDF, sin duplicados ni descripciones vacías, y las 347 marcas de la NMAX siguen intactas.
  - No quedan tandas abiertas.

## Decisiones pendientes del usuario (requisitos 9 y 10)
- **Tarea "discos-clutch":** decidir si se crea (cambio de discos de clutch) y se enlazan los discos de fricción. No se creó sin tu permiso.
- **Clave "sistema" en los mapas:** forzar el sistema desde un mapa necesita un campo nuevo y una migración. `sistema_de` ya acepta el argumento.
- **Honda Wave 110S:** tiene mapa pero no está en la base. Importarla crea un despiece nuevo, y eso no se hizo de noche.
- **Commit de todo lo de la noche:** queda para que lo revises.

## Desacuerdos y decisiones pendientes del usuario
- **Gixxer 150 (decidido por el usuario):** la ficha está bien, la moto tiene **disco** atrás. El catálogo GSX150L6 (2015) solo trae la versión con tambor (fig. 550A). Se quitó el enlace de las bandas y la lámina quedó titulada "Rueda trasera y corona (catálogo de la versión con tambor)". Ya no queda ninguna tarea que no aplique a la moto (verificado). Las pastillas traseras quedan sin pieza enlazada hasta que haya un catálogo de la versión con disco.
- No quedan desacuerdos técnicos. Hubo uno, resuelto: los dientes de los engranajes se dejaron fuera del nombre porque la guía ya los muestra y el nombre queda corto.

## Lo que no se pudo verificar o queda abierto
- **Suzuki GN 125:** sus datos vienen de tiendas en línea y no hay PDF con qué contrastarlos.
- **Aceite de la caja en Dio y Dynamic Pro:** sus catálogos no traen el tornillo de la caja, así que esa tarea queda sin pieza enlazada. En la NMAX, el tornillo de drenaje de la caja tampoco se pudo enlazar: su nombre ("BOLT, FLANGE DEEP RECESS") se repite en otras 6 refs.
- **XR 150L:** en algunas láminas asoma una esquina de la pestaña negra del catálogo. Recortar más cortaría la flecha "FR.".
- **Riesgo latente:** `_numero_bloque` da el mismo número a F-9 y F-9-10 (209), y lo mismo a E-1-1 y E-1-2. Hoy no hay choque porque cada mapa usa una sola variante.
- **No auditado a fondo:** el visor `despiece.js` y la Honda Wave 110S, que tiene mapa pero no está cargada en la base.

## Cómo repetir la auditoría
Los scripts están en el scratchpad de la sesión Auditor. Para conservarlos, copiarlos a una carpeta local que no vaya al repo.
- `chequeo_despiece.py [--todo]`: chequeos automáticos de láminas, piezas, enlaces, diagramas y nombres.
- `contraste_pdf.py [--muestra]`: busca cada código de la base en su PDF de `manual_despiece/` y detecta filas que vienen de páginas de boletín.
- `render.py salida.png clave1 clave2…`: hoja de renders de los dibujos propios.

Ruta: `C:\Users\volkm\AppData\Local\Temp\claude\c8098dd74742036e\241de04c-c8be-44a7-9bd8-95fb1b006a99\scratchpad\`. Se corren desde la raíz del proyecto con `venv/Scripts/python.exe`.

**Críticos encontrados: 5. Corregidos: 4** (enlaces falsos, contaminación Honda, rueda trasera de scooter con cadena y amortiguador de scooter con piezas de cadena). El quinto (la Gixxer) lo decidió el usuario: la moto tiene disco atrás. Se quitó el enlace de las bandas y se aclaró el título de la lámina (verificado). Solo falta el catálogo de la versión con disco.
