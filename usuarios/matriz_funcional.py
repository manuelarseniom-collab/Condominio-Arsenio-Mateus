"""
Matriz funcional central para orientar permissões por perfil e módulo.

Uso sugerido:
- apoiar renderização de menus por perfil
- validar autorização de ações de negócio
- documentar diferenças entre visualizar, criar, aprovar e gerir
"""

from usuarios.models import PerfilAcesso


ACAO_VISUALIZAR = "visualizar"
ACAO_CONSULTAR = "consultar"
ACAO_CRIAR = "criar"
ACAO_EDITAR = "editar"
ACAO_APROVAR = "aprovar"
ACAO_GERIR = "gerir"


MENSAGEM_SERVICO_BLOQUEADO = (
    "Este serviço só pode ser solicitado após reserva confirmada e check-in realizado."
)
MENSAGEM_ACESSO_INTERNO_BLOQUEADO = (
    "Acesso restrito. Esta área é reservada a trabalhadores autorizados e à administração do sistema."
)
MENSAGEM_SEM_PERMISSAO = "Não tem permissão para aceder a esta área."


ROLE_VISITANTE = PerfilAcesso.VISITANTE
ROLE_CLIENTE = PerfilAcesso.CLIENTE_CONFIRMADO
ROLE_TRABALHADOR = "trabalhador"
ROLE_RECEPCAO = PerfilAcesso.RECEPCAO
ROLE_ADMIN_CONDOMINIO = PerfilAcesso.ADMIN_CONDOMINIO
ROLE_ADMIN_SISTEMA = PerfilAcesso.ADMIN_SISTEMA


MATRIZ_MODULOS = {
    "portal_publico": {
        ROLE_VISITANTE: {ACAO_VISUALIZAR},
        ROLE_CLIENTE: {ACAO_VISUALIZAR},
        ROLE_TRABALHADOR: {ACAO_VISUALIZAR},
        ROLE_RECEPCAO: {ACAO_VISUALIZAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_VISUALIZAR},
        ROLE_ADMIN_SISTEMA: {ACAO_VISUALIZAR},
    },
    "disponibilidade": {
        ROLE_VISITANTE: {ACAO_CONSULTAR},
        ROLE_CLIENTE: {ACAO_CONSULTAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR, ACAO_CRIAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_CONSULTAR},
        ROLE_ADMIN_SISTEMA: {ACAO_CONSULTAR},
    },
    "pre_reserva": {
        ROLE_VISITANTE: {ACAO_CRIAR},
        ROLE_CLIENTE: {ACAO_CONSULTAR},
        ROLE_TRABALHADOR: {ACAO_CRIAR},
        ROLE_RECEPCAO: {ACAO_CRIAR, ACAO_EDITAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "pagamentos": {
        ROLE_VISITANTE: {ACAO_CRIAR},
        ROLE_CLIENTE: {ACAO_CONSULTAR, ACAO_CRIAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR, ACAO_CRIAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR, ACAO_APROVAR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR, ACAO_APROVAR},
    },
    "servicos_limpeza": {
        ROLE_VISITANTE: {ACAO_VISUALIZAR},
        ROLE_CLIENTE: {ACAO_VISUALIZAR, ACAO_CRIAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR, ACAO_CRIAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "servicos_lavandaria": {
        ROLE_VISITANTE: {ACAO_VISUALIZAR},
        ROLE_CLIENTE: {ACAO_VISUALIZAR, ACAO_CRIAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR, ACAO_CRIAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "servicos_restaurante": {
        ROLE_VISITANTE: {ACAO_VISUALIZAR},
        ROLE_CLIENTE: {ACAO_VISUALIZAR, ACAO_CRIAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR, ACAO_CRIAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "checkin_checkout": {
        ROLE_VISITANTE: set(),
        ROLE_CLIENTE: {ACAO_CONSULTAR},
        ROLE_TRABALHADOR: {ACAO_CRIAR, ACAO_EDITAR},
        ROLE_RECEPCAO: {ACAO_CRIAR, ACAO_EDITAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "relatorios": {
        ROLE_VISITANTE: set(),
        ROLE_CLIENTE: {ACAO_CONSULTAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "gestao_utilizadores": {
        ROLE_VISITANTE: set(),
        ROLE_CLIENTE: {ACAO_EDITAR},
        ROLE_TRABALHADOR: set(),
        ROLE_RECEPCAO: {ACAO_EDITAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
    "gestao_unidades": {
        ROLE_VISITANTE: {ACAO_VISUALIZAR},
        ROLE_CLIENTE: {ACAO_VISUALIZAR},
        ROLE_TRABALHADOR: {ACAO_CONSULTAR},
        ROLE_RECEPCAO: {ACAO_CONSULTAR},
        ROLE_ADMIN_CONDOMINIO: {ACAO_GERIR},
        ROLE_ADMIN_SISTEMA: {ACAO_GERIR},
    },
}


def role_para_matriz(role: str) -> str:
    if role in {
        PerfilAcesso.STAFF_LIMPEZA,
        PerfilAcesso.STAFF_LAVANDARIA,
        PerfilAcesso.STAFF_RESTAURANTE,
        PerfilAcesso.STAFF_MANUTENCAO,
    }:
        return ROLE_TRABALHADOR
    return role


def pode(role: str, modulo: str, acao: str) -> bool:
    role_matrix = role_para_matriz(role)
    permissoes_modulo = MATRIZ_MODULOS.get(modulo, {})
    permissoes_role = permissoes_modulo.get(role_matrix, set())
    return acao in permissoes_role
