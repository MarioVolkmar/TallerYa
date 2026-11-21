# XR 190L: 3D desde Tripo con un método nuevo (20-nov-2026)

GLB: `garaje/static/garaje/modelos/xr190l_tripo2.glb`, **1.013 KB, 78.379 triángulos** (64.322 de Tripo + 14 mil de los internos), 49 nodos (31 piezas visibles y 18 internas). Conectado en `glb.js` (`MODELOS_TRIPO`, clave `"xr[ _-]*190"`, `?v=2`) y, en el mismo archivo, un material `M.blanco` (plástico blanco de fábrica). Scripts en `herramientas_3d/xr190l/`. Copia de trabajo: `privado/tripo/xr190l/`.

## Método (sin heredar el anterior)
1. `comun.py`: lee el GLB, lo gira a las coordenadas del visor (x adelante, y arriba, z lateral) y lo escala para que la distancia entre ejes sea la real (1.353 mm). El ancho resultante, 0,80 m, cuadra con la ficha (830 mm).
2. Ruedas medidas en la malla: centro en el punto de apoyo y radio en la altura del eje. Rines de 21" y 18" según la ficha. El eje de la horquilla sale de un PCA de los puntos a los lados de la rueda.
3. `segmentar.py`: a cada cara le toca una pieza según reglas geométricas en coordenadas de la moto (radio al eje, distancia al eje de la horquilla, cajas, normales). La primera regla que acierta gana. Después, 3 vueltas de voto por mayoría entre caras vecinas para que los bordes queden menos dentados.
4. La geometría de Tripo no se mueve ni se simplifica: solo se reparte. Las normales se calculan sobre la malla entera, así que las piezas empalman sin costura de luz.
5. `construir.py`: arma los nodos `material.parte` con sus extras (pieza, eje, aro, rin, lampara, manubrio, placa, zonas, padre, sin), construye los internos y escribe el GLB cuantizado (posiciones int16, normales int8).
6. `ver_despiece.py`: render propio en numpy (colores falsos, finales o Rayos X) para iterar sin navegador.

## Defectos corregidos
- 3 triángulos sueltos quitados.
- 60 huecos chicos tapados (lazos de borde de hasta 40 aristas; quedaban 575 aristas de borde).
- 203 caras invertidas, detectadas contra la normal promedio de sus vecinas. **Ojo:** en piezas delgadas el criterio puede fallar; falta confirmarlo en el visor.
- No había caras degeneradas ni aristas no-manifold.

## Rayos X (lo único construido nuevo)
- Cilindro con 9 aletas, inclinado 15° adelante, con pistón, biela, culata y tapa de válvulas.
- Cigüeñal de dos volantes, 6 piñones de la caja y canasta del embrague.
- Bujía y capuchón.
- Caja del filtro de aire redondeada, con elemento plisado, ducto y carburador.
- Batería YTX5L con bornes.
- Cableado del faro a la batería, a la bobina y a la cola.

Están en `rayos_x_lateral.png`.

## Colores
Rojo en aletas, guardabarros delantero, máscara y colín. Blanco en la tapa lateral (material fijo `blanco`: con `pintura2` salía roja, porque el segundo tono toma el color principal cuando la moto no trae uno). Negro en el asiento, el chasis, el tanque y la cubierta trasera. Plateado en las barras bajas, el basculante, los aros y los rayos. Motor gris oscuro. Comparaciones en `comparacion_lateral.jpg` y `comparacion_tres_cuartos.jpg`. **Esas dos llevan fotos de referencia: no publicar.**

## Verificado en el visor real (moto 38, usuario de prueba)
- 1280 px: la moto carga con `xr190l_tripo2.glb?v=2` y se ve completa.
- 375 px: también se ve completa, sin desborde horizontal.
- Rayos X: la carrocería pasa a malla translúcida y se ven el motor y el filtro.
- Personalizar: con «Azul» se pintan aletas, guardabarros, máscara y colín, y la tapa lateral sigue blanca. Después se dejó otra vez en «Rojo (de fábrica)».
- No se ve nada flotando.

## Pendiente
- Fuera de este modelo: en el panel del navegador, `/garaje/<id>/` a veces muestra «No pudimos cargar el modelo 3D» sin llegar a pedir ningún GLB. Pasa igual con la Boxer (moto 54). Importando `moto3d.js` a mano, la moto carga bien. En la consola sale «An unknown error occurred when fetching the script», que viene del registro del service worker `/sw.js`.
- Bordes de pieza aún dentados en algunas zonas (asiento con tapa lateral, cola). Las llantas las vuelve a tornear el visor.
- Sin revisar de cerca: escape, posición de la placa y las direccionales delanteras (no quedaron separadas: van en la máscara). Estribos y pedales van en chasis.
- Las calcas «XR 190L» se declaran en `calcas_fabrica`, pero no se probaron.
