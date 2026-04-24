-- Script unico para base condominio_arsenio_mateus
-- Alinhado com as queries atuais de main.py, app_gui.py e database.py

CREATE DATABASE IF NOT EXISTS condominio_arsenio_mateus;
USE condominio_arsenio_mateus;

CREATE TABLE IF NOT EXISTS unidades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE,
    nome VARCHAR(100) NOT NULL,
    andar INT NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    area_m2 DECIMAL(10,2) NOT NULL,
    preco_mensal DECIMAL(12,2) NULL DEFAULT NULL,
    disponivel BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    telefone VARCHAR(30),
    email VARCHAR(100)
);

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
);

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
);

CREATE INDEX idx_unidades_disponivel ON unidades (disponivel);
CREATE INDEX idx_reservas_estado ON reservas (estado_reserva);
CREATE INDEX idx_pagamentos_data ON pagamentos (data_pagamento);

DELIMITER $$

CREATE TRIGGER trg_pagamentos_sincronizar_valor
BEFORE INSERT ON pagamentos
FOR EACH ROW
BEGIN
    IF NEW.valor IS NULL OR NEW.valor = 0 THEN
        SET NEW.valor = NEW.valor_pago;
    END IF;
END$$

DELIMITER ;

INSERT IGNORE INTO unidades (codigo, nome, andar, tipo, area_m2, disponivel) VALUES
('1A-T2-1', 'Apartamento T2 1', 1, 'T2', 95, TRUE),
('1A-T2-2', 'Apartamento T2 2', 1, 'T2', 95, TRUE),
('1A-T2-3', 'Apartamento T2 3', 1, 'T2', 95, TRUE),
('1A-T2-4', 'Apartamento T2 4', 1, 'T2', 95, TRUE),
('1A-T2-5', 'Apartamento T2 5', 1, 'T2', 95, TRUE),
('1A-ESC-1', 'Escritorio 1', 1, 'ESCRITORIO', 40, TRUE),
('1A-ESC-2', 'Escritorio 2', 1, 'ESCRITORIO', 40, TRUE),
('1A-ESC-3', 'Escritorio 3', 1, 'ESCRITORIO', 40, TRUE),
('1A-ESC-4', 'Escritorio 4', 1, 'ESCRITORIO', 40, TRUE),
('1A-ESC-5', 'Escritorio 5', 1, 'ESCRITORIO', 40, TRUE),
('2A-T1-1', 'Apartamento T1 1', 2, 'T1', 70, TRUE),
('2A-T1-2', 'Apartamento T1 2', 2, 'T1', 70, TRUE),
('2A-T2-1', 'Apartamento T2 1', 2, 'T2', 95, TRUE),
('2A-T2-2', 'Apartamento T2 2', 2, 'T2', 95, TRUE),
('2A-T2-3', 'Apartamento T2 3', 2, 'T2', 95, TRUE),
('2A-T2-4', 'Apartamento T2 4', 2, 'T2', 95, TRUE),
('3A-T1-1', 'Apartamento T1 1', 3, 'T1', 70, TRUE),
('3A-T1-2', 'Apartamento T1 2', 3, 'T1', 70, TRUE),
('3A-T1-3', 'Apartamento T1 3', 3, 'T1', 70, TRUE),
('3A-T2-1', 'Apartamento T2 1', 3, 'T2', 95, TRUE),
('3A-T2-2', 'Apartamento T2 2', 3, 'T2', 95, TRUE),
('3A-T2-3', 'Apartamento T2 3', 3, 'T2', 95, TRUE),
('4A-T1-1', 'Apartamento T1 1', 4, 'T1', 70, TRUE),
('4A-T1-2', 'Apartamento T1 2', 4, 'T1', 70, TRUE),
('4A-T1-3', 'Apartamento T1 3', 4, 'T1', 70, TRUE),
('4A-T2-1', 'Apartamento T2 1', 4, 'T2', 95, TRUE),
('4A-T2-2', 'Apartamento T2 2', 4, 'T2', 95, TRUE),
('4A-T2-3', 'Apartamento T2 3', 4, 'T2', 95, TRUE),
('5A-T1-1', 'Apartamento T1 1', 5, 'T1', 70, TRUE),
('5A-T1-2', 'Apartamento T1 2', 5, 'T1', 70, TRUE),
('5A-T1-3', 'Apartamento T1 3', 5, 'T1', 70, TRUE),
('5A-T2-1', 'Apartamento T2 1', 5, 'T2', 95, TRUE),
('5A-T2-2', 'Apartamento T2 2', 5, 'T2', 95, TRUE),
('5A-T2-3', 'Apartamento T2 3', 5, 'T2', 95, TRUE),
('6A-MASTER-1', 'Apartamento Master', 6, 'MASTER', 180, TRUE);
