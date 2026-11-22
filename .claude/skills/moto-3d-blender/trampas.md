# moto-3d-blender: trampas

- **Ejes**: Tripo trae z adelante, y arriba, −x del lado del escape; el visor quiere x adelante y escape en −z. Es una reflexión: se invierte el orden de los índices. El visor pone `raiz.scale.z = -1`, así que en pantalla queda bien; en Blender (sin ese reflejo) los renders se voltean al componer el resumen.
- **Escala** uniforme por la distancia entre ejes de la ficha (centros de las cajas de las llantas). Los ejes salen de un círculo ajustado a la banda de rodadura.
- **Faro**: la parte de Tripo es la lámpara (sin piezas propias). Con `cara` la lente es lo que mira hacia afuera; lo demás, `negro_brillo.carcasa_*`. Sin `recorte` la mica sale blanca plana; con `recorte`, tira + reflector. El cono sale de los reflectores (la tira lleva `cono: false`).
- **Bordes serrados** entre farola y carenado: superficies de Tripo que se cruzan; los arregla `recorte` del faro (el usuario lo cuenta como «error puntual»). Quedan astillas finas de Tripo en el borde del carenado.
- Llanta de Tripo algo achatada abajo: al girar baja hasta ~2 cm. Medir con `Box3.setFromObject(o, true)` (sin `true` la caja girada crece y parece que cabecea).
- Panel del navegador en el puerto 8031/8001: el service worker muestra «Sin conexión»; borrar registros y cachés y recargar. `/garaje/<pk>/vista-3d/` no tiene botones: Personalizar, Rayos X y Encender están en `/garaje/<pk>/`.
- `capturar.py` necesita `venv/Scripts/python.exe` (importa Django para la cookie).
- Recorte del faro: si el borde sigue serrado, la parte que tapa la mica no está en `contra` (en la Aerox era la zona azul de las mismas partes 48 y 56, y las partes 2 y 5). Diagnóstico: contar centros de triángulos de cada parte debajo de la recta, dentro de la huella de la mica y delante de ella.
- `glbio.atributo` respeta `byteStride` (los GLB que salen de gltf-transform lo traen).
- El panel del navegador puede negar localhost: verificar con `capturar.py` (Chrome sin ventana); para una moto de otro usuario, copiar el script con su correo.
- **Simplificar**: con un solo error para todo, el rin trasero se metía 7 mm en la llanta; por eso las ruedas van con `error_ruedas` más fino. La revisión acepta hasta −12 mm, pero mirar que quede ≥ −3 mm.
- **Placa**: la medida 23,5 × 13,5 cm es la habitual de moto en Colombia; no se encontró la ficha técnica oficial en línea (la Resolución 5228 de 2016 es de centros de reconocimiento de conductores).
- **Consola de Windows (cp1252)**: no imprimir «≤», «→» ni similares en los mensajes de `revisar.py`: rompe la salida.
- **Farolas «ojos de mapache»** (Aerox, ronda 3): la carcasa por `cara` y el sobrante del recorte iban a `negro_brillo` y hacían un antifaz; el borde de abajo quedaba serrado por el carenado. Arreglo: `recorte.contorno` de la foto. Probado y descartado: pasar a mica también lo que tapa (sin quitarlo): apagada salen vetas de la tira sobre el reflector.
- **Normales de Tripo ruidosas**: elegir triángulos por normal da manchas; suavizar el valor sobre la malla (`suavizar`, 20 pasadas) y cortar por la isolínea.
- **Placa atravesada**: el soporte trae pestañas que salen más que su cara media; la placa va por delante del punto más saliente + 4 mm.
- **Puntitos oscuros en la mica encendida** (Aerox, ronda 4): no son triángulos del carenado delante (`tapan.py` no los muestra). Ya se probó: voltear los triángulos de Tripo al revés (se quedó), simplificar con bordes fijos (se quedó) y meter el reflector 3 mm bajo la tira (empeoró: se quitó). La causa sigue sin aislar; puede ser material translúcido o doble capa de la mica. Mirar `pintarVivo` en moto3d.js.

## Rueda que cabecea al girar (Aerox, 21-nov-2026)
- Un pedazo de guardabarros venía dentro de la llanta delantera de Tripo: el ajuste del eje (15 % de puntos más lejanos) se corrió 9 mm hacia arriba, el rin cortado por cilindro quedaba «redondo» alrededor del eje malo (el chequeo del rin no lo veía) y el pedazo giraba con la rueda. Arreglo: eje por ajuste robusto del borde por sectores, restos fuera del radio a un nodo fijo, chequeo de redondez de la llanta alrededor del pivote.
- `capturar.py`: con luces de noche la caja de la moto incluía halos y conos y la cámara se corría; ahora en modelo completo la caja sale solo de las mallas del GLB.
