"""Datos de demo de TallerYa Ruta: un domiciliario con moto, 4 semanas de jornadas, gastos, mantenimientos y Plus,
y 3 talleres aliados. Solo para local (pide DEBUG). Se puede correr varias veces: borra y rehace lo del usuario demo.

Uso: manage.py demo_domiciliarios [--sin-plus]
Entrar con: domiciliario@demo.tallerya / demo-ruta-2026
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from cuentas.models import Perfil, Suscripcion
from cupones.models import Motociclista
from domiciliarios.models import Jornada, PerfilDomiciliario, TallerAliado, Verificacion
from garaje.models import Gasto, LecturaKm, LineaMoto, Mantenimiento, Moto, TareaMantenimiento
from talleres.models import Taller

CORREO = "domiciliario@demo.tallerya"
CLAVE = "demo-ruta-2026"
KM_DIA = 175


class Command(BaseCommand):
    help = "Crea los datos de demo de TallerYa Ruta (plan para domiciliarios). Solo con DEBUG."

    def add_arguments(self, parser):
        parser.add_argument("--sin-plus", action="store_true", help="El domiciliario demo queda sin Plus")

    @transaction.atomic
    def handle(self, *args, sin_plus=False, **opts):
        if not settings.DEBUG:
            raise CommandError("Solo en local (DJANGO_DEBUG=1).")
        hoy = timezone.localdate()
        User = get_user_model()
        usuario = User.objects.filter(email=CORREO).first() or User(username=CORREO, email=CORREO)
        usuario.first_name = "Andrés"
        usuario.set_password(CLAVE)
        usuario.save()
        perfil = Perfil.de(usuario)
        perfil.terminos_aceptados = perfil.terminos_aceptados or timezone.now()
        perfil.correo_verificado = True
        perfil.guia_terminada = perfil.guia_terminada or timezone.now()
        perfil.save()
        motero, _ = Motociclista.objects.get_or_create(usuario=usuario, defaults={"nombre": "Andrés Domiciliario",
                                                                                  "celular": "573009997001"})
        motero.motos.all().delete()  # rehace todo lo de la demo
        PerfilDomiciliario.objects.filter(motociclista=motero).delete()

        linea = (LineaMoto.objects.filter(nombre__icontains="NKD").first() or LineaMoto.objects.filter(activo=True).first())
        km_hoy = 31_200
        dias = 35
        moto = Moto.objects.create(
            motociclista=motero, linea=linea, modelo=2022, apodo="La de la ruta", placa="KLM45F",
            soat_vence=hoy + timedelta(days=19), tecno_vence=hoy + timedelta(days=210), matricula=hoy - timedelta(days=900),
            km_inicial=km_hoy - KM_DIA * dias, km_actual=km_hoy,
            **({} if linea else {"marca_otra": "AKT", "linea_otra": "NKD 125", "tipo_otra": "calle"}),
        )
        Moto.objects.filter(pk=moto.pk).update(creado=timezone.now() - timedelta(days=dias))
        moto.refresh_from_db()

        lecturas, jornadas, gastos = [], [], []
        dp = PerfilDomiciliario.objects.create(motociclista=motero, moto=moto, km_semana=KM_DIA * 6,
                                               dias_semana=6, plataformas=["rappi", "didi"])
        for atras in range(dias - 1, -1, -1):
            fecha = hoy - timedelta(days=atras)
            if fecha.weekday() == 6:  # descansa el domingo
                continue
            km = km_hoy - KM_DIA * atras
            lecturas.append(LecturaKm(moto=moto, km=km, fecha=fecha))
            jornadas.append(Jornada(perfil=dp, fecha=fecha, ingreso=85_000 + (atras * 7_919) % 60_000, km_fin=km))
            gastos.append(Gasto(moto=moto, fecha=fecha, tipo=Gasto.Tipo.GASOLINA, valor=13_000 + (atras % 3) * 2_000,
                                notas="Demo"))
        LecturaKm.objects.bulk_create(lecturas)
        Jornada.objects.bulk_create(jornadas)
        Gasto.objects.bulk_create(gastos + [
            Gasto(moto=moto, fecha=hoy - timedelta(days=12), tipo=Gasto.Tipo.ACEITE, valor=38_000, notas="Demo"),
            Gasto(moto=moto, fecha=hoy - timedelta(days=5), tipo=Gasto.Tipo.REPUESTO, valor=45_000, notas="Pastillas (demo)"),
            Gasto(moto=moto, fecha=hoy - timedelta(days=3), tipo=Gasto.Tipo.LAVADA, valor=10_000, notas="Demo"),
        ])
        # Mantenimientos recientes (aceite, cadena, pastillas y filtro); el resto queda "sin registro"
        hechos = {"aceite": 8, "cadena": 2, "freno_del": 5, "filtro_aire": 15}
        for tarea in TareaMantenimiento.objects.filter(activo=True, pieza__in=list(hechos)).order_by("orden"):
            if tarea.pieza not in hechos:
                continue  # una sola tarea por pieza (la primera del plan)
            atras = hechos.pop(tarea.pieza)
            Mantenimiento.objects.create(moto=moto, tarea=tarea, km=km_hoy - KM_DIA * atras,
                                         fecha=hoy - timedelta(days=atras), notas="Demo")

        motero.suscripciones.all().delete()
        if not sin_plus:
            Suscripcion.objects.create(motociclista=motero, notas="Plan domiciliario · demo").activar()

        # Verificado (sin fotos: así queda tras la revisión) y una pregunta en el foro de domiciliarios
        Verificacion.objects.create(perfil=dp, plataforma="rappi", autorizacion=timezone.now(),
                                    estado=Verificacion.Estado.APROBADA, moto=moto, revisado_en=timezone.now(),
                                    vence=hoy + timedelta(days=150))
        from foro.models import Categoria, Pregunta
        Pregunta.objects.filter(autor=usuario).delete()
        Pregunta.objects.create(autor=usuario, categoria=Categoria.DOMICILIARIOS, linea=linea,
                                titulo="¿Cada cuánto le cambian la cadena si ruedan 170 km al día?",
                                cuerpo="Trabajo en Rappi con una NKD. ¿A cuántos km les dura el kit de arrastre a ustedes?")

        descuentos = ["10 % en mano de obra", "Cambio de aceite con revisión de frenos gratis", "15 % en kit de arrastre"]
        aliados = 0
        for i, taller in enumerate(Taller.objects.filter(activo=True).order_by("-abierto_24h", "nombre")[:3]):
            TallerAliado.objects.update_or_create(taller=taller, defaults={"descuento": descuentos[i], "activo": True, "orden": i})
            aliados += 1
        self.stdout.write(self.style.SUCCESS(
            f"Demo lista: {CORREO} · {len(jornadas)} jornadas · {aliados} talleres aliados · "
            f"{'sin Plus' if sin_plus else 'con Plus'}."))
