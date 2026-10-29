# Transporte HTTPS privado de agentes

Paquete experimental independiente del dominio y sin listener automático.

## Política de acceso

- Un nodo `pending` con credencial `pending` solo puede enviar heartbeat, publicar capacidades y consultar su propio estado.
- Un nodo `active` con credencial `active` puede acceder a las rutas de agente configuradas.
- Combinaciones inconsistentes, estados revocados y credenciales vencidas fallan cerradas.
- La autorización se evalúa por operación; no se confía en cabeceras proxy ni en datos del cuerpo para decidir permisos.

## Controles

- La aplicación ASGI rechaza HTTP plano con 426. El listener TLS exige certificado y clave; no se inicia automáticamente.
- Listener y cliente solo aceptan RFC1918 IPv4, IPv6 ULA o loopback; rechazan DNS, IP pública, rangos de documentación, link-local y CGNAT.
- El agente envía `Authorization: Bearer`, `X-Agent-Nonce` (UUID), `X-Agent-Timestamp` (ISO-8601 con zona) y `X-Request-ID` (UUID).
- Nonces persistentes en PostgreSQL, ventana temporal de ±5 minutos y rechazo de replay.
- Las escrituras requieren `Idempotency-Key` de 16-200 caracteres. El runner PostgreSQL conserva el hash del payload y el snapshot de respuesta en la misma transacción que la operación de dominio; una clave con payload distinto devuelve conflicto.
- El handler de escritura recibe `conn` y debe usar esa misma conexión para que la mutación de dominio y la respuesta idempotente sean atómicas.
- Límite de cuerpo por defecto: 1 MiB.
- `InMemoryRateLimiter` limita a 60 solicitudes/minuto/nodo por proceso y solo es apropiado para pruebas o un único worker.
- `PostgresRateLimiter` usa un UPDATE atómico en la fila del nodo y aplica el límite global entre workers/procesos. Requiere la migración `db/migrations/0003_agent_rate_limit.sql`; el contador se satura para evitar desbordamiento.
- El cliente `AgentHTTPSClient` usa la CA explícita, verifica cadena y hostname/IP, exige TLS 1.2+, no sigue redirects, rechaza path traversal y limita timeout, cuerpos y respuestas.
- `AgentTransportRuntime` conecta el cliente con un journal compatible: persiste progreso/resultados antes de enviarlos y ofrece `sync_pending_receipts(limit=100)` para recorrer un lote acotado. El journal debe exponer `list_pending_receipts(limit=...)` y `mark_receipt_synced(operation_id, expected_status=..., expected_result=...)`. Tras HTTP 2xx solo se confirma la versión exacta enviada; si el recibo cambió durante la petición, el ACK tardío se rechaza y la versión nueva permanece pendiente. Las APIs antiguas sin versión fallan cerradas. Los estados `accepted` no se envían como resultados. No ejecuta tareas ni inicia polling por sí solo.
- Las respuestas no incluyen tokens, SQL ni excepciones internas.
- Los handlers de dominio no configurados responden 503; el paquete no ejecuta shell/ADB ni comandos Android.

## Integración

Para el primer tramo de telemetría, usar:
- `authenticate=make_database_authenticator(connect)`
- `consume_nonce=make_database_nonce_consumer(connect)`
- `idempotency_runner=make_database_idempotency_runner(connect)`
- `rate_limiter=PostgresRateLimiter(connect)` para despliegues reales/multiworker.
- `handlers=make_postgres_agent_handlers(connect)`
- `AgentTransportRuntime(client=https_client, bearer_token=token, journal=agent_journal, local_node_id=node_id)` para integrar el cliente con el journal local del agente.

Los handlers incluidos vuelven a comprobar estado/credencial bajo bloqueo de fila antes de mutar; guardan heartbeat/capacidades y consultan únicamente el nodo autenticado. Los handlers de tareas/reconciliación están implementados en la rama de bandeja durable y se conectan solo al crear explícitamente `make_postgres_agent_handlers`; esta PR sigue draft y no habilita ningún listener ni despliegue. La reconciliación permanece de solo lectura; no se ejecuta Android, ADB ni shell.

## Estado de validación y pendientes

La última CI de la rama consolidada PR #85 pasó contra PostgreSQL desechable:
- Transporte [#38281405401](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38281405401): **182 pruebas** y `pip check` limpio; incluye la suite de journal/SQLite.
- Persistencia/servicio [#38281404982](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38281404982): 32 pruebas de persistencia, 18 de guard y 54 de autorización; `pip check` limpio.
- Esquema [#38281404382](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38281404382): migraciones e invariantes aprobadas.

Pendiente:
- Integrar el cliente HTTPS y el journal con el bucle real del agente y validar en hardware anfitrión.
- Completar el manual de generación, rotación, respaldo y distribución de CA local.
- No conectar handlers de producción ni desplegar hasta cerrar los criterios anteriores.

Los tests de configuración TLS usan archivos ficticios para probar restricciones del listener, no para simular certificados válidos. El paquete no instala software en PCs físicas ni requiere APIs o servicios de pago.

## Instalación local del monorepo

El transporte delega la autorización en el paquete canónico `cluster-agent-auth`. Instala ambos paquetes desde la raíz del repositorio; no instales el transporte de forma aislada.

```sh
python -m pip install -e "packages/cluster-agent-auth[test]"
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pip check
```

La autenticación PostgreSQL devuelve `credential_expires_at`; la política canónica vuelve a validar ese timestamp en cada operación.

## Pruebas locales

```sh
python -m pip install -e "packages/cluster-agent-auth[test]"
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pytest packages/cluster-agent-transport/tests -q
```


## Inventario de módulos (v1, en revisión)

- `PUT /agent/v1/modules` acepta IDs de una lista cerrada: `agent-supervisor`, `agent-transport`, `agent-guard`, `task-journal` y `android-engine`.
- Solo un nodo `active` puede publicar estados de módulos. Un nodo `pending` recibe 403 y conserva exclusivamente heartbeat, capacidades y consulta de su propio estado.
- El Master fija `checked_at`; no confía en el reloj del Worker.
- Si el heartbeat supera 90 segundos o el reporte supera 5 minutos, el estado leído pasa a `unknown`, con origen `master-check` y código seguro (`NODE_STALE` o `REPORT_STALE`).
- Migración requerida: `db/migrations/0004_worker_module_inventory.sql`. No está desplegado ni conectado a PCs físicas.

- Esquema normativo del payload: [worker-module-inventory-v1.schema.json](../../docs/contracts/worker-module-inventory-v1.schema.json); [ejemplo](../../docs/contracts/examples/worker-module-inventory-v1.example.json).

## Bandeja durable de tareas (en revisión)

- `POST /agent/v1/tasks/claim` entrega una única asignación tipada a un nodo `active/active` y saludable; los nodos `pending` reciben 403.
- Claim, aceptación, progreso y resultado usan idempotencia, nonce anti-replay, propietario, epoch y leases de entrega/asignación.
- El claim bloquea la tarea, instancia y operación con `FOR UPDATE ... SKIP LOCKED`; la respuesta incluye las dos expiraciones de lease.
- Los resúmenes de resultado se limitan a 1 MB y rechazan claves sensibles en snake_case, kebab-case o camelCase.
- `POST /agent/v1/reconcile` es estrictamente read-only: devuelve discrepancias y `mutations_applied=0`; `unknown` requiere revisión.
- Migración secuencial al inventario de módulos: `db/migrations/0005_agent_task_inbox.sql`; smoke SQL: `db/tests/0005_agent_task_inbox_smoke.sql`.
- La prueba de integración PostgreSQL cubre doble claim concurrente, recuperación idempotente, lease de entrega, estados terminales, campos sensibles y epoch obsoleto. La integración con el bucle real del agente sigue pendiente.

No activar listeners ni desplegar en nodos físicos hasta que la pila completa esté revisada y sus pruebas pasen sobre el HEAD actualizado.


## Sincronización durable del agente

`AgentReceiptSyncLifecycle` ejecuta `runtime.sync_pending_receipts(limit=...)` en un hilo independiente, con lotes acotados, reintentos con backoff/jitter y activación por reconexión. El ACK solo se persiste después de HTTP 2xx; si se pierde la respuesta, el mismo recibo se reintenta con la clave de idempotencia estable. El supervisor de telemetría debe permanecer independiente de este worker.

- El journal SQLite es local y durable; sin conectividad conserva recibos para reintentar.
- Heartbeat, capacidades y consulta de estado siguen requiriendo conectividad y no se encolan en esta capa.
- Este coordinador no reclama ni ejecuta tareas, no abre listeners y no activa ADB/shell.
- La prueba de integración crea TLS de loopback, SQLite y PostgreSQL desechable; no sustituye pruebas en hardware físico.


## Supervisor de telemetría

`AgentNodeSupervisor` coordina heartbeat, capacidades y consulta de estado con ciclos separados y límites explícitos; la sincronización durable usa `AgentReceiptSyncLifecycle` en un hilo independiente. La fábrica `build_agent_components()` construye el cliente TLS, runtime, journal/sincronizador y supervisor sin arrancar hilos automáticamente.

El CLI `geelark-agent --config /ruta/agente.toml` requiere configuración explícita y mantiene `credential_provider = "file"` por defecto; Linux/systemd puede usar `credential_provider = "systemd"` cuando el servicio monte una credencial mediante `LoadCredential`. No se incluye unit file ni instalador de producción. No se ejecutan tareas, ADB ni shell.


## Retención y mantenimiento manual

La política de vencimiento y la rutina manual de preview/poda se documentan en [Manual de retención de agentes](../../docs/MANUAL_RETENCION_AGENTES.md). No hay limpieza automática ni cron. Los scopes desconocidos no se vencen; los informes inciertos/conflictivos solo pueden borrarse tras exportación revisada, antigüedad >365 días y doble confirmación.


## Ensamblado recomendado para PostgreSQL

Usa `create_postgres_agent_app(connect)` para cablear autenticación, nonces, idempotencia, handlers PostgreSQL y el limitador compartido de 60 solicitudes/minuto por nodo. El callback `connect` debe abrir conexiones con credenciales fuera del DSN y TLS verificado si PostgreSQL es remoto. La función solo construye la app ASGI: no inicia un listener ni configura TLS. El runtime debe servirla exclusivamente por HTTPS. El limitador en memoria de `create_agent_app` es para pruebas/desarrollo, no para límites globales multiworker.


## Leases de tareas y reloj autoritativo — 2026-10-12

- La lease de entrega de 30 segundos solo gobierna la fase `delivered` y el ACK inicial. Si la tarea ya está `accepted` o `running`, el vencimiento de esa lease no bloquea el progreso ni el resultado.
- La lease de asignación y el `assignment_epoch` siguen siendo obligatorios para aceptar/progresar/finalizar; si vencen, la operación falla cerrada.
- La reconciliación reconoce el par esperado `agent_tasks.status=delivered` + `operations.status=accepted`. Una entrega no aceptada cuya lease vence queda en hold; una tarea activa con lease de asignación vigente no queda bloqueada por la antigua lease de entrega.
- Las comparaciones de leases usan `now()` de PostgreSQL, no el reloj del proceso, para evitar aceptar asignaciones vencidas si el reloj de la aplicación está atrasado.
- Pruebas de regresión: progreso tras vencer la lease de entrega, reconciliación de tareas activas y simulación de reloj de aplicación una hora atrasado.

## Revalidación de ACK durable — 2026-10-12

- Se integró en la rama del supervisor el journal versionado del PR #38, incluyendo migraciones v1→v3 y pruebas de recibos.
- `mark_receipt_synced` compara estado y resultado canónicos bajo `BEGIN IMMEDIATE`; un ACK de versión obsoleta no oculta el recibo actual. `unknown` puede sincronizarse como incertidumbre sin convertirse en éxito/fallo.
- El workflow fija el journal al commit `5815bc6e8f4146099e5fff028008fdf9f0ede5d6`, ejecuta primero la suite del journal y luego la suite del transporte. La prueba SQLite real ya no se omite por falta de API.
- CI del HEAD `17222427612d41c6cea0a16d2633a8b819933393`: transporte #38281405401 (182 pruebas + journal/SQLite), esquema #38281404382 y persistencia/servicio #38281404982; `pip check` limpio. La evidencia cubre CI y PostgreSQL desechable, no instalación en Windows ni despliegue real.
