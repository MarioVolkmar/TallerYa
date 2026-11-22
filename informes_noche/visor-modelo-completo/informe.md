# Visor «modelo completo» y página de etiquetado 3D (21-nov-2026)

Puntos 1 y 2 de la estrategia 3D aprobada. Sin commit.

## 1. Visor en modo «modelo completo»
- Un GLB con `extras.modelo_completo: true` **en la escena** se muestra tal cual (`garaje/static/garaje/js/moto3d/glb.js`, `montarGlb` + `quitarGenericas`). El visor solo:
  - gira las ruedas (`extras.rueda`, y en los GLB viejos `extras.eje` como pivote),
  - enciende las luces del GLB (`extras.lampara`; las de la moto genérica se descartan),
  - pinta según Personalizar (materiales compartidos, como antes),
  - aplica Rayos X (`extras.interno`).
- En ese modo no se ponen placa, pata, espejos de otros estilos, escape ni visor genéricos, ni accesorios (tampoco baúl ni LED), ni pantalla del tablero. Las llantas no se tornean ni se labran, y se ignoran `manubrio` y `acomodar`.
- Los GLB sin la marca siguen igual: la NMAX conserva la placa, los espejos y el baúl y LED (`nmax_sin_cambios.jpg`).
- Marcador: `herramientas_3d/comun/marcar_completo.py archivo.glb [--quitar]`: reescribe solo el JSON y pasa `gltf-transform validate` sin errores. `herramientas_3d/aerox155/final.py` lo llama al final, así que regenerar la Aerox no pierde la marca.
- Marcados (con `?v=` subido): Aerox `aerox155_tripo3` (v=8), Eco Deluxe `ecodeluxe100_tripo` (v=6) y XR 190L `xr190l_tripo4` (v=8).

| Moto | Captura | Nota |
|---|---|---|
| Aerox | `aerox_tres_cuartos.jpg`, `aerox_rojo_atras.jpg`, `aerox_luces.jpg`, `aerox_rayos.jpg` | Personalizar en rojo: solo la carrocería. Luces y Rayos X bien. Ya no lleva placa. |
| Eco Deluxe | `eco_tres_cuartos.jpg`, `eco_rueda.jpg` | La llanta de Tripo queda sin huecos, pero **lisa** (sin el labrado de antes) y sin placa. |
| XR 190L | `xr190l_tres_cuartos.jpg` | Se ve bien. Sin placa. |

**Decide el usuario:** en la Eco y la XR, el aspecto cambia en dos cosas: la llanta pierde el labrado y la moto queda sin placa. Para volver atrás: `marcar_completo.py <glb> --quitar` y bajar el `?v=`. Si en el modo completo se quiere la placa, falta un extra `placa_glb` o modelarla en el GLB.

## 2. Página de etiquetado (solo staff)
- `/garaje/etiquetar-3d/` muestra la lista de modelos: los GLB del visor y, en local, los de `privado/tripo/**` (salen con el chip «Tripo sin convertir»; nunca se publican).
- `/garaje/etiquetar-3d/<modelo>/` muestra el 3D con la parte actual en lava y las demás pintadas con el color de su acabado. Se elige la pieza (44 piezas comunes) y uno de los 14 acabados, y luego «Confirmar y seguir». Las partes van de la más grande a la más pequeña. Tocar una parte en el 3D la elige. Hay vistas Lado, Frente y Atrás, y «Solo esta».
- Las sugerencias se prueban en este orden: la etiqueta ya guardada, el nombre de la parte (`material.pieza` o palabras en inglés), la parte más parecida del glosario (posición normalizada atrás-adelante, piso-arriba y centro-costado, más el tamaño relativo) y por último reglas de forma (llantas, discos, luces, motor y restos diminutos).
- Al guardar se escribe `garaje/etiquetas_3d/<modelo>.json` y se rehace `garaje/etiquetas_3d/glosario.json` con las partes **confirmadas** de todas las motos. Guarda solo cada 10 confirmaciones y al terminar.
- En el celular, el 3D queda fijo arriba y «Confirmar y seguir» va justo debajo del nombre de la parte. Así se etiqueta una parte cada pocos segundos: unas 60 partes caben en unos 10 minutos.
- Archivos: `garaje/etiquetas_3d.py`, `garaje/vista_etiquetar_3d.py`, plantillas `garaje/etiquetar_3d*.html`, `garaje/static/garaje/js/etiquetar3d.js`, el bloque «Etiquetar 3D» al final de `secciones/garaje.css`, 4 rutas en `garaje/urls.py` y las pruebas en `garaje/tests_etiquetar_3d.py`.
- Con la Aerox (66 partes), 62 sugerencias salieron del nombre y 4 de las reglas de forma. Con un GLB de Tripo sin nombres, las sugerencias saldrán del glosario a medida que se etiqueten motos.

## Verificación
- Pruebas del garaje (`manage.py test garaje --exclude-tag=lenta`): 252 OK.
- revisar-ux a 1280 y 375 px: sin bloqueantes ni importantes propios. Lo que marca (toques de 40 px en la cabecera y en «volver», el contador de la campanita) es ruido conocido del sitio. Capturas: `etiquetar_375.jpg`, `etiquetar_1280.jpg`.
- Estilo nuevo justificado: la grilla de acabados con muestra de color no tenía equivalente en la guía. Usa los tokens existentes, pero no se sumó a `anexo-guia.md` porque es una página interna de staff.

## Trampas y pendientes
- La base local tiene sin aplicar `garaje/0038_perfil_uso_y_lecturas_estimadas`, que otra sesión dejó sin commit: `/garaje/<pk>/` da error 500 en el 8001. Probé con una copia migrada en el scratchpad y no toqué `db.sqlite3`.
- Con el panel del navegador oculto no corren `requestAnimationFrame` ni `IntersectionObserver`: el visor no arranca. Para revisar, hay que simularlos e importar el módulo; el truco está en `cargar_visor.js` del scratchpad de esta sesión.
- Un GLB de Tripo sin convertir puede pesar millones de triángulos: en el celular conviene etiquetar el GLB armado (con partes separadas) y no el crudo.

## Ronda 2: huecos en la llanta trasera de la Aerox (pedido de Ejecutivo)
- **Causa:** no era el estilo de rin. Las caras de la llanta de Tripo vienen abiertas o con la normal al revés, y el visor las dibujaba por una sola cara (`side` = FrontSide). Por dentro de la rueda se veían huecos (`aerox_rueda_tras_antes.jpg`). Al dibujar las dos caras desaparecen (`aerox_rueda_tras_doble_cara.jpg`).
- **Arreglo en glb.js:** en modo completo todas las mallas del GLB se dibujan por las dos caras. Solo cambia el material, no la geometría.
- **Estilo de rin:** en modo completo `aplicarEstilo` (moto3d.js) ya no arma ni oculta rines. «Rines y detalles» solo cambia el color: de fábrica queda el material del GLB (`userData.glbMat`) y con un color elegido se usa `M.rin`. `opciones().estiloRin = false` y `personalizar.js` oculta la sección «Rines». Las motos viejas siguen igual.
- **Placa:** en modo completo vuelve a ponerse (es la excepción que permite el usuario).
- **FALTA verificar:** la rueda delantera de cerca, las dos girando, que el cambio de color funcione, y correr de nuevo las pruebas del garaje. La sesión llegó al tope de contexto.

## Ronda 2: verificación final (21-nov)
- Aerox (/garaje/59/vista-3d/): llanta y rin, delantera y trasera, vistos de cerca por los dos lados (`aerox_rueda_del_a/b.png`, `aerox_rueda_tras_a/b.png`): sin huecos. Los pivotes de rueda giran las 9-10 mallas alrededor de su eje (desvío del centro ≤ 1,7 cm en 1,3 rad); las ruedas giran en la animación de entrada/salida.
- «Rines y detalles»: con la Plata elegida cambian solo `rin.rin_del` y `rin.rin_tras` (pasan a `M.rin`); llantas y disco quedan igual; la sección «Estilo de rin» sigue oculta. Placa amarilla visible atrás. Captura: `aerox_color_rines.png` (muestra Rayos X al cargar).
- Eco Deluxe (60), XR 190L (38) y NMAX (3): bien, sin errores de consola (`eco_final.png`, `xr190l_final.png`, `nmax_final.png`).
- Etiquetado (`etiquetar_final.png`, 900 px, staff): carga el Aerox tripo3 (66 partes), sin errores de consola. Detalle menor: el selector «Pieza» abre en «Llanta delantera» aunque la parte sea `plastico.interior` (el acabado sí se sugiere).
- Pruebas: `manage.py test garaje --exclude-tag=lenta --parallel 1`: 252 OK (en paralelo una prueba de /mi-taller/ rompe el ejecutor por un error de pickle, ajeno a esto).
