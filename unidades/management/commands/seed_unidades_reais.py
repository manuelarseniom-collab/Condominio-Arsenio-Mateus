from decimal import Decimal

from django.core.management.base import BaseCommand

from unidades.models import Unidade


TIPOLOGIAS = {
    "T0": {
        "preco": Decimal("500000"),
        "capacidade": 2,
        "sofa": True,
        "quartos": 0,
        "descricao": "Estudio com kitchenette, WC, TV, ar condicionado e sofa-cama.",
    },
    "T1": {
        "preco": Decimal("750000"),
        "capacidade": 3,
        "sofa": True,
        "quartos": 1,
        "descricao": "Apartamento T1 com suite, sala, cozinha, TV e ar condicionado.",
    },
    "T2": {
        "preco": Decimal("1000000"),
        "capacidade": 4,
        "sofa": False,
        "quartos": 2,
        "descricao": "Apartamento T2 equipado com sala, cozinha e conforto familiar.",
    },
    "T3": {
        "preco": Decimal("1200000"),
        "capacidade": 6,
        "sofa": False,
        "quartos": 3,
        "descricao": "Apartamento T3 amplo para familia, com sala e cozinha equipada.",
    },
    "PENTHOUSE": {
        "preco": Decimal("2000000"),
        "capacidade": 8,
        "sofa": False,
        "quartos": 4,
        "descricao": "Penthouse premium com 4 suites, sala grande, cozinha e terraco privado.",
    },
}


UNIDADES_POR_ANDAR = {
    1: [("101", "T1"), ("102", "T1"), ("103", "T1"), ("104", "T0"), ("105", "T0"), ("106", "T3")],
    2: [("201", "T1"), ("202", "T1"), ("203", "T0"), ("204", "T0"), ("205", "T3")],
    3: [("301", "T1"), ("302", "T1"), ("303", "T1"), ("304", "T0"), ("305", "T0"), ("306", "T2"), ("307", "T2")],
    4: [
        ("401", "T1"),
        ("402", "T1"),
        ("403", "T1"),
        ("404", "T1"),
        ("405", "T1"),
        ("406", "T1"),
        ("407", "T0"),
        ("408", "T0"),
        ("409", "T2"),
    ],
    5: [("501", "T1"), ("502", "T1"), ("503", "T1"), ("504", "T1"), ("505", "T1"), ("506", "T1"), ("507", "T0"), ("508", "T0")],
    6: [("601", "PENTHOUSE")],
}


class Command(BaseCommand):
    help = "Semeia unidades reais do edificio Arsénio Mateus (idempotente)."

    def handle(self, *args, **options):
        criadas = 0
        atualizadas = 0

        for andar, unidades in UNIDADES_POR_ANDAR.items():
            for codigo, tipologia in unidades:
                cfg = TIPOLOGIAS[tipologia]
                defaults = {
                    "nome": f"Apartamento {codigo}",
                    "andar": andar,
                    "tipo": tipologia,
                    "area_m2": Decimal("65.00") if tipologia != "PENTHOUSE" else Decimal("280.00"),
                    "preco_mensal": cfg["preco"],
                    "disponivel": True,
                    "descricao": cfg["descricao"],
                    "capacidade": cfg["capacidade"],
                    "possui_sofa_cama": cfg["sofa"],
                    "observacoes": "",
                    "numero_quartos": cfg["quartos"],
                }
                obj, created = Unidade.objects.update_or_create(codigo=codigo, defaults=defaults)
                if created:
                    criadas += 1
                    self.stdout.write(self.style.SUCCESS(f"Criada unidade {obj.codigo} ({obj.tipo})"))
                else:
                    atualizadas += 1
                    self.stdout.write(self.style.WARNING(f"Atualizada unidade {obj.codigo} ({obj.tipo})"))

        self.stdout.write(
            self.style.SUCCESS(f"Seed concluido: {criadas} criadas, {atualizadas} atualizadas, total {criadas + atualizadas}.")
        )
