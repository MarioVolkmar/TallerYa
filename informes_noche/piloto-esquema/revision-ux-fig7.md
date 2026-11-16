# Revisión UX: fig. 7 «Bomba de aceite y drenaje» (`motor/aceite.html`)

Revisora UX · 16-nov-2026 (07:56–07:58). La medí con `medir_lamina.py` en los 6 anchos (rúbrica v3) y la revisé a ojo con dos capturas: la vista general a 1280 y el grupo «Tapón de drenaje y tamiz» con la hoja a 390.

## Veredicto: aprueba
| Medible (6 · 8 · 9 · 10 · 11 · 12) | A ojo (1 · 2 · 3 · 4 · 5 · 7) | **Total** | Bloqueantes |
|---|---|---|---|
| 4 · 4,7 · 5 · 5 · 4,7 · 4,8 = **4,70** | 5 · 4,5 · 5 · 4 · 4 · 4,5 | **4,60** | ninguno |

**¿Piezas oscuras que se vuelven mancha? No.** La bomba (engranaje) y el tapón son metálicos y claros, con brillo y volumen, y el cárter va solo como contorno punteado de referencia. Se distinguen sin leer las píldoras, al revés que en la fig. 11.

## Medidas
- **Grupos:** son 2 (Drenaje y Bomba), con marcas de 45 px, sin fallas ni solapes. Los textos de contexto («Cárter, lámina 10» y «Perno de drenaje A, lámina 10») orientan bien.
- **Distribución:** el dibujo se ve completo en los 6 anchos (236 px a 360 y 469 px a 1280). Al entrar a un grupo, «Desarmar» queda a la vista, y el desarme dura 1,5 s.
- **Hoja inferior:** ocupa el 12 % de la pantalla, con nombre y botón de cerrar, sin tapar la pieza.
- **Toque:** 4 de 5 piezas tienen 24 px o más a 360; el resorte 5 queda en 20 px.
- **Ficha:** «¿Se repara?» está a 0,35 pantallas y «Pedir», a 0,77.
- **Lista con buscador:** «bomba» da 3 resultados.
- **Lo demás:** el 3D abre en el tamiz y no hay desborde ni errores de consola.

## Qué corregir (nada bloquea)
1. **Encuadre del grupo «Tapón de drenaje y tamiz» en el celular:** el tapón queda chico (unos 25 px) en medio de un lienzo casi vacío. El motor fija un ancho mínimo de encuadre (`minW = 380` unidades en `encuadreGrupo`) que, en grupos de piezas chicas, no deja acercar lo suficiente.
   - **Cómo:** bajar ese mínimo para los grupos chicos (por ejemplo, a 220) o hacerlo proporcional al tamaño del grupo. El tapón, el tamiz y el resorte se verían 1,5 veces más grandes, y el resorte 5 pasaría de 20 px a más de 24.
   - **Es del motor:** sirve para todas las láminas con grupos de piezas chicas.
2. **Letra de respaldo:** 4 reglas de `esquema.css` usan `font-family:"Oswald"` sin respaldo.
   - Si Google Fonts tarda o no carga (red lenta, sin señal: el caso de la moto varada), esos textos salen con letra de imprenta. Pasó en mi captura de 1280 con la cinta, el subtítulo del visor y los textos de contexto del dibujo.
   - **Cómo:** agregar `,"Archivo",system-ui,sans-serif` a esas 4 reglas. Es del motor y no cuesta nada.
3. **Ficha de contexto «Aceite de motor»:** bien que exista, porque es lo que más busca el motero. Conviene que el buscador la encuentre con «aceite» y que su resumen diga cada cuánto se cambia (lo hace el prototipo v3 con la línea de resumen).
