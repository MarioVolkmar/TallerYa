# Aerox 155 estilizada con Blender (aerox155_tripo2.glb, ?v=11)

Resultado: `garaje/static/garaje/modelos/aerox155_tripo2.glb`, 1,08 MB, 75,6 mil triángulos, 58 nodos. `gltf-transform validate`
no da errores ni avisos. En `moto3d/glb.js` solo cambió la entrada `aerox` de `MODELOS_TRIPO`. El GLB anterior (`aerox155_tripo.glb`)
sigue en su lugar. Sin commit.

## Flujo (herramientas_3d/aerox155/)
1. `blender/geometria.py` (Blender 5.3 sin ventana, copia del método de la Eco Deluxe): une vértices, quita degenerados, tapa
   huecos chicos, Decimate suave, suavizado por ángulo y, nuevo, **Laplaciano con los bordes fijos** en la carrocería, la pintura,
   el sillín, el motor y el escape: quita las arrugas que deja la textura horneada de Tripo.
2. `blender/arreglos.py` (numpy, `glbio.py`): extras del original con la geometría de Blender, más:
   - **Orientación restituida** donde `recalc_face_normals` volteó la pieza entera (sillín, carrocería y rin delantero quedaban invisibles).
   - **Faros (ojos LED), 5 piezas cada uno**: `vidrio.mica_faro_*` es una superficie cuadrática ajustada a los vértices de la
     mica de Tripo, así que conserva su curva. El contorno es polar: el máximo por sector, suavizado con esquinas vivas. Se suman
     `cromo.aro_faro_*` (bisel de 3,5 mm), `negro_brillo.carcasa_faro_*` (marco que tapa el borde serrado del carenado),
     `cromo.reflector_faro_*` (copa de 3 cm detrás) y `luz.faro_*` (emisor con la forma de la mica, metido 8 mm, que mira
     adelante, con `lampara: faro`). Se quitan los trozos de escudo y nariz que asomaban tras la mica.
   - **Stop** con marco negro brillante. **Direccionales traseras** cortadas con un plano: la mica ámbar atrás se enciende y la
     carcasa queda en negro brillante. **Delanteras** con aro cromado fino.
   - **Rin a la medida**: la pestaña del rin delantero estaba en 170 mm y el talón de la llanta en 192 mm (esa era la franja).
     Ahora los dos rines llegan a 185,5 mm (14"), estirados solo de la maza hacia afuera, y el talón de la llanta queda 4 mm
     dentro de la pestaña. El radio exterior de la llanta no se tocó.
   - **Acabados PBR** (`extras.acabado`): sillín de vinilo con sheen, plásticos mate, rines con clearcoat, puños y espejos.
3. `capturar.py`: captura en Chrome sin ventana (sesión de usuario@prueba.com, moto 59, fondo blanco).
   Uso: `capturar.py salida.png 59 luces vistas.json ancho alto`.

Para rehacerlo:
`blender -b --factory-startup --python geometria.py -- aerox155_tripo.glb blender.glb informe.json`
y luego `python arreglos.py aerox155_tripo.glb blender.glb aerox155_tripo2.glb`.

## Verificado en el visor (/garaje/59/)
- Capturas: `final_lateral.png`, `final_tres_cuartos.png`, `final_luces.png` (luces encendidas), `personalizar_rojo.png`
  (rojo en la pintura y dorado en los rines, sin derrames) y `antes_v6.png` (la versión anterior).
- Rayos X: los 15 internos siguen en el GLB y el visor arranca en Rayos X sin errores. Hay 7 lámparas: 2 faros, stop y 4 direccionales.

## Pendiente o limitado
- La carrocería conserva la forma de Tripo: las manchas negras y grises de la textura horneada siguen como zonas `plastico`,
  y bajo el sillín la forma sigue algo irregular.
- En la captura sin ventana el emisor del faro se ve gris claro, sin halo. Falta mirarlo encendido en el visor real con
  bloom y, si hace falta, agrandar el emisor o volverlo un anillo.
- La pata lateral genérica del visor sigue visible (trampa conocida del método).
