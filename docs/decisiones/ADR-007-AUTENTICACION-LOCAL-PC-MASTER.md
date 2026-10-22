# ADR-007 — Autenticación local del panel PC-MASTER

**Estado:** decisión aceptada; implementación candidata en PR #104, todavía draft y sin integración/despliegue. La numeración ADR-007 mantiene identificadores únicos: ADR-005 corresponde a autenticación de agentes y ADR-006 a lectura de estado Master/Worker.  
**Fecha:** 2026-10-11. **Renumerada:** 2026-10-22 para resolver la colisión entre ramas apiladas.

## Contexto

El panel de operaciones necesita consultar snapshots reales sin abrir operaciones administrativas de escritura. El proyecto mantiene un coste obligatorio de $0 USD y no puede depender de OAuth/SaaS ni de APIs de pago.

## Decisión

1. PC-MASTER gestiona la autenticación del operador localmente.
2. El panel y la API se sirven en el mismo origen con HTTPS obligatorio.
3. Las contraseñas se derivan con PBKDF2-HMAC-SHA256, salt aleatorio y 600.000 iteraciones.
4. Las sesiones usan tokens opacos; SQLite almacena solo SHA-256 del token, con expiración a 8 horas y revocación.
5. PostgreSQL usa exclusivamente el rol `geelark_master_reader`, con lectura de `geelark_control.nodes`, transacciones read-only y timeouts.
6. La interfaz solo consulta snapshots; no se añaden tareas, shell, ADB, reconciliación ni mutaciones.
7. Las pruebas administrativas se integran en el workflow de persistencia existente cuando cambia el paquete, evitando un workflow paralelo.

## Alternativas descartadas

- Supabase Auth / Cloudflare Access / OAuth externo: dependencia de proveedor no necesaria para autenticación local.
- Credenciales o tokens en HTML/localStorage: exposición innecesaria en el navegador.
- Reutilizar el usuario PostgreSQL administrador: privilegios excesivos.
- Servir el panel por HTTP: incompatible con cookie Secure y control de transporte requerido.

## Consecuencias y pendientes

- El acceso a snapshots requiere que PostgreSQL esté disponible; una base remota requiere Internet y TLS verificado. Para autonomía máxima, preferir PostgreSQL local.
- Deben configurarse certificados y secretos fuera de Git.
- Debe ejecutarse `packages/cluster-master-admin/sql/verify_readonly_role.sql` conectado como lector para verificar grants reales.
- La CI del HEAD actual de PR #104 (`3b71c7979f068e5759d263dd9af13f65fc1161fd`) reporta suite raíz 293 passed/3 skipped, Windows ACL 50 passed/8 skipped y `pip check` limpio. Es evidencia de pruebas automatizadas para ese SHA, no aceptación manual, integración ni despliegue. PostgreSQL remoto exige `host=` explícito y `sslmode=verify-full`.
- No considerar operativo hasta probar el flujo en el PC-MASTER real y completar revisión de seguridad.
