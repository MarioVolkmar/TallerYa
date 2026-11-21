# Piloto · Paso 2: kilometraje fácil

Estado: hecho, sin commit. Suite rápida: 847 pruebas OK. Pruebas nuevas: `garaje/tests_kilometraje.py` (11).

## Qué hace
- **Perfil de uso** (campo opcional «¿cómo la usas?» en el formulario de la moto): fines de semana 9, ciudad 25, trabajo/domicilios 70, carretera 45 km/día. Es el ritmo inicial (`plan._ritmo_perfil`), después de registro/matrícula y antes del supuesto por año del modelo. Con ≥2 lecturas (≥7 días) manda el ritmo real, como antes.
- **Km estimado + confirmación de un toque**: en la tarjeta del odómetro, «¿Vas por unos 8.400 km?» Sí / Corregir (ancla al campo de km) / Ahora no (se calla 7 días). Sale si la última lectura tiene ≥30 días y hay ritmo. «Sí» crea `LecturaKm(estimada=True)`; el servidor valida que el km suba y sea creíble.
- **Taller**: ya creaba lectura al verificar un servicio; ahora pasa por `registrar_lectura` (reutilizable para el paso 3) y recalibra el ritmo.
- **Recordatorios del plan**: cada tarea pendiente (`_tarea.html`) cierra con «Cotizar con un taller cercano» (directorio filtrado por servicio) y «Pedir mecánico a domicilio» (listado de domicilio, filtrado si el servicio existe con ese nombre).

## Archivos
Nuevos: `garaje/kilometraje.py`, `garaje/tests_kilometraje.py`, `garaje/migrations/0038_perfil_uso_y_lecturas_estimadas.py` (Moto.perfil_uso, Moto.km_pregunta_pospuesta, LecturaKm.estimada).
Editados: `garaje/models.py`, `plan.py`, `forms.py`, `views.py` (`confirmar_km`, `_url_domicilio`, contexto `pregunta_km`), `urls.py`, `servicio_taller.py`, plantillas `moto.html`, `_tarea.html`, `form_moto.html`, `talleres/static/talleres/css/secciones/garaje.css`, `cotizador/tests.py` (la prueba buscaba «Cotizar» suelto; ahora busca las frases del cotizador de repuestos).

## UX (revisar-ux manual con Chrome sin ventana, base temporal)
1280 y 375 px: sin desbordes, todos los toques ≥44 px, mismos componentes (btn-lava, btn-borde). Capturas: `km_375.png`, `km_1280.png` (pregunta), `km_cta_375.png`, `km_cta_1280.png` (botones).
Pendiente/ojo: el selector de perfil usa el estilo genérico de campo; no se probó la pantalla de registro en captura. Las cifras km/día por perfil son supuestos a validar con moteros.
