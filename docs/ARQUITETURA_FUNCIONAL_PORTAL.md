# Arquitetura Funcional do Portal Arsénio Mateus

Este documento descreve a arquitetura funcional implementada para separar o portal por perfis, menus, permissões e fluxos operacionais.

## Camadas funcionais

1. **Público/comercial**: conteúdo institucional, disponibilidade e pré-reserva.
2. **Cliente/hóspede**: acompanhamento de reservas, pagamentos e serviços.
3. **Receção**: operação de reservas/pagamentos/clientes.
4. **Staff de serviços**: execução de tarefas por área.
5. **Administração**: visão global e gestão transversal.

## Perfis ativos

- `visitante`
- `cliente_pendente`
- `cliente_confirmado`
- `recepcao`
- `staff_limpeza`
- `staff_lavandaria`
- `staff_restaurante`
- `staff_manutencao`
- `admin`
- `admin_condominio`
- `admin_sistema`

## Regras de acesso

- Controle por role com `role_required`.
- `middleware` da área `/conta/` permite cliente pendente/confirmado, receção e administração.
- Menus adaptativos por perfil via context processor (`navigation_context`).

## Fluxos-chave

### Cliente novo

1. Pesquisa disponibilidade no portal público.
2. Seleciona unidade real.
3. Submete pré-reserva com criação/associação de conta.
4. Reserva persiste com estado `aguardando_pagamento`.
5. Sistema gera fatura e pagamento pendente.
6. Redireciona para resumo/pagamento por `reservation_id`.
7. Reserva aparece em “Minhas reservas”.

### Serviços durante estadia

- Serviços no portal cliente só ficam disponíveis a partir do primeiro dia da estadia com reserva confirmada/ativa.

## Menus por perfil (implementação atual)

- **Visitante**: menu público completo + registo/login.
- **Cliente**: dashboard, minhas reservas, pagamentos/faturas, serviços, histórico.
- **Receção**: reservas, pagamentos, clientes, serviços solicitados, relatórios.
- **Staff**: dashboard + minhas tarefas.
- **Administração**: menu interno completo (reservas, pagamentos, apartamentos, serviços, relatórios).
