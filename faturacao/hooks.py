"""
Registo central de sinais ligados a faturacao (reserva, servicos).
Evita dependencias circulares entre apps no import time.
"""

from decimal import Decimal

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

_REGISTERED = False


def _sync_restaurante_pedido(pedido):
    from faturacao.models import ItemFatura
    from faturacao.services import add_item_fatura, obter_fatura_principal_reserva, recalcular_total_fatura
    from restaurante.models import PedidoRestaurante

    pedido = PedidoRestaurante.objects.get(pk=pedido.pk)
    pedido.recalcular_total()

    if not pedido.reserva_id:
        return
    fatura = obter_fatura_principal_reserva(pedido.reserva)
    if not fatura:
        return
    ref = f"Restaurante pedido #{pedido.pk}"
    ItemFatura.objects.filter(fatura=fatura, descricao=ref).delete()
    recalcular_total_fatura(fatura)
    if pedido.total and pedido.total > 0:
        add_item_fatura(fatura, ref, 1, Decimal(str(pedido.total)))


def register_invoice_signals():
    global _REGISTERED
    if _REGISTERED:
        return
    _REGISTERED = True

    from lavandaria.models import PedidoLavandaria
    from limpeza.models import PedidoLimpeza
    from reservas.models import Reserva
    from restaurante.models import ItemPedidoRestaurante

    from faturacao.services import add_item_fatura, criar_fatura_base_para_reserva, obter_fatura_principal_reserva

    @receiver(post_save, sender=Reserva, dispatch_uid="fam_reserva_fatura")
    def reserva_criada(sender, instance, created, **kwargs):
        if created:
            criar_fatura_base_para_reserva(instance)

    @receiver(post_save, sender=PedidoLimpeza, dispatch_uid="fam_limpeza_item")
    def limpeza_criada(sender, instance, created, **kwargs):
        if not created:
            return
        fatura = obter_fatura_principal_reserva(instance.reserva)
        if not fatura:
            return
        desc = f"Limpeza ({instance.get_tipo_display()}) #{instance.pk}"
        add_item_fatura(fatura, desc, 1, instance.preco)

    @receiver(post_save, sender=PedidoLavandaria, dispatch_uid="fam_lav_item")
    def lavandaria_criada(sender, instance, created, **kwargs):
        if not created:
            return
        fatura = obter_fatura_principal_reserva(instance.reserva)
        if not fatura:
            return
        desc = f"Lavandaria ({instance.get_tipo_display()}) #{instance.pk}"
        add_item_fatura(fatura, desc, 1, instance.preco_total)

    @receiver(post_save, sender=ItemPedidoRestaurante, dispatch_uid="fam_rest_item_save")
    @receiver(post_delete, sender=ItemPedidoRestaurante, dispatch_uid="fam_rest_item_del")
    def restaurante_itens(sender, instance, **kwargs):
        _sync_restaurante_pedido(instance.pedido)

    from faturacao.models import ItemFatura
    from faturacao.services import recalcular_total_fatura

    @receiver(post_save, sender=ItemFatura, dispatch_uid="fam_itemfatura_save")
    @receiver(post_delete, sender=ItemFatura, dispatch_uid="fam_itemfatura_del")
    def item_fatura_alterado(sender, instance, **kwargs):
        recalcular_total_fatura(instance.fatura)
