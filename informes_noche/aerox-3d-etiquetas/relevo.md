# Relevo: Aerox tripo4 (21-nov-2026, ronda 3 hecha, sin commit)

Estado: `aerox155_tripo4.glb?v=8`, 1,45 MB, revisión OK (ronda 5 abajo). Rama `piloto`, sin commit.

Ciclo, ~1 min: `python -I .claude/skills/moto-3d-blender/scripts/correr.py .claude/skills/moto-3d-blender/fichas/aerox155.json informes_noche/aerox-3d-etiquetas`

## Ronda 3: los tres errores del usuario
1. **Farolas**: `recorte.contorno` en la ficha. Es el polígono de `farola.jpg`, con u de afuera al centro y v de arriba abajo. Sin `cara`, ya no queda carcasa negra.
   - Lo del carenado que tapa la mica se quita.
   - Los huecos sin mica detrás pasan a mica.
   - La mica que sobra afuera pasa a pintura o a plástico mate.
   - Capturas: `arreglo2_farola.png` (apagada) y `arreglo2_farola_luces.png`.
   - Queda por mejorar: motas oscuras de pocos píxeles en el borde de abajo. Además, la foto tiene un filete gris oscuro bajo la mica que el modelo no tiene.
2. **Placa**: ahora va en la parte 46, «porta placa», con inclinación de −0,41 rad. Se pega 4 mm por delante de lo más saliente del soporte, para que las pestañas no la atraviesen. Captura: `arreglo2_placa.png`.
3. **Panel delantero**: es el interior del frente bajo el manubrio, en la parte 4, zona 0. Pasa a plástico negro mate con `forzar_cara` (normal suavizada que mira atrás, umbral 0,15). Captura: `arreglo2_panel.png`.

## Lo que pasó a la skill
- `armar.py`: `recorte_mica` con `contorno`, `forzar_cara` + `suavizar`, y la placa pegada delante de las pestañas.
- `SKILL.md` y `trampas.md` actualizados, y copia en el respaldo `~/.claude/skills_respaldo/tallerya/moto-3d-blender/`.

## Ronda 4 (v=6, 1,45 MB, revisión OK)
- **Mica con sombreado suave**: normales promediadas y triángulos volteados al frente. El simplificador ahora usa `--lock-border`. La ficha pasa a `simplificar.error 0,0018` para no pasar de 1,5 MB.
- **Placa más pequeña** (v=7): la colombiana actual al 78 %, 18,3 × 10,5 cm, con las mismas proporciones y diseño. Es el valor por defecto de `PLACA_CO`. El usuario descartó la de los modelos antiguos.
- **Capturas**: `arreglo3_farola.png` (apagada a la izquierda, encendida a la derecha) y `arreglo3_placa.png`.
- **Pendiente**: con la luz encendida aún se ven puntitos y rayitas oscuras en la mica, sobre la costura tira/reflector y en el borde de abajo. La causa no está aislada; ver lo que ya se probó en `trampas.md`. Siguiente paso: revisar el material de `luz` en `pintarVivo` (moto3d.js), por si es translúcido o no escribe profundidad, y si la mica de Tripo tiene doble capa.

## Si el usuario pide más
- Ajustar `contorno` en la ficha.
- Si la mancha negra del panel cubre de más o de menos, ajustar `forzar_cara.4.0.umbral`: subirlo cubre menos.

## Ronda 5 (v=8, 1,45 MB, revisión OK): detalles finales del usuario
- **Tablero**: la zona «tacometro» (parte 6, zona 3) sale como `pantalla.tablero` (M.pantalla): negra apagada, brilla con «Encender». `moto3d.js` `pintarVivo`. Captura: `detalle_tablero.png` (de día y de noche, encendida).
- **Ruedas**: la delantera giraba sobre un eje 8,6 mm más alto que su centro, porque un pedazo de guardabarros pegado a la llanta (412 triángulos) jalaba el ajuste y además giraba con ella. Ahora el eje sale de un ajuste robusto y los restos quedan fijos en `plastico.restos_rueda_del`. `revisar.py` revisa la redondez y los restos. Captura: `detalle_rueda.png` (ruedas giradas 1,3 rad).
- **Personalizar** (todos los «modelo completo», también la Eco Deluxe): solo Color de la moto, Acabado, Rines y Sillín, sin pestañas. Calcas ocultas hasta que el GLB traiga `extras.calcas`. Lo guardado de otras opciones se ignora en el visor, no se borra. NMAX y las genéricas, igual. Archivos: `personalizar.js` (`ajustarCompleto`), `moto.html` (clases `solo-generica`/`con-calcas`), `garaje.css`, `moto3d.js` (`aplicarPersonalizacion`, `opciones`), `glb.js` (`calcasModelo`). Captura: `detalle_personalizar_375.png`.
- **Pendiente**: los puntitos oscuros de la farola encendida. No alcanzó el tiempo; el siguiente paso sigue siendo el de la ronda 4.

## Ronda 6 (HECHA, ver «Ronda 6: resultado» al final; pedido del usuario vía Ejecutivo, 21-nov): calcas de fábrica, sin calcas personalizadas
**1. Desactivar las calcas personalizadas en todas las motos, sin borrar nada.**
- Interruptor de configuración `CALCAS_PERSONALIZADAS = False` en `config/settings.py`. Pasarlo a la plantilla por contexto, o por `json_script` en los datos del visor, y luego a `personalizar.js` y `moto3d.js`.
- En falso:
  - Se ocultan la subpestaña «Personalizadas» (`#sub-propias`, `#sub-panel-propias` en `moto.html` ~l.326-347) y el botón «Color» y el editor de color de cada calca de fábrica (`pintarFabrica`, `personalizar.js` ~l.140-170).
  - Queda solo la lista de calcas de fábrica con su interruptor (`estilo.sin_fabrica`).
  - El visor ignora `cfg.calcas`, como ya hace hoy el modelo completo en `aplicarPersonalizacion` (`moto3d.js`): los datos guardados quedan intactos y no rompen nada.
- La pestaña Calcas solo aparece si `TallerYa3D.calcasFabrica()` trae algo. En el modelo completo, hoy la clase `sin-calcas` depende de `opciones().calcas` = `extras.calcas` de la escena: unificarlo con «hay calcas de fábrica».
- Reactivar = poner el valor en `True`. Anotarlo en el informe.

**2. Calcas de fábrica de la Aerox (y paso nuevo de la skill `moto-3d-blender`, trabajo 3D: opus).**
- Fuente: `FOTOS_MODELADO_TRIPO/yamaha_aerox_155/referencia/`. Las principales: logo «AEROX», franjas y gráficos de los costados, logo Yamaha.
- Cada calca va como capa aparte y fina sobre `pintura.*`, separada 1-2 mm de la superficie (sin z-fighting), con textura chica recortada y fondo transparente. La geometría de Tripo no cambia.
- Marcas: `extras.calcas_fabrica` con `en: [x, y]`, como las genéricas (ver cómo `glb.js` y `calcasFabrica()` las ubican), y `extras.calcas: true` en la escena (`glbio.escribir(..., {"modelo_completo": True, "calcas": True})`).
- Capturas: `detalle_calcas.png`, una con todas visibles y otra con una oculta.
- La sección «Personalizar en modelo completo» del `SKILL.md` ya explica cómo marcarlas; sumar el paso con fuente y recorte.

## Ronda 6: resultado (v=10, `aerox155_tripo5.glb`, 1,44 MB, revisión OK, sin commit)
- **Rueda delantera**: eje y centro estaban bien (inclinación 0,1°, trasera 0,4°). La deformidad era el disco de Tripo: le falta ~90° (lo que tapaba la mordaza) y el hueco daba vueltas. Ahora el disco que no es de revolución queda fijo (`armar.py` `de_revolucion`); `revisar.py` revisa inclinación del eje y que todo lo que gira sea de revolución. Trasera limpia. Al parar, el visor deja las dos ruedas en ángulo 0 exacto (`moto3d.js` `ruedasHacia`, todas las motos). Captura: `detalle_rueda_del.png` (girada 1,3 rad).
- **Calcas personalizadas apagadas**: `config/settings.py` `CALCAS_PERSONALIZADAS = False` (variable de entorno). **Reactivar: poner `True`.** Llega por `datos_3d` y `personalizacion` (`garaje/views.py`); `moto3d.js` no las dibuja, `personalizar.js` + `garaje.css` (`.sin-calcas-propias`) ocultan la subpestaña, el contador y el color de las de fábrica. Nada borrado.
- **Calcas de fábrica de la Aerox** (ficha `calcas_fabrica` + `calcas_zonas`): «aerox», filete cian del costado, filete de la cola, rayas del frente, insignia lisa del escudo (sin emblema de la marca) y ABS. Visor: decal de 5 cm en modelos completos, sigue por piezas vecinas con zona. Formas nuevas `linea` e `insignia` en `calcas_fabrica.js`. Capturas: `detalle_calcas.png`, `detalle_calcas_oculta.png` («aerox» quitada).
- **Eco Deluxe**: ahora muestra la pestaña Calcas con sus calcas de fábrica genéricas (ya se dibujaban). NMAX no se pudo abrir con `usuario@prueba.com` (sus motos son de otros usuarios).
- **Pendiente**: puntitos de la farola encendida (rondas 4-5); afinar posición del filete de la cola si el usuario lo pide.
