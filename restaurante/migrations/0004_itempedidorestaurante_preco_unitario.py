from decimal import Decimal

from django.db import migrations, models


def preencher_preco_unitario(apps, schema_editor):
    ItemPedidoRestaurante = apps.get_model("restaurante", "ItemPedidoRestaurante")
    for item in ItemPedidoRestaurante.objects.select_related("produto").all():
        preco = getattr(item.produto, "preco", None) or Decimal("0.00")
        item.preco_unitario = preco
        item.save(update_fields=["preco_unitario"])


class Migration(migrations.Migration):

    dependencies = [
        ("restaurante", "0003_pedidorestaurante_estoque_baixado_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="itempedidorestaurante",
            name="preco_unitario",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=10),
        ),
        migrations.RunPython(preencher_preco_unitario, migrations.RunPython.noop),
    ]
