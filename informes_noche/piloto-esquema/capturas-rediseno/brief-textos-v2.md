# Brief: textos v2 de una lámina del esquema (subagente sonnet)

Proyecto TallerYa (Django, todo en español de Colombia, motos en Medellín). Raíz: `C:/Users/volkm/OneDrive/Desktop/TallerYa`. `M` = `informes_noche/piloto-esquema/motor`.
Tu tarea: reescribir al **estilo v2** los textos de una lámina que ya existe (v1) y dejarlos en un JSON nuevo. No toques ningún otro archivo. No hagas commit. No leas PDF.

## Qué leer (solo esto)
1. La v1: `M/datos/<lamina>.json` (con Python: `fichas`, `pasos[].t`, `cadenas`, `cuando`, `textoArmado`). Es la fuente del contenido: no inventes datos nuevos; reordena, acorta y aclara.
2. El modelo de estilo ya aprobado: `informes_noche/piloto-esquema/capturas-rediseno/armar26v2.py`, líneas 33-200 (funciones por concepto) y 291-312 (pasos). Imita ese tono.

## Estilo v2
- Segunda persona (tú), frases cortas, acciones concretas: «Revísala si…», «Cámbiala cuando…». Síntomas de moto (lo que sientes, ves u oyes), no de carro.
- **Sin «(N)» ni números de catálogo en la prosa, ni nombres de catálogo en inglés.** Para nombrar otra pieza de la lámina usa un enlace `[[clave|texto]]`, donde clave es la clave de su ficha (p. ej. `[[9|pastillas]]`, `[[liquido|líquido]]`). Solo claves que existan en `fichas`. Uno o dos enlaces por campo como mucho; no enlaces la pieza a sí misma.
- **Se acorta la explicación, NUNCA la seguridad.** Copia (con tus palabras, pero completos) todos los avisos de seguridad, pasos de cierre y marcas que haya en la v1: piezas o líquido nuevo, purgar (con ABS, en el taller), probar el freno con la moto quieta antes de rodar, tapar la pintura, vaciar/jeringa, manubrio recto, marcas de posición, orden y torque de apriete «del manual de servicio», compresor de resorte, llave de sujeción, frío del motor, etc. Si dudas, déjalo.
- Cifras sin fuente: «aprox.». Torques y medidas sin fuente: «manual de servicio».

## Salida: `informes_noche/piloto-esquema/capturas-rediseno/v2-textos-<lamina>.json` (UTF-8)
```
{
 "fichas": { "<clave>": {
     "nombre": "solo si el de la v1 es confuso o largo; si no, omítelo",
     "que": "1 frase: qué es y dónde va",
     "sirve": "1-2 frases",
     "sintomas": ["2-4 señales"],
     "fallas": [["desgaste|calor|humedad|maluso|golpe|edad", "1-2 frases"]],
     "decision": "repara|reutiliza|cambia",
     "porque": "1-2 frases que digan lo mismo que decision",
     "dif": "facil|taller",
     "cuando": "1-2 frases con km/años de la v1 si los hay",
     "arrastra": ["Causa corta → efecto en [[clave|pieza]]"],
     "certezaDe": {"que":"ok|ap","sirve":"ok|ap","sintomas":"ok|ap","fallas":"ok|ap","porque":"ok|ap","cuando":"ok|ap"}
 }},
 "pasos": {"0": "texto del paso 0 sin «Paso N de M» ni números", "1": "..."},
 "textoArmado": "...",
 "cadenas": [{"t":"título","p":[["clave","eslabón"],...]}],
 "cuando": [{"i":0,"que":"...","cuando":"..."}]
}
```
- Todas las fichas de la v1, también las de contexto (`ctx:true`), salvo `cat`, `codigo`, `conecta`, `certeza`, `forma3d` y `efectos`, que se conservan de la v1 (no los escribas).
- `certezaDe`: según la lista `certeza` de esa ficha en la v1. «ok» solo si el dato sale del catálogo o del manual; práctica de taller y proporciones = «ap». Omite los campos vacíos.
- `pasos`: mismas claves que los índices de `pasos` de la v1, mismo orden y contenido. Empieza con un título corto en `<b>…</b>` (p. ej. `<b>Pastillas.</b> Sácalas…`), sin números de pieza.
- `cadenas` y `cuando`: mismo número y orden que la v1; en `cuando` reescribe solo `que` y `cuando` (la `fuente` se conserva).
- Al final, verifica con Python que el JSON carga, que no queda ningún «(» seguido de dígitos en la prosa y que cada `[[clave|` existe en `fichas`. Responde en 3 líneas: archivo, nº de fichas y pasos, y cualquier duda mecánica que encontraste en la v1.
