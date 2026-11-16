# Relevo: fig. 26 de la NMAX (bombas de freno) y mejora de la skill hacer-lamina

## Hecho (16-nov-2026)
- Lámina lista para revisión: `motor/datos/nmax-fig26.json`, `motor/datos/nmax-fig26-arte.js`, `motor/bomba-freno.html`, `motor/prueba-nmax-fig26.html`.
  - Validador en OK; medir_lamina sin bloqueantes (UX 4,58); 35 min contra 95 de la CVT.
  - Constructor en el scratchpad de la sesión: `armar26.py` + `fichas26.py`. Si se pierde, se edita el JSON directo.
- **No tocar `nmax-fig26.*`** mientras la revisora y ux-piloto califican.

## En curso: mejora de la skill (pedido de Auxiliares, fase `mejora_skill`)
1. Grillas PNG en vez de leer el PDF.
2. Modelo de estilo: una lámina del mismo sistema.
3. anexo-formato: 16a/16b, #fnCorte con data-ym/xm y esq-solo-pc/movil, esq-oculto-arm y `alPrincipio`. Si se agrega al motor, se comprueba con la firma.
4. `motor/separar_numeros.py` (la repulsión de números del despiece).
5. Meta de densidad: criterio 6 ≥ 4,5.
6. Métricas: pct_seguro y pct_certeza_total, uso_plan, cronómetro de las revisoras, solapamiento.
7. Recortar la sección 2 de brief-lamina y el brief del esqueleto.

Al terminar, un solo mensaje corto a Auxiliares.

## Hecho: mejora de la skill (4 min). En curso: correcciones tras las revisiones (fase `correcciones`)
- Revisión mecánica 4,4 (sube a 4,8 con M1 y M2); UX 4,45, pasa. Revisiones en `informes_noche/piloto-esquema/revision-*-fig26.md`.
- Lámina (se regenera con `armar26.py`; ojo: `cuando` se acumulaba en cada corrida, por eso el nivel salía repetido):
  - M1: kits 2 y 22 cada 2 años con el líquido (manual pp. 9-7 y 9-25), «Seguro», más su fila en «Cuándo».
  - M2: una sola fila de nivel, «antes de cada salida» (manual).
  - M3: la bomba completa trae lo que tiene punto bajo el ASSY.
  - M4: tuerca nueva, el perno se reutiliza.
  - U2: etiqueta «Manguera» a 360.
- Motor: U1 alto fijo del texto de «Cómo funciona»; U3 zoom o pista con más de 20 números.
- Validador: V1 kits o sellos sin los 2 años del líquido; V2 filas repetidas en «Cuándo».
- Skill y criterios-ux: regla de densidad de ux-piloto.
- Sitio: `garaje/despiece_fichas.py:62,68` y `despiece_guia_mecanica.py`, nivel «antes de cada salida», más la prueba focalizada.
- Al final: validador, medir_lamina, firma del freno y la CVT, y un solo mensaje a Auxiliares.
