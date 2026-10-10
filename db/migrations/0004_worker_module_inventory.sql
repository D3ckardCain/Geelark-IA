-- Inventario acotado de módulos reportado por Workers autorizados.
-- checked_at lo fija el Master al aceptar el reporte.
BEGIN;
ALTER TABLE geelark_control.nodes
    ADD COLUMN IF NOT EXISTS module_reports jsonb NOT NULL DEFAULT '[]'::jsonb
        CHECK (
            CASE
                WHEN jsonb_typeof(module_reports) = 'array'
                    THEN jsonb_array_length(module_reports) <= 32
                ELSE false
            END
        );
COMMENT ON COLUMN geelark_control.nodes.module_reports IS
    'Inventario de módulos no autoritativo; los reportes obsoletos se presentan como unknown.';
COMMIT;
