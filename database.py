import mysql.connector
from mysql.connector import Error
from datetime import datetime, date

from calculo_reserva import (
    calcular_valor_reserva,
    valor_mensal_efetivo,
    quantidade_periodos_reserva,
)


DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "2005",
    "database": "condominio_arsenio_mateus",
}


def get_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Erro ao ligar ao MySQL: {e}")
    return None


def _has_unidades_preco_mensal(cursor):
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'unidades'
          AND COLUMN_NAME = 'preco_mensal'
        """
    )
    return int(cursor.fetchone()[0]) > 0


def _ensure_unidades_preco_mensal(cursor):
    if not _has_unidades_preco_mensal(cursor):
        cursor.execute(
            """
            ALTER TABLE unidades
            ADD COLUMN preco_mensal DECIMAL(12,2) NULL DEFAULT NULL
            AFTER area_m2
            """
        )


def _backfill_unidades_preco_mensal(cursor):
    cursor.execute(
        """
        UPDATE unidades
        SET preco_mensal = CASE UPPER(TRIM(tipo))
            WHEN 'T1' THEN 500000
            WHEN 'T2' THEN 750000
            WHEN 'MASTER' THEN 1500000
            WHEN 'ESCRITORIO' THEN 200000
            ELSE preco_mensal
        END
        WHERE preco_mensal IS NULL OR preco_mensal = 0
        """
    )


def create_tables():
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unidades (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo VARCHAR(20) NOT NULL UNIQUE,
        nome VARCHAR(100) NOT NULL,
        andar INT NOT NULL,
        tipo VARCHAR(20) NOT NULL,
        area_m2 DECIMAL(10,2) NOT NULL,
        preco_mensal DECIMAL(12,2) NULL DEFAULT NULL,
        disponivel BOOLEAN NOT NULL DEFAULT TRUE
    )
    """)

    _ensure_unidades_preco_mensal(cursor)
    _backfill_unidades_preco_mensal(cursor)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nome VARCHAR(100) NOT NULL,
        telefone VARCHAR(30),
        email VARCHAR(100)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        codigo_reserva VARCHAR(40) UNIQUE,
        unidade_id INT NOT NULL,
        cliente_id INT NOT NULL,
        modalidade VARCHAR(20) NOT NULL DEFAULT 'mensal',
        data_inicio DATE NOT NULL,
        data_fim DATE NOT NULL,
        quantidade_periodos INT NOT NULL DEFAULT 1,
        valor_total DECIMAL(12,2) NOT NULL,
        origem VARCHAR(30) DEFAULT 'site',
        status_reserva VARCHAR(20) DEFAULT 'ativa',
        estado_reserva VARCHAR(20) NOT NULL DEFAULT 'pendente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_reserva_unidade FOREIGN KEY (unidade_id) REFERENCES unidades(id),
        CONSTRAINT fk_reserva_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        reserva_id INT NOT NULL,
        cliente_id INT NOT NULL,
        valor_pago DECIMAL(12,2) NOT NULL,
        valor DECIMAL(12,2) NOT NULL,
        metodo_pagamento VARCHAR(50) NOT NULL,
        referencia VARCHAR(100) NULL,
        data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_pagamento_reserva FOREIGN KEY (reserva_id) REFERENCES reservas(id),
        CONSTRAINT fk_pagamento_cliente FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_unidades_disponivel ON unidades (disponivel)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservas_estado ON reservas (estado_reserva)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pagamentos_data ON pagamentos (data_pagamento)")

    cursor.execute("DROP TRIGGER IF EXISTS trg_reservas_preencher_unidade_codigo")

    cursor.execute("DROP TRIGGER IF EXISTS trg_pagamentos_sincronizar_valor")
    cursor.execute("""
    CREATE TRIGGER trg_pagamentos_sincronizar_valor
    BEFORE INSERT ON pagamentos
    FOR EACH ROW
    BEGIN
        IF NEW.valor IS NULL OR NEW.valor = 0 THEN
            SET NEW.valor = NEW.valor_pago;
        END IF;
    END
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Tabelas criadas com sucesso!")


def populate_unidades():
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()

    def _pm(tipo):
        return valor_mensal_efetivo(None, tipo)

    unidades = [
        # 1º andar: 5 T2 + 5 escritórios
        ("1A-T2-1", "Apartamento T2 1", 1, "T2", 95, True, _pm("T2")),
        ("1A-T2-2", "Apartamento T2 2", 1, "T2", 95, True, _pm("T2")),
        ("1A-T2-3", "Apartamento T2 3", 1, "T2", 95, True, _pm("T2")),
        ("1A-T2-4", "Apartamento T2 4", 1, "T2", 95, True, _pm("T2")),
        ("1A-T2-5", "Apartamento T2 5", 1, "T2", 95, True, _pm("T2")),
        ("1A-ESC-1", "Escritório 1", 1, "ESCRITORIO", 40, True, _pm("ESCRITORIO")),
        ("1A-ESC-2", "Escritório 2", 1, "ESCRITORIO", 40, True, _pm("ESCRITORIO")),
        ("1A-ESC-3", "Escritório 3", 1, "ESCRITORIO", 40, True, _pm("ESCRITORIO")),
        ("1A-ESC-4", "Escritório 4", 1, "ESCRITORIO", 40, True, _pm("ESCRITORIO")),
        ("1A-ESC-5", "Escritório 5", 1, "ESCRITORIO", 40, True, _pm("ESCRITORIO")),

        # 2º andar: 2 T1 + 4 T2
        ("2A-T1-1", "Apartamento T1 1", 2, "T1", 70, True, _pm("T1")),
        ("2A-T1-2", "Apartamento T1 2", 2, "T1", 70, True, _pm("T1")),
        ("2A-T2-1", "Apartamento T2 1", 2, "T2", 95, True, _pm("T2")),
        ("2A-T2-2", "Apartamento T2 2", 2, "T2", 95, True, _pm("T2")),
        ("2A-T2-3", "Apartamento T2 3", 2, "T2", 95, True, _pm("T2")),
        ("2A-T2-4", "Apartamento T2 4", 2, "T2", 95, True, _pm("T2")),

        # 3º andar: 3 T1 + 3 T2
        ("3A-T1-1", "Apartamento T1 1", 3, "T1", 70, True, _pm("T1")),
        ("3A-T1-2", "Apartamento T1 2", 3, "T1", 70, True, _pm("T1")),
        ("3A-T1-3", "Apartamento T1 3", 3, "T1", 70, True, _pm("T1")),
        ("3A-T2-1", "Apartamento T2 1", 3, "T2", 95, True, _pm("T2")),
        ("3A-T2-2", "Apartamento T2 2", 3, "T2", 95, True, _pm("T2")),
        ("3A-T2-3", "Apartamento T2 3", 3, "T2", 95, True, _pm("T2")),

        # 4º andar: igual ao 3º
        ("4A-T1-1", "Apartamento T1 1", 4, "T1", 70, True, _pm("T1")),
        ("4A-T1-2", "Apartamento T1 2", 4, "T1", 70, True, _pm("T1")),
        ("4A-T1-3", "Apartamento T1 3", 4, "T1", 70, True, _pm("T1")),
        ("4A-T2-1", "Apartamento T2 1", 4, "T2", 95, True, _pm("T2")),
        ("4A-T2-2", "Apartamento T2 2", 4, "T2", 95, True, _pm("T2")),
        ("4A-T2-3", "Apartamento T2 3", 4, "T2", 95, True, _pm("T2")),

        # 5º andar: igual ao 3º
        ("5A-T1-1", "Apartamento T1 1", 5, "T1", 70, True, _pm("T1")),
        ("5A-T1-2", "Apartamento T1 2", 5, "T1", 70, True, _pm("T1")),
        ("5A-T1-3", "Apartamento T1 3", 5, "T1", 70, True, _pm("T1")),
        ("5A-T2-1", "Apartamento T2 1", 5, "T2", 95, True, _pm("T2")),
        ("5A-T2-2", "Apartamento T2 2", 5, "T2", 95, True, _pm("T2")),
        ("5A-T2-3", "Apartamento T2 3", 5, "T2", 95, True, _pm("T2")),

        # 6º andar: master
        ("6A-MASTER-1", "Apartamento Master", 6, "MASTER", 180, True, _pm("MASTER")),
    ]

    sql = """
    INSERT IGNORE INTO unidades (codigo, nome, andar, tipo, area_m2, disponivel, preco_mensal)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(sql, unidades)
    _ensure_unidades_preco_mensal(cursor)
    _backfill_unidades_preco_mensal(cursor)

    conn.commit()
    cursor.close()
    conn.close()
    print("Unidades do prédio inseridas com sucesso!")


def listar_unidades():
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    preco_col = "preco_mensal" if _has_unidades_preco_mensal(cursor) else "NULL AS preco_mensal"
    cursor.execute(f"""
    SELECT id, codigo, nome, andar, tipo, area_m2, disponivel, {preco_col}
    FROM unidades
    ORDER BY andar, codigo
    """)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()
    return resultados


def _validar_datas_reserva(data_inicio, data_fim):
    try:
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False
    return inicio <= fim


def _periodo_disponibilidade(data_inicio=None, data_fim=None):
    """Referência única: sem datas válidas → hoje (alinha dashboard e lista rápida)."""
    if data_inicio and data_fim and _validar_datas_reserva(data_inicio, data_fim):
        return data_inicio, data_fim
    hoje = date.today().strftime("%Y-%m-%d")
    return hoje, hoje


def listar_unidades_disponiveis(data_inicio=None, data_fim=None):
    """Unidades sem reserva não cancelada a sobrepor o intervalo [inicio, fim]."""
    conn = get_connection()
    if not conn:
        return []

    di, df = _periodo_disponibilidade(data_inicio, data_fim)

    cursor = conn.cursor()
    preco_col = "u.preco_mensal" if _has_unidades_preco_mensal(cursor) else "NULL AS preco_mensal"
    cursor.execute(f"""
    SELECT u.id, u.codigo, u.nome, u.andar, u.tipo, u.area_m2, u.disponivel, {preco_col}
    FROM unidades u
    WHERE NOT EXISTS (
        SELECT 1
        FROM reservas r
        WHERE r.unidade_id = u.id
          AND LOWER(COALESCE(r.estado_reserva, '')) <> 'cancelada'
          AND %s <= r.data_fim
          AND %s >= r.data_inicio
    )
    ORDER BY u.andar, u.codigo
    """, (di, df))
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()
    return resultados


def sincronizar_disponibilidade_unidades():
    """Alinha `unidades.disponivel` com reservas ativas (não canceladas) em CURDATE()."""
    conn = get_connection()
    if not conn:
        return

    cursor = conn.cursor()
    cursor.execute("""
    UPDATE unidades u
    SET disponivel = NOT EXISTS (
        SELECT 1
        FROM reservas r
        WHERE r.unidade_id = u.id
          AND LOWER(COALESCE(r.estado_reserva, '')) <> 'cancelada'
          AND CURDATE() <= r.data_fim
          AND CURDATE() >= r.data_inicio
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def obter_metricas_dashboard():
    """
    Métricas coerentes para KPIs (mesma regra de disponibilidade que listar_unidades_disponiveis sem datas).
    Volume financeiro = mesma base que relatorio_financeiro().
    """
    conn = get_connection()
    if not conn:
        return {
            "total_unidades": 0,
            "unidades_disponiveis": 0,
            "reservas_pendentes": 0,
            "total_clientes": 0,
            "total_reservas_financeiro": 0,
            "valor_total_financeiro": 0.0,
        }

    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM unidades")
    total_unidades = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT COUNT(*)
    FROM unidades u
    WHERE NOT EXISTS (
        SELECT 1
        FROM reservas r
        WHERE r.unidade_id = u.id
          AND LOWER(COALESCE(r.estado_reserva, '')) <> 'cancelada'
          AND CURDATE() <= r.data_fim
          AND CURDATE() >= r.data_inicio
    )
    """)
    unidades_disponiveis = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT COUNT(*) FROM reservas WHERE LOWER(COALESCE(estado_reserva, '')) = 'pendente'
    """)
    reservas_pendentes = int(cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = int(cursor.fetchone()[0])

    cursor.execute("""
    SELECT COUNT(*), COALESCE(SUM(valor_total), 0)
    FROM reservas
    WHERE LOWER(COALESCE(estado_reserva, '')) <> 'cancelada'
    """)
    row = cursor.fetchone()
    total_reservas_financeiro = int(row[0])
    valor_total_financeiro = float(row[1])

    cursor.close()
    conn.close()

    return {
        "total_unidades": total_unidades,
        "unidades_disponiveis": unidades_disponiveis,
        "reservas_pendentes": reservas_pendentes,
        "total_clientes": total_clientes,
        "total_reservas_financeiro": total_reservas_financeiro,
        "valor_total_financeiro": valor_total_financeiro,
    }


def registrar_cliente(nome, telefone, email):
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO clientes (nome, telefone, email)
    VALUES (%s, %s, %s)
    """, (nome, telefone, email))
    conn.commit()

    cliente_id = cursor.lastrowid

    cursor.close()
    conn.close()
    return cliente_id


def buscar_cliente_por_nome(nome):
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, nome, telefone, email
    FROM clientes
    WHERE LOWER(nome) = LOWER(%s)
    ORDER BY id DESC
    LIMIT 1
    """, (nome.strip(),))
    resultado = cursor.fetchone()

    cursor.close()
    conn.close()
    return resultado


def obter_ultimo_id_cliente():
    conn = get_connection()
    if not conn:
        return 0

    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(MAX(id), 0) FROM clientes")
    resultado = cursor.fetchone()

    cursor.close()
    conn.close()
    return int(resultado[0]) if resultado else 0


def criar_cliente_automaticamente(nome, telefone="", email=""):
    nome_limpo = (nome or "").strip()
    if not nome_limpo:
        return None

    proximo_id = obter_ultimo_id_cliente() + 1
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO clientes (id, nome, telefone, email)
    VALUES (%s, %s, %s, %s)
    """, (proximo_id, nome_limpo, (telefone or "").strip(), (email or "").strip()))
    conn.commit()

    cursor.close()
    conn.close()
    return proximo_id


def obter_ou_criar_cliente(nome, telefone="", email=""):
    encontrado = buscar_cliente_por_nome(nome)
    if encontrado:
        cliente_id, _nome, telefone_atual, email_atual = encontrado
        novo_telefone = (telefone or "").strip()
        novo_email = (email or "").strip()
        telefone_final = novo_telefone or (telefone_atual or "")
        email_final = novo_email or (email_atual or "")

        # Sempre sincroniza os dados informados no ato da reserva.
        if telefone_final != (telefone_atual or "") or email_final != (email_atual or ""):
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("""
                UPDATE clientes
                SET telefone = %s, email = %s
                WHERE id = %s
                """, (telefone_final, email_final, cliente_id))
                conn.commit()
                cursor.close()
                conn.close()
        return cliente_id
    return criar_cliente_automaticamente(nome, telefone, email)


def buscar_tipo_unidade(codigo_unidade):
    conn = get_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute("""
    SELECT tipo
    FROM unidades
    WHERE codigo = %s
    """, (codigo_unidade,))
    resultado = cursor.fetchone()

    cursor.close()
    conn.close()

    return resultado[0] if resultado else None


def unidade_disponivel(codigo_unidade):
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()
    cursor.execute("""
    SELECT disponivel
    FROM unidades
    WHERE codigo = %s
    """, (codigo_unidade,))
    resultado = cursor.fetchone()

    cursor.close()
    conn.close()

    return bool(resultado[0]) if resultado else False


def _validar_intervalo_reserva_estrito(data_inicio, data_fim):
    """Reserva exige data_fim > data_inicio (regra de valor e negócio)."""
    try:
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False
    return fim > inicio


def validar_conflito_reserva(unidade_id, data_inicio, data_fim):
    conn = get_connection()
    if not conn:
        return True

    cursor = conn.cursor()
    cursor.execute("""
    SELECT 1
    FROM reservas r
    WHERE r.unidade_id = %s
      AND LOWER(COALESCE(r.estado_reserva, '')) <> 'cancelada'
      AND %s <= r.data_fim
      AND %s >= r.data_inicio
    LIMIT 1
    """, (unidade_id, data_inicio, data_fim))
    conflito = cursor.fetchone() is not None

    cursor.close()
    conn.close()
    return conflito


def criar_reserva(cliente_id, unidade_id, data_inicio, data_fim, status, valor=None):
    # `valor` é ignorado: o total do período vem sempre de calcular_valor_reserva (preço mensal × datas).
    if not _validar_intervalo_reserva_estrito(data_inicio, data_fim):
        return (
            False,
            "Datas invalidas: data fim deve ser maior que data inicio (formato AAAA-MM-DD).",
        )

    conn = get_connection()
    if not conn:
        return False, "Falha na ligação à base de dados."

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id
    FROM clientes
    WHERE id = %s
    """, (cliente_id,))
    cliente = cursor.fetchone()

    if not cliente:
        cursor.close()
        conn.close()
        return False, "Cliente nao encontrado."

    preco_col = "preco_mensal" if _has_unidades_preco_mensal(cursor) else "NULL AS preco_mensal"
    cursor.execute(f"""
    SELECT id, tipo, {preco_col}
    FROM unidades
    WHERE id = %s
    """, (unidade_id,))
    resultado = cursor.fetchone()

    if not resultado:
        cursor.close()
        conn.close()
        return False, "Unidade nao encontrada."

    unidade_id = resultado[0]
    tipo_unidade = resultado[1]
    preco_mensal_col = resultado[2]

    try:
        valor_mensal = valor_mensal_efetivo(preco_mensal_col, tipo_unidade)
        valor_total = calcular_valor_reserva(valor_mensal, data_inicio, data_fim)
        qtd_periodos = quantidade_periodos_reserva(data_inicio, data_fim)
    except ValueError as exc:
        cursor.close()
        conn.close()
        return False, str(exc)

    if validar_conflito_reserva(unidade_id, data_inicio, data_fim):
        cursor.close()
        conn.close()
        return False, "Conflito de reserva no periodo selecionado."

    cursor.execute("""
    INSERT INTO reservas (
        codigo_reserva,
        unidade_id,
        cliente_id,
        modalidade,
        data_inicio,
        data_fim,
        quantidade_periodos,
        valor_total,
        origem,
        status_reserva,
        estado_reserva
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        f"RES-{cliente_id}-{unidade_id}-{data_inicio}",
        unidade_id,
        cliente_id,
        "mensal",
        data_inicio,
        data_fim,
        qtd_periodos,
        valor_total,
        "site",
        status.lower(),
        status.lower()
    ))

    conn.commit()

    cursor.close()
    conn.close()
    sincronizar_disponibilidade_unidades()
    return True, "Reserva criada com sucesso!"


def recalcular_valor_total_reserva(reserva_id):
    """Recalcula valor_total e quantidade_periodos a partir da unidade e das datas."""
    conn = get_connection()
    if not conn:
        return False, "Falha na ligação à base de dados."

    cursor = conn.cursor()
    preco_col = "u.preco_mensal" if _has_unidades_preco_mensal(cursor) else "NULL AS preco_mensal"
    cursor.execute(
        f"""
        SELECT r.unidade_id, r.data_inicio, r.data_fim, u.tipo, {preco_col}
        FROM reservas r
        JOIN unidades u ON u.id = r.unidade_id
        WHERE r.id = %s
        """,
        (reserva_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return False, "Reserva não encontrada."

    _uid, di, df, tipo_un, preco_col = row[0], row[1], row[2], row[3], row[4]
    try:
        vm = valor_mensal_efetivo(preco_col, tipo_un)
        novo_valor = calcular_valor_reserva(vm, di, df)
        qper = quantidade_periodos_reserva(di, df)
    except ValueError as exc:
        cursor.close()
        conn.close()
        return False, str(exc)

    cursor.execute(
        """
        UPDATE reservas
        SET valor_total = %s, quantidade_periodos = %s
        WHERE id = %s
        """,
        (novo_valor, qper, reserva_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True, f"Valor atualizado para {novo_valor:.2f} Kz."


def corrigir_reservas_antigas(apenas_zeros=True):
    """
    Atualiza reservas com valor_total 0 ou NULL (e opcionalmente todas as não canceladas).
    Devolve (atualizadas, ignoradas_erro).
    """
    conn = get_connection()
    if not conn:
        return 0, 0

    cursor = conn.cursor()
    preco_col = "u.preco_mensal" if _has_unidades_preco_mensal(cursor) else "NULL AS preco_mensal"
    if apenas_zeros:
        cursor.execute(
            f"""
            SELECT r.id, r.data_inicio, r.data_fim, u.tipo, {preco_col}
            FROM reservas r
            JOIN unidades u ON u.id = r.unidade_id
            WHERE (r.valor_total IS NULL OR r.valor_total = 0)
            """
        )
    else:
        cursor.execute(
            f"""
            SELECT r.id, r.data_inicio, r.data_fim, u.tipo, {preco_col}
            FROM reservas r
            JOIN unidades u ON u.id = r.unidade_id
            WHERE LOWER(COALESCE(r.estado_reserva, '')) <> 'cancelada'
            """
        )

    rows = cursor.fetchall()
    atualizadas = 0
    ignoradas = 0

    for rid, di, df, tipo_un, preco_col in rows:
        try:
            vm = valor_mensal_efetivo(preco_col, tipo_un)
            novo_valor = calcular_valor_reserva(vm, di, df)
            qper = quantidade_periodos_reserva(di, df)
        except ValueError:
            ignoradas += 1
            continue

        cursor.execute(
            """
            UPDATE reservas
            SET valor_total = %s, quantidade_periodos = %s
            WHERE id = %s
            """,
            (novo_valor, qper, rid),
        )
        atualizadas += int(cursor.rowcount > 0)

    conn.commit()
    cursor.close()
    conn.close()
    return atualizadas, ignoradas


def cancelar_reserva(reserva_id):
    conn = get_connection()
    if not conn:
        return False

    cursor = conn.cursor()

    cursor.execute("""
    UPDATE reservas
    SET estado_reserva = 'cancelada', status_reserva = 'cancelada'
    WHERE id = %s
    """, (reserva_id,))
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        return False

    conn.commit()

    cursor.close()
    conn.close()
    sincronizar_disponibilidade_unidades()
    return True


def relatorio_financeiro():
    conn = get_connection()
    if not conn:
        return 0, 0.0

    cursor = conn.cursor()
    cursor.execute("""
    SELECT COUNT(*), COALESCE(SUM(valor_total), 0)
    FROM reservas
    WHERE LOWER(COALESCE(estado_reserva, '')) <> 'cancelada'
    """)
    resultado = cursor.fetchone()

    cursor.close()
    conn.close()

    total_reservas = resultado[0]
    total_valor = float(resultado[1])
    return total_reservas, total_valor


def registrar_pagamento(reserva_id, cliente_id, valor, metodo_pagamento):

    conn = get_connection()
    if not conn:
        return False, "Falha na ligação à base de dados."

    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, estado_reserva
    FROM reservas
    WHERE id = %s
    """, (reserva_id,))

    reserva = cursor.fetchone()

    if not reserva:
        cursor.close()
        conn.close()
        return False, "Reserva não encontrada."

    estado = reserva[1]

    if estado == "paga":
        cursor.close()
        conn.close()
        return False, "Esta reserva já está paga."

    cursor.execute("""
    INSERT INTO pagamentos (reserva_id, cliente_id, valor_pago, valor, metodo_pagamento)
    VALUES (%s, %s, %s, %s, %s)
    """, (reserva_id, cliente_id, valor, valor, metodo_pagamento))

    cursor.execute("""
    UPDATE reservas
    SET estado_reserva = 'paga'
    WHERE id = %s
    """, (reserva_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return True, "Pagamento registado com sucesso."


def listar_pagamentos():
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.id, p.reserva_id, c.nome, p.valor, p.metodo_pagamento, p.data_pagamento, p.referencia
    FROM pagamentos p
    JOIN clientes c ON p.cliente_id = c.id
    ORDER BY p.id DESC
    """)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()
    return resultados


def relatorio_financeiro_mensal():
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
    SELECT DATE_FORMAT(data_pagamento, '%Y-%m') AS mes, COUNT(*), COALESCE(SUM(valor), 0)
    FROM pagamentos
    GROUP BY DATE_FORMAT(data_pagamento, '%Y-%m')
    ORDER BY mes DESC
    """)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()
    return resultados


def listar_reservas_pendentes():
    conn = get_connection()

    if not conn:
        return []

    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        r.id,
        c.nome,
        u.codigo,
        r.data_inicio,
        r.data_fim,
        r.valor_total
    FROM reservas r
    JOIN clientes c ON r.cliente_id = c.id
    JOIN unidades u ON r.unidade_id = u.id
    WHERE r.estado_reserva = 'pendente'
    ORDER BY r.id DESC
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultados


def listar_reservas_dashboard():
    conn = get_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    cursor.execute("""
    SELECT
        r.id,
        c.nome,
        u.codigo,
        r.data_inicio,
        r.data_fim,
        r.valor_total,
        COALESCE(NULLIF(r.estado_reserva, ''), r.status_reserva, 'pendente') AS estado
    FROM reservas r
    JOIN clientes c ON r.cliente_id = c.id
    JOIN unidades u ON r.unidade_id = u.id
    ORDER BY r.id DESC
    """)
    resultados = cursor.fetchall()

    cursor.close()
    conn.close()
    return resultados
def listar_clientes():
    conn = get_connection()

    if not conn:
        return []

    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, telefone, email
        FROM clientes
        ORDER BY id DESC
    """)

    resultados = cursor.fetchall()

    cursor.close()
    conn.close()

    return resultados


if __name__ == "__main__":
    conn = get_connection()

    if conn:
        print("Ligação ao MySQL feita com sucesso!")
        print("Base de dados ativa:", DB_CONFIG["database"])
        conn.close()
    else:
        print("Falha na ligação ao MySQL.")

    create_tables()
    populate_unidades()
