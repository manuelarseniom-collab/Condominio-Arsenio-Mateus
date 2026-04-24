# Matriz funcional por perfil e por módulo

Este documento define a arquitetura funcional do portal Arsenio Mateus para orientar implementação, QA e operação.

## Perfis oficiais

- `visitante_interessado`
- `cliente_confirmado`
- `trabalhador`
- `recepcionista`
- `admin_condominio`
- `admin_sistema`

## Princípios de acesso

1. Visitante pode ver conteúdo público e serviços, mas não pode solicitar serviços operacionais.
2. Cliente só solicita serviços após reserva confirmada/ativa e check-in realizado.
3. Trabalhador atua na operação e apoio ao cliente, sem gestão administrativa crítica.
4. Recepcionista tem perfil interno ampliado para reservas, pagamentos e relatórios operacionais.
5. Administração (condomínio/sistema) tem visão global de gestão.
6. Acesso interno é separado e discreto no portal público.
7. Ações internas em nome do cliente devem ser registadas e auditáveis.

## Mensagens padrão

- **Serviço antes do check-in:**  
  `Este serviço só pode ser solicitado após reserva confirmada e check-in realizado.`

- **Acesso interno indevido:**  
  `Acesso restrito. Esta área é reservada a trabalhadores autorizados e à administração do sistema.`

- **Sem permissão geral:**  
  `Não tem permissão para aceder a esta área.`

## Matriz por perfil (resumo executivo)

### 1) visitante_interessado

- Público: consultar
- Disponibilidade: consultar
- Pré-reserva: criar
- Pagamentos: pagar reserva iniciada
- Área cliente: não
- Serviços: visualizar apenas
- Área interna/admin: não

### 2) cliente_confirmado

- Público: consultar
- Área cliente: sim
- Minhas reservas/pagamentos: sim
- Serviços: solicitar apenas após check-in
- Área interna/admin: não

### 3) trabalhador

- Área interna operacional: sim
- Reservas/serviços/clientes/disponibilidade: operar e apoiar
- Reserva assistida: criar em nome do visitante
- Check-in/check-out: apoiar
- Administração crítica: não

### 4) recepcionista

- Área interna: sim
- Reservas/pagamentos/clientes/serviços: operar com foco front-office
- Relatórios operacionais: sim
- Configurações críticas: não (salvo política)

### 5) admin_condominio

- Acesso de gestão global do condomínio
- Gere reservas, pagamentos, serviços, trabalhadores, clientes, unidades e relatórios

### 6) admin_sistema

- Acesso total
- Tudo do admin_condominio + utilizadores/perfis/permissões e configurações sistémicas

## Matriz por módulo

Legenda: `V=visualizar`, `C=criar`, `E=editar`, `A=aprovar/validar`, `G=gerir`, `-=sem acesso`

| Módulo | visitante_interessado | cliente_confirmado | trabalhador | recepcionista | admin_condominio | admin_sistema |
|---|---|---|---|---|---|---|
| Portal público | V | V | V | V | V | V |
| Disponibilidade | V | V | V | V/C (apoio) | V | V |
| Pré-reserva | C | V (suas) | C (assistida) | C/E (assistida) | G | G |
| Pagamentos | C (reserva iniciada) | V/C (seus) | V/C (autorizado + rastreio) | V/C (apoio) | A/G | A/G |
| Área do cliente | - | V/E (perfil próprio) | - | - | V (quando necessário) | V (quando necessário) |
| Serviços - Limpeza | V | C (após check-in) | V/C operacional | V | G | G |
| Serviços - Lavandaria | V | C (após check-in) | V/C operacional | V | G | G |
| Serviços - Restaurante | V (menu) | C (após check-in) | V/C operacional | V | G | G |
| Check-in / Check-out | - | V (estado) | C/E (apoio) | C/E (operar) | G | G |
| Reservas internas/assistidas | - | - | C/E | C/E | G | G |
| Relatórios | - | V (histórico próprio) | V (operacionais) | V (reservas/serviços) | G | G |
| Gestão administrativa | - | - | - | E (limitado por política) | G | G |
| Gestão de utilizadores | - | E (próprio) | - | E (limitado) | G (política) | G total |
| Gestão de apartamentos/unidades | V | V | V | V | G | G |

## Regras específicas de serviços

### Limpeza

- Cliente solicita apenas com estadia ativa
- Formulário: dias, data início, observações
- Preço base: `Kz 10.000/dia`
- Cálculo: `total = dias x 10.000`

### Lavandaria (tabela base)

- Camisa — Kz 2.500
- Blusa — Kz 2.500
- T-shirt — Kz 2.000
- Calção — Kz 2.000
- Calças — Kz 3.000
- Saia — Kz 2.500
- Vestido simples — Kz 4.000
- Casaco leve — Kz 4.500
- Fato completo — Kz 7.500
- Lençóis — Kz 4.000
- Toalha — Kz 2.000
- Edredão/cobertor leve — Kz 8.000

### Restaurante (menu base)

**Bebidas**
- Água 50cl — Kz 500
- Refrigerante lata — Kz 800
- Sumo natural — Kz 1.500
- Cerveja nacional — Kz 1.200

**Refeições**
- Bitoque — Kz 6.500
- Frango grelhado com acompanhamento — Kz 7.500
- Peixe grelhado com acompanhamento — Kz 8.500
- Arroz com carne — Kz 5.500
- Arroz com frango — Kz 5.000
- Hambúrguer com batatas — Kz 4.500
- Omelete completa — Kz 3.500
- Sandes mista — Kz 2.500

**Pequeno-almoço e extras**
- Café — Kz 700
- Chá — Kz 600
- Leite — Kz 800
- Pão com manteiga e ovo — Kz 2.000
- Pequeno-almoço simples — Kz 3.500

## Menus recomendados por perfil interno

### Trabalhador
- Dashboard
- Reservas
- Serviços solicitados
- Clientes
- Disponibilidade
- Nova reserva assistida
- Check-in / Check-out
- Relatórios

### Recepcionista
- Dashboard
- Reservas
- Pagamentos
- Clientes
- Serviços solicitados
- Disponibilidade
- Nova reserva assistida
- Check-in / Check-out
- Relatórios

### Administração
- Painel geral
- Reservas
- Histórico de reservas
- Pagamentos
- Serviços
- Clientes
- Trabalhadores
- Apartamentos
- Check-in / Check-out
- Relatórios
- Configurações

## Resultado esperado

- Experiência pública comercial clara
- Serviços ativados no momento correto da estadia
- Área do cliente útil e contextual
- Área interna focada em operação e apoio
- Administração com visão global e controle total
