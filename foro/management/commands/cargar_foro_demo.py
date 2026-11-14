"""Contenido de ejemplo del foro por tema. Solo agrega lo que falta (no borra ni cambia lo existente)."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from foro.models import Categoria, Pregunta, Respuesta
from talleres.models import Marca

# (tema, marca, título, cuerpo, [respuestas (autor, texto)], índice de la solución o None)
EJEMPLOS = [
    (Categoria.MANTENIMIENTO, "Yamaha", "¿Cada cuánto se cambia la correa de una NMAX?",
     "Voy en 14.000 km y nunca la he cambiado. ¿Se revisa o se cambia directo?",
     [("taller", "Revísala en cada mantenimiento y cámbiala según lo que indique el manual de tu moto o antes si tiene grietas."),
      ("camila", "A mí me la cambiaron junto con los rodillos y quedó como nueva.")], 0),
    (Categoria.RUTAS, None, "Ruta corta para el domingo saliendo de Medellín",
     "Busco una ruta de medio día, con buena vía y un sitio para desayunar. ¿Recomendaciones?",
     [("andres", "Yo hago Santa Elena y bajo por Guarne, buena vía y hay dónde comer.")], None),
    (Categoria.REPUESTOS, "AKT", "¿Dónde consigo un espejo original para la NKD 125?",
     "Se me partió el izquierdo y los genéricos vibran mucho.", [], None),
    (Categoria.TALLERES, None, "¿Qué preguntarle a un taller antes de dejarle la moto?",
     "Es mi primera moto y no sé bien qué pedir para que no me cobren de más.",
     [("taller", "Pide el presupuesto por escrito antes de empezar y que te muestren las piezas que cambian."),
      ("camila", "Y pregunta si dan garantía por el trabajo.")], 0),
    (Categoria.FALLAS, "Honda", "La moto se apaga en los semáforos cuando está caliente",
     "Pasa sobre todo al final del día. Prende bien en frío.", [], None),
]


class Command(BaseCommand):
    help = "Agrega preguntas de ejemplo al foro, una por tema, sin borrar nada."

    def handle(self, *args, **opciones):
        User = get_user_model()
        autores = {
            "andres": User.objects.filter(username="andres.demo@tallerya.local").first(),
            "camila": User.objects.filter(username="camila.demo@tallerya.local").first(),
            "taller": User.objects.filter(username="paisa.demo@tallerya.local").first(),
        }
        if not all(autores.values()):
            self.stdout.write("Faltan los usuarios demo del foro: corre primero cargar_demo.")
            return
        nuevas = 0
        for tema, marca, titulo, cuerpo, respuestas, solucion in EJEMPLOS:
            if Pregunta.objects.filter(titulo=titulo).exists():
                continue
            autor = autores["camila"] if nuevas % 2 else autores["andres"]
            p = Pregunta.objects.create(autor=autor, titulo=titulo, cuerpo=cuerpo, categoria=tema,
                                        marca=Marca.objects.filter(nombre=marca).first() if marca else None)
            creadas = [Respuesta.objects.create(pregunta=p, autor=autores[quien], cuerpo=texto) for quien, texto in respuestas]
            if solucion is not None and creadas:
                p.mejor_respuesta = creadas[solucion]
                p.save(update_fields=["mejor_respuesta"])
            nuevas += 1
        # Las dos preguntas demo originales quedan en su tema (solo si siguen en "General")
        Pregunta.objects.filter(titulo__startswith="¿Cada cuánto debo cambiar el aceite", categoria=Categoria.GENERAL).update(categoria=Categoria.MANTENIMIENTO)
        Pregunta.objects.filter(titulo__startswith="La NMAX hace un chillido", categoria=Categoria.GENERAL).update(categoria=Categoria.FALLAS)
        self.stdout.write(f"Preguntas de ejemplo nuevas: {nuevas}")
