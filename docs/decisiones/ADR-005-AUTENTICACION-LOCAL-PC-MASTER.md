# ADR-005 — Autenticación local del panel PC-MASTER

**Estado:** decisión aceptada; implementación en PR #76, todavía draft y sin despliegue.  
**Fecha:** 2026-10-11.

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
- El HEAD de código `5182e177e4679876de4d7bf51a21cc4541654aa7` pasó CI en [ejecución #38190719448](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38190719448): 26 pruebas administrativas, pruebas negativas de privilegios PostgreSQL, suites del clúster y `pip check`. PostgreSQL remoto exige `host=` explícito y `sslmode=verify-full`. Esto no sustituye la prueba con la base real ni la instalación en PC-MASTER.
- No considerar operativo hasta probar el flujo en el PC-MASTER real y completar revisión de seguridad.
