# Generated manually — estados de agenda, hóspedes e referência de pagamento

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservas", "0002_alter_reserva_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="reserva",
            name="numero_hospedes",
            field=models.PositiveSmallIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="reserva",
            name="observacoes",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="reserva",
            name="pagamento_entidade",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Entidade bancária de referência (referência multibanco / similar).",
                max_length=5,
            ),
        ),
        migrations.AddField(
            model_name="reserva",
            name="pagamento_referencia",
            field=models.CharField(
                blank=True,
                db_index=True,
                default="",
                help_text="Referência numérica associada ao pagamento da pré-reserva.",
                max_length=12,
            ),
        ),
        migrations.AlterField(
            model_name="reserva",
            name="status",
            field=models.CharField(
                choices=[
                    ("rascunho", "Rascunho"),
                    ("pendente", "Pendente"),
                    ("pre_reserva", "Pre-reserva"),
                    ("aguardando_pagamento", "Aguardando pagamento"),
                    ("pagamento_em_validacao", "Pagamento em validacao"),
                    ("aguardando_confirmacao", "Aguardando confirmacao"),
                    ("confirmada", "Confirmada"),
                    ("ativa", "Ativa"),
                    ("concluida", "Concluida"),
                    ("cancelada", "Cancelada"),
                ],
                default="rascunho",
                max_length=30,
            ),
        ),
    ]
