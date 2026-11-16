# Relevo — Planos / esquema del despiece

## Hecho (sin commit)
- Dibujos propios en `garaje/diagramas.py`: formas rehechas según cada pieza real (tapón de varilla con empaque, bujía, abrazaderas, cadena). Piezas nuevas: bomba de agua, cable CBS, neumático, radios, dirección con dos juegos de rodamientos, capuchón.
- Ubicación de cada pieza: la primera palabra del nombre manda (`_TIPO_INICIO`, `herraje_para`). Reglas Yamaha Colombia (`_YAMAHA_CO`) y de ruedas (`_RUEDAS`), más `OPCIONALES` y `PUESTOS_FIJOS`.
- Importador `importar_despiece`:
  - `tarea_al_sello`: la tarea se marca en el empaque o retén, no en el tapón.
  - Reglas globales, más las claves `descripciones`, `variante` y `especificaciones` en los mapas.
- Nombres en `despiece_variantes.py`: frases Yamaha CO, nombres por sistema, nombres de sellos y empaques con su dueño.
- Guías nuevas en `despiece_guia_mecanica.py`. En `views.guia_de`:
  - intervalo del plan de cada moto, con `intervalo_para(..., anio=)`;
  - cuidado del filtro de aire por línea (`_FILTRO_AIRE_POR_LINEA`).
- Piezas de tarea que no salen en los planos: aparecen con la pastilla "No aparece en los planos" (`fuera_planos`).
- Pieza inicial de cada lámina: vencida, luego pronto, luego desconocida.
- Carga diferida del despiece (`despiece_json`), con esqueleto y botón de reintentar.
- Aerox 155: migración 0022 y mapa `yamaha_aerox155_bvt2.json` (24 láminas).
- Gixxer en dos versiones (Carburador y FI ABS): `Despiece.variante` (0024), `especificaciones` (0025) y `Despiece.para` según el año.
- Comando `auditar_tareas_despiece`: 0 sistemas abren la pieza equivocada.
- Amortiguador trasero: se deja en 20.000 km, como pidió el usuario.

## Pendiente
- Volver a correr `manage.py test garaje -v 1` después del último cambio de `anio` (las pruebas focalizadas ya pasan).
- Dos tareas sin pieza en el plano: batería de la Boxer y barras de la Dynamic. Se aceptan así por ahora.
- Commit solo cuando el usuario lo pida.

## Archivos clave
- `garaje/diagramas.py`, `garaje/despiece_variantes.py`, `garaje/despiece_guia_mecanica.py`
- `garaje/views.py` (`datos_despiece`, `guia_de`, `PIEZAS_DE_TAREA`), `garaje/static/garaje/js/despiece.js`
- `garaje/management/commands/importar_despiece.py`, `auditar_tareas_despiece.py`
- `garaje/despiece_mapas/*.json`, `garaje/tests.py` (clases PuestosFijos, PiezaPorPrimeraPalabra, LoteCriterios, PiezaInicial, DespiecePorAnio)
