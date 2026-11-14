# Datos: pico y placa de motos y vencimientos (SOAT, técnico-mecánica)

Investigado el 2026-11-14. **Confianza**: alta = fuente oficial que lo dice expresamente; media = varias fuentes coinciden pero no vi el texto oficial; baja = fuentes que no coinciden o no verificables.

## 1. Pico y placa de motos — Valle de Aburrá, 2.º semestre 2026

### Regla vigente

| Campo | Valor | Confianza |
| --- | --- | --- |
| Vigencia | desde el **lunes 3 de agosto de 2026**; según la prensa, hasta el **29 de enero de 2027** (la fuente oficial no da fecha de fin) | alta (inicio) · media (fin) |
| Dígito de la placa en motos | el **primero** que aparece en la placa (en carros es el último) | alta |
| Días | lunes a viernes; no aplica sábados, domingos ni festivos | alta |
| Horario | **5:00 a. m. a 8:00 p. m.**, continuo | alta |
| Vehículos | motos, mototriciclos, tricimotos y ciclomotores, de 2 y 4 tiempos | alta |
| Dónde | Medellín y los 9 municipios del Valle de Aburrá (Bello, Envigado, Itagüí, Sabaneta, La Estrella, Caldas, Copacabana, Girardota, Barbosa). Cada municipio saca su propio decreto con la misma rotación. | alta (Medellín) · media (resto) |

### Rotación (lista para código)

| Día | Primer dígito restringido |
| --- | --- |
| Lunes | 5 y 8 |
| Martes | 1 y 4 |
| Miércoles | 0 y 2 |
| Jueves | 3 y 6 |
| Viernes | 7 y 9 |

```python
ROTACION_2026_2 = {"lunes": "5,8", "martes": "1,4", "miercoles": "0,2", "jueves": "3,6", "viernes": "7,9"}
VIGENTE_DESDE = date(2026, 8, 3)
VIGENTE_HASTA = date(2027, 1, 29)  # confianza media: falta el decreto
HORA_INICIO, HORA_FIN = time(5, 0), time(20, 0)
DIGITO = "primero"
```

**El código ya la tiene.** La migración `garaje/migrations/0014_rotacion_medellin_2026_2.py` carga esta misma rotación (`digito="primero"`), y `garaje/pico_placa.py` ya excluye fines de semana y festivos de Colombia (Ley 51 de 1983). Lo que falta revisar:

- **Fecha de fin.** Conviene poner `vigente_hasta = 2027-01-29` y avisar al usuario cuando no haya regla vigente.
- **Pausa de fin de año.** En diciembre de 2025 la medida se suspendió por Navidad y Año Nuevo, y Medellín la reanudó el 19 de enero de 2026. Es probable que se repita, pero cada año sale en un decreto aparte: no se puede programar de antemano. Hay que cargarla a mano cuando se publique.

### Cómo rota

- Cambia **cada semestre**: en febrero (el 1.er semestre de 2026 arrancó el 2 de febrero) y en agosto. La Alcaldía y el Área Metropolitana la anuncian unas semanas antes.
- La primera semana de cada rotación es **pedagógica**, sin multas (en 2026 fue del 3 al 6 de agosto).
- No hay una fórmula fija que permita calcular la rotación siguiente: hay que cargar cada semestre con el decreto nuevo.

### Excepciones útiles para la app

| Excepción | Detalle | Confianza |
| --- | --- | --- |
| Domicilios y mensajería | Motos de reparto exentas, **con inscripción previa** ante Movilidad (licencia y prueba de la actividad) | alta |
| Eléctricas, híbridas y a gas | Exentas como vehículos en general (normas nacionales); la página de Medellín no lo dice expresamente para motos | media |
| Vías exentas en Medellín | Sistema Vial del Río (autopista Sur, avenida Regional, Regional Occidental), avenida 33 del río a Las Palmas, avenida Las Palmas, La Iguaná, calzada oriente-occidente del puente Horacio Toro. Tampoco aplica en los 5 corregimientos. | alta |
| Itagüí, Envigado, Sabaneta | Autopista Sur libre en Itagüí; avenida Regional libre en Sabaneta y Envigado | media (prensa) |
| Bello | Mantiene la restricción en la autopista Norte y en la avenida Regional (entre la estación Niquía y la autopista Medellín-Bogotá) | media (prensa) |

### Multa

| Dato | Valor | Confianza |
| --- | --- | --- |
| Sanción | Multa más inmovilización de la moto | alta |
| Monto | La página de Medellín dice "15 SMDLV, $499.999", pero parece un texto viejo. *El Colombiano* da **$633.111 (52,29 UVB)** desde el 10 de agosto de 2026. | baja |

Recomendación: en la app poner "multa e inmovilización", sin una cifra fija.

### Lo que no pude verificar

- Los decretos de 2026-2 de Envigado, Sabaneta, Bello e Itagüí. El de Itagüí (Decreto 1011 de 2026) está publicado, pero es un PDF escaneado que no pude leer.
- La rotación del 1.er semestre de 2027: todavía no está publicada.

## 2. Revisión técnico-mecánica (RTM) de motos

| Regla | Valor | Confianza |
| --- | --- | --- |
| Primera revisión | a los **2 años** de la fecha de matrícula (Ley 769 de 2002, art. 52, modificada; ratificado en la guía del RUNT) | alta |
| Después | **cada año**, antes de la fecha en que vence la anterior | alta |
| Motos eléctricas | Desde 2026 también deben hacerla, con las mismas fechas (según la prensa; hay notas que no coinciden) | media |
| Precio de referencia 2026 | $217.000 – $248.000 en un CDA (cada CDA fija su tarifa) | media |
| Dónde verificar | RUNT, consulta por placa (gratis) | alta |

Ojo: la Ley 2294 de 2023 pasó a **5 años** la primera revisión de los **carros** particulares, pero las motos siguen con 2.

Lista para código:

```python
def proxima_rtm(fecha_matricula, ultima_rtm=None):
    if ultima_rtm:
        return ultima_rtm + relativedelta(years=1)
    return fecha_matricula + relativedelta(years=2)
```

## 3. SOAT

| Regla | Valor | Confianza |
| --- | --- | --- |
| Vigencia | **1 año** desde la fecha de inicio de cobertura que aparece en la póliza | alta |
| Sanción por no tenerlo | 30 SMDLV más inmovilización (grúa y parqueadero aparte); para liberar la moto hay que comprar el SOAT | alta (regla) · baja (monto en pesos: las fuentes no coinciden) |
| Dónde verificar | RUNT, consulta por placa, pestaña "Póliza SOAT" (gratis) | alta |

## 4. Qué datos pedir para los avisos

| Dato | Sirve para | Obligatorio |
| --- | --- | --- |
| Placa | pico y placa (primer dígito) | sí |
| Fecha de **vencimiento** del SOAT | aviso de SOAT; es más fácil que pedir la fecha de expedición | sí |
| Fecha de **matrícula** | primera RTM (matrícula + 2 años) | sí, si la moto tiene menos de 2 años o nunca hizo RTM |
| Fecha de vencimiento de la última RTM | RTM siguiente | sí, si ya hizo alguna |
| Municipio donde circula | excepciones de vías (opcional) | no |
| Es moto de reparto inscrita / eléctrica | excepción del pico y placa | no |

Avisos sugeridos (no son norma, solo producto): **30, 7 y 1 días** antes del vencimiento del SOAT y de la RTM, y pico y placa la tarde anterior, como ya hace `recordar_pico_placa`.

## Fuentes

- Alcaldía de Medellín — [Pico y Placa Medellín 2026, segundo semestre](https://www.medellin.gov.co/es/secretaria-de-movilidad/pico-y-placa-medellin-2023-segundo-semestre/) (página oficial; la URL dice 2023 pero el contenido es de 2026), consultada el 2026-11-14.
- Alcaldía de Medellín — [La nueva rotación comenzará a regir el lunes 3 de agosto](https://www.medellin.gov.co/es/sala-de-prensa/noticias/la-nueva-rotacion-del-pico-y-placa-en-medellin-comenzara-a-regir-a-partir-del-lunes-3-de-agosto/).
- Alcaldía de Medellín — [Se reanuda el pico y placa el 19 de enero](https://www.medellin.gov.co/es/sala-de-prensa/noticias/desde-este-lunes-19-de-enero-se-reanuda-el-pico-y-placa-en-medellin-tras-suspension-temporal-por-fin-de-ano/) (pausa de fin de año).
- Área Metropolitana — [Nueva rotación del Pico y Placa en Medellín y el Valle de Aburrá 2026](https://www.metropol.gov.co/Paginas/Noticias/Nueva%20rotacion%20del%20Pico%20y%20Placa%20en%20Medellin%20y%20el%20Valle%20de%20Aburra%202026.aspx).
- Tránsito de Itagüí — [Decreto 1011 de 2026](https://www.transitoitagui.gov.co/wp-content/uploads/2026/08/decreto_1011_-2026_picoyplaca.pdf) (PDF escaneado, no lo pude leer).
- Prensa: [El Colombiano, rotación 2026-2](https://www.elcolombiano.com/medellin/rotacion-pico-y-placa-medellin-segundo-semestre-de-2026-PP39145875), [Infobae, 27-07-2026](https://www.infobae.com/colombia/2026/07/27/pico-y-placa-en-medellin-cambiara-desde-agosto-asi-sera-la-nueva-rotacion-y-las-sanciones-por-incumplir-la-medida/), [Valora Analitik](https://www.valoraanalitik.com/pico-y-placa-en-medellin-tendra-nueva-rotacion-para-el-segundo-semestre-de-2026-hay-excepciones/).
- RTM: [RUNT, ABC de la renovación de la RTM](https://www.runt.gov.co/sites/default/files/documentos/ABC%20Renovaci%C3%B3n%20RTM.pdf), [Noticias RCN, motos eléctricas](https://www.noticiasrcn.com/economia/motos-electricas-deben-hacer-tecnomecanica-en-colombia-1009298), [El Carro Colombiano, costo de la RTM 2026](https://www.elcarrocolombiano.com/dos-ruedas/costo-revision-tecnico-mecanica-de-motos-en-2026-precios-multas-y-tramites/).
- SOAT: [Noticias RCN, consulta por placa en el RUNT](https://www.noticiasrcn.com/economia/soat-placa-2026-runt-1045130), [Semana, SOAT vigente 2026](https://www.semana.com/vehiculos/articulo/su-soat-esta-vigente-en-2026-asi-puede-consultarlo-con-solo-la-placa-del-vehiculo/202602/).
