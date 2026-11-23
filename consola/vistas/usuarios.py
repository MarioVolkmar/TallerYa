"""Sección Usuarios: listado, ficha y acciones (cada una declarada con @accion: permiso y bitácora automáticos)."""
import secrets
import string

from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, Q
from django.shortcuts import get_object_or_404

from cuentas import roles
from cuentas.models import Suscripcion
from cupones.models import CodigoCupon, Motociclista
from domicilio.models import MecanicoDomicilio
from foro.models import Pregunta, Respuesta
from notificaciones.models import Notificacion
from talleres.models import Resena, SolicitudCita, Taller

from ..acciones import ErrorAccion, accion
from ..eliminacion import Dependencia, analizar
from ..forms import FiltroUsuarios, UsuarioForm
from ..limites import LIMITES
from ..paginacion import paginar
from ..models import Bitacora

User = get_user_model()

# En la consola «Sin perfil» se llama por lo que es: cuentas que no terminaron el registro (p. ej. creadas con Google)
NOMBRES_ROL = {**roles.NOMBRES, roles.SIN_PERFIL: "Registro incompleto"}
AYUDA_INCOMPLETO = "Cuentas que se crearon pero no terminaron el registro"


# ---------- Rol (consultando la base, no cachés de la instancia) ----------
def rol_actual(u):
    if u.is_staff:
        return roles.ADMIN
    if Taller.objects.filter(usuario=u).exists():
        return roles.TALLER
    if Motociclista.objects.filter(usuario=u).exists():
        return roles.MOTERO
    if MecanicoDomicilio.objects.filter(usuario=u).exists():
        return roles.MECANICO
    return roles.SIN_PERFIL


def nombre_rol(u):
    return NOMBRES_ROL[rol_actual(u)]


def taller_de(u):
    return Taller.objects.filter(usuario=u).first()


def motero_de(u):
    return Motociclista.objects.filter(usuario=u).first()


def con_marca_domiciliario(qs):
    """Anota es_domiciliario, dom_vigente y dom_pendiente (una subconsulta cada una, sin N+1)."""
    from django.utils import timezone
    from domiciliarios.models import PerfilDomiciliario, Verificacion
    return qs.annotate(
        dom_vigente=Exists(Verificacion.objects.filter(perfil__motociclista__usuario=OuterRef("pk"),
                                                       estado=Verificacion.Estado.APROBADA,
                                                       vence__gte=timezone.localdate())),
        es_domiciliario=Exists(PerfilDomiciliario.objects.filter(motociclista__usuario=OuterRef("pk"))),
        dom_pendiente=Exists(Verificacion.objects.filter(perfil__motociclista__usuario=OuterRef("pk"),
                                                         estado=Verificacion.Estado.PENDIENTE)))


def filtrar_por_rol(qs, rol):
    if rol == "domiciliario":
        return qs.filter(es_domiciliario=True)
    if rol == "domiciliario_pendiente":
        return qs.filter(dom_pendiente=True)
    sin_taller = Q(taller__isnull=True)
    return {
        roles.ADMIN: qs.filter(is_staff=True),
        roles.TALLER: qs.filter(is_staff=False, taller__isnull=False),
        roles.MOTERO: qs.filter(sin_taller, is_staff=False, motociclista__isnull=False),
        roles.SIN_PERFIL: qs.filter(sin_taller, is_staff=False, motociclista__isnull=True),
    }.get(rol, qs)


# ---------- Protecciones comunes ----------
def _proteger(request, u, que):
    """que: 'quitar_admin', 'desactivar' o 'eliminar'."""
    verbos = {"quitar_admin": "quitarte el rol de administrador", "desactivar": "desactivar tu propia cuenta",
              "eliminar": "eliminar tu propia cuenta"}
    if u.pk == request.user.pk:
        raise ErrorAccion(f"No puedes {verbos[que]}.")
    if u.is_superuser and not request.user.is_superuser:
        raise ErrorAccion("Esta cuenta es superusuario: solo otro superusuario puede cambiarla.")
    if u.is_staff and u.is_active and not User.objects.filter(is_staff=True, is_active=True).exclude(pk=u.pk).exists():
        raise ErrorAccion("Es el único administrador activo; nombra a otro antes.")


def _solo_superusuario(request, u):
    if u.is_superuser and not request.user.is_superuser:
        raise ErrorAccion("Esta cuenta es superusuario: solo otro superusuario puede cambiarla.")


# ---------- Eliminación segura: reglas ----------
def _de_motero(contar):
    def contar_usuario(u):
        m = motero_de(u)
        return contar(m) if m else 0
    return contar_usuario


REGLAS_ELIMINAR = [
    Dependencia("talleres vinculados", "taller vinculado", lambda u: Taller.objects.filter(usuario=u).count(), True,
                "es la cuenta de un taller; primero cámbiale el rol para desvincularla."),
    Dependencia("motos", "moto", _de_motero(lambda m: m.motos.count()), True,
                "son su garaje y la hoja de vida de cada moto."),
    Dependencia("citas", "cita", lambda u: SolicitudCita.objects.filter(usuario=u).count(), True,
                "son parte del historial de los talleres."),
    Dependencia("códigos de cupón", "código de cupón", _de_motero(lambda m: m.codigos.count()), True,
                "hay cupones entregados o canjeados a su nombre."),
    Dependencia("suscripciones Plus", "suscripción Plus", _de_motero(lambda m: m.suscripciones.count()), True,
                "son registros de pago."),
    Dependencia("preguntas en el foro", "pregunta en el foro", lambda u: Pregunta.objects.filter(autor=u).count(),
                efecto="se borran con sus respuestas."),
    Dependencia("respuestas en el foro", "respuesta en el foro", lambda u: Respuesta.objects.filter(autor=u).count(),
                efecto="se borran."),
    Dependencia("reseñas", "reseña", lambda u: Resena.objects.filter(usuario=u).count(), efecto="quedan anónimas."),
    Dependencia("notificaciones", "notificación", lambda u: Notificacion.objects.filter(usuario=u).count(),
                efecto="se borran."),
]


def analizar_eliminacion(request, u):
    extra = []
    if u.pk == request.user.pk:
        extra.append("Es tu propia cuenta.")
    elif u.is_staff:
        extra.append("Es administrador: quítale el rol antes de borrarla.")
    return analizar(u, REGLAS_ELIMINAR, extra)


# ---------- Acciones (permiso, transacción y bitácora: consola.acciones.correr) ----------
CAMPOS_ROL = {"rol": ("Rol", nombre_rol), "taller": ("Taller vinculado", taller_de)}


@accion("usuarios.cambiar_rol", modelo=User, nombre="Cambiar rol", campos=CAMPOS_ROL,
        frase="Cambió el rol del usuario #{pk} a {d[rol]}", exito="Ahora es {d[rol]}.")
def cambiar_rol(request, u):
    nuevo = request.POST.get("rol", "")
    if nuevo not in (roles.ADMIN, roles.TALLER, roles.MOTERO):
        raise ErrorAccion("Elige un rol válido.")
    if nuevo == roles.ADMIN:
        _solo_superusuario(request, u)
        u.is_staff = True
    else:
        if u.is_staff:
            _proteger(request, u, "quitar_admin")
            u.is_staff = False
        actual = taller_de(u)
        if nuevo == roles.TALLER and not actual:
            pk = request.POST.get("taller", "")
            taller = Taller.objects.filter(pk=pk, usuario__isnull=True).first() if pk.isdigit() else None
            if not taller:
                raise ErrorAccion("Para el rol Taller elige un taller que aún no tenga cuenta.")
            taller.usuario = u
            taller.save(update_fields=["usuario"])
        if nuevo == roles.MOTERO:
            if actual:
                actual.usuario = None
                actual.save(update_fields=["usuario"])
            if not motero_de(u):
                raise ErrorAccion("Esta cuenta no tiene perfil de motero (celular); debe completarlo desde su cuenta.")
    u.save(update_fields=["is_staff"])


@accion("usuarios.estado", modelo=User, nombre="Activar o desactivar",
        campos={"activa": ("Cuenta activa", lambda u: u.is_active)},
        frase="{verbo} la cuenta del usuario #{pk}", exito="Cuenta {estado}.")
def cambiar_estado(request, u):
    activar = request.POST.get("activa") == "1"
    if not activar:
        _proteger(request, u, "desactivar")
    u.is_active = activar
    u.save(update_fields=["is_active"])
    return {"ctx": {"verbo": "Activó" if activar else "Desactivó", "estado": "activada" if activar else "desactivada"}}


@accion("usuarios.editar", modelo=User, nombre="Editar datos",
        campos={"nombre": ("Nombre", lambda u: u.first_name), "apellido": ("Apellido", lambda u: u.last_name),
                "correo": ("Correo", lambda u: u.email)},
        frase="Editó los datos del usuario #{pk}", exito="Datos guardados.")
def editar(request, u):
    _solo_superusuario(request, u)
    form = UsuarioForm(request.POST, instance=u)
    if not form.is_valid():
        raise ErrorAccion(" ".join(f"{form.fields[c].label}: {e[0]}" for c, e in form.errors.items()))
    form.save()


def contrasena_temporal():
    largo = LIMITES["contrasena_temporal"]["max"]
    alfabeto = string.ascii_letters + string.digits
    while True:
        clave = "".join(secrets.choice(alfabeto) for _ in range(largo))
        if any(c.isdigit() for c in clave) and any(c.isupper() for c in clave) and any(c.islower() for c in clave):
            return clave


@accion("usuarios.contrasena", modelo=User, nombre="Restablecer contraseña", campos={},
        frase="Restableció la contraseña del usuario #{pk}",
        exito="Contraseña temporal creada. Compártela por un canal seguro: se muestra una sola vez.")
def restablecer_contrasena(request, u):
    _solo_superusuario(request, u)
    clave = contrasena_temporal()
    u.set_password(clave)  # también cierra sus sesiones abiertas (cambia el hash de sesión)
    u.save(update_fields=["password"])
    return {"extra": {"contrasena": clave},
            "cambios_extra": [{"campo": "password", "etiqueta": "Contraseña", "antes": "(oculta)",
                               "despues": "temporal nueva (oculta)"}]}


@accion("usuarios.eliminar", modelo=User, nombre="Eliminar",
        campos={"correo": ("Correo", lambda u: u.email), "rol": ("Rol", nombre_rol)},
        frase="Eliminó la cuenta del usuario #{pk} ({a[correo]})", exito="Cuenta eliminada.")
def eliminar(request, u):
    analisis = analizar_eliminacion(request, u)
    if not analisis.se_puede:
        raise ErrorAccion("No se puede eliminar. " + " ".join(analisis.bloqueos) + " Puedes desactivarla en su lugar.")
    _proteger(request, u, "eliminar")
    # Sin motos, códigos ni Plus (ya se verificó): el perfil de motero (celular) se va con la cuenta
    Motociclista.objects.filter(usuario=u).delete()
    u.delete()
    return {"eliminado": True, "extra": {"redirigir": "?seccion=usuarios"}}


# ---------- Vista de la sección ----------
def seccion(request):
    if request.GET.get("id"):
        return ficha(request, request.GET["id"])
    form = FiltroUsuarios(request.GET)
    datos = form.cleaned_data if form.is_valid() else {}
    qs = con_marca_domiciliario(User.objects.select_related("perfil", "taller", "motociclista")).order_by("-date_joined")
    if datos.get("q"):
        q = datos["q"]
        filtro = (Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
                  | Q(taller__nombre__icontains=q))
        if q.lstrip("#").isdigit():
            filtro |= Q(pk=int(q.lstrip("#")))
        qs = qs.filter(filtro)
    qs = filtrar_por_rol(qs, datos.get("rol"))
    if datos.get("estado"):
        qs = qs.filter(is_active=datos["estado"] == "activa")
    datos_pagina = paginar(request, qs, "usuarios")
    return "consola/usuarios.html", {
        "form": form, "filas": [(u, roles.rol_de(u), analizar_eliminacion(request, u)) for u in datos_pagina["pagina"]], "nombres_rol": NOMBRES_ROL,
        "ayuda_incompleto": AYUDA_INCOMPLETO, **datos_pagina,
    }


def ficha(request, pk):
    u = get_object_or_404(User.objects.select_related("perfil"), pk=int(pk) if str(pk).isdigit() else 0)
    motero = motero_de(u)
    citas = SolicitudCita.objects.filter(usuario=u).select_related("taller", "servicio").order_by("-creado")
    preguntas = Pregunta.objects.filter(autor=u).order_by("-pk")
    codigos = (CodigoCupon.objects.filter(motociclista=motero).select_related("cupon__taller").order_by("-creado")
               if motero else CodigoCupon.objects.none())
    from domiciliarios.models import Verificacion
    verificaciones = (Verificacion.objects.filter(perfil__motociclista__usuario=u)
                      .select_related("perfil__motociclista__usuario", "moto", "revisado_por").order_by("-creado")[:10])
    return "consola/usuario_ficha.html", {
        "verificaciones": verificaciones, "es_domiciliario": hasattr(motero, "domiciliario") if motero else False,
        "u": u, "rol_u": rol_actual(u), "nombres_rol": NOMBRES_ROL, "ayuda_incompleto": AYUDA_INCOMPLETO, "motero": motero, "taller_u": taller_de(u),
        "motos": motero.motos.select_related("linea__marca") if motero else [],
        "citas": citas[:8], "n_citas": citas.count(),
        "codigos": codigos[:8], "n_codigos": codigos.count(),
        "plus": motero.suscripciones.all()[:5] if motero else [],
        "preguntas": preguntas[:5], "n_preguntas": preguntas.count(),
        "n_respuestas": Respuesta.objects.filter(autor=u).count(),
        "n_resenas": Resena.objects.filter(usuario=u).count(),
        "talleres_libres": Taller.objects.filter(usuario__isnull=True).order_by("nombre").only("pk", "nombre"),
        "historial": Bitacora.objects.filter(objeto_tipo="user", objeto_id=u.pk)[:10],
        "eliminacion": analizar_eliminacion(request, u),
        "form": UsuarioForm(instance=u), "es_yo": u.pk == request.user.pk,
    }
