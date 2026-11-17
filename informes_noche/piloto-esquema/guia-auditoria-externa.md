# Guía de auditoría externa (cada 5 láminas)

Para una **sesión nueva e independiente**, sin el historial de quien creó las láminas. Tiempo: ~20 min. Los PDF solo se leen.

**Entrada:** `informes_noche/piloto-esquema/auditoria-pendiente.md`, con las 5 láminas desde la última auditoría y sus notas de creación, de la revisión integrada y de la medición.

## Qué haces
1. **Sortea 2 de las 5** (p. ej. `python -c "import random;print(random.sample([...],2))"`) y revísalas a fondo, la parte mecánica y la de UX:
   - mecánica: contra el catálogo y el manual de la moto (`manual_despiece/<moto>/`, buscando texto con pymupdf; sin páginas en imagen salvo que sea imprescindible);
   - UX: con `guia-revision-rapida.md` y la CVT (`motor/cvt.html`, fig. 12) como referencia de calidad;
   - para cada una usa `motor/revision/<lamina>.md` y la página `motor/<pagina>.html`, con una sola captura por lámina.
2. **Compara tus notas con las de la revisión integrada** (las de `auditoria-pendiente.md`): si alguna difiere en **más de 0,3**, la revisión integrada está siendo blanda; propón el cambio concreto a `guia-revision-rapida.md` o a los prompts de las revisoras.
3. **Tendencia:** mira las notas y los tiempos de las últimas láminas en `metricas.py informe <lamina>`. ¿Bajan las notas? ¿Se repiten los mismos hallazgos?
4. **Registra la auditoría:** `venv/Scripts/python.exe informes_noche/piloto-esquema/motor/metricas.py auditoria <la más nueva de las 5> <sigue|ajustar|parar>`. Borra `auditoria-pendiente.md` y el contador vuelve a cero.

## Qué entregas
Una página, `informes_noche/piloto-esquema/auditoria-<fecha>.md`:
- **Veredicto:** `sigue` / `ajustar` / `parar`, en la primera línea, con una frase de por qué;
- tus notas frente a las de la revisión integrada, para las 2 láminas;
- tendencia (3 líneas);
- cambios propuestos (máximo 5), sin aplicarlos.

Al usuario solo le llega el veredicto. Si es `parar`, él revisa una muestra antes de seguir.
