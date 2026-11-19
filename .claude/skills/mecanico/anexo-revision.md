# Anexo: revisión técnica (para usar como revisora)

**Meta:** ≤ 5 min y ≤ 15 k tokens por archivo o lámina. Leer solo lo necesario: con Python, las claves de texto (fichas, pasos, fallas, tips), nunca el JSON entero; el manual, solo por `garaje/intervalos/<slug>.json` o `buscar_manual.py` (una línea por hallazgo).

## Lista (en este orden; parar en lo grave)
1. **Seguridad** — ¿algún paso con frenos, dirección, llantas, gasolina, batería, escape caliente o soporte de la moto sin su aviso? ¿Algo grave que no manda al taller? ¿Urgencia `seguir` en algo de frenos o dirección?
2. **Nada inventado** — cada torque, holgura, capacidad, presión, medida de bujía o intervalo tiene fuente (manual o catálogo) o dice «aprox.» / «sin dato». Ninguna falla «del modelo» sin una URL que se la atribuya a ese modelo.
3. **Pieza correcta** — regla de la primera palabra; la tarea va en lo que se cambia (empaque, no tapón; o-ring de la tapa del filtro, no la tapa); la pieza existe en el catálogo de esa versión; el conjunto tiene sentido mecánico (engranajes que engranan, retén donde sale un eje, sin «primera» en una scooter).
4. **Unidades y formato** — km, N·m (kgf·m solo entre paréntesis si el manual lo da), mm, L o ml, psi con kPa, °C; miles con punto («6.000 km»), decimales con coma («0,8 mm»); rango con raya corta («0,7–0,8 mm»).
5. **Nombres y lenguaje** — español de Colombia (`anexo-terminologia.md`); un solo nombre por pieza en todo el archivo y el mismo que usa `garaje/despiece_glosario.py`; segunda persona; síntomas de moto; sin «defecto de fábrica».
6. **Coherencia** — el intervalo citado coincide con `garaje/intervalos/<slug>.json`; los enlaces `tareas`, `pieza` y `diagnostico` existen (`TareaMantenimiento.clave`, `TareaMantenimiento.Pieza`, `diagnostico.py`); variante correcta (tambor o disco, carburador o inyección).

## Salida (corta, para pegar en el informe de la otra skill)
```
Revisión mecánica — <archivo o lámina> — <n> hallazgos (G graves · A ajustes)
G1 [seguridad] ficha 12 «Purga del freno»: falta «bombea la manigueta antes de rodar». → agregar al final del paso 4.
A1 [nombre] ref. 14 «Visor de aceite» → «Tapón con varilla» (catálogo: PLUG, OIL LEVEL); la tarea va en su o-ring (ref. 15).
A2 [fuente] falla «correa-se-come»: sin URL del modelo → alcance "tipo".
Bien: …(una línea)
```
- **G (grave)**: seguridad, dato inventado, pieza o tarea equivocada → se corrige siempre, antes de entregar.
- **A (ajuste)**: nombre, unidad, estilo, cita incompleta → se propone; lo aplica quien hizo el contenido si cabe en su tiempo.
- Máximo 10 hallazgos: si hay más, los 10 más importantes y «+N del mismo tipo».
- No reescribas el contenido: di qué cambiar y dónde.
