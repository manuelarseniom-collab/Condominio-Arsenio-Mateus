from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from reservas.models import Reserva
from unidades.models import Unidade
from usuarios.models import PerfilAcesso, PerfilUsuario

from .models import Depoimento


class DepoimentosTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_model = get_user_model()

    def _criar_utilizador(self, username: str, role: str):
        user = self.user_model.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="Teste@123",
        )
        PerfilUsuario.objects.create(user=user, role=role)
        return user

    def _criar_reserva(self, user, status: str):
        cliente = Cliente.objects.create(
            user=user,
            nome=f"Cliente {user.username}",
            telefone="+244900000000",
            email=user.email,
        )
        unidade = Unidade.objects.create(
            codigo=f"U-{user.username[:8]}",
            nome="Apartamento Teste",
            andar=1,
            tipo="T1",
            area_m2=Decimal("50.00"),
            preco_mensal=Decimal("200000.00"),
            disponivel=True,
        )
        hoje = timezone.localdate()
        return Reserva.objects.create(
            cliente=cliente,
            unidade=unidade,
            data_inicio=hoje - timedelta(days=1),
            data_fim=hoje + timedelta(days=2),
            status=status,
            nome_completo=cliente.nome,
            telefone=cliente.telefone,
            email=cliente.email,
        )

    def test_visitante_ve_apenas_depoimentos_publicados(self):
        user = self._criar_utilizador("clientepub", PerfilAcesso.CLIENTE_CONFIRMADO)
        reserva = self._criar_reserva(user, "concluida")
        Depoimento.objects.create(
            user=user,
            reserva=reserva,
            titulo="Publicado",
            comentario="Muito bom",
            avaliacao=5,
            status="aprovado",
            publicado=True,
            abusivo=False,
        )
        Depoimento.objects.create(
            user=user,
            titulo="Oculto",
            comentario="Nao deve aparecer",
            avaliacao=1,
            status="rejeitado",
            publicado=False,
            abusivo=True,
        )
        response = self.client.get(reverse("site_publico:depoimentos"))
        self.assertContains(response, "Publicado")
        self.assertNotContains(response, "Oculto")

    def test_cliente_sem_reserva_elegivel_nao_cria_depoimento(self):
        user = self._criar_utilizador("clientesemreserva", PerfilAcesso.CLIENTE_CONFIRMADO)
        self._criar_reserva(user, "confirmada")
        self.client.force_login(user)
        response = self.client.get(reverse("site_publico:criar_depoimento"), follow=True)
        self.assertContains(response, "Só é possível deixar depoimento após uma estadia ativa ou concluída.")

    def test_cliente_com_reserva_ativa_cria_depoimento_pendente(self):
        user = self._criar_utilizador("clienteativo2", PerfilAcesso.CLIENTE_CONFIRMADO)
        self._criar_reserva(user, "ativa")
        self.client.force_login(user)
        response = self.client.post(
            reverse("site_publico:criar_depoimento"),
            {
                "titulo": "Boa estadia",
                "comentario": "Gostei muito da experiência.",
                "avaliacao": 5,
            },
            follow=True,
        )
        self.assertContains(
            response,
            "O seu depoimento foi enviado e ficará visível após validação da administração.",
        )
        depoimento = Depoimento.objects.get(user=user)
        self.assertEqual(depoimento.status, "pendente")
        self.assertFalse(depoimento.publicado)

    def test_trabalhador_nao_pode_criar_depoimento(self):
        user = self._criar_utilizador("workerdepo", PerfilAcesso.RECEPCAO)
        self.client.force_login(user)
        response = self.client.get(reverse("site_publico:criar_depoimento"), follow=True)
        self.assertContains(
            response,
            "Para deixar um depoimento, é necessário ter uma reserva ativa ou concluída.",
        )

    def test_admin_marca_depoimento_como_abusivo(self):
        cliente_user = self._criar_utilizador("clienteabuso", PerfilAcesso.CLIENTE_CONFIRMADO)
        reserva = self._criar_reserva(cliente_user, "concluida")
        depoimento = Depoimento.objects.create(
            user=cliente_user,
            reserva=reserva,
            titulo="Comentario",
            comentario="Texto improprio",
            avaliacao=1,
            status="pendente",
            publicado=False,
            abusivo=False,
        )
        admin_user = self._criar_utilizador("admindepo", PerfilAcesso.ADMIN)
        self.client.force_login(admin_user)
        self.client.post(
            reverse("site_publico:admin_depoimentos"),
            {
                "depoimento_id": depoimento.id,
                "acao": "abusivo",
                "motivo_moderacao": "Conteúdo ofensivo",
            },
            follow=True,
        )
        depoimento.refresh_from_db()
        self.assertTrue(depoimento.abusivo)
        self.assertEqual(depoimento.status, "rejeitado")
        self.assertFalse(depoimento.publicado)
        self.assertEqual(depoimento.motivo_moderacao, "Conteúdo ofensivo")
