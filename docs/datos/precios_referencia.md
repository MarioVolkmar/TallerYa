# Datos: precios de referencia de mantenimiento de motos (Medellín, 2026, COP)

Investigado el 2026-11-14.

**Conclusión: no hay una fuente oficial ni un estudio de precios por servicio en Medellín.** Lo que existe son notas de prensa con 2–3 talleres, blogs comerciales y precios de repuestos en tiendas en línea. Sirven como rango **orientativo**, no como tarifa. Ninguna fuente separa bien por cilindraje.

Confianza:
- **media**: dos o más fuentes de 2025–2026 coinciden, y al menos una es de Medellín.
- **baja**: una sola fuente, o fuentes que no coinciden, o sin ciudad.
- **sin datos**: no encontré nada fiable; no publicar cifra.

## Tabla lista para código

"Total" = repuestos + mano de obra en un taller de barrio o independiente (no concesionario). Baja = hasta ~150 cc; media = ~150–400 cc.

| Servicio | Baja (≤150 cc) | Media (150–400 cc) | Confianza | Base |
| --- | --- | --- | --- | --- |
| Cambio de aceite con filtro | $50.000 – $100.000 | $80.000 – $150.000 | media | 3 fuentes 2025–26; un taller de Laureles "desde $100.000" |
| Mantenimiento general / sincronización | $150.000 – $250.000 | $160.000 – $300.000 | media | 2 talleres de Medellín (*El Colombiano*, oct-2026) |
| Pastillas de freno (un juego, solo repuesto) | $30.000 – $80.000 | $40.000 – $150.000 | baja | *El Colombiano* ($32.000 NMAX; $70–150 mil originales DR150), blog ($40–80 mil) |
| Kit de arrastre (solo repuesto) | $70.000 – $160.000 | $150.000 – $350.000 | baja | precios de tiendas (TVS ~$70 mil, Pulsar NS200 $125–223 mil, Duke 200 ~$260 mil, Dominar ~$340 mil); premium más caro |
| Juego de llantas (solo repuesto) | $150.000 – $500.000 | $400.000 – $700.000 | baja | blog 2025; dueño de una DR150 ($400–700 mil, marcas premium) |
| Revisión de frenos / ajustes básicos (mano de obra) | $30.000 – $70.000 | $30.000 – $70.000 | baja | un blog, sin ciudad |
| Mano de obra: instalar kit de arrastre | sin datos | sin datos | — | no encontré nada |
| Mano de obra: cambio o montaje de llanta | sin datos | sin datos | — | no encontré nada |

Para tener los datos como estructura de código:

```python
# (min, max) en COP. None = sin datos fiables: no mostrar cifra.
PRECIOS_REFERENCIA_2026 = {
    "cambio_aceite":         {"baja": (50_000, 100_000),  "media": (80_000, 150_000),  "confianza": "media", "incluye": "aceite, filtro y mano de obra"},
    "mantenimiento_general": {"baja": (150_000, 250_000), "media": (160_000, 300_000), "confianza": "media", "incluye": "repuestos básicos y mano de obra"},
    "pastillas_freno":       {"baja": (30_000, 80_000),   "media": (40_000, 150_000),  "confianza": "baja",  "incluye": "solo repuesto"},
    "kit_arrastre":          {"baja": (70_000, 160_000),  "media": (150_000, 350_000), "confianza": "baja",  "incluye": "solo repuesto"},
    "llantas_juego":         {"baja": (150_000, 500_000), "media": (400_000, 700_000), "confianza": "baja",  "incluye": "solo repuesto"},
    "revision_frenos":       {"baja": (30_000, 70_000),   "media": (30_000, 70_000),   "confianza": "baja",  "incluye": "mano de obra"},
    "mo_kit_arrastre":       None,
    "mo_cambio_llanta":      None,
}
```

## Recomendaciones para la función

1. **Mostrar rangos, no un precio.** Agregar siempre "Precio orientativo, confirma con el taller", la fecha ("nov-2026") y qué incluye (solo repuesto, o repuesto y mano de obra).
2. **Mostrar solo las filas de confianza media** (aceite y mantenimiento general). Las de confianza baja, como mucho con aviso; las que no tienen datos, nunca.
3. **La mejor fuente somos nosotros.** Los talleres de TallerYa ya cargan precios por servicio en su perfil. Con 5 o más talleres por servicio, calcular la mediana y el rango intercuartil y reemplazar esta tabla. Además, eso sí es un dato propio y defendible ante Ruta N.
4. **Ajuste anual.** Asopartes reporta un alza de ~23 % en la mano de obra especializada en 2026, por el salario mínimo. Revisar la tabla cada enero.

## Fuentes

- *El Colombiano*, 23-10-2026: [¿Cuánto cuesta mantener una moto? La cuenta puede superar los $500.000 mensuales](https://www.elcolombiano.com/negocios/cuanto-cuesta-mantener-una-moto-colombia-2026-HF42655714). Talleres de Manrique y Buenos Aires (Medellín), cotización para NMAX, dueño de una DR150, Asopartes.
- SYM Colombia, 10-11-2025: [¿Cuánto cuesta mantener una moto en Colombia en 2026?](https://symcolombia.co/costos-reales-de-tener-moto/). Blog de una marca; rangos nacionales.
- Autolex: [¿Cuánto cuesta un cambio de aceite en Medellín? Precios 2026](https://autolex.com.co/guias/cuanto-cuesta-cambio-de-aceite-medellin). Sobre todo carros; mano de obra de $30.000 a $100.000.
- Grupo Premium Laureles: [Cambio de aceite y filtros en Medellín](https://www.grupopremium.com.co/sedes/medellin/aceite-filtros/). "Desde $100.000".
- Kits de arrastre, precios de tienda (consultados el 2026-11-14): [Auteco](https://www.auteco.com.co/kit-de-arrastre-21016874/p), [Mercado Libre](https://motos.mercadolibre.com.co/repuestos-cuatrimotos/kit-arrastre), [2G Moto](https://2gmoto.com.co/categoria-producto/kit-de-arrastre-motos/); [Pulzo, 2023](https://www.pulzo.com/carros/cuando-cambiar-kit-arrastre-moto-cuanto-vale-colombia-consejos-PP3235611) ($80.000 a $500.000).
