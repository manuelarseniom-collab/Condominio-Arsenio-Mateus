from decimal import Decimal

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.db.utils import OperationalError, ProgrammingError


def seed_produtos_base(app_config, **kwargs):
    if app_config.label != "restaurante":
        return
    from restaurante.models import CategoriaProduto, ProdutoRestaurante

    try:
        if CategoriaProduto.objects.exists():
            return
        refeicoes = CategoriaProduto.objects.create(nome="Refeicoes", ordem=1)
        bebidas = CategoriaProduto.objects.create(nome="Bebidas e cafe", ordem=2)

        ProdutoRestaurante.objects.bulk_create(
            [
                ProdutoRestaurante(
                    categoria=refeicoes,
                    nome="Pequeno almoco",
                    preco=Decimal("5000"),
                ),
                ProdutoRestaurante(
                    categoria=refeicoes,
                    nome="Almoco",
                    preco=Decimal("12000"),
                ),
                ProdutoRestaurante(
                    categoria=refeicoes,
                    nome="Jantar",
                    preco=Decimal("12000"),
                ),
                ProdutoRestaurante(
                    categoria=bebidas,
                    nome="Refrigerante",
                    preco=Decimal("1500"),
                ),
                ProdutoRestaurante(
                    categoria=bebidas,
                    nome="Cafe",
                    preco=Decimal("1200"),
                ),
            ]
        )
    except (ProgrammingError, OperationalError):
        return


class RestauranteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "restaurante"

    def ready(self):
        post_migrate.connect(seed_produtos_base, sender=self)
