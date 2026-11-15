# Primer uso guiado (guía de bienvenida)

## Qué hace
Quien tiene perfil de motociclista, **no tiene motos** y **no ha terminado ni saltado la guía** cae en ella al:
- registrarse con correo (`cuentas:registro`, si no trae `?next=`),
- terminar «Completar perfil → motero» tras crear la cuenta con Google,
- volver con Google a una cuenta existente sin motos,
- entrar con correo y contraseña sin `?next=` (nueva `EntrarView`).

Un `?next=` válido siempre gana (p. ej. venía de reclamar un cupón).

## Los 4 pasos (indicador arriba, «Saltar guía» en los pasos 1–3)
1. **Tu moto** y 2. **Último mantenimiento**: el mismo formulario de «Agregar moto» con `?guia=1`
   (`garaje.views.agregar`): mismo selector de marca/línea, año, km y las opciones Hace poco / A los … km / No sé / Sin idea.
   En modo guía: título de bienvenida, sin la sección de documentos (va en el paso 4) y el botón final dice «Ver mi plan».
   Sin JavaScript, «Siguiente» guarda directo y sigue al paso 3.
2. **Tu plan** (`/bienvenida/<pk>/`): la moto en 3D (iframe de `garaje:vista_3d`, como en la portada) y «Lo urgente»
   (o «Todo al día · Lo que viene»), más un aviso de cuántos mantenimientos quedaron sin registro.
3. **Qué más** (`/bienvenida/<pk>/listo/`): tarjetas a guardar fechas de SOAT/técnico (editar moto), SOAT y CDA,
   talleres filtrados por la marca de su moto y foro/rodadas. Llegar aquí marca la guía como vista.

«Saltar guía» (`POST /bienvenida/saltar/`) la marca como vista y lleva a su moto o al inicio. Si vuelve a `/bienvenida/`
con moto ya creada, va directo al paso 3.

## Archivos
- `cuentas/models.py`: `Perfil.guia_terminada` + migración `cuentas/0005_perfil_guia_terminada.py`
- `cuentas/guia.py` (nuevo): `pendiente`, `marcar_vista`, `destino`
- `cuentas/views.py`: redirecciones de registro, Google, completar; `EntrarView`. `cuentas/urls.py`: usa `EntrarView`
- `garaje/vista_bienvenida.py` (nuevo), `garaje/urls.py` (4 rutas)
- `garaje/views.py`: bandera `guia` en `agregar`; el armado de «Lo urgente»/«Todo al día» pasó a `resumen_plan(plan)`
  (lo usan el detalle de la moto y la guía; sin cambio de comportamiento)
- Plantillas: `garaje/bienvenida.html`, `garaje/_pasos_guia.html` (nuevas), `garaje/form_moto.html` (modo guía)
- CSS al final de `tallerya.css` (bloque «Guía de bienvenida»); `npm run css` corrido
- Pruebas: `garaje/tests_bienvenida.py` (nuevo, 7); ajustadas 5 en `cuentas/tests.py` que esperaban el destino viejo

## Verificación
- Pruebas: guía + cuentas + GarajeTests (70) OK; suite completa al final (ver resultado en el mensaje a Auxiliares).
- 360 px: sin scroll horizontal; en celular el indicador muestra solo el nombre del paso actual (números en los demás).
  Paso 3 visto en el navegador; el iframe 3D usa `color-scheme: normal` y `pointer-events: none` (fondo transparente y
  no atrapa el scroll), igual que la portada.
- Los pasos 1–2 y 4 se verificaron con el cliente de pruebas, no en el navegador: la sesión del navegador era la cuenta
  real del usuario (5 motos) y no quise cerrarla ni escribir en ella.

## Pendiente / ideas
- No se tocó `base.html` ni la portada. Si se quiere, la portada podría mostrar «Termina tu bienvenida» a quien saltó la
  guía y sigue sin motos (hoy simplemente no vuelve a salir, como se pidió).
- El paso 1 usa el selector nativo con grupos por marca; el combobox con búsqueda del diagnóstico (`diag_buscador.js`)
  está atado a los ids de esa página. Reusarlo en el alta sería una mejora aparte.
