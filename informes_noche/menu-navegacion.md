# Menú y navegación de TallerYa (18-nov-2026)

Reorganización de `templates/base.html` según la propuesta aprobada. Sin commit.

## Antes
- **Escritorio (motociclista):** unos 10 elementos en una sola barra: Talleres · A domicilio · Cupones · Foro · Diagnóstico · Papeles ▾ · Mi garaje · Mi ruta · ¿Te varaste? · | · Plus · avatar · campana. Un script la iba compactando y, si no cabía, la pasaba a menú hamburguesa.
- **Visitante:** lo mismo, más Entrar y Crear cuenta (veía «Mi garaje», que lo mandaba al inicio de sesión).
- **Taller:** Talleres, A domicilio, Cupones, Foro, Validar cupón, Plus y la cápsula con su nombre (llevaba al panel).
- **Celular:** botón «Menú» (`<details>`) con una lista larga de unos 15 enlaces; no había barra inferior.
- Diagnóstico como entrada principal; en la portada no tenía un acceso propio.

## Después
- **Motociclista:** 4 entradas: **Talleres ▾** (directorio, mecánicos a domicilio) · **Mi garaje ▾** (mis motos, ¿Qué le pasa a tu moto?, SOAT, técnico-mecánica (CDA) y Mi ruta solo con Ruta activo y `DOMICILIARIOS_ACTIVO`) · **Comunidad ▾** (foro, rodadas) · **Cupones**. A la derecha, fijos: **¿Te varaste?** (rojo), la campana y el **avatar con menú** (Mi cuenta, Plus, Mis insignias, Mi ruta si aplica, Instalar app y Salir).
- **Taller:** Panel · Citas · Validar cupón · Mi perfil, más la campana y el avatar (panel, perfil, agenda, instalar app, salir).
- **Visitante:** Talleres ▾ · Comunidad ▾ · **Diagnóstico** · ¿Te varaste? · Entrar · Crear cuenta. El diagnosticador abre sin sesión y sirve de gancho para probar la página antes de registrarse (pedido del usuario tras revisar el menú). En el celular, la barra inferior del visitante es Inicio, Talleres, Diagnóstico, Comunidad y Emergencia, y «Entrar» sube a la cabecera junto a Crear cuenta (58×44 px y 131×44 px a 375 px, sin desborde).
- **Staff:** sigue con su cabecera corta (Consola, Usuarios, Talleres, Moderación, Ver sitio y Admin técnico solo para superusuarios), y además Consola en el menú del avatar. No lleva barra inferior.
- **Celular (< 1024 px):** arriba solo el logo, la campana y el avatar (44×44 px). Abajo, una **barra fija** de 5 botones con ícono y texto (73×60 px a 375 px): Inicio, Talleres, Mi garaje, Comunidad y Emergencia. Al visitante le sale Diagnóstico en lugar de Mi garaje, y el taller tiene la suya: Inicio, Panel, Citas, Validar y Mi perfil. El body reserva el alto de la barra más `env(safe-area-inset-bottom)`. Chispa, «Instalar app» y los avisos flotantes suben para quedar encima de la barra. Los diálogos (z ≥ 60) la tapan, porque la barra está en z 45. Lo demás (cupones, a domicilio, diagnóstico, SOAT, CDA y rodadas) va en el menú del avatar, en el grupo «Más de TallerYa».
- **Accesibilidad:** los submenús se abren con clic o teclado, sin hover (`talleres/static/talleres/js/menu.js`). Usan `aria-expanded` y `aria-controls`; las flechas recorren los enlaces, Escape cierra y devuelve el foco al botón, y el clic o el foco fuera también cierran. La sección activa lleva `aria-current="true"` en el botón y `aria-current="page"` en el enlace exacto. La lógica está en `talleres/templatetags/navegacion.py` (`seccion_activa`). Se conserva «Saltar al contenido».
- **Diagnóstico:** nueva tarjeta «¿Qué le pasa a tu moto?» en la portada, en la sección Papeles (`data-diag-portada`). La página de la moto y Emergencias ya tenían su acceso, así que no se duplicó. También sigue en el pie.

## Archivos
- `templates/base.html` (cabecera, barra inferior y carga de `menu.js`) · `talleres/templatetags/navegacion.py` (nuevo) · `talleres/static/talleres/js/menu.js` (nuevo).
- `talleres/static/talleres/css/tallerya.css`: bloque nuevo al final, «Navegación por secciones». Se recompiló `tw.css` con `npm run css`.
- `talleres/templates/talleres/inicio.html`: tarjeta de diagnóstico. Ojo: la portada es zona de la sesión «Proyecto tallerYa»; el cambio es pequeño y está marcado con un comentario.
- Pruebas: `talleres/tests_navegacion.py` (nuevo, 11 pruebas: menú por rol, Mi ruta con y sin bandera o perfil, barra inferior, sección activa, saltar al contenido y accesos a diagnóstico). Se ajustaron `tramites/tests.py` (ya no existe el menú «Papeles») y `consola/tests_fase2.py` (el visitante ya no ve «Mi garaje»).
- Quedan sin uso: `templates/parciales/menu_servicios.html` y las reglas `.menu-movil` / `.menu-panel` / `nav-hamburguesa` del CSS. Se pueden borrar más adelante.

## Verificación
- Suite completa: **802 pruebas OK** (incluye `config/tests_seguridad.py`).
- Navegador a 1280 px y a 375 px. **Motociclista** en vivo, con la sesión que ya tenía el navegador: sin desborde ni scroll horizontal, los 4 submenús responden a clic, flechas, Escape y clic fuera, el menú del avatar termina por encima de la barra y Chispa e Instalar app quedan a 8-11 px sobre la barra. **Visitante**: se cargó la página sin cookies dentro de un iframe de 375 px, con logo y Crear cuenta arriba y la barra de 5 botones de 60 px. **Taller y staff**: solo con las pruebas automáticas, porque no hubo forma de entrar con esas cuentas en el navegador (no se permitió crear sesiones en la base local ni leer `privado/`).
- Nota: el servidor del puerto 8001 (de otra sesión) mostró un error de plantilla hasta que se reinició, porque las bibliotecas de etiquetas nuevas exigen reinicio. Se reinició con `touch` a un módulo ya cargado.
