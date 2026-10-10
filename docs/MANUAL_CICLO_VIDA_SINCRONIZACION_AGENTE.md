# Manual técnico: ciclo de vida de sincronización del agente

## Propósito y límites

El módulo `AgentReceiptSyncLifecycle` conecta el ciclo de vida del proceso agente con `AgentTransportRuntime.sync_pending_receipts()`. Envía recibos que ya están guardados de forma durable en SQLite. No ejecuta tareas, Android, ADB ni shell; no abre puertos ni listeners; tampoco modifica la configuración de TLS o almacena el token bearer.

## Integración en el proceso agente

1. Construir el journal SQLite y el cliente HTTPS con CA explícita, validación de certificado/hostname y timeout.
2. Construir `AgentTransportRuntime` con el journal y la credencial obtenida de un almacén protegido del sistema operativo.
3. Crear `AgentReceiptSyncLifecycle(runtime=runtime, batch_size=100)`.
4. Llamar a `start()` una sola vez al iniciar el proceso. El sincronizador intenta drenar la cola en un hilo separado.
5. Cuando el detector de conectividad confirme que la red volvió, llamar a `notify_reconnected()`.
6. Mantener heartbeat y publicación de capacidades en el ciclo independiente del agente; los fallos de sincronización no bloquean ese hilo.
7. Durante el apagado ordenado, llamar a `stop(timeout=5)`. Si devuelve `False`, el hilo no terminó dentro del plazo: no se debe afirmar que el apagado de la sincronización concluyó limpiamente.

## Reintentos y durabilidad

- Cada llamada procesa como máximo `batch_size` recibos (1–1000).
- Un error o una respuesta HTTP no exitosa deja el recibo pendiente; el runtime solo guarda el ACK después de un HTTP 2xx.
- El backoff exponencial comienza en 1 segundo, crece hasta 60 segundos y aplica jitter multiplicativo para evitar sincronizaciones simultáneas de muchos nodos. Los valores son configurables.
- Un lote completo confirmado se sigue inmediatamente con otro lote. Una cola vacía queda a la espera de la señal de reconexión; no genera sondeo continuo.
- El callback de error recibe solo el código genérico `RECEIPT_SYNC_FAILED`, nunca el cuerpo HTTP, token ni excepción original.
- El hilo es daemon como protección final del proceso; el apagado ordenado debe llamar explícitamente a `stop()`. El timeout de red del cliente HTTPS debe ser finito.

## Qué funciona offline

- El journal local SQLite conserva recibos ante reinicios y pérdida de red.
- El sincronizador reintenta al iniciar y cuando recibe la notificación de reconexión.
- Heartbeat, capacidades, consulta de estado, reclamación de tareas y cualquier operación remota requieren conectividad.
- El sincronizador no crea recibos ni cambia el estado de la tarea local; únicamente transmite los recibos ya persistidos.

## Pruebas y estado

Las pruebas unitarias usan un runtime simulado y cubren inicio, lote limitado, reintento, jitter, reconexión, configuración inválida y apagado. La prueba `test_receipt_sync_postgres_integration.py` genera una CA/certificado efímeros, levanta Uvicorn en loopback con TLS real, usa `AgentHTTPSClient`, un journal SQLite real y PostgreSQL desechable. Simula la pérdida del primer ACK después del commit y verifica que el reintento use la misma clave idempotente con nonce nuevo, que no duplique la mutación y que el ACK quede persistido en SQLite. El commit `6ac3f07e69b2c80bd3d5e68347e1f5c3dd64b4e1` pasó run 126: 57 pruebas aprobadas, 1 advertencia, `pip check` correcto. La prueba debe seguir ejecutándose para cada cambio de código; no se han realizado pruebas en PCs físicas.
