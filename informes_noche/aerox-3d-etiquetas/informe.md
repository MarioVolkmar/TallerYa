# Aerox 155: 3D con las etiquetas del usuario (21-nov-2026, sin commit)

**Resultado**: `garaje/static/garaje/modelos/aerox155_tripo4.glb` (3,07 MB, 238 mil triángulos, 66 nodos, `extras.modelo_completo`), conectado en `MODELOS_TRIPO` (`aerox155_tripo4.glb?v=1`). Los GLB anteriores siguen ahí. Se armó con la skill nueva **moto-3d-blender** en un comando de unos 35 s.

Revisión: `resumen.png` (6 vistas junto a las fotos), `final_lateral.png`, `final_tres_cuartos.png` y `final_luces.png` (de noche y encendida).

## Qué se hizo
- La geometría de Tripo no cambió: solo se giró y escaló parejo (distancia entre ejes de 1,35 m), se repartió por etiquetas y se partió por zonas. La llanta delantera se separó del rin por radio, cortando triángulos sin mover vértices. No se agregaron piezas propias: el faro es la farola de Tripo.
- Materiales según el texto de cada parte y zona (`fichas/aerox155.armado.json`):
  - un material por acabado;
  - `pintura` solo en carenado, tapas laterales, guardabarros delantero y el plástico que dice «color principal»;
  - plástico mate en negro y brillante en negro de piano;
  - translúcido solo el visor.
- Luces:
  - 2 faros (`luz`): lente que mira adelante y carcasa negra;
  - stop (zona roja de la parte 15);
  - 4 direccionales: delanteras en la parte 73 y la zona 1 de la parte 2, traseras en las zonas de mica de las partes 59 y 61.
- Ruedas: llanta, rin y disco con `extras.rueda` y pivote en el eje ajustado. En el visor los dos pivotes están en su eje y llanta, rin y disco giran juntos.
- Placa sobre el soporte de la parte 65. Los internos de Rayos X vienen de `aerox155_tripo3.glb` (mismas coordenadas).
- Etiquetas ambiguas, resueltas en la ficha (`forzar`):
  - **parte 12, sin texto**: por posición es el espejo izquierdo, simétrico de la 6 (negro mate con espejo cromado);
  - levas 53 y 68, y caliper 18: la página las había deducido como disco;
  - mofle y soportes 19, 34 y 50: «negro» pasa a metal oscuro;
  - guaya 51: negra;
  - carcasas de las direccionales traseras 59 y 61: negras.

## Verificado
- `revisar.py` OK: sin flotantes ni transparencias fuera del visor, tonos parejos, rin centrado (hueco talón–pestaña de −2 a 0 mm), placa y luces con emisivo. `gltf-transform validate` sin errores.
- Visor en `/garaje/59/` (puertos 8031 y 8001):
  - modo completo y 66 nodos del GLB;
  - Rayos X muestra los internos y Moto los oculta;
  - Encender sube el faro a 2,6 y el stop a 1,5; de noche se ven el haz y las direccionales;
  - Personalizar en rojo pinta solo los 4 nodos `pintura.*`;
  - 375 px sin desborde.

## Pendiente / a juicio del usuario
- **Bordes serrados del faro**: son el borde de las superficies de Tripo que se cruzan con el carenado. Solo se arreglan tocando geometría, así que se dejaron. Si el usuario los señala, cuentan como «error puntual».
- **Haz del faro**: sale unos 40° hacia afuera, porque los faros de la Aerox van en V.
- **Peso**: 3,07 MB contra 1,49 MB de la tripo3, porque no se simplificó para no tocar la geometría. Si el usuario lo permite, se puede bajar con `gltf-transform simplify`.
- **Llanta delantera**: al girar baja hasta 18 mm en un punto, porque Tripo la dejó un poco achatada.

# Ronda de arreglos (21-nov-2026, sin commit) — `aerox155_tripo4.glb?v=4`

**Resultado**: 1,42 MB (antes 3,22), 104 mil triángulos, 71 nodos. `revisar.py` OK, `gltf-transform validate` sin errores. Capturas: `arreglo_lateral.png`, `arreglo_tres_cuartos.png`, `arreglo_luces.png` (de noche, encendida), `arreglo_luces_atras.png` y `arreglo_farola.png` (de cerca, de día y encendida). Resumen: `resumen.png`.

1. **Bordes**: la zona de cada vértice se suaviza (Laplaciano) y los triángulos se parten por la isolínea 0,5, sin mover vértices. Queda fijo en `armar.py` para todas las motos.
2. **Farolas**: el borde de arriba de cada mica es ahora una recta en V invertida, como en la foto. Se ajusta al borde visible y se parten por ella la mica y lo que la tapaba: carenado 4, 16, 2 y 5 y la zona azul de las mismas partes 48 y 56. La mica se divide en **tira LED** (2 cm arriba, `luz`) y **reflector cromado** debajo (`luz_reflector`, que también enciende). Quedan unas astillas finas en el borde azul de Tripo; se pueden limpiar si el usuario las señala.
3. **Luces** (solo en modo completo, `moto3d.js`/`glb.js`; las motos viejas no cambian):
   - apagada, la mica se ve clara, no blanca plana;
   - encendida, la tira y el reflector brillan fuerte;
   - el haz va casi al frente (antes salía 40° de lado) y hay halo en las 4 micas del faro;
   - el stop es más intenso y proyecta luz roja atrás (1,9 m);
   - las direccionales parpadean más fuerte en el saludo de Encender. El visor solo tiene ese parpadeo, no intermitentes continuas.
4. **Placa colombiana**: 23,5 × 13,5 cm sobre el portaplacas (parte 65). La 46 queda más arriba y adelante, así que la 65 sigue siendo la buena. Esa medida no se pudo confirmar en la norma en línea: la Resolución 5228 de 2016 trata de los centros de reconocimiento de conductores. Es la medida habitual; queda como `PLACA_CO` en la skill.
5. **Gato lateral**: metal negro (`chasis`); `deduccion_3d.py` ya reconoce «gato», «gato lateral», «soporte lateral» y «pata».
6. **Peso**: gltf-transform weld + simplify (ratio 0,25, error 0,0015; ruedas con 0,0007) y reescritura cuantizada con los mismos extras. La silueta del resumen no cambia. El hueco talón–pestaña del rin trasero queda en −3 mm (Tripo trae −2).

Verificado con Chrome sin ventana: Aerox en 1280 y 375 px con luces; Eco Deluxe (/garaje/60/) y NMAX (pk 3) siguen bien de noche y encendidas. El Browser pane negó localhost, así que no se probó Personalizar ni Rayos X a mano en esta ronda; los nombres `pintura.*` no cambiaron.
