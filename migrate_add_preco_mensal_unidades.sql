USE condominio_arsenio_mateus;

ALTER TABLE unidades
ADD COLUMN IF NOT EXISTS preco_mensal DECIMAL(12,2) NULL DEFAULT NULL
AFTER area_m2;

UPDATE unidades
SET preco_mensal = CASE UPPER(TRIM(tipo))
    WHEN 'T1' THEN 500000
    WHEN 'T2' THEN 750000
    WHEN 'MASTER' THEN 1500000
    WHEN 'ESCRITORIO' THEN 200000
    ELSE preco_mensal
END
WHERE preco_mensal IS NULL OR preco_mensal = 0;
