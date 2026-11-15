"""Tema demo largo del foro con respuestas en hilo, menciones y mensajes largos. Idempotente: si ya existe, no duplica.

Uso: manage.py demo_foro_hilo
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from foro.menciones import alias, notificar_publicacion
from foro.models import Categoria, Pregunta, Reaccion, Respuesta, Voto
from talleres.models import Marca

TITULO = "Mi NMAX pierde fuerza subiendo a Santa Elena y huele a quemado: ¿correa o embrague?"
CUERPO = (
    "Tengo una NMAX 155 modelo 2021 con 23.000 km. Desde hace dos semanas, subiendo por Las Palmas hacia Santa Elena "
    "con parrillero, la moto se queda: acelero, el motor sube de vueltas pero no avanza igual, y arriba en el mirador "
    "sentí un olor como a quemado.\n\nEn plano anda normal. El último mantenimiento fue a los 18.000 (aceite y filtro de "
    "aire). ¿Qué puede ser? ¿Es peligroso seguir subiendo así mientras la llevo a revisar?"
)

# Usuarios demo propios del hilo (sin contraseña utilizable: solo para mostrar el tema).
USUARIOS = {
    "valen": ("valentina.hilo@tallerya.local", "Valentina"),
    "juanpa": ("juanpablo.hilo@tallerya.local", "Juan Pablo"),
    "fabio": ("fabio.hilo@tallerya.local", "Don Fabio"),
    "luisa": ("luisa.hilo@tallerya.local", "Luisa"),
    "mateo": ("mateo.hilo@tallerya.local", "Mateo"),
    "yese": ("yesenia.hilo@tallerya.local", "Yesenia"),
}
# Si ya existen los demo generales (cargar_demo), también participan.
EXISTENTES = {"camila": "camila.demo@tallerya.local", "andres": "andres.demo@tallerya.local",
              "taller": "paisa.demo@tallerya.local"}
RESPALDO = {"camila": ("camila.hilo@tallerya.local", "Camila"), "andres": ("andres.hilo@tallerya.local", "Andrés"),
            "taller": ("sebastian.hilo@tallerya.local", "Sebastián (mecánico)")}

# (clave, autor, responde a (clave o None = al tema), horas después de la pregunta, texto). {@quien} = mención.
MENSAJES = [
    ("r1", "juanpa", None, 1, "Eso suena a correa patinando o a las zapatas del embrague centrífugo gastadas. El síntoma "
     "de «sube de vueltas y no avanza» es clásico de la transmisión. ¿Cuándo le cambiaste la correa?"),
    ("n1", "valen", "r1", 2, "Nunca 🙈 La compré usada con 15.000 km y no sé si el dueño anterior la cambió."),
    ("n2", "fabio", "n1", 3,
     "Entonces casi seguro va por ahí, mija. En estas lomas de Medellín la transmisión de una scooter trabaja el doble: "
     "Las Palmas, Santa Elena, la subida a Robledo… todo eso con parrillero es castigo para la correa.\n\n"
     "Lo que yo revisaría, en este orden:\n"
     "1. La correa: que no tenga grietas por dentro (por fuera puede verse bien) y que no esté más angosta de lo que "
     "dice el manual.\n"
     "2. Los rodillos: si están planos de un lado, la moto no «estira» bien la relación.\n"
     "3. Las zapatas del embrague y la campana: si la campana está vidriada o rayada, patina y huele a quemado.\n"
     "4. El resorte de torque: cansado hace que la moto se quede en las subidas.\n\n"
     "Y mientras tanto no la fuerce subiendo con parrillero, porque si la correa se revienta en plena loma es peligroso "
     "y además puede dañar la tapa."),
    ("n3", "valen", "n2", 4, "Don Fabio, ¿eso lo puedo hacer yo con herramienta básica o mejor la llevo?"),
    ("n4", "fabio", "n3", 5, "Con herramienta básica no: hay que trabar la polea y usar la llave de impacto o una "
     "herramienta especial. Llévela a un taller que trabaje scooter. {@taller} les mete mucha mano a las NMAX."),
    ("n5", "taller", "n4", 7, "Gracias, Don Fabio. Valentina, con gusto la revisamos. Antes de abrir te damos el "
     "presupuesto y te mostramos las piezas que salgan gastadas."),
    ("n6", "camila", "n1", 8, "A mí me pasó lo mismo con la mía y era la correa con grietas por dentro. Por fuera se "
     "veía perfecta, por eso no la habían cambiado."),
    ("n7", "andres", "r1", 9, "Ojo que no siempre es la correa: a un amigo le pasaba lo mismo y era el filtro de aire "
     "de la transmisión (el de la tapa del CVT) tapado de mugre. La correa se recalentaba y patinaba."),
    ("n8", "juanpa", "n7", 10, "Buen punto, {@andres}. Ese filtro casi nadie lo limpia y en Medellín, con tanto polvo de "
     "obra, se tapa rapidísimo."),
    ("n9", "mateo", "n8", 12, "¿Dónde queda ese filtro en la NMAX? Tengo la misma moto y nunca lo he visto."),
    ("n10", "andres", "n9", 13, "Detrás de una tapita plástica en la parte de arriba de la tapa del CVT, al lado "
     "izquierdo. Son unos tornillos y sale. Si lo ves negro, toca limpiarlo o cambiarlo."),
    ("r2", "luisa", None, 14, "Pregunta de novata: ¿el olor a quemado puede ser también de las pastillas de freno? "
     "Bajando Las Palmas yo voy frenando todo el tiempo."),
    ("n11", "fabio", "r2", 15,
     "Puede ser, pero ella dice que lo sintió subiendo, no bajando. Bajando sí pasa mucho: en las automáticas casi no hay "
     "freno de motor, entonces uno baja colgado de los frenos y las pastillas se calientan hasta que huelen.\n\n"
     "Consejo para bajar Las Palmas: frene a ratos y suelte, alternando delantero y trasero, en vez de llevar el freno "
     "pisado todo el tiempo. Así el disco se enfría y la pastilla dura más."),
    ("n12", "luisa", "n11", 16, "Ah, no sabía que en las automáticas casi no hay freno de motor. ¡Gracias, Don Fabio!"),
    ("n13", "yese", "n11", 18, "Yo hago Las Palmas a diario para ir al trabajo en Rionegro y me tocó cambiar pastillas "
     "a los 8.000 km. Bajar es lo que más las gasta, tal cual."),
    ("n14", "luisa", "n13", 19, "¿A los 8.000? Uff. ¿Y te salieron caras?"),
    ("n15", "yese", "n14", 20, "No tanto, pero cambia mucho de un taller a otro. Mejor pide cotización a dos o tres "
     "talleres del directorio y compara."),
    ("r3", "taller", None, 22,
     "Te dejo lo que revisamos en el taller cuando llega una scooter con ese síntoma, para que sepas qué preguntar "
     "donde la lleves:\n\n"
     "• Correa: medimos el ancho y la doblamos para ver grietas por dentro.\n"
     "• Rodillos y rampa: si los rodillos están planos o la rampa marcada, se cambian juntos.\n"
     "• Embrague (zapatas) y campana: miramos el desgaste de las zapatas y si la campana está vidriada.\n"
     "• Resorte de torque y guía: si el resorte está cansado, la moto se queda en las subidas.\n"
     "• Filtro de la transmisión: se limpia o se cambia, como dijo {@andres}.\n\n"
     "Con 23.000 km y sin historial, lo más probable es correa y rodillos. Pide que te muestren las piezas viejas y "
     "anota el kilometraje del cambio para el próximo."),
    ("n16", "valen", "r3", 23, "Súper claro, gracias. ¿Me la pueden ver el sábado en la mañana?"),
    ("n17", "taller", "n16", 24, "Claro que sí. Escríbenos desde la ficha del taller para separarte el turno."),
    ("n18", "juanpa", "r3", 26, "Coincido en todo. Yo agregaría revisar el rodamiento de la polea: cuando suena como "
     "un silbido al arrancar, también puede estar pidiendo cambio."),
    ("r4", "mateo", None, 30, "Medio fuera del tema pero útil: ¿subir con parrillero a Santa Elena todos los días acorta "
     "mucho la vida de la correa? Yo hago unos 40 km diarios con loma."),
    ("n19", "fabio", "r4", 31, "Sí la acorta, mijo. Con su uso yo la revisaría bastante antes de lo que dice el manual "
     "y la cambiaría apenas vea la primera grieta. Más barato cambiarla a tiempo que quedarse varado en la loma."),
    ("n20", "mateo", "n19", 32, "Entonces mejor bajo el intervalo. ¿Eso se puede poner en el garaje de TallerYa?"),
    ("n21", "camila", "n20", 34, "Sí. Yo en el plan de mantenimiento de mi moto puse el intervalo de la correa más "
     "corto y me avisa cuando se acerca. Lo cambias desde la tarea, en «ajustar»."),
    ("n22", "valen", "n21", 35, "{@camila} ¡no sabía que se podía cambiar el intervalo! Lo voy a poner apenas salga "
     "del taller."),
    ("r5", "valen", None, 98,
     "Actualización: la llevé al taller el sábado. Era la correa, con grietas por dentro como dijo {@camila}, y los "
     "rodillos planos de un lado. La campana estaba bien, menos mal.\n\n"
     "Cambiaron correa y rodillos y limpiaron el filtro de la transmisión que mencionó {@andres}, que estaba negro. "
     "Ayer subí a Santa Elena con parrillero y sube como nueva, sin olor a nada.\n\n"
     "Gracias a todos, en especial a {@fabio} y a {@taller}. Ya dejé anotado el kilometraje del cambio en el garaje."),
    ("n23", "fabio", "r5", 99, "Qué bueno, mija. Ahora no deje pasar tanto la próxima."),
    ("n24", "juanpa", "r5", 100, "¡Bacano! Marca como solución la respuesta del taller, así le sirve al siguiente que "
     "busque lo mismo 😉"),
    ("n25", "valen", "n24", 101, "Listo, ya quedó marcada."),
    ("n26", "andres", "r5", 103, "Me alegra que haya servido lo del filtro. Ese detalle se le olvida a todo el mundo."),
]
VOTOS = {"r3": ["valen", "juanpa", "fabio", "camila", "mateo"], "n2": ["valen", "camila", "luisa"],
         "n7": ["mateo", "juanpa"], "n11": ["luisa", "yese"], "r5": ["fabio", "andres"]}

# Reacciones por número de mensaje en MENSAJES (0 = primero) o "p" (la pregunta): [(autor, tipo)]
REACCIONES = {"p": [("juanpa", "preocupa"), ("camila", "preocupa"), ("mateo", "gusta")],
              "r3": [("valen", "encanta"), ("fabio", "gusta"), ("luisa", "gusta"), ("yese", "gusta")],
              "n2": [("valen", "encanta"), ("mateo", "gusta")], "n11": [("luisa", "encanta")],
              "r5": [("fabio", "encanta"), ("camila", "encanta"), ("juanpa", "divierte"), ("taller", "gusta")],
              "n4": [("taller", "divierte")], "n15": [("luisa", "gusta")]}


class Command(BaseCommand):
    help = "Crea un tema demo largo del foro con respuestas en hilo y menciones (no duplica si ya existe)."

    def handle(self, *args, **opciones):
        existente = Pregunta.objects.filter(titulo=TITULO).first()
        if existente:
            self._reacciones(existente)
            self.stdout.write(f"El tema demo ya existe ({existente.respuestas.count()} respuestas): "
                              f"{existente.get_absolute_url()}")
            return
        with transaction.atomic():
            pregunta = self._crear()
        self.stdout.write(self.style.SUCCESS(
            f"Tema demo creado con {pregunta.respuestas.count()} respuestas: {pregunta.get_absolute_url()}"))

    def _usuarios(self):
        User = get_user_model()
        usuarios = {}
        for clave, correo in EXISTENTES.items():
            usuarios[clave] = User.objects.filter(username=correo).first()
        for clave, (correo, nombre) in {**USUARIOS, **{k: v for k, v in RESPALDO.items() if not usuarios.get(k)}}.items():
            u, creado = User.objects.get_or_create(username=correo, defaults={"email": correo, "first_name": nombre})
            if creado:
                u.set_unusable_password()
                u.save(update_fields=["password"])
            usuarios[clave] = u
        return usuarios

    def _crear(self):
        from garaje.models import LineaMoto
        u = self._usuarios()
        menciones = {f"{{@{k}}}": f"@{alias(v)}" for k, v in u.items()}

        def texto(t):
            for marca, valor in menciones.items():
                t = t.replace(marca, valor)
            return t

        inicio = timezone.now() - timedelta(days=6)
        marca = Marca.objects.filter(nombre__iexact="Yamaha").first()
        linea = LineaMoto.objects.filter(nombre__icontains="NMAX").select_related("marca").first()
        pregunta = Pregunta.objects.create(autor=u["valen"], titulo=TITULO, cuerpo=CUERPO, categoria=Categoria.FALLAS,
                                           marca=marca or (linea.marca if linea else None),
                                           linea=linea if linea and (not marca or linea.marca_id == marca.pk) else None,
                                           vistas=187)
        Pregunta.objects.filter(pk=pregunta.pk).update(creado=inicio)
        creadas = {}
        for clave, autor, padre, horas, cuerpo in MENSAJES:
            r = Respuesta.objects.create(pregunta=pregunta, autor=u[autor], padre=creadas.get(padre), cuerpo=texto(cuerpo))
            Respuesta.objects.filter(pk=r.pk).update(creado=inicio + timedelta(hours=horas))
            notificar_publicacion(r, pregunta, u[autor])
            creadas[clave] = r
        for clave, quienes in VOTOS.items():
            for q in quienes:
                if creadas[clave].autor_id != u[q].pk:
                    Voto.objects.get_or_create(usuario=u[q], respuesta=creadas[clave])
        pregunta.mejor_respuesta = creadas["r3"]
        pregunta.save(update_fields=["mejor_respuesta"])
        pregunta.refresh_from_db()
        pregunta.recalcular_actividad()  # las fechas se movieron hacia atrás para que el hilo se vea realista
        self._reacciones(pregunta)
        return pregunta

    def _reacciones(self, pregunta):
        """Agrega las reacciones demo que falten (también a un tema creado antes de existir las reacciones)."""
        u = self._usuarios()
        respuestas = list(pregunta.respuestas.order_by("creado", "pk"))
        claves = {clave: respuestas[i] for i, (clave, *_resto) in enumerate(MENSAJES) if i < len(respuestas)}
        for clave, lista in REACCIONES.items():
            objetivo = {"pregunta": pregunta} if clave == "p" else {"respuesta": claves.get(clave)}
            if None in objetivo.values():
                continue
            autor_id = (pregunta if clave == "p" else objetivo["respuesta"]).autor_id
            for quien, tipo in lista:
                if u[quien].pk != autor_id:
                    Reaccion.objects.get_or_create(usuario=u[quien], **objetivo, defaults={"tipo": tipo})
