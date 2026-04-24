-- Opcional: alinhar uma BD antiga que já tenha `unidade_codigo` em `reservas`.
-- O código Python já não usa esta coluna (usa só `unidade_id` + JOIN a `unidades`).
-- Execute no MySQL Workbench ou CLI; comente linhas que falharem se o objeto não existir.

USE condominio_arsenio_mateus;

DROP TRIGGER IF EXISTS trg_reservas_preencher_unidade_codigo;

-- Se o índice existir:
-- DROP INDEX idx_reservas_unidade_codigo ON reservas;

-- Se a coluna existir:
-- ALTER TABLE reservas DROP COLUMN unidade_codigo;
