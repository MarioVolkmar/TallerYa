"""Deja la base LOCAL con un único juego de datos demo: solo cuentas @prueba.com, completas y verificadas.

    python manage.py preparar_demo_prueba            # borra lo demo viejo, completa/crea las cuentas @prueba.com y verifica
    python manage.py preparar_demo_prueba --listar   # solo muestra qué se borraría
    python manage.py preparar_demo_prueba --verificar

Idempotente. Contraseña común: variable PASSWORD_DEMO_PRUEBA (ver .env.example) o la de talleres/demo_prueba.py.
Se niega a correr sin DEBUG (producción) salvo --forzar.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from talleres import demo_prueba


class Command(BaseCommand):
    help = "Limpia los datos demo viejos y deja las cuentas @prueba.com completas (solo local)."

    def add_arguments(self, parser):
        parser.add_argument("--listar", action="store_true", help="Solo lista lo que se borraría")
        parser.add_argument("--verificar", action="store_true", help="Solo imprime la tabla de perfil por cuenta")
        parser.add_argument("--sin-borrar", action="store_true", help="No borra lo demo viejo")
        parser.add_argument("--forzar", action="store_true", help="Corre aunque DEBUG esté apagado (nunca en producción)")

    def handle(self, *args, **o):
        if not settings.DEBUG and not o["forzar"]:
            raise CommandError("Es solo para la base local (DEBUG). Usa --forzar si de verdad lo necesitas.")
        if o["listar"]:
            for clave, valor in demo_prueba.resumen_demo().items():
                self.stdout.write(f"{clave}: {len(valor) if isinstance(valor, list) else valor}" + (f" -> {', '.join(valor)}" if isinstance(valor, list) else ""))
            return
        if not o["verificar"]:
            if not o["sin_borrar"]:
                r = demo_prueba.limpiar_demo()
                self.stdout.write(f"Borrado: {len(r['usuarios'])} usuarios, {len(r['talleres'])} talleres, {len(r['mecanicos'])} mecánicos, "
                                  f"{r['moteros']} moteros, {r['resenas']} reseñas, {r['citas']} citas/visitas, {r['cupones']} cupones, {r['fotos']} fotos.")
            demo_prueba.preparar()
        self.stdout.write("correo | rol | % perfil | falta")
        for correo, rol, pct, falta in demo_prueba.verificar():
            self.stdout.write(f"{correo} | {rol} | {pct} % | {', '.join(falta) or '-'}")
