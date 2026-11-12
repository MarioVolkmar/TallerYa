# TallerYa

Directorio de talleres de motos en Medellín. MVP en Django.

## Funciones (fase 1)
- Buscar talleres por texto, barrio, servicio y marca.
- Perfil del taller: servicios, marcas, horario, WhatsApp, calificación.
- Pedir cita y dejar reseña.
- Registro de talleres (queda inactivo hasta aprobarlo en el admin).
- Admin para verificar, activar, destacar y moderar.

## Correr en local (Windows)
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py cargar_demo
python manage.py createsuperuser
python manage.py runserver
```
Abrir http://127.0.0.1:8000 (admin en `/admin`).

Tests: `python manage.py test`

## Próximas fases
- Fase 2: cupones, canjes y referidos.
- Fase 3: suscripción para motociclistas y foro de preguntas.
- Producción: PostgreSQL, variables de entorno (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`), deploy en Railway/Render.
