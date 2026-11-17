---
name: revisar-seguridad
description: Revisión de seguridad y velocidad de TallerYa antes de desplegar o tras cambios grandes (OWASP Top 10, ASVS nivel 2, checklist de despliegue de Django). Corre revisar.py (config de producción, cabeceras y CSP, patrones de XSS/CSRF/SQL/IDOR en el código, secretos en el repo y el historial, dependencias, pruebas de autorización, consultas y ms de las páginas principales, peso de estáticos) y guía lo que pide criterio humano. Úsala cuando pidan "revisar seguridad", "antes de desplegar", "auditoría", "¿es seguro?", "¿por qué está lento?" o tras agregar vistas, modelos, subidas de archivos o JS nuevo.
---

# Revisar seguridad y velocidad (TallerYa)

Barata y repetible: el script hace lo mecánico (~1 min) y tú solo miras lo que sale en **FALLA** o **AVISO** y lo que
abajo pide criterio. No leas el código entero: ve directo al archivo:línea de cada hallazgo.

## 1. Correr el script

```bash
venv/Scripts/python.exe .claude/skills/revisar-seguridad/revisar.py --sin-red
```
- Sin `--sin-red` también corre `pip-audit` y `npm audit` (únicas comprobaciones que consultan internet: solo mandan
  nombres y versiones de paquetes a las bases de vulnerabilidades). `pip-audit` hay que instalarlo una vez en el venv
  (`venv/Scripts/pip install pip-audit`; está en requirements-dev.txt).
- `--solo config,cabeceras,codigo,secretos,dependencias,autorizacion,velocidad,estaticos` para una parte.
- Sale con código 1 si hay alguna FALLA. Nunca imprime secretos (solo archivo:línea o commit·archivo).
- `velocidad` guarda `ultima_velocidad.json` (junto al script): cópialo antes de optimizar para comparar después.
- Nada se prueba contra servicios externos ni fuera de localhost: las páginas se piden con el test client de Django
  con la configuración de producción (DEBUG=0, SECRET_KEY aleatoria) dentro de una transacción que se deshace.

Qué hace cada sección:
| Sección | Comprueba |
|---|---|
| config | `check --deploy` con settings de producción; DEBUG, cookies Secure/HttpOnly/SameSite, HSTS, X-Frame, MD5, SECRET_KEY en código, `.env.example` completo |
| cabeceras | HSTS, X-Frame-Options, nosniff, Referrer-Policy, COOP, Permissions-Policy, CSP (y si es débil), HTTP→HTTPS, flags de cookies |
| codigo | `\|safe`, `mark_safe`, `autoescape off`, `innerHTML`, `csrf_exempt`, SQL crudo, `eval`, `pickle`/`yaml.load`, `shell=True`, redirecciones con `next` sin validar, CDN sin SRI, campos de archivo, objetos por `pk` sin dueño, `fetch` POST sin CSRF |
| secretos | claves en archivos rastreados y en todo el historial de git; que lo local (`despiece_local/`, `manual_despiece/`, `planos_a_generar/`, `privado/`, `media/`, `db.sqlite3`, `.env`) no esté en git y esté en `.gitignore` |
| dependencias | `pip-audit -r requirements.txt` y `npm audit` |
| autorizacion | corre `config/tests_seguridad.py` (IDOR de cada vista con `<pk>`, barrido anónimo de todas las URL, consola solo staff, frenos de intentos, subidas) y `cuentas/tests_seguridad.py` |
| velocidad | ms (mejor de 3), consultas SQL y KB de las páginas principales, anónimo, motero y taller; avisa >300 ms o >35 consultas |
| estaticos | WhiteNoise con manifest, GZip, `tw.css` purgado, estáticos pesados, 3D/despiece fuera de `base.html`, `<img>` sin `loading`, fotos grandes en `media/` |

## 2. Tratar lo que sale

- **Hallazgo real** → arreglar con prueba (en `config/tests_seguridad.py` si es de autorización/entradas, o junto a la app).
- **Falso positivo o ya revisado** → una línea en `permitidos.txt` (`ruta|patrón|motivo y fecha`). No silencies una
  categoría entera: ruta lo más concreta posible.
- **Vista nueva con `<pk>`** → súmala a `IdorTests._casos()`; **página pública nueva** → a `PUBLICAS`. El barrido anónimo
  falla a propósito si aparece una URL que responde 200 sin sesión y no está en la lista.
- Severidad: **crítica** = toma de cuentas, datos de todos, ejecución de código; **alta** = datos o acciones de otra
  persona, pago sin pagar, XSS almacenado; **media** = abuso a escala (sin freno), fuga menor, defensa en profundidad que
  falta; **baja** = endurecimiento.
- Lo que cambie la experiencia o pida decisión (política de contraseñas, CSP con nonces, dependencias nuevas, HSTS
  largo) se **propone** en el informe; no se aplica sin el usuario.

## 3. Criterio humano (lo que el script no ve)

Mira solo lo que cambió desde la última revisión (`git diff --stat <commit de la revisión anterior>`).
1. **Autorización por objeto**: en cada vista nueva, ¿el queryset filtra por `request.user` (o `taller=request.user.taller`,
   `moto__motociclista=...`)? ¿Los POST cambian solo lo propio? ¿Las acciones de staff usan `solo_admin` / `staff_member_required`?
2. **Lógica de negocio**: pagos (Plus, SOAT: `SOAT_PAGO_SIMULADO` apagado en producción), cupones (PIN y frenos), citas
   (estados válidos), reseñas (no a uno mismo, límite por hora), códigos de un solo uso, cosas que se puedan repetir.
3. **Subidas**: contenido real (firma + Pillow, como `talleres/subidas.py`), tamaño, nombre aleatorio; lo privado fuera de
   `MEDIA_ROOT`; `/media/` solo entrega imágenes y videos (`config/urls.py: servir_media`).
4. **XSS**: texto de usuarios siempre con autoescape o `textContent`; JSON hacia JS con `json_script`; nada de `|safe` sobre
   datos de la base.
5. **Cuentas**: enumeración (registro dice "ya existe": mitigado con freno por IP), frenos en login/admin/recuperar/registro,
   verificación de correo antes de acciones sensibles, Google OAuth con `state` + PKCE + `email_verified`.
6. **CSP**: si se agregó un script/estilo/iframe de otro dominio, súmalo en `config/cabeceras.py` y comprueba en el navegador
   (consola: "Content Security Policy") las páginas afectadas. 3D y despiece requieren sesión.
7. **Velocidad**: en una vista nueva con listas, `select_related`/`prefetch_related` y una prueba con `assertNumQueries` o
   comparando 1 vs N elementos (ver `cuentas/tests_velocidad.py`, `garaje/tests_velocidad.py`).
8. **Despliegue (Render)**: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` generada, `DJANGO_ALLOWED_HOSTS` y
   `DJANGO_CSRF_TRUSTED_ORIGINS` con el dominio, `PROXIES_DE_CONFIANZA` correcto (mirar `X-Forwarded-For` real),
   `REDIS_URL` si hay más de un proceso (los frenos viven en la caché), `CARGAR_DEMO=0` en producción real, discos para
   `DJANGO_MEDIA_ROOT` y `DJANGO_PRIVADO_ROOT`.

## 4. Informe

Escribe/actualiza `informes_noche/revision-seguridad-velocidad.md`: tabla por hallazgo (severidad, dónde, cómo se explota
o por qué es lento, arreglo, estado), lo propuesto sin aplicar y la tabla de velocidad antes/después. Corre la suite
rápida (`manage.py test --exclude-tag=lenta -v 1`) tras los arreglos y la completa antes de desplegar.
