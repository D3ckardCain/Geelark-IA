# Corrección de snapshots administrativos

Base: `f9ea8f49355e98e8ef2e89e81a98e893952ca712`.

## Problema
La consulta administrativa renombraba health_state como reported_health_state y usaba datetime.now() local. Confundía la salud derivada con la declaración del agente y podía clasificar mal un heartbeat si el reloj del proceso estaba desfasado.

## Solución
Leer reported_health_state, existente desde la migración 0003. Después de obtener las filas, consultar SELECT clock_timestamp() por la misma conexión y usar ese instante UTC en generated_at y en todos los snapshots. Si falla la consulta del reloj, se propaga el error al manejador HTTP existente; no se fabrican datos con la hora local.
La lectura conserva el límite de 500 nodos y solo ejecuta SELECT. Panel, autenticación, ACL y lanzador se conservan.

## Pruebas
- Heartbeat vencido con reloj PostgreSQL adelantado/atrasado una hora frente al proceso.
- Lista vacía con fecha PostgreSQL verificable.
- Error del reloj sin fallback local.
- PostgreSQL desechable real: salud reportada unhealthy frente a salud derivada healthy; resultado degraded y generated_at entre dos mediciones PostgreSQL.
- Suites Linux, Windows/lanzador, raíz e integración PostgreSQL 16.

Los resultados del commit se registran en #139 tras revisar Actions. No se despliegan workers ni redroid. #77 y #27 siguen pendientes; no se fusionan ni cierran PR/issues.
