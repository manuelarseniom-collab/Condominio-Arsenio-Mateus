## Checklist de Produção - Portal Arsénio Mateus

- Perfis isolados e dinâmicos por sessão (`visitante_interessado`, `cliente`, `trabalhador`, `administrador`).
- Menus e navegação condicionados por `perfil_atual` em templates base.
- Logout via `POST` + CSRF, com limpeza de sessão e redirecionamento para home pública.
- Bloqueio de URL direta para áreas sem permissão com mensagem de acesso não autorizado.
- Rotas internas protegidas por decoradores de perfil (`cliente_required`, `interno_required`, `trabalhador_required`, `administrador_required`).
- Regras de ativação do cliente aplicadas: pagamento confirmado + reserva confirmada => cliente ativo.
- Fluxo de confirmação manual por WhatsApp ativo na operação interna.
- Testes automatizados de autenticação/perfil/sessão executados com sucesso.
- `python manage.py check` executado sem issues.
- Backup local da base SQLite criado em `backups/`.

## Itens recomendados antes de produção real

- Definir `DEBUG=False`.
- Definir `SECRET_KEY` segura via variável de ambiente.
- Configurar `ALLOWED_HOSTS` com domínios reais.
- Ativar HTTPS/reverse proxy e políticas de cookies seguras.
- Configurar backend de email SMTP real.
