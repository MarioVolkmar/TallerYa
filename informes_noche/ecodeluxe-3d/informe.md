# Hero Eco Deluxe 100: 3D desde el modelo despiezado de Tripo

**Resultado**: `garaje/static/garaje/modelos/ecodeluxe100_tripo.glb` (**1,41 MB**, **103.266 triángulos**, 70 nodos:
51 de Tripo + 19 internos), conectado en `MODELOS_TRIPO` de `moto3d/glb.js` con la clave `eco[ _-]*deluxe` y `?v=2`
(único cambio en ese archivo). Probado en `/garaje/60/` (moto de prueba «Eco prueba 3D» de `usuario@prueba.com`):
carga sin errores del 3D a 1280 y 375 px, Personalizar pinta (probado con rojo vivo: sin derrames en ruedas, cables ni
guardabarros), Rayos X muestra los 19 internos y el modo moto los oculta, sin desborde horizontal en el celular.
Capturas: `final_lateral.png` y `final_tres_cuartos.png` (negro de fábrica, luces encendidas).

## Método y por qué

No usé el motor de `moto-3d-tripo`: está hecho para **una malla fundida** que hay que partir con campos por vértice y
color de textura. Este modelo ya llega en 79 partes cerradas y sin textura; partirlo otra vez sería trabajar contra él.
Hice un flujo propio y corto (scripts en `privado/tripo/ecodeluxe100/scripts/`, la skill queda intacta):

1. `stats.py` + `vistas.py`: caja de cada parte y un render de puntos con el número de cada parte en 4 vistas para
   identificarlas contra la foto. `islas.py`: cada parte resultó **una sola isla** (no hay restos sueltos que limpiar).
2. `armar.py`: cambio de ejes (Tripo: z adelante, −x escape → visor: x adelante, escape en −z; es una reflexión, así que
   se invierte el orden de los vértices), **escala uniforme 1,9515** por la distancia entre ejes de la ficha (1.235 mm).
   Con esa escala el largo da 1,95 m (ficha ≈ 1,965 m) y la llanta 0,61 m (2.75-18): no hizo falta tocar ningún eje.
   Agrupa partes por pieza real, parte las que son dos piezas y refleja los pares que Tripo dejó de un solo lado.
3. `simp.mjs` (meshoptimizer, borde bloqueado): baja cada pieza con su razón (llantas 12 %: el visor las tornea igual;
   luces 60 %; pintura 40 %; resto 30 %). 302 mil → 100 mil triángulos sin cambiar la silueta.
4. `escribir.py`: GLB cuantizado como el de las otras motos, **acabado por material** en `extras.acabado`, extras de
   ubicación medidos sobre la malla (ejes, placa, manubrio, baúl, pantalla del reloj) y los internos de Rayos X.

**Pintar por material**: cada nodo lleva el prefijo del material real (`pintura`, `negro_brillo`, `plastico`, `chasis`,
`metal`, `cromo`, `motor`, `carter`, `caucho`, `asiento`, luces), y donde el material compartido no basta, un
`acabado` PBR propio (aluminio pulido, pintura de escape, zamak, aletas mate). El color de la carrocería sale de la moto
del usuario (Personalizar); las luces son emisivas (`luz`, `stop`, `ambar`, `reflector`).

**Internos de Rayos X**: Tripo no trae internos. Usé los 19 de la Boxer CT 100 (motor de 100 cc del mismo tipo: cilindro,
pistón, cigüeñal, cárter con aceite, bujía, carburador, filtro, batería con bornes), trasladados al centro del motor de la
Eco (pistón, cigüeñal y bujía corridos 7 cm hacia la culata, que en la Eco va más acostada). La batería y el filtro caen
dentro de la caja bajo el sillín (parte 5).

## Parte → pieza → material

| Partes Tripo | Nodo | Pieza real | Material |
|---|---|---|---|
| 0 / 25 | `caucho.llanta_tras` / `_del` | llantas 2.75-18 (con `eje`, el visor las tornea) | caucho |
| 15+31 / 8 (radio > 9,8 cm) | `metal.aro_tras` / `_del` | aro | metal |
| 15+31 / 8 (radio medio) | `cromo.rayos_tras` / `_del` | rayos | cromo |
| 15+31 / 8 (radio < 4,2 cm) | `metal.tambor_tras` / `_del` | tambor de freno | aluminio fundido (acabado) |
| 6, 10 | `pintura.tanque` | tanque y su tapa lateral | pintura |
| 3 (cara frontal, círculo) | `luz.faro` | lente del faro | emisivo, `lampara: faro` |
| 3 (resto) | `pintura.farola` | carenado del faro (`visor_fijo`) | pintura |
| 4 | `pintura.guardabarros_del` | guardabarros delantero | pintura |
| 26 | `pintura.colin` | colín | pintura |
| 32 + su reflejo | `pintura.tapa_lateral_izq` / `_der` | tapas laterales (Tripo solo dejó la izquierda) | pintura |
| 7 / 9 | `negro_brillo.caja_der` / `_izq` | cajas bajo el tanque («Power Start») | negro brillante |
| 1 | `asiento.asiento` | sillín | vinilo |
| 22 | `stop.stop` | stop | emisivo rojo |
| 55, 57 | `ambar.direccional_del_a` / `_b` | direccionales delanteras | ámbar |
| 53 + su reflejo | `ambar.direccional_tras_a` / `_b` | direccionales traseras (Tripo dejó una) | ámbar |
| 76 + su reflejo | `reflector.reflector_del_a` / `_b` | reflectores de la horquilla | reflector |
| 27, 19 | `plastico.guardabarros_tras` | guardabarros trasero y portaplaca (placa medida aquí) | plástico mate |
| 43, 78 | `plastico.guardabarros_int` | guardabarros interior | plástico mate |
| 52, 54, 58, 64 | `plastico.cubre_horquilla` | cubiertas y soportes del faro | plástico mate |
| 41, 48 | `negro_brillo.reloj` | velocímetro (con pantalla redonda) | negro brillante |
| 20, 21 | `metal.horquilla` | barras de la horquilla | aluminio pulido (acabado) |
| 14, 30 | `oscuro.manubrio` | manubrio (`manubrio`, `sin`) | oscuro |
| 38, 56 | `caucho.punos` | puños y mandos | caucho |
| 61, 74 | `metal.palancas` | palanca y tuerca de dirección | metal |
| 18, 37 | `oscuro.espejos` | espejos | oscuro |
| 62 / 46, 67, 70 / 50 | `oscuro.chapa` / `.cables` / `.pito` | chapa, cables, pito | oscuro |
| 24, 44, 66, 73, 16, 33 | `chasis.chasis` | bastidor y defensa | acero pintado |
| 39, 49, 65, 36 | `chasis.basculante` | basculante | acero pintado |
| 35, 72, 68 / 12, 69, 63, 77 | `chasis.pata` / `.posapies` | pata lateral y central / posapiés | acero pintado |
| 29, 71, 75 | `metal.varilla_freno` | varilla y pedal de freno | metal |
| 13, 28, 59, 60 | `metal.amortiguadores` | amortiguadores | metal |
| 5 | `oscuro.caja_bateria` | caja de batería bajo el sillín | oscuro |
| 2 (atrás) / 2 (adelante) | `oscuro.guardacadena` / `motor.bloque` | guardacadena / cárter y caja | lámina pintada / motor |
| 42 | `motor.tapa_embrague` | tapa redonda derecha | aluminio pulido (acabado) |
| 34, 45 | `carter.tapa_magneto` | tapa izquierda y pedal de cambios | cárter |
| 47 | `oscuro.cilindro` | cilindro y culata | negro mate (acabado) |
| 40 | `metal.carburador_visto` | carburador y admisión | zamak (acabado) |
| 11, 23, 51, 17 | `oscuro.escape` | silenciador, punta, soporte y codo | pintura de escape (acabado) |

## Pendiente

- **Calcas de fábrica** (gráficos plateados del tanque y el carenado): no puse `calcas_fabrica`; la moto sale negra lisa
  más las calcas de la moto del usuario. Falta ubicarlas como en la Boxer.
- **Parrilla blanca** de la foto: no la encontré como pieza en Tripo (debe estar fundida en el colín 26); no se separó.
- Identificación por caja y vista, no por foto de cerca: dudosas 45 (cambios o pedal), 16 y 36 (travesaño o soporte),
  44 (tubo o cable), 40 (carburador con admisión). El material les queda bien igual.
- El lente del faro se cortó con un círculo sobre la cara frontal del carenado: encendido se ve como un disco blanco
  con borde algo irregular.
- No corrí `revisar.py` de la skill (pide su carpeta de trabajo `T` de una malla fundida); revisé con capturas del
  visor a 1280 y 375 px y con chequeos en la página.
- Moto de prueba creada: pk 60, «Eco prueba 3D» (copia de la Boxer del usuario de prueba). Borrarla cuando ya no haga falta.
- Sin commit.
