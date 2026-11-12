#!/usr/bin/env bash
# Build de Render: instala dependencias, junta estáticos y aplica migraciones.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Datos de ejemplo (talleres, cupones, foro). Es seguro repetirlo: no duplica nada.
if [ "$CARGAR_DEMO" = "1" ]; then
  python manage.py cargar_demo
fi

# Crea el administrador la primera vez si se definieron las variables
# DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL y DJANGO_SUPERUSER_PASSWORD.
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py createsuperuser --no-input 2>/dev/null || echo "El administrador ya existe."
fi
