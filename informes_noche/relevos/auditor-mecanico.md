# Relevo — Auditor mecánico (2026-11-15)

## Qué hice
- Audité la exactitud mecánica en 4 áreas y mandé las correcciones a cada dueño, que ya las verificó:
  - **Diagnóstico** (`garaje/diagnostico.py`, de Auditor Planos): síntoma "inestable", olor en humo, avisos de "no la ruedes"; 22/22 pruebas pasan.
  - **Esquemas** (`garaje/diagramas.py`, de Planos):
    - Dirección con dos balineras; cámara y radios en las ruedas.
    - Cable CBS en NKD y CR4; ABS de un canal en Aerox y Gixxer FI.
  - **Fichas** (`garaje/views.py`, de Planos):
    - `_se_compra` filtra los repuestos que no se compran.
    - `_FILTRO_AIRE_POR_LINEA` da el consejo según el tipo de filtro: viscoso, espuma o seco.
    - Las guías toman las cifras del plan de cada moto.
  - **Datos de `LineaMoto`** (migraciones 0023 y 0026–0030, de Garaje): rines y suspensiones corregidos según los manuales.
- **Intervalos**: las 25 líneas tienen `garaje/intervalos/<slug>.json`, escrito por Auditor Planos con mis cifras; ArchivosIntervalosTests da OK.
  - Aproximadas: NS200, Boxer, Discover, RS 200 (aceite a 5.000 km por la regla Bajaj), NKD, GN, Apache (manual 4V), Duke y RC (manual 2024) y Gixxer FI 2020 (usa las cifras de la 2015).

## Pendiente
- Si aparece el manual de la Gixxer FI ABS 2020, rehacer esa versión con Auditor Planos.
- Nada tiene commit.

## Archivos clave
- Notas `capa3-*.md` (cifras con su fuente) en la carpeta compartida de notas de Auxiliares.
- Memoria: `intervalos-por-moto.md`.
- Manuales solo en `manual_despiece/<moto>/` (local). Los PDF de studocu traen datos personales en las marcas de agua: no copiar su texto.
