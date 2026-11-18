# TallerYa Ruta — el plan para domiciliarios

Rama: `claude/plus-domiciliarios-cff951` (worktree propio; no está unida a main).
Bandera: `DOMICILIARIOS_ACTIVO=1` en el entorno o en `.env` (apagada por defecto).

## 1. Diseño

### Qué les duele
Un domiciliario de Rappi, DiDi, iFood o mensajería en Medellín rueda 150–300 km al día, 6 días a la semana.
La moto es su herramienta de trabajo, así que:

1. **Un día sin moto es un día sin plata.** Una cadena reventada o un aceite quemado le cuesta el arreglo y además el día de trabajo.
2. **Los intervalos del manual no le sirven.** Para él, "cada 3.000 km" son 2 semanas, y el uso severo (pare-arranque, carga, lluvia, polvo) desgasta más rápido.
3. **No sabe si la moto le deja plata.** Tanquea a diario y paga aceite, llantas y pastillas, pero no sabe cuánto le cuesta cada km ni cuánto le queda de lo que gana.
4. **Las multas e inmovilizaciones salen caras.** Le puede pasar por un SOAT o una técnico-mecánica vencidos o por pico y placa, que en Medellín aplica a motos (primer dígito de la placa, 5 a. m.–8 p. m.).
5. **No tiene tiempo para el taller.** Necesita un taller que lo atienda en el día o fuera del horario de trabajo.
6. **A veces la plataforma o la flota le pide demostrar que la moto está en buen estado.**

### Qué resuelve cada beneficio (filtrado y priorizado)

| # | Beneficio | Dolor | Piloto | Plan |
|---|-----------|-------|--------|------|
| 1 | **Plan de uso intensivo**: con los km por semana adelanta los intervalos de las piezas que más sufren (aceite, filtro de aire, cadena, frenos, llantas, correa) y los muestra en días | 1, 2 | ✅ | Gratis |
| 2 | **Cierre de jornada en 20 s**: km del tablero, lo que ganó y lo que tanqueó. Calcula el balance de la semana y del mes (ingresos − gastos), el costo por km y la ganancia por km | 3 | ✅ | Gratis |
| 3 | **Tablero "Mi ruta"**: pico y placa de hoy y mañana, SOAT y técnico-mecánica, lo próximo del plan intensivo y el balance, en una sola pantalla de celular | 4 | ✅ | Gratis |
| 4 | **Talleres aliados para domiciliarios**: atienden en el día o en horario extendido, con su descuento | 5 | ✅ | Lista gratis; **descuento con Plus** |
| 5 | **Comprobante "mantenimiento al día"**: enlace firmado que vence en 30 días, para mostrar a la plataforma o a la flota (plan, SOAT y técnico-mecánica, sin datos privados) | 6 | ✅ | **Plus** |
| 6 | Urgencias prioritarias: emergencias ya existentes; mecánico a domicilio cuando exista | 1 | 🔗 enlace a emergencias | Fase 2 |
| 7 | Cupones exclusivos de marcas (lubricantes, llantas) | 3 | — | Fase 2 |
| 8 | Canal del foro para domiciliarios | — | — | Fase 2 (cambia `foro.Categoria`, que tiene migración propia) |
| 9 | Planes para flotas | 6 | — | Fase 2 |

Los recordatorios de SOAT, técnico-mecánica y pico y placa **ya existen** en `garaje` (avisos y WhatsApp). El plan no los duplica: los muestra juntos en el tablero.

**Sobre el pico y placa (verificado el 18-nov-2026):** en Medellín aplica a motos de 2 y 4 tiempos según el primer dígito de la placa, de 5:00 a. m. a 8:00 p. m. Es la regla que ya está cargada en `garaje` (rotación del 3-ago-2026, Decreto 1490 de 2026). **No pude confirmar si hay excepción para motos de domicilio**: la página de preguntas de la Secretaría de Movilidad trae esa pregunta, pero no encontré la respuesta. La página no promete ninguna excepción. **Pendiente: leer el artículo de excepciones del decreto.**

### Precio sugerido
- **Gratis** (para atraer y retener): marcarse como domiciliario, plan intensivo, jornadas y balance, tablero y lista de talleres aliados. Son los que más datos y uso diario generan, y el domiciliario cuida mucho cada peso.
- **Plus domiciliario: $4.900/mes** (variable `DOMICILIARIOS_PRECIO_PLUS`), la mitad del Plus normal ($9.900). Activa los descuentos de los talleres aliados y el comprobante, y conserva todo lo del Plus normal.
  Usa la misma `cuentas.Suscripcion`: se paga por Nequi y el admin la activa a mano igual que siempre. La nota dice "Plan domiciliario" para cobrar el precio correcto.
- **Patrocinio (fase 2):** los talleres aliados pagan por aparecer, porque el domiciliario vuelve cada 2–3 semanas por aceite y es un cliente muy recurrente. Las marcas de lubricantes y llantas pueden pagar cupones. Más adelante, las flotas pagan por repartidor.

  Razonamiento: con ~$4.900, un descuento del 10 % en un cambio de aceite (~$35.000) ya se paga solo en el primer mes.

### Alcance del piloto (una noche)
Del 1 al 5 de la tabla, más la página de presentación, el formulario para marcarse, los datos de demo y las pruebas.

## 2. Qué quedó hecho y cómo probarlo

App nueva **`domiciliarios`** (nombre comercial: **TallerYa Ruta**). Todo está detrás de `DOMICILIARIOS_ACTIVO`.

| URL | Qué es |
|-----|--------|
| `/domiciliarios/` | Presentación pública: para qué sirve, cuánto se adelanta cada pieza, precios, talleres aliados y cómo activarlo |
| `/domiciliarios/activar/` | Marcarse como domiciliario: moto (solo las propias), plataformas, km por semana y días. Al final, "Ya no soy domiciliario" |
| `/domiciliarios/mi-ruta/` | Tablero: pico y placa, SOAT y técnico-mecánica, estado del plan, cierre de jornada, balance de la semana y del mes, plan intensivo, talleres aliados con descuento (Plus), emergencias, comprobante (Plus) u oferta de Plus |
| `/domiciliarios/c/<token>/` | Comprobante público firmado (Plus): placa con los últimos dígitos ocultos, solo el primer nombre, `noindex` y `no-referrer` |
| Mi garaje y la ficha de la moto | Tarjeta "¿Trabajas en domicilios?" o "Mi ruta". Con la bandera apagada no aparece |
| Admin | Domiciliarios, Jornadas y **Talleres aliados de domiciliarios** (ahí se marcan: en el día, horario extendido, descuento) |

### Probarlo en local
Desde la carpeta del worktree, con una base aparte (cmd de Windows):

```
set DJANGO_DEBUG=1
set DOMICILIARIOS_ACTIVO=1
set DATABASE_URL=sqlite:///C:/ruta/temporal/dm.sqlite3
C:\dev\TallerYa\venv\Scripts\python.exe manage.py migrate
C:\dev\TallerYa\venv\Scripts\python.exe manage.py cargar_demo
C:\dev\TallerYa\venv\Scripts\python.exe manage.py demo_domiciliarios
C:\dev\TallerYa\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8013
```

- **Usuario de demo** (solo local): `domiciliario@demo.tallerya` / `demo-ruta-2026`, con Plus. Con `--sin-plus` se ve la oferta de Plus.
- **La demo trae** 5 semanas de jornadas, gasolina diaria, mantenimientos recientes y 3 talleres aliados.
- **Esta noche** se probó en `http://localhost:8013` con una base temporal. La base de `C:\dev\TallerYa` no se tocó.
- **Captura** (celular, 540 px): `informes_noche/plus-domiciliarios/mi-ruta-celular.png`. A 375 px tampoco hay scroll horizontal (comprobado en el navegador).

### Pruebas
- **`manage.py test domiciliarios`: 22 pruebas**. Cubren:
  - la bandera apagada: todas las URL dan 404, y Mi garaje y la ficha de la moto no muestran nada;
  - la presentación, activar, el IDOR de la moto ajena, el login y el POST obligatorio;
  - las jornadas: km, gasolina, reemplazo y km menor;
  - los cálculos del plan y del balance, y la solicitud de Plus;
  - el comprobante: sin Plus, token alterado, anular enlaces viejos y placa oculta.
- **Suite completa: 661 pruebas OK** (~31 s).
- **`config.tests_seguridad` y `cuentas.tests_seguridad`** con la bandera encendida: OK. Se agregó `domiciliarios/` a `PUBLICAS` del barrido anónimo.
- **`revisar-seguridad`** (código, cabeceras y secretos): sin fallas nuevas. Queda el aviso que ya existía de `'unsafe-inline'` en la CSP.

## 3. Decisiones
- **Se reutiliza `cuentas.Suscripcion` para el Plus**: no hay un modelo de pago nuevo.
  - El botón "Quiero Plus domiciliario" crea o anota la solicitud con la nota `Plan domiciliario · $4.900/mes`, y el admin la activa como siempre.
  - Hoy `activar()` da 30 días a cualquier precio: el precio menor depende de que el admin lea la nota. Fase 2: un campo `plan` en la suscripción.
- **Nada se duplica**: los km van a `garaje.LecturaKm`, la gasolina a `garaje.Gasto` (y aparece en Gastos y consumo), y los documentos y el pico y placa salen de `garaje`. `Jornada` guarda solo lo que ganó.
- **Plan intensivo** = el plan de `garaje.plan` (con los intervalos del manual por línea) con factores de uso severo:
  - Factores: aceite 0,7, filtro de aire 0,6, cadena y correa 0,75, frenos 0,75 y llantas 0,8. **Son aproximados y la página lo dice.**
  - El ritmo es el mayor entre los km por semana declarados y el de las lecturas reales.
  - Usa las funciones internas `_estado_tarea` y `nivel_tarea` de `garaje/plan.py`: si cambian, hay que revisar `domiciliarios/intensivo.py`.
- **Comprobante sin tabla nueva**:
  - Es un enlace firmado con `django.core.signing` (sal propia) que vence a los 30 días. Anular sube `version_comprobante` y los enlaces viejos dejan de abrir.
  - Sin Plus vigente no abre.
  - No muestra documentos ni la placa completa, y aclara que TallerYa no inspeccionó la moto.
- **Talleres aliados en un modelo aparte** (`TallerAliado`, uno a uno con `Taller`): no se toca la migración de `talleres`.
- **El foro para domiciliarios queda en fase 2**: agregar una categoría cambia `foro.Categoria` y crea una migración en `foro`, y la rama no sería tan fácil de revertir.
- **La app está siempre instalada**: sus tablas se crean aunque la bandera esté apagada. Es inofensivo y permite prender y apagar sin migrar. Apagada, las URL dan 404 y `{% aviso_domiciliarios %}` no pinta nada.
- **Sin clases nuevas de Tailwind**: CSS propio en `domiciliarios/static/domiciliarios/dm.css` (prefijo `dm-`), así que no hizo falta correr `npm run css`.

## 4. Precio sugerido
- **Base gratis.**
- **Plus domiciliario a $4.900/mes** (`DOMICILIARIOS_PRECIO_PLUS`).
- **Fase 2:** patrocinio de talleres aliados y marcas, y un plan por repartidor para flotas.

El razonamiento está en la sección 1.

## 5. Fase 2
1. **Flotas**: una empresa paga N cupos, invita a sus repartidores y ve en un tablero cuáles motos están al día (con el permiso de cada uno).
2. Campo `plan` en `Suscripcion` (normal o domiciliario) para que el precio quede guardado y no dependa de la nota.
3. Canal del foro "Domiciliarios" (nueva categoría en `foro.Categoria`).
4. Cupones de marcas solo para domiciliarios (aceite, llantas, pastillas) y aliados que paguen por aparecer primero.
5. Urgencias prioritarias: conectar con «Mecánicos a domicilio» cuando esté en main.
6. Avisos push o por WhatsApp del plan intensivo ("te toca aceite en 2 días"), reutilizando `garaje.avisos`.
7. Recordatorio para cerrar la jornada al final del día y resumen semanal.
8. **Verificar las excepciones del pico y placa** para motos de domicilio en el Decreto 1490 de 2026 antes de anunciar algo.
9. Comprobante con QR (ya existe `garaje/qr.py`).
10. Límite de intentos en el cierre de jornada antes de desplegar.

## 6. Reversión
**Apagar sin tocar código:** quitar `DOMICILIARIOS_ACTIVO` del entorno (viene apagada).

**Si la rama no se une:** basta con no unirla (`git branch -D claude/plus-domiciliarios-cff951`).

**Quitarlo del todo, si la rama ya se unió:**
1. Borrar las 3 tablas con `manage.py migrate domiciliarios zero`. Los gastos y km que creó quedan en el garaje.
2. Borrar la carpeta `domiciliarios/`.
3. En `config/settings.py`, quitar `"domiciliarios"` de `INSTALLED_APPS` y las 3 líneas de `DOMICILIARIOS_*`.
4. En `config/urls.py`, quitar la línea `include("domiciliarios.urls")`.
5. En `garaje/templates/garaje/garaje.html` y `moto.html`, quitar `domiciliarios_tags` del `{% load %}` y la línea `{% aviso_domiciliarios %}`.
6. En `config/tests_seguridad.py`, quitar `"domiciliarios/"` de `PUBLICAS`.

## 7. Archivos tocados
**Nuevos:**
- `domiciliarios/`:
  - `models.py`, `admin.py`, `apps.py`, `bandera.py`, `intensivo.py`, `balance.py`, `comprobante.py`, `forms.py`, `views.py`, `urls.py`, `tests.py`
  - `migrations/0001_initial.py`
  - `templatetags/domiciliarios_tags.py`
  - `templates/domiciliarios/` (5 plantillas)
  - `static/domiciliarios/dm.css`
  - `management/commands/demo_domiciliarios.py`
- `informes_noche/plus-domiciliarios.md` y `informes_noche/plus-domiciliarios/mi-ruta-celular.png`

**Modificados** (pocas líneas cada uno):
- `config/settings.py`
- `config/urls.py`
- `config/tests_seguridad.py`
- `garaje/templates/garaje/garaje.html`
- `garaje/templates/garaje/moto.html`
