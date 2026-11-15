# Chatbot de Chispa (sin IA, listo para conectarla)

El botón flotante es Chispa entera, sin círculo, de pie abajo a la derecha en todo el sitio. Flota unos 4 px sobre su sombra, parpadea y salta al abrir el chat. En reposo los dos brazos cuelgan simétricos. Saluda cada 9 s y, en escritorio, de inmediato al pasar el cursor o al enfocarla con teclado; si ya está saludando, no se corta ni se repite. Al saludar gira el mismo brazo derecho colgante sobre el hombro (`.ch-b-der-giro`, un envoltorio nuevo del componente): sube por fuera, saluda y baja con ease-out hasta su pose exacta, sin cambiar de elemento. El JS pone la clase `.cc-saluda` durante 2,2 s. Al pasar el cursor también salta una ráfaga de 6 chispas y el destello del arco por el electrodo (clase `.cc-chispea`, unos 0,5 s).

**Esconder a Chispa:**
- Se esconde arrastrándola hacia el borde derecho, con el mouse en escritorio o deslizando el dedo en celular. Si se suelta pasados 60 px se esconde; si no, vuelve a su sitio.
- El cursor de mano sugiere que se puede arrastrar, y la primera vez sale una pista discreta: «Arrástrame al borde para esconderme».
- En la cabecera del chat hay un ícono de ojo tachado, del mismo estilo que la ×, para esconderla. Con el cursor, foco o al tocarlo, el de esconder se pone mostaza y el ojo se cierra, y la × se pone lava y gira 90°. Los dos crecen un poco (1,06) en 0,2 s y tienen tooltip («Esconder a Chispa» / «Cerrar»).
- Escondida, el borde de la pantalla hace de pared: asoma un lado de la cabeza con un ojo, inclinada, y una manito agarrada al borde. Con el cursor encima se asoma más y mira; al hacer clic (o tocarla en celular) sale completa saludando; al retirar el cursor vuelve a esconderse.
- El estado se recuerda en `localStorage` (`tallerya-chispa-escondida`). Mientras está escondida no sale el globito, y el botón se anuncia como «Mostrar a Chispa».

## Cómo funciona
1. Saludo: «¡Hola, {nombre}! Soy Chispa, tu copiloto de taller. ¿En qué te ayudo hoy?». Sin sesión dice «¡Hola! Soy Chispa…».
2. Temas en chips → preguntas → respuesta en burbujas. Antes de cada respuesta aparece «Chispa está escribiendo…» con sus ojos barriendo.
3. La respuesta trae botones de acción a la página correcta (Ver mi plan, Buscar taller, Pico y placa de mi moto, Agregar moto, Emergencias…) y preguntas relacionadas.
4. También hay un buscador por palabras clave. Si no encuentra nada, responde «No encontré…» y ofrece el foro.

| Tema | Preguntas |
|---|---|
| Mi moto y mantenimiento | 8 |
| Papeles y pico y placa | 3 |
| Talleres y citas | 6 |
| Diagnóstico y despiece | 2 |
| Foro y rodadas | 2 |
| Cuenta y Plus | 4 |
| App en el celular | 2 |

Las respuestas están escritas a partir del código (estimación de km en `garaje/plan.py`, pico y placa en `garaje/pico_placa.py`, vencimientos en `garaje/avisos.py`, etc.).

## Archivos
- **App `ayuda`:**
  - `faq.json`: los datos.
  - `motor.py`: buscador, personalización y punto único de respuesta.
  - `views.py` y `urls.py`: `ayuda:catalogo` → `/ayuda/catalogo.json` y `ayuda:preguntar` → `/ayuda/preguntar/?id=…` o `?q=…`.
  - `tests.py`: 9 pruebas.
- **Interfaz:** `ayuda/templates/ayuda/_chispa_chat.html` (botón; se incluye en `templates/base.html` dentro de `{% block chat_ayuda %}`, que una página puede vaciar), `ayuda/static/ayuda/js/chispa-chat.js` (con `defer`; arma la ventana y pide los datos solo al abrirla) y `ayuda/static/ayuda/css/chispa-chat.css`.
- **Componente:** `parciales/chispa.html` tiene un parámetro nuevo, `vista`: `"boton"` deja a Chispa entera sin el espacio de la escoba y `"cara"` la recorta desde el visor. El JS usa la cara en la cabecera y en «escribiendo».
- **Registro:** `ayuda` está en `INSTALLED_APPS` y en `config/urls.py`.

## Agregar o cambiar preguntas
Edita `ayuda/faq.json`. Cada pregunta tiene esta forma:
```json
{
  "id": "pico-placa",
  "pregunta": "¿Cómo funciona el pico y placa en Medellín?",
  "claves": ["pico y placa", "restriccion", "placa"],
  "respuesta": ["Párrafo corto 1.", "Párrafo 2. Puede usar {moto} y {nombre}."],
  "acciones": [{"texto": "Pico y placa de mi moto", "url_nombre": "garaje:moto", "con_moto": true, "ancla": "pico-placa", "texto_sin_moto": "Agregar moto"}],
  "relacionadas": ["soat", "notificaciones"]
}
```
- **`claves`:** frases o palabras que alguien escribiría. Pesan más que el texto de la pregunta.
- **`url_nombre`:** nombre de URL de Django.
  - Con `con_moto: true` usa la primera moto del usuario; sin moto va a `garaje:bienvenida` (o a `sin_moto`) con el texto `texto_sin_moto`.
  - `ancla` añade `#…` a la URL.
- **Al terminar:** corre `manage.py test ayuda -v 1`. La prueba falla si una URL no existe o si una relacionada no tiene pregunta.
- **Reinicio:** el JSON se lee una vez por proceso, así que hay que reiniciar el servidor para ver los cambios.

## Conectar IA después
Todo pasa por `ayuda.motor.responder(texto, pregunta_id, usuario)`, que siempre devuelve:
```json
{"fuente": "faq|ia|sin_respuesta", "id": "…|null", "pregunta": "…", "respuesta": ["…"], "acciones": [{"texto": "…", "url": "…"}], "relacionadas": [{"id": "…", "pregunta": "…"}]}
```
Para usar un modelo, cambia el final de `responder()`: cuando `buscar()` no encuentre nada (o siempre, usando el FAQ como contexto), llama al modelo y devuelve esa misma forma con `"fuente": "ia"`. El JS no cambia.

Recomendaciones:
- **Contexto:** pásale al modelo `faq.json` y `contexto_usuario()` (nombre, moto, próxima tarea).
- **Acciones:** limita las acciones a las `url_nombre` que ya existen en el FAQ, para que no invente enlaces.
- **Clave:** guárdala en una variable de entorno, nunca en el código.
- **Abuso:** agrega un límite de peticiones por IP o usuario en `views.preguntar`. Si la petición pasa a POST, el JS debe mandar el token CSRF.

## Accesibilidad y carga
- **Botón:** tiene `aria-haspopup="dialog"`, `aria-expanded` y una etiqueta clara.
- **Ventana:** usa `role="dialog"` con `aria-modal` y título. Los mensajes van en `role="log"` con `aria-live="polite"`.
- **Teclado:** el foco queda dentro de la ventana con Tab, Esc la cierra y el foco vuelve al botón. En celular, tocar el fondo también la cierra.
- **Sin movimiento:** con «reducir movimiento» no hay animaciones.
- **Globito «¿Te ayudo?»:** es una viñeta de pensamiento crema con dos burbujitas hacia Chispa, sin ×. Sale al cargar la página (entrada de 0,3 s), dura 7 s y vuelve cada 60 s. Tocarlo abre el chat; tocar fuera o Esc lo cierra y no vuelve nunca (`localStorage` `tallerya-chispa-globito-cerrado`). En celular es más pequeño y va encima de la cabeza de Chispa.
- **Carga:**
  - El botón (SVG en línea) y el CSS son livianos. El JS va diferido y la ventana y los datos se cargan solo al abrir.
  - El CSS va enlazado en el include, dentro del `<body>`. Si la sesión que optimiza la carga lo prefiere, puede moverse al `<head>` o cargarse en diferido.
- **Convivencia:**
  - Si aparece la barra «Instala TallerYa», el botón sube (`body:has(.instalar-app:not([hidden]))`).
  - No hay otros botones fijos abajo en celular. Los avisos flotantes (`.aviso-flotante`, z-index 80) quedan por encima del botón (z-index 55).

## Pendientes y notas
- **Bloque `chat_ayuda`:** cualquier página puede ocultar el botón con un bloque vacío (p. ej. la vista 3D a pantalla completa, si molesta).
- **Datos que pueden cambiar:**
  - Pico y placa: la regla vigente está cargada hasta el 29-ene-2027 y la respuesta recomienda confirmar con Movilidad.
  - Plus: el número de Nequi en settings es un marcador; la respuesta no lo menciona.
- **Sin probar en dispositivo real:** revisado con capturas sin interfaz a 360, 390, 1280 y 1440 px.
