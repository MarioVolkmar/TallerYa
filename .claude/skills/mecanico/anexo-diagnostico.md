# Anexo: árboles de diagnóstico

Fuente de verdad: `garaje/diagnostico.py` (solo datos). `garaje/vista_diagnostico.py` lo pinta en `/diagnostico/` y `garaje/fallas.py` enlaza cada falla frecuente a una rama con `"diagnostico": {"s": "<síntoma>", "<pregunta>": "<valor>"}`. **No inventes claves:** antes de enlazar, `Grep` de la clave en `diagnostico.py`.

## Forma de una rama
```
síntoma (lo que la persona nota, en sus palabras)
 └ 1-3 preguntas que la persona puede contestar sin herramienta («¿de dónde viene?», «¿cuándo?», «¿cómo suena?»)
    └ resultado = causa más probable para esas respuestas
         · prueba simple que puede hacer ella misma («revisa»)
         · explicación de 1-2 frases: por qué pasa y qué se daña si se deja
         · urgencia: seguir | pronto | parar
         · piezas candidatas (patrones del nombre visible en el despiece) y sistema
```
En `diagnostico.py`:
- `SINTOMAS[clave]`: `nombre`, `icono`, `preguntas` (`clave`, `texto`, `opciones` = `(valor, texto, condición)`, `si` = solo se muestra con ciertas respuestas) y `reglas` = lista `(condición, resultado)`; **gana la primera que se cumple**, así que lo específico va antes que lo general.
- Condiciones de moto: `{"t": "cvt"}` / `{"t": "cadena"}` (transmisión) y la refrigeración (`"r"`), las únicas diferencias entre motos.
- `RESULTADOS[clave]`: `sistema` (mismos nombres que `despiece_sistemas.SISTEMAS`), `subgrupo`, `urgencia`, `causa`, `explicacion`, `revisa`, `piezas` (regex sobre el nombre en español), `excluir`, `otros_sistemas`, `servicio`.

## Criterio para ordenar causas
1. **Lo más probable en una moto de Medellín** (uso diario, lluvia, lomas): primero lo que se gasta (aceite, bujía, kit de arrastre, bandas, correa) y después lo que se daña (biela, embrague, estator).
2. **Lo más barato y fácil de comprobar** antes que lo caro: gasolina, fusible, borne de batería, nivel de aceite, holgura de la guaya, presión de llantas.
3. **Lo peligroso se marca aunque sea menos probable**: freno, dirección, llanta, fuga de gasolina → `parar`.
4. Si dos causas dan el mismo síntoma, una pregunta más que las separe (cuándo, cómo suena, qué color de humo); si no hay pregunta posible sin herramienta, el resultado dice las dos y manda al taller.

## Urgencia
| valor | cuándo | texto en la página |
|---|---|---|
| `seguir` | molestia sin riesgo ni daño que crezca rápido | «Puedes seguir rodando» |
| `pronto` | el daño crece si se deja; esta semana al taller | «Revísalo pronto» |
| `parar` | riesgo para la persona o para el motor | «No la ruedes» (grúa o mecánico a domicilio) |

## Prueba simple («revisa»)
Una sola acción, sin desarmar ni herramienta especial, segura con la moto quieta: mirar el nivel en la mirilla o la varilla, mirar si gotea y de dónde, mover la rueda de lado a lado, medir la holgura de la cadena con la mano, probar la luz de freno, oler el escape. Nunca «prueba a ver si frena» rodando.

## Rama nueva: lista de control
- [ ] La pregunta se contesta sin herramienta y sin saber de mecánica.
- [ ] La condición de transmisión o refrigeración está donde cambia la causa (no hay «correa» en una moto de cadena).
- [ ] La regla específica va antes que la general.
- [ ] `piezas` encuentra algo en al menos dos despieces (probar con `piezas_candidatas`) y `excluir` quita tapas y tornillería.
- [ ] Urgencia según la tabla; lo de frenos, dirección, llantas y gasolina nunca es `seguir`.
- [ ] La explicación no promete un costo ni un arreglo sin ver la moto.
- [ ] Si cambias `diagnostico.py`: `venv/Scripts/python.exe manage.py test garaje.tests_diagnostico garaje.tests_fallas -v 1` y, si una falla frecuente apunta a la rama, que la clave siga existiendo.
