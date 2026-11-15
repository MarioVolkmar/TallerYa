"""Rodadas demo del Valle de Aburrá y alrededores: próximas, casi llenas, llena y pasadas, con asistentes y comentarios.

Idempotente: una rodada con el mismo título no se vuelve a crear. Uso: manage.py demo_rodadas
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from foro.models import Asistencia, Categoria, Pregunta, Respuesta, Rodada

# Usuarios demo (los mismos del tema demo del foro si existen; si no, se crean sin contraseña utilizable)
USUARIOS = {
    "valen": ("valentina.hilo@tallerya.local", "Valentina"), "juanpa": ("juanpablo.hilo@tallerya.local", "Juan Pablo"),
    "fabio": ("fabio.hilo@tallerya.local", "Don Fabio"), "luisa": ("luisa.hilo@tallerya.local", "Luisa"),
    "mateo": ("mateo.hilo@tallerya.local", "Mateo"), "yese": ("yesenia.hilo@tallerya.local", "Yesenia"),
    "sara": ("sara.rodada@tallerya.local", "Sara"), "kevin": ("kevin.rodada@tallerya.local", "Kevin"),
    "manu": ("manuela.rodada@tallerya.local", "Manuela"), "esteban": ("esteban.rodada@tallerya.local", "Esteban"),
    "dora": ("dora.rodada@tallerya.local", "Doña Dora"), "santi": ("santiago.rodada@tallerya.local", "Santiago"),
}
EXISTENTES = {"camila": "camila.demo@tallerya.local", "andres": "andres.demo@tallerya.local",
              "taller": "paisa.demo@tallerya.local"}

# (título, organizador, días desde hoy, hora, punto de encuentro, destino, nivel, cupo, asistentes, detalles, comentarios)
RODADAS = [
    ("Madrugón a Santa Elena por Las Palmas", "valen", 2, "06:00", "Parque de El Poblado",
     "Santa Elena por Las Palmas, regreso por Piedras Blancas y Guarne", "principiante", 15,
     ["juanpa", "luisa", "mateo", "sara", "manu"],
     "Ritmo suave, ideal si es tu primera rodada en grupo. Paramos a desayunar arepa de chócolo en Santa Elena. "
     "Lleva impermeable: arriba suele lloviznar temprano.",
     [("luisa", "¡Voy! Es mi primera rodada, ¿el ritmo es de verdad suave?"),
      ("valen", "Tranqui, Luisa: vamos a 50–60 y nadie se queda solo. Hay barredor al final."),
      ("mateo", "Yo llevo la herramienta básica por si alguien se vara.")]),
    ("Guatapé y la Piedra del Peñol", "juanpa", 5, "07:00", "Estación de servicio de la salida a Copacabana (autopista Medellín–Bogotá)",
     "Guatapé por Marinilla y El Peñol; almuerzo en el malecón", "intermedio", 10,
     ["valen", "fabio", "yese", "kevin", "esteban", "camila", "andres", "santi"],
     "Unos 80 km por trayecto. Tanqueen antes de salir; en la vía hay peajes y tramos con tractomulas.",
     [("kevin", "¿Se puede ir con parrillero?"),
      ("juanpa", "Sí, Kevin, siempre que los dos lleven casco y chaleco reflectivo."),
      ("yese", "Quedan solo dos cupos, ¡apúrense!")]),
    ("Alto de Minas y almuerzo en Santa Bárbara", "fabio", 12, "06:30", "Estación Envigado del metro",
     "Alto de Minas por la vía a Caldas, Santa Bárbara y regreso por La Pintada si da el tiempo", "avanzado", 8,
     ["mateo", "kevin", "esteban", "santi", "andres", "juanpa", "taller"],
     "Ruta de curvas y subida larga. Revisen frenos y llantas antes; no es para estrenar moto.",
     [("taller", "Los que vayan pueden pasar el jueves por el taller y les revisamos frenos gratis."),
      ("fabio", "Cupo completo, mijos. Si alguien se baja, avise para que entre otro.")]),
    ("Represa La Fe y El Retiro, plan tranquilo", "luisa", 20, "08:00", "Centro comercial Santafé (parqueadero de motos)",
     "Represa La Fe, El Retiro y café en el parque", "principiante", None,
     ["sara", "manu", "dora"],
     "Sin afán: vía buena, paradas para fotos y café. Cupo libre.",
     [("dora", "¡Qué rico un plan así! Llevo a mi nieto de parrillero.")]),
    ("Santa Fe de Antioquia por el túnel de Occidente", "mateo", 26, "07:30", "Parque de San Antonio de Prado",
     "Santa Fe de Antioquia por el túnel de Occidente, Puente de Occidente y regreso", "intermedio", 20,
     ["valen", "yese", "kevin", "luisa", "camila", "santi"],
     "Calor fuerte al bajar: hidratación y protector solar. En el túnel, luces encendidas y sin adelantar.",
     [("camila", "¿Alguien sabe si el Puente de Occidente está abierto para motos?"),
      ("mateo", "Para cruzar a pie sí; las motos se dejan a la entrada. Vamos igual a tomar fotos.")]),
    ("Jardín por el suroeste, dos días", "esteban", 40, "06:00", "Estación Itagüí del metro",
     "Jardín por Bolombolo y Andes, noche en Jardín y regreso por Ciudad Bolívar", "avanzado", 12,
     ["fabio", "juanpa"],
     "Plan de dos días: cada quien paga su hospedaje. Unos 130 km por trayecto con tramos destapados cortos.",
     []),
    ("Rodada nocturna al Alto de las Palmas", "yese", -6, "19:30", "Parque de El Poblado",
     "Alto de las Palmas, mirador y regreso por la Avenida 34", "intermedio", 12,
     ["valen", "luisa", "mateo", "kevin", "manu", "santi", "andres", "camila", "esteban", "juanpa"],
     "De noche: chaleco reflectivo obligatorio y luces revisadas.",
     [("manu", "¡Qué rodada tan bacana! La vista de la ciudad desde el mirador es otra cosa."),
      ("kevin", "Gracias por organizar, Yesenia. ¿Repetimos el mes que viene?"),
      ("yese", "¡Claro! Les aviso por aquí.")]),
    ("San Pedro de los Milagros por la vía a Belmira", "andres", -25, "07:00", "Estación Caribe del metro",
     "San Pedro de los Milagros por la vía a Belmira, regreso por Entrerríos", "principiante", 15,
     ["valen", "sara", "dora", "luisa"],
     "Ruta lechera: paramos a comer quesito y buñuelo.",
     [("sara", "Fue mi primera rodada y quedé feliz. ¡Gracias, Andrés!")]),
]


class Command(BaseCommand):
    help = "Crea rodadas demo (próximas, llena, casi llena y pasadas) con asistentes y comentarios, sin duplicar."

    def handle(self, *args, **opciones):
        u = self._usuarios()
        nuevas = 0
        ahora = timezone.localtime()
        with transaction.atomic():
            for titulo, org, dias, hora, punto, destino, nivel, cupo, asistentes, detalles, comentarios in RODADAS:
                if Pregunta.objects.filter(titulo=titulo).exists():
                    continue
                h, m = map(int, hora.split(":"))
                fecha = (ahora + timedelta(days=dias)).replace(hour=h, minute=m, second=0, microsecond=0)
                publicada = min(fecha - timedelta(days=10), ahora - timedelta(hours=3))
                pregunta = Pregunta.objects.create(autor=u[org], titulo=titulo, categoria=Categoria.RUTAS, cuerpo=detalles)
                rodada = Rodada.objects.create(pregunta=pregunta, organizador=u[org], fecha_hora=fecha,
                                               punto_encuentro=punto, destino=destino, nivel=nivel, cupo=cupo)
                for quien in [org] + asistentes:
                    Asistencia.objects.get_or_create(rodada=rodada, usuario=u[quien])
                for i, (quien, texto) in enumerate(comentarios):
                    r = Respuesta.objects.create(pregunta=pregunta, autor=u[quien], cuerpo=texto)
                    Respuesta.objects.filter(pk=r.pk).update(creado=publicada + timedelta(hours=6 * (i + 1)))
                Pregunta.objects.filter(pk=pregunta.pk).update(creado=publicada)
                pregunta.refresh_from_db()
                pregunta.recalcular_actividad()
                nuevas += 1
        from django.urls import reverse
        self.stdout.write(self.style.SUCCESS(f"Rodadas demo nuevas: {nuevas} (total {Rodada.objects.count()}). "
                                             f"Ver: {reverse('foro:rodadas')}"))

    def _usuarios(self):
        User = get_user_model()
        usuarios = {}
        for clave, correo in EXISTENTES.items():
            usuarios[clave] = User.objects.filter(username=correo).first()
        for clave, (correo, nombre) in USUARIOS.items():
            usuario, creado = User.objects.get_or_create(username=correo, defaults={"email": correo, "first_name": nombre})
            if creado:
                usuario.set_unusable_password()
                usuario.save(update_fields=["password"])
            usuarios[clave] = usuario
        # Si no están los demo generales, sus lugares los ocupan usuarios de esta lista
        for clave, reemplazo in (("camila", "manu"), ("andres", "esteban"), ("taller", "fabio")):
            usuarios[clave] = usuarios[clave] or usuarios[reemplazo]
        return usuarios
