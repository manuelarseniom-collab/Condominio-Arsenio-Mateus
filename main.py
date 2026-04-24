from database import (
    listar_unidades,
    listar_unidades_disponiveis,
    registrar_cliente,
    criar_reserva,
    listar_reservas_pendentes,
    obter_ou_criar_cliente,
    validar_conflito_reserva,
    cancelar_reserva,
    relatorio_financeiro,
    registrar_pagamento,
    listar_pagamentos,
    relatorio_financeiro_mensal,
)


def mostrar_unidades():
    unidades = listar_unidades()

    print("\n===== TODAS AS UNIDADES =====")
    if not unidades:
        print("Nenhuma unidade encontrada.")
        return

    for unidade in unidades:
        _uid, codigo, nome, andar, tipo, area_m2, disponivel = unidade
        estado = "DISPONIVEL" if disponivel else "RESERVADO"
        print(f"{codigo} | {nome} | Andar {andar} | {tipo} | {area_m2} m2 | {estado}")


def mostrar_unidades_disponiveis():
    unidades = listar_unidades_disponiveis()

    print("\n===== UNIDADES DISPONIVEIS =====")
    if not unidades:
        print("Nenhuma unidade disponível.")
        return

    for unidade in unidades:
        _, codigo, nome, andar, tipo, area_m2, _ = unidade
        print(f"{codigo} | {nome} | Andar {andar} | {tipo} | {area_m2} m2 | DISPONIVEL")


def cadastrar_cliente():
    print("\n===== CADASTRAR CLIENTE =====")

    nome = input("Nome: ").strip()
    telefone = input("Telefone: ").strip()
    email = input("Email: ").strip()

    cliente_id = registrar_cliente(nome, telefone, email)

    if cliente_id:
        print(f"Cliente registado com sucesso! ID: {cliente_id}")
    else:
        print("Falha ao registar cliente.")


def reservar_unidade():
    print("\n===== FAZER RESERVA =====")

    nome_cliente = input("Nome do cliente: ").strip()
    if not nome_cliente:
        print("Nome do cliente é obrigatório.")
        return
    telefone = input("Telefone do cliente: ").strip()
    if not telefone:
        print("Telefone é obrigatório no ato da reserva.")
        return
    email = input("Email do cliente: ").strip()
    if not email:
        print("Email é obrigatório no ato da reserva.")
        return

    data_inicio = input("Data inicio (AAAA-MM-DD): ").strip()
    data_fim = input("Data fim (AAAA-MM-DD): ").strip()

    unidades = listar_unidades_disponiveis(data_inicio, data_fim)
    if not unidades:
        print("Nenhuma unidade disponível para o período informado.")
        return

    print("\nUnidades disponíveis:")
    for unidade in unidades:
        uid, codigo, nome, andar, tipo, area_m2, _ = unidade
        print(f"{uid} | {codigo} | {nome} | Andar {andar} | {tipo} | {area_m2} m2")

    try:
        unidade_id = int(input("ID da unidade para reservar: ").strip())
    except ValueError:
        print("ID da unidade invalido.")
        return

    unidade_selecionada = next((u for u in unidades if u[0] == unidade_id), None)
    if not unidade_selecionada:
        print("Unidade não está na lista disponível.")
        return

    if validar_conflito_reserva(unidade_id, data_inicio, data_fim):
        print("Conflito de reserva detectado para o período.")
        return

    cliente_id = obter_ou_criar_cliente(nome_cliente, telefone, email)
    if not cliente_id:
        print("Falha ao obter/criar cliente automaticamente.")
        return

    confirmar = input("Confirmar reserva? (s/n): ").strip().lower()

    if confirmar == "s":
        sucesso, mensagem = criar_reserva(
            cliente_id,
            unidade_id,
            data_inicio,
            data_fim,
            "PENDENTE",
            0.0,
        )
        print(mensagem)
    else:
        print("Reserva cancelada.")


def ver_reservas():
    reservas = listar_reservas_pendentes()

    print("\n===== RESERVAS =====")
    if not reservas:
        print("Nenhuma reserva encontrada.")
        return

    for reserva in reservas:
        if len(reserva) == 7:
            rid, nome, unidade, inicio, fim, valor, estado = reserva
            print(
                f"Reserva #{rid} | Cliente: {nome} | Unidade: {unidade} | "
                f"{inicio} a {fim} | {valor} Kz | Estado: {estado}"
            )
        else:
            rid, nome, unidade, inicio, fim, valor = reserva
            print(
                f"Reserva #{rid} | Cliente: {nome} | Unidade: {unidade} | "
                f"{inicio} a {fim} | {valor} Kz"
            )


def ver_reservas_pendentes():
    reservas = listar_reservas_pendentes()

    print("\n===== RESERVAS PENDENTES =====")
    if not reservas:
        print("Nenhuma reserva pendente.")
        return

    for reserva in reservas:
        rid, nome, unidade, inicio, fim, valor = reserva
        print(
            f"Reserva #{rid} | Cliente: {nome} | Unidade: {unidade} | "
            f"{inicio} a {fim} | {valor} Kz | Estado: pendente"
        )


def cancelar_uma_reserva():
    print("\n===== CANCELAR RESERVA =====")

    try:
        reserva_id = int(input("ID da reserva: ").strip())
    except ValueError:
        print("ID invalido.")
        return

    sucesso = cancelar_reserva(reserva_id)

    if sucesso:
        print("Reserva cancelada com sucesso!")
    else:
        print("Reserva nao encontrada.")


def ver_relatorio_financeiro():
    total_reservas, total_valor = relatorio_financeiro()

    print("\n===== RELATORIO FINANCEIRO =====")
    print(f"Total de reservas: {total_reservas}")
    print(f"Valor total reservado: {total_valor:.2f} Kz")


def registar_um_pagamento():
    print("\n===== REGISTAR UM PAGAMENTO =====")

    try:
        reserva_id = int(input("ID da reserva: ").strip())
        cliente_id = int(input("ID do cliente: ").strip())
        valor = float(input("Valor pago: ").strip())
    except ValueError:
        print("Dados invalidos.")
        return

    metodo = input("Metodo de pagamento: ").strip()

    sucesso, mensagem = registrar_pagamento(
        reserva_id,
        cliente_id,
        valor,
        metodo,
    )

    print(mensagem)


def ver_pagamentos():
    pagamentos = listar_pagamentos()

    print("\n===== PAGAMENTOS =====")
    if not pagamentos:
        print("Nenhum pagamento encontrado.")
        return

    for pagamento in pagamentos:
        print(pagamento)


def ver_relatorio_mensal():
    relatorio = relatorio_financeiro_mensal()

    print("\n===== RELATORIO FINANCEIRO MENSAL =====")
    if not relatorio:
        print("Nenhum pagamento registado.")
        return

    for linha in relatorio:
        print(linha)


def menu():
    while True:
        print("\n===== SISTEMA DO CONDOMINIO =====")
        print("1 - Ver todas as unidades")
        print("2 - Ver unidades disponiveis")
        print("3 - Cadastrar cliente")
        print("4 - Fazer reserva")
        print("5 - Ver reservas")
        print("6 - Ver reservas pendentes")
        print("7 - Cancelar reserva")
        print("8 - Relatorio financeiro geral")
        print("9 - Registar pagamento")
        print("10 - Ver pagamentos")
        print("11 - Relatorio financeiro mensal")
        print("12 - Sair")

        opcao = input("Escolha uma opcao: ").strip()

        if opcao == "1":
            mostrar_unidades()
        elif opcao == "2":
            mostrar_unidades_disponiveis()
        elif opcao == "3":
            cadastrar_cliente()
        elif opcao == "4":
            reservar_unidade()
        elif opcao == "5":
            ver_reservas()
        elif opcao == "6":
            ver_reservas_pendentes()
        elif opcao == "7":
            cancelar_uma_reserva()
        elif opcao == "8":
            ver_relatorio_financeiro()
        elif opcao == "9":
            registar_um_pagamento()
        elif opcao == "10":
            ver_pagamentos()
        elif opcao == "11":
            ver_relatorio_mensal()
        elif opcao == "12":
            print("Encerrando sistema...")
            break
        else:
            print("Opcao invalida.")


if __name__ == "__main__":
    menu()