from django import template

register = template.Library()


@register.inclusion_tag("tramites/_soat_ficha.html")
def soat_ficha(moto, doc):
    """Botón del SOAT en la ficha de la moto: estado del pedido en curso o "Pedir" si ya toca renovar."""
    from tramites.models import PedidoSoat
    pedido = moto.pedidos_soat.exclude(estado=PedidoSoat.Estado.CANCELADA).first()
    if pedido and not pedido.activo and pedido.estado != PedidoSoat.Estado.EMITIDA:
        pedido = None
    mostrar = pedido and (pedido.activo or doc["estado"] == "ok")
    return {"moto": moto, "pedido": pedido if mostrar else None,
            "pedir": not mostrar and (doc["estado"] in ("pronto", "urgente", "vencido") or not doc["vence"])}
