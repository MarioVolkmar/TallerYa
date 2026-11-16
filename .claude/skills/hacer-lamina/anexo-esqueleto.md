# Brief del subagente para extraer el catálogo (solo si falta `M/catalogo/<moto>.json`; en serie)

El esqueleto de la lámina lo arma `M/esqueleto_v2.py` en segundos y no lleva subagente. Este brief es solo para la primera lámina de una moto nueva, cuando todavía no hay catálogo extraído. Se pasa con `Agent` (`model: "sonnet"`) y se espera el resultado: no se dibuja en paralelo.
**Catálogo que no es Yamaha** (Auteco/Bajaj o genérico en español; el comando de abajo da «0 figuras»): sin subagente, `… extraer_catalogo.py <pdf> M/catalogo/<moto>.json --figura <N> --columna <versión>` saca solo esa figura en segundos (sin `--columna`, lista las versiones; los «… Completo» van a `conjuntos`, fuera de `partes`).

---
Tarea mecánica en el repo TallerYa (Django, todo en español). Python: `venv/Scripts/python.exe` con `PYTHONIOENCODING=utf-8`. No hagas commit.
Extrae el catálogo de partes de <moto> con:
`venv/Scripts/python.exe informes_noche/piloto-esquema/motor/catalogo/extraer_catalogo.py <pdf> informes_noche/piloto-esquema/motor/catalogo/<moto>.json`
El PDF solo se lee: nunca se edita, mueve ni borra, y no sale del equipo. Si el layout de las tablas sale raro, mira **una** página con `Read` y `pages`, nunca el PDF entero.
Comprueba con Python que la figura <N> tiene refs, descripciones, cantidades y códigos, y responde en 4 líneas: archivo, nº de figuras y filas, cómo quedó la figura <N> y cualquier fila dudosa.
---
