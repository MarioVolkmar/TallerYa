# XR 190L con Blender, desde cero (xr190l_tripo4.glb)

**Estado:** conectado en `glb.js` (`xr190l_tripo4.glb?v=6`). Carga sin errores en el visor (1280 y 375 px). Personalizar, Rayos X y las luces encendidas funcionan. Sin commit. Tardó ~1 h 40 min: se pasó del límite de 1 h.

## Método
1. **Entrada.** El GLB de Tripo (`privado/tripo/xr190l_cero/modelo-3d-xr190l.glb`) resultó ser **una sola malla de 64 k triángulos, sin textura, sin material y sin UV**. Por eso el color no sale de una textura horneada: sale de segmentar por geometría.
2. **Orientación y escala** (`comun.py`). Se rota 90° en Z (es una rotación, no un espejo: el escape sigue a la derecha). La escala es uniforme y sale de la distancia entre ejes de la ficha (1,355 m, ejes en x = ±0,6775 como en la moto procedural). El piso queda en z = 0. Con eso el largo total da 2,08 m (ficha ≈ 2,09 m) y los radios de rueda medidos dan 0,322 m adelante y 0,309 m atrás (ficha: 90/90-19 ≈ 0,32 m, 110/90-17 ≈ 0,31 m).
3. **Zonas** (`vista.py` → `construir.py`). Se hicieron vistas ortográficas lateral, de frente y de atrás con una cuadrícula de 5 cm. Sobre ellas se midieron las zonas de cada pieza: cajas laterales, la línea del sillín, la línea de la horquilla, radios alrededor de cada eje, el lado del escape y la normal de la cara para micas y espejos. Cada cara se clasifica por su centro. Antes de clasificar, la malla se **corta con planos** (bisect) en los bordes que se ven: la mica de la farola, las tapas blancas, las aletas, el tanque y la división de la horquilla. Así el borde entre piezas es recto y no dentado. Después, un suavizado de 3 pasadas pasa a la pieza vecina las caras sueltas (menos en luces y ruedas).
4. **Ruedas.** Se separan por radio: caucho, aro y rayos con maza. El disco y la corona salen por radio y lado. La llanta va con `pieza` y `eje`, así que el visor la rehace como sólido de revolución redondo y labrado (`torno: "redondo"`): queda sin huecos donde la tapaban el guardabarros o la horquilla. El aro tiene `aro` (plateado de serie, toma el color de Personalizar) y los rayos tienen `rin`.
5. **Rayos X.** Las piezas internas son primitivas con `interno: true` y su `pieza` de mantenimiento: pistón, biela, cigüeñal, 4 engranajes de la caja, clutch y magneto (pieza motor), cárter de aceite (aceite), bujía, filtro de aire, cuerpo de aceleración e inyector (PGM-FI, como en la foto), batería, monoamortiguador (suspension_tras) y 3 tramos de cableado.
6. **Exportación** (`hacer.sh`). Blender exporta con extras → `gltf-transform quantize` (posiciones int16, normales int8) → `separar_vistas.py` → `validate` (0 errores, 0 avisos).
   - **Trampa:** el lector de `glb.js` no suma `accessor.byteOffset`, y gltf-transform deja varios accessors en un mismo bufferView. Eso daba geometría con NaN. `separar_vistas.py` deja un bufferView por accessor; así no hubo que tocar `glb.js`.
7. **Piezas genéricas del visor.**
   - Los espejos de Tripo van con `padre: "espejos.fabrica"`: reemplazan a los genéricos, que salían repetidos.
   - La máscara lleva `rol: "visor_fijo"`, que quita la lámina blanca genérica que tapaba la farola.
   - La placa procedural se lleva al guardabarros trasero con `extras.placa`.

Comando: `sh herramientas_3d/xr190l_cero/hacer.sh <carpeta temporal>`. Tarda ~1 min y corre un solo Blender.

## Pieza → material
| Pieza (nodo) | Material del visor | Nota |
|---|---|---|
| pintura.aletas, .mascara, .guardabarros_del, .colin | pintura (rojo de la moto, Personalizar) | aletas del tanque, máscara de la farola, guardabarros delantero, colín |
| blanco.tapa_lateral_i / _d | blanco, tono #eef0f2 | tapas blancas de fábrica |
| plastico.tanque, .aletas_bajo, .tapa_trasera, .guardabarros_tras | plastico (negro mate) | lomo del tanque negro, como en la foto; guardabarros trasero con placa |
| asiento.sillin | asiento (Personalizar) | |
| chasis.chasis, chasis.parrilla | chasis (tono #1d2023, Personalizar) | |
| metal.basculante, .barras_del | metal | basculante y botellas plateados |
| caucho.fuelles_del, caucho.punos | caucho | fuelles de la horquilla, puños |
| oscuro.horquilla_sup, .manubrio, .estribos, .espejos | oscuro | |
| espejo.luna | espejo | |
| motor.motor | motor, tono #34383b | motor negro (pieza motor) |
| titanio.silenciador, .tubo_escape | titanio | escape al lado derecho |
| caucho.llanta_del / _tras | caucho labrado (torneada) | eje [±0,6775; 0,322 / 0,309] |
| metal.aro_* (aro), metal.rayos_* (rin) | metal | |
| disco.disco_del, oscuro.corona | disco / oscuro | giran con la rueda |
| luz.farola | luz, lampara faro | farola de Tripo, en su sitio |
| stop.stop | stop, lampara stop | |
| ambar.direccional_del_i/d, _tras_i/d | ámbar, lampara direccional | 4 direccionales separadas |
| internas (21 nodos) | cromo, metal, carter, aceiteVisible, bujia, oscuro, bateria, resorte | solo en Rayos X |

## Números
- **Peso:** 958 KB (tope 1,5 MB).
- **Triángulos:** 70.252 (64 k de Tripo, más los cortes rectos y ~1 k de internas).
- **Nodos:** 59.

## Pendientes y defectos a la vista
- **Farola:** la mica es un recuadro recortado en la superficie de Tripo, que no trae una lente modelada. Se ve definida y alumbra, pero es plana y sin reflector. Mejora posible: una lente con relieve y una parábola internas, modeladas en Blender sobre ese recuadro.
- **Tapa blanca izquierda:** el borde de arriba todavía muestra algo de dientes donde la superficie de Tripo es irregular. Otro corte por la curva real del borde lo dejaría limpio.
- **Lado derecho:** el silenciador tapa casi toda la tapa blanca. Es fiel a la geometría, pero hay que confirmarlo contra la moto real.
- **Pata lateral:** la que se ve es la procedural (protegida por el visor) y no la de Tripo, que quedó dentro de `chasis`.
- **Cadena:** queda la procedural (interna, en Rayos X); la de Tripo va dentro del basculante y no es una pieza aparte.
- **Página del garaje a 375 px:** en dos intentos salió «No pudimos cargar el modelo 3D», porque un módulo JS no se pudo descargar ("unknown error when fetching the script") antes del temporizador de `moto.html`. El mismo GLB carga bien a 375 px en `/garaje/38/vista-3d/`, así que parece del servidor de desarrollo, cargado por otras sesiones, y no del modelo. Falta repetirlo con el equipo libre.
- No se corrió `revisar-ux` ni `optimizar-velocidad`, porque no hubo cambio de interfaz: solo cambió la URL del modelo.
- No se instaló nada. Ayudaría un decodificador meshopt en el visor: el GLB bajaría a ~300 KB.

## Archivos
- `garaje/static/garaje/modelos/xr190l_tripo4.glb` y el cambio de una línea en `garaje/static/garaje/js/moto3d/glb.js`.
- `herramientas_3d/xr190l_cero/`: `comun.py`, `vista.py`, `analizar.py`, `construir.py`, `separar_vistas.py`, `hacer.sh`.
- Capturas del visor en esta carpeta: `final_lateral.png`, `final_tres_cuartos.png`, `final_luces.png`.

## Arreglos del 21-nov (v=7)
- **Cilindro encima, entre el sillín y el colín:** era el escape genérico del visor (`moto.escapeFabrica`, que el visor protege). Se quitó sin tocar `glb.js`: el silenciador y el tubo de Tripo llevan `padre: "escapeFabrica"`, así el visor vacía el genérico y pone el de Tripo en su lugar. Personalizar lo sigue manejando como escape de fábrica.
- **Farola:** ya no es un recuadro. Sigue la forma que trae la máscara de Tripo, medida de frente en `vista_farola.py`: bajo la ceja (z 0,982) y hasta el arco de abajo (z 0,862), con la forma de escudo de la XR. Va cortada con planos por sus bordes, con la mica `luz.farola` (lámpara faro) y un marco negro de 7 mm, `plastico.marco_farola`. El visor no pone otra farola encima: las lámparas del GLB reemplazan a las genéricas y la máscara sigue con `visor_fijo`.
- **Llantas:** el visor sí las retornea (`tornearLlanta`, por `caucho` + `eje` + nombre «llanta»). Las medía con todo el caucho de Tripo dentro de R + 4 cm, que incluía pedazos del guardabarros y el costado inflado, y salían de R 0,38 m y 17 cm de ancho. Ahora el caucho se limita al ancho de la ficha (90/90-19 adelante y 110/90-17 atrás: medio ancho 0,049 y 0,059 m) y al radio medido. Se descartan 686 caras de costado sobrante que tapa la llanta torneada. Medido en el visor: delantera Ø 0,661 m × 0,107 m y trasera Ø 0,656 m × 0,122 m (llevan la holgura de 3 mm del torno), con el pivote justo en el eje.
- Peso: 968 KB. Validación: 0 errores. Capturas: `arreglo_lateral.png` y `arreglo_tres_cuartos.png`.
- `glb.js`: solo cambió `?v=7`.
