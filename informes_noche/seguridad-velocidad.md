# Seguridad y velocidad — revisión de la noche (15-nov-2026)

Sin commit. Archivos tocados: `cuentas/limites.py` (nuevo), `cuentas/forms.py`, `cuentas/views.py`, `cupones/views.py`,
`talleres/views.py`, `tramites/forms.py`, `tramites/tests.py`, `config/settings.py`, `foro/rodadas.py`, `garaje/models.py`,
`garaje/views.py`, `garaje/plan.py`, `garaje/gastos.py`.
Pruebas nuevas: `cuentas/tests_seguridad.py` (7), `foro/tests_velocidad.py` (4) y `garaje/tests_velocidad.py` (2).
Suite completa: 460 pruebas OK (antes de la 2.ª tanda de garaje; después, garaje + notificaciones: 212 OK).

## 1. Seguridad

### Corregido (con prueba)
| Gravedad | Hallazgo | Arreglo |
|---|---|---|
| Alta | **Login sin límite de intentos**: se podía probar contraseñas sin freno. | `EntrarForm.clean`: 10 fallos por correo o 30 por IP en 15 min bloquean (aunque luego llegue la clave buena). Entrar bien limpia el contador del correo. |
| Alta | **IP real tras el proxy de Render**: el freno del canje de cupones usaba `REMOTE_ADDR`, que en Render es la IP del proxy (la misma para todos): 8 fallos de cualquiera bloqueaban el canje a todo el mundo 15 min. | `cuentas/limites.ip_cliente`: lee `X-Forwarded-For` desde la derecha según `PROXIES_DE_CONFIANZA` (1 si existe la variable `RENDER`, 0 en local). Lo que el cliente inventa a la izquierda se ignora. |
| Media | **Reseñas anónimas ilimitadas** en la ficha del taller: cualquiera inflaba o hundía la nota en segundos. | Máximo 3 reseñas por hora por taller y persona (cuenta o IP); citas, 5 por hora. |
| Media | **El dueño podía reseñar su propio taller** (ficha y "Calificar" en Mi cuenta). | Bloqueado en ambos sitios. |
| Baja | Tarjeta de propiedad (pedido de SOAT) solo se validaba por extensión. | Ahora también por contenido (JPG/PNG/WEBP/PDF/HEIC). La prueba existente se ajustó a un JPG con firma real. |

### Revisado sin problemas
- **XSS**: `menciones.renderizar` escapa todo el texto y arma los enlaces con `format_html`; los `|safe` y `mark_safe`
  restantes son SVG/QR propios o `help_text` del código. JSON en plantillas con `json_script`/`escapejs`. Sin `autoescape off`.
- **CSRF**: todas las acciones POST con el middleware; la única exenta es `/tareas/<nombre>/` (token Bearer ≥20
  caracteres, `hmac.compare_digest`, lista cerrada de comandos, 404 sin token).
- **IDOR**: motos, documentos, mantenimientos, "Poner al día", citas del motero (`_base(request.user)`), citas,
  reseñas, cupones y fotos del taller (`taller=request.user.taller`), pedidos SOAT (`moto__motociclista`) filtran por dueño.
  Editar/eliminar del foro exige `autor=request.user`; marcar mejor respuesta, `pregunta__autor`.
- **Documentos**: fuera de `MEDIA_ROOT` (`PRIVADO_ROOT`, sin URL pública), nombre aleatorio, 5 MB, extensión + firma,
  se entregan con `nosniff` y `no-store` solo al dueño; se borran del disco al cambiar el archivo o eliminar la moto.
- **Integrante**: solo nombre público, conteos y publicaciones visibles; nunca correo ni celular. El autocompletado de @ tampoco.
- **settings**: `DEBUG` lo apaga `render.yaml` (`DJANGO_DEBUG=0`); sin `DEBUG`, falta `SECRET_KEY` → error. Cookies
  seguras, SSL, HSTS y nosniff en producción.

### Pendiente / dudoso (no tocado)
1. **Confirmar `PROXIES_DE_CONFIANZA=1` en Render**: si Render pone más de un salto en `X-Forwarded-For` (p. ej. Cloudflare +
   balanceador), la IP leída sería la del proxy y el freno por IP volvería a ser global. Revisar el encabezado en el primer
   despliegue y ajustar la variable. El freno por correo del login no depende de esto.
2. `DEBUG` vale `True` si falta `DJANGO_DEBUG`: seguro con `render.yaml`, pero un despliegue manual sin la variable quedaría
   en modo depuración. Propuesta: valor por defecto `False` fuera de local (cambia el arranque local; decidirlo el usuario).
3. Recuperar contraseña (`PasswordResetView`) sin límite: permite mandar muchos correos a una dirección ajena.
4. Votar, reaccionar y editar en el foro no tienen límite por hora (votos y reacciones se alternan sin avisos repetidos;
   editar puede sumar menciones nuevas, máx. 10 por versión). Bajo riesgo.
5. Reportes: 3 cuentas distintas ocultan cualquier publicación (diseño); con cuentas falsas se puede abusar. Con Google/correo
   verificado es más difícil; anotar para moderación.
6. HSTS de 1 hora y sin `includeSubDomains`: subirlo cuando el dominio sea definitivo.
7. `RIFF` se acepta como firma de imagen (WEBP) pero no comprueba que sea `WEBP`; solo afecta al propio dueño.

## 2. Velocidad

Medido con `CaptureQueriesContext` sobre `db.sqlite3` (Client de pruebas, mejor de 3, en una transacción que se deshace;
script en el scratchpad de la sesión). Los ms son orientativos: la máquina tenía otras sesiones trabajando y variaban
±50 % entre corridas; las consultas son exactas.

| Página | Consultas antes | Después | ms antes | ms después |
|---|---|---|---|---|
| Portada (anónimo) | 13 | 13 | 75 | 51 |
| Portada (con sesión) | 19 | 19 | 62 | 47 |
| Mi garaje (5 motos) | 30 | 10 | 91 | 18 |
| Detalle de moto | 34 | 30 | 216 | 67 |
| Foro: lista | 5 | 5 | 84 | 55 |
| Pregunta larga (31 resp.) | 14 | 14 | 349 | 136 |
| Rodadas | 4 | 3 | 48 | 16 |
| Rodada (asistentes) | 21 | 15 | 80 | 51 |
| Talleres | 12 | 11 | 55 | 43 |
| Detalle de taller | 14 | 14 | 54 | 41 |

Cambios: asistentes de la rodada con `usuario__perfil` (quita 1 consulta por asistente para el avatar); Rodadas y Talleres
cuentan sus pestañas/estadísticas con un solo `aggregate`; `Despiece.para` se recuerda en la moto durante la petición
(la ficha lo pedía 3 veces). 2.ª tanda (con `garaje/views.py` ya libre): Mi garaje carga una vez las tareas activas,
precarga mantenimientos, ajustes y lecturas de todas las motos y elige sus catálogos de despiece en una consulta
(`Despiece.precargar`), así que ya no crece con las motos; la ficha precarga los ajustes (plan + agenda) y Gastos lee las
lecturas una vez (`gastos._puntos`). `garaje/tests_velocidad.py` lo comprueba con `assertNumQueries`. El foro, la portada y los talleres ya estaban sin N+1.
`foro/tests_velocidad.py` comprueba con `assertNumQueries` que pregunta en hilo, lista del foro, rodada, Rodadas, portada,
Talleres y ficha del taller hacen las mismas consultas con 1 elemento que con muchos.

### Pendiente (velocidad)
- **Pregunta larga**: lo caro no es SQL sino la plantilla (≈300 `include` y 240 `{% url %}` para 31 respuestas). Mejora
  posible: precalcular las URL por respuesta en la vista o usar `{% include ... only %}`; no lo toqué porque
  `foro/templates/foro/pregunta.html` y `rodada.html` tienen cambios sin commit de otra sesión.
- **Ficha de la moto (30 consultas)**: ya no hay consultas repetidas por elemento; quedan consultas distintas una sola
  vez cada una (hoja de vida, gastos, pico y placa, talleres sugeridos, despiece). Bajarlas más pide reorganizar la vista.
- Plantillas del foro: siguen sin tocar (la sesión de celular puede estar en ellas).
- No añadí caché de fragmentos: lo estable (barrios, servicios) son consultas de <1 ms; cachearlo retrasaría altas sin ganancia.
