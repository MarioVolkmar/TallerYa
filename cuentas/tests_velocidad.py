"""Mi cuenta no debe hacer más consultas por tener más motos (antes: ~5 por moto)."""
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from garaje.models import Moto, Motociclista


class MiCuentaConsultasTests(TestCase):
    def _consultas(self, n_motos):
        u = get_user_model().objects.create_user(f"m{n_motos}@x.co", f"m{n_motos}@x.co", "clave-larga-1")
        m = Motociclista.objects.create(usuario=u, nombre="Ana", celular=f"57300111000{n_motos}")
        for i in range(n_motos):
            Moto.objects.create(motociclista=m, marca_otra="Yamaha", linea_otra="NMAX", tipo_otra="scooter", modelo=2022,
                                km_inicial=1000, km_actual=5000, placa=f"AB{n_motos}{i}1C")
        self.client.force_login(u)
        self.client.get("/cuenta/")  # calienta cachés de la primera visita
        with CaptureQueriesContext(connection) as q:
            self.assertEqual(self.client.get("/cuenta/").status_code, 200)
        return len(q)

    def test_no_crece_con_las_motos(self):
        self.assertEqual(self._consultas(1), self._consultas(4))
