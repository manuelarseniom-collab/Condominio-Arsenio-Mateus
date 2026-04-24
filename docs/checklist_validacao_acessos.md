# Checklist de validacao operacional de acessos

## 1) Portal publico
- [ ] Visitante acede a `Início`, `Apartamentos`, `Disponibilidade`, `Serviços`, `Restaurante`, `FAQ`, `Depoimentos`, `Contactos` sem login.
- [ ] Navbar mostra `Área do cliente` e `Acesso interno` (sem expor ações internas diretas).
- [ ] Visitante que tenta abrir área interna recebe mensagem de área restrita.

## 2) Cliente
- [ ] Cliente sem reserva confirmada não entra na área de cliente.
- [ ] Cliente com reserva confirmada entra na área do cliente.
- [ ] Cliente com reserva confirmada, mas sem estadia ativa, vê bloqueio de serviços.
- [ ] Mensagem de bloqueio de serviços: "Serviço disponível apenas para hóspedes com estadia iniciada."
- [ ] Cliente com estadia ativa consegue aceder ao módulo de serviços.

## 3) Trabalhador
- [ ] Login de trabalhador funciona apenas com credenciais internas autorizadas.
- [ ] Trabalhador acede ao dashboard interno.
- [ ] Trabalhador vê menus operacionais (reservas, serviços solicitados, clientes, disponibilidade, check-in/check-out, relatórios).
- [ ] Trabalhador não acede a áreas exclusivas de administração.

## 4) Administracao
- [ ] Login de administração funciona apenas para perfis administrativos.
- [ ] Administração acede ao painel geral com visão global.
- [ ] Administração consegue consultar reservas, histórico, pagamentos, serviços, clientes, trabalhadores e apartamentos.
- [ ] Administração mantém acesso transversal às áreas necessárias.

## 5) Mensagens e UX
- [ ] Mensagem de acesso restrito aparece em tentativas sem permissão.
- [ ] Mensagem de orientação ao utilizador aponta a área correta (cliente/interno).
- [ ] Textos de perfil usam nomenclatura institucional: visitante interessado, cliente confirmado, trabalhador, recepcionista, administrador do condomínio, administrador do sistema.

## 6) Verificacao tecnica minima
- [ ] Executar `python manage.py check`.
- [ ] Executar `python manage.py test usuarios`.
- [ ] Validar manualmente cenários críticos em navegador com utilizadores de teste.
