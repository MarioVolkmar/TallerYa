# Talleres demo completos — informe (15-nov-2026)

Objetivo: dos perfiles de taller que se vean como talleres reales de TallerYa, dentro de los datos demo (`cargar_demo`; en producción se apaga con `CARGAR_DEMO=0`).

## Los dos talleres (ficticios)
| | **Taller Doble Leva** | **Torque Sur Motos** |
|---|---|---|
| Lugar | Cra 76 # 30A-45, Belén Rosales (Medellín) | Cl 38 Sur # 44-15, Centro (Envigado) |
| Perfil | Motos de trabajo y scooters ≤200 cc · $ Económico · destacado | Media y alta cilindrada · $$ Intermedio · emergencias y despinche a domicilio |
| Horario | Lun-Vie 8-18, Sáb 8-14 (franjas en `HorarioTaller`) | Lun-Sáb 7:30-18:30 |
| Mecánicos (en la descripción) | Jhon Fredy (jefe, inyección), Yésica (frenos/arrastre), Mateo (scooters/CVT) | Andrés Felipe (jefe, KTM/Bajaj), Luisa Fernanda (eléctrico), Camilo (suspensiones) |
| Marcas | AKT, Bajaj, Honda, Yamaha, Suzuki, TVS | KTM, Bajaj, Yamaha, Honda, Suzuki, Hero |
| Galería | portada, 4 fotos y 1 video (11 s) | portada, 4 fotos y 1 video (19 s) |
| Reseñas | 6 (5,5,4,5,3,5), 3 con respuesta del taller | 5 (5,4,5,2,5), 2 con respuesta |
| Cupón | Pre-revisión técnico-mecánica gratis con el cambio de aceite (60 días, 40 cupos) | 10 % en kit de arrastre de 150-400 cc (45 días, 30 cupos) |

- Los nombres se buscaron en la web el 15-nov-2026 y no aparecen negocios con esos nombres en Medellín ni en Envigado. Las direcciones son plausibles pero inventadas. El WhatsApp es el mismo número de prueba (`573000000000`) de los demás talleres demo, para no usar el número de alguien real.
- Cada taller tiene una cuenta `<clave>.demo@tallerya.local` sin contraseña utilizable, así que su panel se ve solo entrando desde el admin.
- **Citas y servicio hecho** (solo si existen las motos de la cuenta demo del garaje, o sea con DEBUG):
  - En Doble Leva: 3 citas (hoy, mañana y en 3 días).
  - En Torque Sur: 3 citas (hoy, en 2 días y una atendida hace 6 días).
  - Por cada moto de Sofía, una cita atendida con su servicio registrado y verificado por `garaje.servicio_taller.crear`:
    - NKD 125 en Doble Leva: aceite y filtro de aire más cadena, $165.000.
    - NMAX 155 en Torque Sur: aceite y aceite de transmisión, $98.000.
  - Esos servicios alimentan la hoja de vida y el plan de cada moto.

## Precios (COP, mano de obra más repuestos típicos)
| Servicio | ≤150 cc | 150-400 cc | >400 cc |
|---|---|---|---|
| Cambio de aceite (aceite incluido) | 38-60 mil | 70-130 mil | 170-290 mil |
| Kit de arrastre instalado | 140-240 mil | 280-520 mil | 650 mil-1,3 M |
| Frenos (pastillas delanteras instaladas) | 45-75 mil | 80-150 mil | 180-340 mil |
| Sincronización (bujía, filtro, limpieza inyector/carburador, válvulas) | 110-170 mil | 180-320 mil | 380-650 mil |
| Suspensión (barras: aceite y retenes) | — | 170-280 mil | 320-520 mil |
| Pre-revisión técnico-mecánica | 30-50 mil (cualquier cc) | | |
| Diagnóstico eléctrico | 40-70 mil (cualquier cc) | | |

Doble Leva publica la parte baja de cada rango y Torque Sur la media y alta.

**Criterio**: no encontré listas públicas de talleres de motos de Medellín para 2026. Partí de referencias de mercado de 2024-2025 (precio del aceite de 1 L para baja cilindrada y de 3-4 L sintético para alta; kits AKT/Bajaj genéricos frente a kits de marca) y les sumé la subida de los servicios de mantenimiento: +10,34 % anual a julio de 2026, según [El Colombiano](https://www.elcolombiano.com/inicio/llevar-el-carro-al-mecanico-esta-mas-caro-CE41017401).

La pre-revisión no incluye la tarifa del CDA, que en 2026 va de unos $218.000 a $247.000 para motos según [elcarrocolombiano](https://www.elcarrocolombiano.com/?p=306181) y [grupor5](https://www.grupor5.com/blog/movilidad/revision-tecnico-mecanica).

Son rangos orientativos: conviene que un mecánico real los revise. No afectan las medianas públicas de precios, porque esas exigen 3 o más talleres de Medellín.

## Fotos y videos
- Todo viene de **Pexels**, con licencia libre para uso comercial y sin atribución. Elegí material sin caras reconocibles en primer plano y sin logos.
- La URL de cada archivo está en `talleres/demo/fuentes.txt`.
- Las fotos están en WebP calidad 72, de máximo 1600 px y de 42 a 132 KB cada una. Los videos son la versión SD de Pexels (640 px, 0,99 y 1,15 MB) y cada uno tiene su póster en WebP.
- `talleres/demo/` pesa unos 3 MB y va en el repo, para que el demo funcione desplegado. `cargar_demo` copia los archivos al almacenamiento de medios.
- No hay ffmpeg en este equipo, así que los videos no se recomprimieron. Ya son livianos.

## Video en el perfil (nuevo)
- `FotoTaller.video` (FileField) e `imagen` ahora opcional, que hace de póster. Migración `talleres/0017_video_galeria.py`.
- En **Editar perfil** hay un campo "Agregar un video corto": MP4/WEBM de máximo 20 MB, hasta 2 videos, que cuentan dentro de las 8 fotos. Si no tiene póster se ve el primer cuadro.
- En el **detalle** la miniatura muestra ▶ y el visor reproduce el video con controles; se pausa al cerrar. Usa `preload="metadata"`/`none` y `loading="lazy"` en las fotos.
- El admin también tiene el campo de video.
- Archivos tocados:
  - `talleres/models.py`, `admin.py`, `views.py` (editar_perfil y eliminar_foto).
  - Plantillas `detalle.html` (miniaturas y visor; ya tenía cambios de otra sesión, solo hice reemplazos puntuales), `editar_perfil.html` y la nueva `_galeria_medio.html`.
  - Unas líneas al final de `tallerya.css`.

## Archivos nuevos
`talleres/demo_talleres.py` (datos y carga, idempotente), `talleres/demo/` (12 imágenes, 2 videos, `fuentes.txt`), `talleres/tests_demo.py` (5 pruebas), migración `0017`. `cargar_demo.py` llama a `demo_talleres.cargar()` al final. Se agregan los servicios "Kit de arrastre" y "Sincronización" a la lista general, porque hacían falta para publicar esos precios.

## Verificación
- Con el cliente de pruebas sobre la base local:
  - El detalle de los dos talleres responde 200, con video, mecánicos, precios y reseñas.
  - `/mi-taller/`, `/mi-taller/servicios/` (2 servicios verificados) y `/mi-taller/citas/` responden bien con cada cuenta.
  - Los dos talleres salen en el directorio y en las páginas SEO por servicio (`/talleres/servicio/kit-de-arrastre/`, `/sincronizacion/`). Doble Leva sale en `/talleres/en/belen/`.
- No hay captura: el panel del navegador estaba oculto y trabado en la revisión del sitio. Falta mirarlo a 360 px.

## Pendiente / a decidir
- **Base local**: `cargar_demo` falla antes de llegar a esta parte porque hay **dos cupones con el título "$20.000 de descuento en cualquier taller aliado"** (`get_or_create` → `MultipleObjectsReturned`). No es de este cambio. Hay que borrar uno en el admin o cambiar ese `get_or_create` por `filter().exists()`. Los talleres se cargaron llamando `demo_talleres.cargar()` directamente.
- Mecánicos y especialidades van en la descripción, porque el perfil no tiene campos propios para eso. Si se quieren como fichas, haría falta un modelo nuevo.
- Antes de lanzar, que un mecánico revise los precios.

## Pruebas
Suite completa: **534 pruebas, todas OK** (43 s). Pruebas nuevas: `talleres.tests_demo`, que cubre la carga idempotente, el servicio verificado en las motos demo, la subida de video, el rechazo de formatos que no sirven y el máximo de videos.

## Seguimiento (cargar_demo robusto)
- `primero_o_crear()` en `talleres/demo_talleres.py` reemplaza los `get_or_create` de cupones, talleres y barrios de `cargar_demo`. Si hay repetidos usa el primero y nunca borra nada.
- Causa del "duplicado": `cargar_cupones_puntos` crea a propósito un cupón por puntos con el mismo título que el premio por referidos.
- Prueba nueva: `ComandoCargarDemoTests` corre el comando dos veces con cupones repetidos del usuario. Las 6 pruebas de `talleres.tests_demo` pasan.
- `cargar_demo` ya se corrió en la base local y los dos talleres quedaron cargados.
- La captura a 360 px sigue pendiente: el panel del navegador está oculto y rechaza la navegación.

## Rediseño del detalle del taller (aprobado por el usuario)
- **Orden nuevo**:
  1. Cabecera: verificado, nombre, ★ nota y número de reseñas, barrio, «Abierto ahora · cierra a las…» o «Cerrado · abre…» (calculado con los turnos de la agenda), descripción corta, y botones Pedir cita / WhatsApp / Llamar.
  2. **Precios desde**: tabla corta con una fila por servicio y una columna por cilindraje publicado. Tocar el servicio abre la cita con ese servicio elegido. Los servicios sin precio salen como chips.
  3. Franja de fotos de una fila con «Ver las N fotos».
  4. Quiénes te atienden.
  5. Especialidades, marcas y Cómo trabajamos.
  6. Cupones.
  7. Reseñas.
  8. Ubicación con mapa.
- Se quitó la sección repetida «03 Fotos» y la portada en mosaico.
- Las leyendas ya no van sobre las miniaturas: salen solo en el visor, pequeñas y debajo, con «n de N».
- **Campos estandarizados** (migración `talleres/0018_perfil_estandarizado.py`):
  - `equipo`: lista de nombre, rol, años y especialidad; máximo 6.
  - `especialidades`: claves de una lista cerrada de 14 en `talleres/perfil.py`.
  - `garantia_meses`.
  - `compromisos`: 5 casillas.
  - `descripcion`, que pasa a máximo 300 caracteres en el formulario. No hay límite en la base, así que nada se recorta.
- **Panel → Editar perfil**:
  - Indicador «Perfil completo», que ahora también cuenta precios, equipo, especialidades y garantía o compromisos.
  - Contador de la descripción.
  - Filas del equipo.
  - Casillas de especialidades y compromisos, y selector de garantía.
  - Un POST sin el equipo no lo borra.
- **SEO**:
  - El JSON-LD agrega `knowsAbout` (especialidades y marcas), `employee`, `makesOffer` (precio mínimo por servicio en COP) y la garantía como `amenityFeature`.
  - La meta descripción menciona las especialidades y la garantía.
- **Demo**:
  - Los dos talleres ya usan los campos nuevos.
  - `completar_perfil()` llena solo los campos vacíos de un taller ya cargado y cambia la descripción larga vieja por la corta. Ya se aplicó en la base local.
- Un taller sin estos datos se ve bien: las secciones vacías no aparecen y la numeración se ajusta.
- **Pruebas**:
  - `talleres/tests_perfil.py` (7 pruebas nuevas).
  - Se ajustaron 2 pruebas viejas de `talleres/tests.py`, porque ahora el perfil muestra solo el «desde» y la franja reemplaza la galería.
  - Suite completa: **547 OK**.
- **Sin captura**: el panel del navegador sigue rechazando la navegación. Lo verifiqué con el cliente de pruebas: orden de las secciones, JSON-LD, taller sin datos y formulario.
- En el celular, la tabla de precios se desplaza sola dentro de su tarjeta si no cabe; la página no se desplaza de lado.
