from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Carga los mecánicos a domicilio de demostración (ficticios). Es seguro repetirlo: no duplica."

    def handle(self, *args, **opts):
        from domicilio import demo
        demo.cargar(self.stdout)
