# Historial: motos hechas y tiempos

Toma el modelo de Tripo como base y lo deja como modelo realista de la línea. Motos hechas: NMAX 155 (58,6 MB y
1,9 M de triángulos con textura → 1,2 MB, 64 piezas) y AKT NKD 125 (0,8 MB y 47 mil triángulos sin textura →
0,96 MB, 55 piezas) y Bajaj Boxer CT 100 (49 mil triángulos sin textura → 1,03 MB, 54 piezas, `fichas/boxer100.py`) y Yamaha XTZ 150
(48 mil sin textura, girada → 0,97 MB, 52 piezas, `fichas/xtz150.py`).

`fichas/nmax155_cortar.py` y `nmax155_internos.py` son la ficha de la NMAX en el formato viejo (un programa
suelto por paso, con `por_pieza.mjs` y `exportar.py` aparte): sirven de ejemplo de reglas **por color**; para
retocar la NMAX conviene pasarlas antes al formato nuevo.

### Tiempos medidos

| Paso | NMAX (formato viejo) | NKD (motor + ficha) | Boxer CT 100 | XTZ 150 |
|---|---|---|---|---|
| Extraer + preparar | ~1 min | 2,5 s | 3 s |
| Simplificar | ~1 min | no hizo falta | no hizo falta |
| Una vuelta cortar → exportar | 1,5–2 min | 4,4 s (14 s con render de revisión) | 6 s (11 s con render) |
| Render de revisión, por vista | ~20 s | 3,4 s | ~1,5 s |
| Vueltas hasta la primera entrega | ~25 | 5 | 5 (6 renders leídos) |
| Del GLB a la página | varias horas | ~25 min | ~13 min (con pruebas y capturas) | ~17 min (3 vueltas, 6 renders) |

Lo que más pesa ahora no es la máquina sino **mirar**: cada render o captura que se lee cuesta más que la vuelta.
Pedir en un solo `--ver` todas las vistas de una ronda y en la página armar una hoja de varias vistas por captura.

- Yamaha XTZ 125 y MT-03 (19-nov-2026): ver la memoria relevo-moto-3d-tripo.md.
