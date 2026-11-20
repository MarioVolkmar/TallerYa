---
name: moto-3d-tripo
description: Convierte un modelo 3D de moto generado con Tripo (un GLB de una sola malla, millones de triángulos y textura horneada) en el GLB liviano que usa el visor de TallerYa, con piezas separadas y con nombre, bordes lisos entre piezas, luces y discos limpios, placa en su sitio y piezas internas con forma real para Rayos X. Úsala cuando el usuario envíe un GLB de Tripo de una moto y pida «reconstruir», «adaptar» o «montar en la página» ese modelo, o pulir uno ya convertido.
---

# moto-3d-tripo

Toma el modelo de Tripo como base y lo deja como modelo realista de la línea (hechas: NMAX, NKD, Boxer CT 100, XTZ 150,
XTZ 125, MT-03; detalle y tiempos en `referencia/historial.md`).

Leer cuando haga falta (no de entrada):
- `referencia/trampas.md`: modelos sin textura, bordes limpios, luces y calcas, ajustes de la NKD, errores ya vistos.
  **Leerla antes de escribir una ficha nueva.**
- `referencia/visor.md`: contrato con `moto3d/glb.js` (lados, llantas torneadas, extras por nodo), verificar en la página
  y capturar con el panel oculto.

## Idea central

El modelo llega como **una sola malla fundida**. No se clasifica triángulo por triángulo (queda dentado): cada pieza es un
**campo por vértice** (positivo = adentro) y las caras que el borde atraviesa **se parten por donde el campo vale cero**.
Campos: regiones analíticas (radios a los ejes de rueda, planos, `banda(v, a, b)`), plantillas (polígonos en una vista:
luces) y color suavizado de la textura. Se combinan con Y / O / NO y se aplican **en orden de prioridad**.
**El motor (`motor.py`) no sabe nada de ninguna moto**; todo lo propio de una moto va en su ficha.

## Pasos (todos con `venv/Scripts/python.exe -I`, carpeta de trabajo `T` en el scratchpad, `S` = `scripts/`)

1. **Inspeccionar** la cabecera del GLB (copiado a una carpeta propia: es un archivo descargado): triángulos y textura.
   Pesado con textura (NMAX) → simplificar (paso 3) y reglas de forma + color. Liviano sin textura (las demás) → no
   simplificar (copiar `w_*.bin` a `s_*.bin`, sin `RAZON`) y solo forma.
2. `extraer.py entrada.glb T` y `preparar.py T <entre ejes en m> [giro]` (giro 90/270 si Tripo la dio a lo largo de z).
   `medir.py S T` ajusta ejes y cajas.
3. Solo si es pesado: `node simplificar.mjs T 160000` (carpeta con `npm install meshoptimizer`).
4. **Qué va pintado, con al menos 3 fotos reales** (fabricante, concesionario, Galgo): tabla pieza por pieza. Solo lo que
   sale del color de la moto en todas las fotos va en `pintura.*`; lo demás en `plastico.*`, `chasis.*` o `metal.*`.
   `pintura2` es el segundo tono: nunca para piezas negras.
5. **Ficha**: copiar `fichas/nkd125.py` (o la más parecida) a `fichas/<moto>.py`: `cortar(m)`, `internos(k)` y opcionales
   `RAZON`, `MEZCLA`, `ISLAS`, `ALISAR`, `SUAVE`, `ESCALAR`, `NIVELAR`, `SITIOS`, `CONSERVAR`, `SOBRANTES`.
6. **Una vuelta = un comando**: `ciclo.py S T S/fichas/<moto>.py T/salida.glb [--ver "der;640;None+atras;1100;(caja)"]
   [--solo stop,faro] [--hasta cortar]`. Lo lento queda en `T/cache`: cambiar una regla no recalcula las demás.
7. **Revisión automática**: `revisar.py S T/salida.glb --nombre "<moto>" --fotos "glob1;glob2" --ficha S/fichas/<moto>.py
   --hoja T/revision.jpg` (~12 s). Ver «Lista final obligatoria».
8. Copiar a `garaje/static/garaje/modelos/`, registrar en `MODELOS_TRIPO` de `moto3d/glb.js` (expresión regular contra
   la línea, sin chocar con otra) y **subir `?v=`**. Verificar en la página (`referencia/visor.md`).

## Reglas

- **Lados**: las fichas trabajan con +z = escape (derecha del piloto); `exportar.py` espeja y el visor vuelve a espejar
  (`raiz.scale.z = -1`). No espejar nada más por cuenta propia.
- **Mirar los dos lados con la foto antes de quitar o agregar algo**: Tripo hace la moto simétrica (copias falsas a
  `_quitar`) y a veces deja una pieza par de un solo lado.
- **Pieza par que falta de un lado** (direccional, espejo, reposapiés): cortar la que existe y `m.espejar(origen, nuevo)`
  (copia reflejada en z = 0). Si el usuario dice que una pieza está en su sitio, **no moverla**: achicarla centrada ahí.
- **Sobrantes**: al cortar, `motor.sobrantes()` quita solo las islas sueltas chicas (< 8 cm, < 400 caras, a > 1,5 cm de
  todo) y los pedazos de piezas de un solo lado que caen del lado contrario (escape a +z; corona, cadena, CVT a -z); nunca
  luces, direccionales, tornillos, placa ni espejos. Lo quitado queda en `T/quitados.json` y sale en la hoja de
  `revisar.py`; para conservar algo: `CONSERVAR = [regex]` en la ficha (`SOBRANTES = False` lo apaga).
- **Pieza pegada a otra** (guardabarros sobre la llanta): `m.desplazar(nombre, fn)` mueve solo esa pieza tras repartir.
- **Luces**: un nodo por lente y por lado con `lampara: {tipo}`; la plantilla se dibuja en la vista hacia donde mira el
  lente; el borde lo define solo la plantilla (nada de normales en la misma regla); la normal no debe mirar al piso.
- **Probar siempre un color vivo de pintura** y mirar ruedas, cables y guardabarros: en una moto negra no se ven derrames.
- **Mirar cuesta más que la vuelta**: pedir todas las vistas de una ronda en un solo `--ver` y en la página una hoja de
  varias vistas por captura (`scale: 0.5`).
- Una ronda con límite de tiempo: entregar lo que haya al llegar.

## Lista final obligatoria (antes de decir «listo»)

1. `revisar.py` sin ERROR (o cada ERROR explicado al usuario) y con `--fotos` de al menos 3 fotos reales. Secciones:
   lado (escape a la derecha, corona a la izquierda), cortes (bordes abiertos a la vista, flotantes, copias simétricas),
   ruedas (eje, aro/rin/disco cubren la vuelta, pintura dentro de la llanta), luces (tamaño, sitio, hacia dónde mira,
   dónde cae la luz, carcasa), **sitio y pares** (cada pieza en su zona según ejes y manubrio, `SITIOS` en la ficha para
   lo aprobado con fotos; pares completos, con la sugerencia `m.espejar`) y pintura (qué cambia con Personalizar).
2. **Entregar la hoja** de `revisar.py` al usuario (SendUserFile) junto con 1 o 2 capturas de la página con las luces
   encendidas (frente y 3/4). Sin hoja no se entrega.
3. En la página: `?v=` nuevo cargado (`v._moto.raiz.userData.glb`), sin errores de consola, solo pata y placa como mallas
   genéricas visibles, placa legible, Personalizar con un color vivo.
4. Pruebas del garaje sin lentas (`manage.py test garaje --exclude-tag=lenta -v 1`) si cambió `glb.js` o `moto3d.js`.
5. Respaldo: copiar los scripts y fichas cambiados y este SKILL.md a `~/.claude/skills_respaldo/tallerya/moto-3d-tripo/`.
