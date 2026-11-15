# Cómo estimamos los km de un mantenimiento (criterio final, 14-nov-2026)

**Moto del ejemplo:** la AKT NKD 125 2022 de la cuenta demo, con 22.000 km. Sus datos son inventados; solo sirven para ver la cuenta. Tarea: **aceite de motor, cada 2.500 km o 120 días**.
**Lecturas:** 14.200 (13-sep) · 15.100 (13-oct) · 16.050 (12-nov), y saltos a 20.000, 21.000 y 22.000 en dos días. Esos saltos se toman como correcciones del odómetro, no como km rodados.

## El ritmo de uso (km por día)
- **Primero, las lecturas de km:** la recta de mejor ajuste, sin las correcciones. En la NKD da 30,6 km/día.
- **Si no hay lecturas suficientes:** los km rodados desde que se registró en TallerYa (si ya pasaron dos semanas).
- **Si tampoco hay eso:** todos los km desde la **fecha de matrícula**, si la moto la tiene (campo "fecha de matrícula" de la moto). Ej.: 22.000 km en 1.000 días = 22 km/día. *(Nuevo: antes se saltaba directo al año del modelo.)*
- **Si no hay matrícula:** el año del modelo (22.000 km desde mediados de 2021 ≈ 11,2 km/día).
- **Sin ningún dato:** 25 km/día.

## (a) Registro con km exacto
- **Regla:** km desde el cambio = km de hoy − km anotado.
- **Ejemplo:** cambio a los 13.700 → 8.300 km, pasado por 5.800 → "Toca ya".
- **Supone:** que el dato es correcto. Solo se equivoca si el número anotado está mal.
- **Antes:** igual.

## (b) Fecha concreta, sin km
- **Regla:** km de ese día = km de hoy − lo rodado desde esa fecha. Lo rodado se reparte parejo entre las dos lecturas que rodean la fecha, sin contar las correcciones del odómetro. Si la fecha es anterior a la primera lectura, se cuenta hacia atrás con el ritmo.
- **Ejemplo:** cambio el 30-sep. Desde ahí hasta hoy rodó ≈ 1.340 km → ese día tenía ≈ 20.660 en la escala del odómetro de hoy. Faltan ≈ 1.160 (54 %).
- **Supone:** que la moto rodó parejo entre lecturas y que un salto imposible (más de 400 km/día) es una corrección.
- **Se equivoca:** si rodó disparejo. Si rodó más después del cambio, los km desde el cambio quedan cortos (subestima); si rodó más antes, se pasa (sobreestima). Un viaje real de más de 400 km en un día se tomaría como corrección (subestima).
- **Antes:** no se podía registrar sin km.

## (c) "Hace unos meses"
- **Regla:** fecha = hoy − meses × 30 días (1, 3, 6 o 12 meses; "Hace más de un año" cuenta 12). El km sale como en (b).
- **Ejemplo:** "hace 3 meses" (16-ago, antes de la primera lectura): 28 días × 30,6 km/día hacia atrás → ≈ 2.710 km desde el cambio → "Toca ya" (108 %).
- **Al agregar una moto** todavía no hay lecturas ni días de uso en TallerYa, así que se usa el ritmo del año del modelo: 90 × 11,2 ≈ 1.000 km desde el cambio (40 %, "Al día").
- **Supone:** que la opción elegida es cercana a la real y que el ritmo representa el uso.
- **Se equivoca:** "Hace más de un año" toma el borde más reciente del rango, así que subestima. El ritmo del modelo se queda corto en motos de trabajo y también subestima. A medida que el dueño registra kilometraje, el ritmo pasa a salir de sus lecturas.
- **Antes:** siempre 25 km/día. En el ejemplo de 3 meses: 2.250 km, "Pronto" (90 %).

## (d) "No sé"
- **Regla:** si la moto llegó con menos km que el intervalo de la tarea, suponemos que la pieza es la de fábrica: los km cuentan desde 0 y el tiempo desde que se registró. Si ya pasó el intervalo, marca "Pronto · revísalo pronto" (amarillo), nunca "Toca ya". Si llegó con más km que el intervalo, queda "Sin registro".
- **Ejemplo:** el kit de arrastre (cada 18.000 km). La moto llegó con 14.200 km, menos que el intervalo, así que contamos 22.000 desde nueva: pasado por 4.000 → "Pronto". Con el aceite, la moto llegó con más km que el intervalo (2.500) → "Sin registro".
- **Supone:** lo peor en km (que nunca se cambió) y lo más benigno en tiempo.
- **Se equivoca:** si la pieza sí se cambió, sobreestima los km. El tiempo lo subestima.
- **Antes:** los mismos km, pero marcaba "Toca ya" (rojo). Ahora la etiqueta dice "Pronto (estimado)".

## (e) "Sin idea" (nuevo, en el diálogo "Registrar mantenimiento")
- **Regla:** en "No sé", el chip "Sin idea" supone que el repuesto nunca se ha cambiado. Cuenta todos los km de la moto (desde 0) y el tiempo desde la fecha de matrícula; si no la hay, desde mediados del año anterior al modelo (la misma suposición del ritmo). Se muestra como lo supuesto: "Pronto (estimado)", nunca "Toca ya" en rojo. No se anota en la hoja de vida, porque no es un servicio hecho.
- **Ejemplo:** el aceite de la NKD con "Sin idea": 22.000 km desde nueva, pasado por 19.500 → "Pronto (estimado)".
- **Supone:** lo peor en km. Si la pieza sí se cambió, sobreestima los km.
- **Diferencia con (d):** (d) se aplica solo, cuando la moto llegó con pocos km y no hay registro; "Sin idea" lo elige el dueño, y vale aunque la moto haya llegado usada.

## Km sin fecha (al poner al día)
La fecha se estima con el ritmo, como mucho dos años atrás. En la NKD, 2.500 km a 30,6 km/día son 82 días. Antes eran 100 días con 25 km/día.

## Corrección aplicada
Antes, la interpolación de (b) y (c) repartía también las correcciones del odómetro. Ahora usa solo los km rodados, con la misma regla del ritmo. El método no cambia; solo deja de contar los saltos imposibles como km rodados.
