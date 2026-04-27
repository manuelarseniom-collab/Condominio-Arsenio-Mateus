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


class AcessoPorPerfilTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_model = get_user_model()

    def _criar_utilizador(self, username: str, role: str, password: str = "Teste@123"):
        user = self.user_model.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password=password,
        )
        PerfilUsuario.objects.create(user=user, role=role)
        return user

    def _criar_cliente_com_reserva(self, user, status: str, inicio_offset: int, fim_offset: int):
        cliente = Cliente.objects.create(
            user=user,
            nome="Cliente Teste",
            telefone="+244900000000",
            email=user.email,
        )
        unidade = Unidade.objects.create(
            codigo=f"U-{user.username[:8]}",
            nome="Apartamento Teste",
            andar=2,
            tipo="T1",
            area_m2=Decimal("52.00"),
            preco_mensal=Decimal("250000.00"),
            disponivel=True,
        )
        hoje = timezone.localdate()
        return Reserva.objects.create(
            cliente=cliente,
            unidade=unidade,
            data_inicio=hoje + timedelta(days=inicio_offset),
            data_fim=hoje + timedelta(days=fim_offset),
            status=status,
            nome_completo=cliente.nome,
            email=cliente.email,
            telefone=cliente.telefone,
        )

    def test_visitante_acede_portal_publico(self):
        response = self.client.get(reverse("site_publico:home"))
        self.assertEqual(response.status_code, 200)

    def test_visitante_nao_acede_dashboard_interno(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("usuarios:login"), response.url)

    def test_cliente_confirmado_nao_acede_painel_interno(self):
        user = self._criar_utilizador("clientebloq", PerfilAcesso.CLIENTE_CONFIRMADO)
        self.client.force_login(user)

        response = self.client.get(reverse("operacoes:painel_admin"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Acesso não autorizado para este perfil.")

    def test_trabalhador_acede_dashboard_e_painel_interno(self):
        user = self._criar_utilizador("trabalhador1", PerfilAcesso.RECEPCAO)
        self.client.force_login(user)

        dashboard = self.client.get(reverse("dashboard:home"))
        painel = self.client.get(reverse("operacoes:painel_staff"))

        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(painel.status_code, 200)

    def test_cliente_confirmado_sem_estadia_ativa_ve_bloqueio_servicos(self):
        user = self._criar_utilizador("clientefuturo", PerfilAcesso.CLIENTE_CONFIRMADO)
        self._criar_cliente_com_reserva(
            user=user,
            status="confirmada",
            inicio_offset=7,
            fim_offset=10,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("portal_cliente:servicos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "reserva confirmada e ter iniciado a sua estadia com check-in")

    def test_cliente_confirmado_com_estadia_ativa_pode_solicitar_servicos(self):
        user = self._criar_utilizador("clienteativo", PerfilAcesso.CLIENTE_CONFIRMADO)
        self._criar_cliente_com_reserva(
            user=user,
            status="ativa",
            inicio_offset=-1,
            fim_offset=2,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("portal_cliente:servicos"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Pode solicitar serviços")

    def test_login_cliente_bloqueia_trabalhador(self):
        user = self._criar_utilizador("workerlogin", PerfilAcesso.RECEPCAO, password="Teste@123")
        response = self.client.post(
            reverse("usuarios:login_cliente"),
            {"login_usuario": user.username, "login_senha": "Teste@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Área do cliente disponível apenas após confirmação da reserva.")

    def test_login_trabalhador_exibe_perfil_trabalhador(self):
        self._criar_utilizador("workerperfil", PerfilAcesso.RECEPCAO, password="Teste@123")
        response = self.client.post(
            reverse("usuarios:login_staff"),
            {"login_usuario": "workerperfil", "login_senha": "Teste@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard de Reservas")

    def test_login_admin_exibe_perfil_administrador(self):
        self._criar_utilizador("adminperfil", PerfilAcesso.ADMIN, password="Teste@123")
        response = self.client.post(
            reverse("usuarios:login_admin"),
            {"login_usuario": "adminperfil", "login_senha": "Teste@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Perfil atual:")
        self.assertContains(response, "Administrador")

    def test_logout_retorna_visitante_interessado(self):
        self._criar_utilizador("workerlogout", PerfilAcesso.RECEPCAO, password="Teste@123")
        self.client.post(
            reverse("usuarios:login_staff"),
            {"login_usuario": "workerlogout", "login_senha": "Teste@123"},
            follow=True,
        )
        self.client.post(reverse("usuarios:logout"), follow=True)
        response = self.client.get(reverse("site_publico:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visitante interessado")

    def test_alternancia_contas_nao_mantem_perfil_anterior(self):
        self._criar_utilizador("adminswitch", PerfilAcesso.ADMIN, password="Teste@123")
        self._criar_utilizador("workerswitch", PerfilAcesso.RECEPCAO, password="Teste@123")

        response_admin = self.client.post(
            reverse("usuarios:login_admin"),
            {"login_usuario": "adminswitch", "login_senha": "Teste@123"},
            follow=True,
        )
        self.assertContains(response_admin, "Administrador")

        self.client.post(reverse("usuarios:logout"), follow=True)

        response_worker = self.client.post(
            reverse("usuarios:login_staff"),
            {"login_usuario": "workerswitch", "login_senha": "Teste@123"},
            follow=True,
        )
        self.assertContains(response_worker, "Dashboard de Reservas")

    def test_login_staff_restaurante_redireciona_para_dashboard_restaurante(self):
        self._criar_utilizador("workerresto", PerfilAcesso.STAFF_RESTAURANTE, password="Teste@123")
        response = self.client.post(
            reverse("usuarios:login_staff"),
            {"login_usuario": "workerresto", "login_senha": "Teste@123"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard do Restaurante")

    def test_login_interno_respeita_next_para_restaurante(self):
        self._criar_utilizador("workerrestonext", PerfilAcesso.STAFF_RESTAURANTE, password="Teste@123")
        response = self.client.post(
            f"{reverse('usuarios:login_interno')}?next={reverse('usuarios:dashboard_restaurante')}",
            {"login_usuario": "workerrestonext", "login_senha": "Teste@123", "next": reverse("usuarios:dashboard_restaurante")},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dashboard do Restaurante")

    def test_acesso_interno_exibe_links_diretos_para_modulos(self):
        response = self.client.get(reverse("usuarios:acesso_interno"))
        self.assertContains(response, reverse("usuarios:dashboard_reservas"))
        self.assertContains(response, reverse("usuarios:dashboard_servicos"))
        self.assertContains(response, reverse("usuarios:dashboard_restaurante"))

    def test_perfil_trabalhador_generico_acede_modulos_em_teste(self):
        user = self._criar_utilizador("workergeneric", "trabalhador")
        self.client.force_login(user)
        reservas = self.client.get(reverse("usuarios:dashboard_reservas"))
        servicos = self.client.get(reverse("usuarios:dashboard_servicos"))
        restaurante = self.client.get(reverse("usuarios:dashboard_restaurante"))
        self.assertEqual(reservas.status_code, 200)
        self.assertEqual(servicos.status_code, 200)
        self.assertEqual(restaurante.status_code, 200)

    def test_refresh_nao_altera_perfil(self):
        self._criar_utilizador("workerrefresh", PerfilAcesso.RECEPCAO, password="Teste@123")
        self.client.post(
            reverse("usuarios:login_staff"),
            {"login_usuario": "workerrefresh", "login_senha": "Teste@123"},
            follow=True,
        )
        primeira = self.client.get(reverse("dashboard:home"))
        segunda = self.client.get(reverse("dashboard:home"))
        self.assertContains(primeira, "Trabalhador")
        self.assertContains(segunda, "Trabalhador")

    def test_visitante_bloqueado_em_paineis_por_url_direta(self):
        resp_cliente = self.client.get("/painel-cliente/", follow=True)
        resp_interno = self.client.get("/painel-interno/", follow=True)
        self.assertContains(resp_cliente, "Entrar")
        self.assertContains(resp_interno, "Acesso interno")

    def test_cliente_nao_acede_painel_interno_por_url_direta(self):
        user = self._criar_utilizador("clienteurl", PerfilAcesso.CLIENTE_CONFIRMADO, password="Teste@123")
        self.client.force_login(user)
        response = self.client.get("/painel-interno/", follow=True)
        self.assertContains(response, "Acesso não autorizado para este perfil.")

    def test_trabalhador_nao_acede_admin_por_url_direta(self):
        user = self._criar_utilizador("workerurl", PerfilAcesso.RECEPCAO, password="Teste@123")
        self.client.force_login(user)
        response = self.client.get(reverse("relatorios:lista"), follow=True)
        self.assertContains(response, "Acesso não autorizado para este perfil.")

    def test_logout_cliente_redireciona_para_inicio_sem_erro(self):
        user = self._criar_utilizador("logoutcliente", PerfilAcesso.CLIENTE_CONFIRMADO, password="Teste@123")
        self.client.force_login(user)
        response = self.client.post(reverse("usuarios:logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visitante interessado")

    def test_logout_trabalhador_redireciona_para_inicio_sem_erro(self):
        user = self._criar_utilizador("logoutworker", PerfilAcesso.RECEPCAO, password="Teste@123")
        self.client.force_login(user)
        response = self.client.post(reverse("usuarios:logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visitante interessado")

    def test_logout_admin_redireciona_para_inicio_sem_erro(self):
        user = self._criar_utilizador("logoutadmin", PerfilAcesso.ADMIN, password="Teste@123")
        self.client.force_login(user)
        response = self.client.post(reverse("usuarios:logout"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visitante interessado")

    def test_apos_logout_nao_reentra_no_painel_por_back_ou_refresh(self):
        user = self._criar_utilizador("logoutguard", PerfilAcesso.RECEPCAO, password="Teste@123")
        self.client.force_login(user)
        self.client.get(reverse("dashboard:home"))
        self.client.post(reverse("usuarios:logout"), follow=True)
        painel = self.client.get(reverse("dashboard:home"), follow=True)
        self.assertContains(painel, "Entrar")

    def test_staff_restaurante_acede_dashboard_restaurante(self):
        user = self._criar_utilizador("restok", PerfilAcesso.STAFF_RESTAURANTE)
        self.client.force_login(user)
        response = self.client.get(reverse("usuarios:dashboard_restaurante"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_staff_restaurante_sem_permissao_em_reservas(self):
        user = self._criar_utilizador("restobloq", PerfilAcesso.STAFF_RESTAURANTE)
        self.client.force_login(user)
        response = self.client.get(reverse("usuarios:dashboard_reservas"), follow=True)
        self.assertContains(response, "Sem permissão para o módulo de Reservas.")

    def test_recepcao_acede_dashboards_modulares(self):
        user = self._criar_utilizador("recepcaook", PerfilAcesso.RECEPCAO)
        self.client.force_login(user)
        reservas = self.client.get(reverse("usuarios:dashboard_reservas"))
        servicos = self.client.get(reverse("usuarios:dashboard_servicos"))
        restaurante = self.client.get(reverse("usuarios:dashboard_restaurante"))
        self.assertEqual(reservas.status_code, 200)
        self.assertEqual(servicos.status_code, 200)
        self.assertEqual(restaurante.status_code, 200)

    def test_cliente_bloqueado_em_modulos_internos(self):
        user = self._criar_utilizador("clientebloqmod", PerfilAcesso.CLIENTE_CONFIRMADO)
        self.client.force_login(user)
        response = self.client.get(reverse("usuarios:dashboard_servicos"), follow=True)
        self.assertContains(response, "Sem permissão para o módulo de Serviços.")

