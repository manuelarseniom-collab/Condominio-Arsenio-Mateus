from decimal import Decimal

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db.utils import OperationalError, ProgrammingError


def seed_tabela_precos(app_config, **kwargs):
    if app_config.label != "faturacao":
        return
    from faturacao.models import TabelaPreco

    try:
        if not TabelaPreco.objects.exists():
            TabelaPreco.objects.bulk_create(
                [
                    TabelaPreco(
                        codigo="baixa",
                        nome="Epoca baixa",
                        multiplicador=Decimal("1.00"),
                    ),
                    TabelaPreco(
                        codigo="media",
                        nome="Epoca media",
                        multiplicador=Decimal("1.10"),
                    ),
                    TabelaPreco(
                        codigo="alta",
                        nome="Epoca alta",
                        multiplicador=Decimal("1.25"),
                    ),
                ]
            )
    except (ProgrammingError, OperationalError):
        pass


class FaturacaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "faturacao"
    verbose_name = "Faturacao"

    def ready(self):
        post_migrate.connect(seed_tabela_precos, sender=self)
        from faturacao.hooks import register_invoice_signals

        register_invoice_signals()
