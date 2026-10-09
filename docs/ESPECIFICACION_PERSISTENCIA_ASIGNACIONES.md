# Especificación de persistencia de asignaciones — Geelark-IA

**Fecha:** 2026-10-09  
**Estado:** diseño para revisión; no implementado ni validado en PostgreSQL.  
**Relacionado:** ADR-004, especificación del planificador y contrato de mensajes del agente.

## 1. Objetivo

Definir las garantías de persistencia para impedir asignaciones duplicadas, admitir reintentos idempotentes y recuperar el estado tras reiniciar el controlador. La propuesta usa PostgreSQL local en la Master, sujeta a la prueba de concepto. No introduce una base cloud ni exige pagos.

## 2. Invariantes obligatorios

1. Una instancia tiene como máximo un propietario vigente.
2. El estado unknown conserva la propiedad y bloquea nuevas asignaciones.
3. Cada cambio de propietario incrementa un epoch durable y monotónico.
4. La intención se persiste antes de enviar una orden al agente.
5. Repetir clave y payload idempotentes devuelve el resultado registrado.
6. Reutilizar una clave con otro payload produce conflicto.
7. La reserva de recursos se actualiza atómicamente; no depende solo de una lectura antigua del heartbeat.
8. La expiración del lease no elimina por sí sola al propietario.
9. Los cambios de estado verifican propietario, epoch y transición permitida.
10. La auditoría permite reconstruir decisiones sin guardar secretos ni datos privados.
11. La interfaz nunca modifica directamente tablas; las mutaciones pasan por servicios de dominio.

## 3. Entidades lógicas

### Nodos
ID UUID, nombre visible, versión del agente/protocolo, estado administrativo, última observación, última secuencia y capacidades versionadas. Estados: pending, active, draining, maintenance, offline, quarantined y revoked.

### Instancias
ID UUID, estado deseado/observado, nodo propietario nullable, epoch actual, vencimiento de lease, motor, digest de imagen, perfil de recursos y timestamps. No borrar la fila para resolver un estado desconocido.

### Reservas de recursos
ID, nodo, instancia, epoch, RAM, almacenamiento, CPU, estado held/released/uncertain y timestamps. Las reservas se combinan con telemetría; no la sustituyen.

### Operaciones
ID de operación, instancia, nodo, epoch, tipo, estado, código de error, request ID y timestamps. Guardar solo un resumen de resultado sin secretos.

### Registros de idempotencia
Ámbito, clave, hash SHA-256 del payload canónico, operación asociada, respuesta saneada y vencimiento. Restricción única sobre ámbito y clave. No almacenar credenciales.

### Eventos de asignación
Registro append-only de instancia, epoch, nodo, estados anterior/nuevo, actor, motivo, IDs de solicitud/operación y timestamp del servidor.

### Outbox
ID de evento, instancia, epoch, tipo, payload tipado, fecha de creación/envío y contador de intentos. El outbox evita perder una orden si el controlador cae después del commit y antes de enviarla. La entrega puede repetirse; el agente debe deduplicar la operación y comprobar epoch.

## 4. Transacción de asignación

1. Validar autorización, esquema y clave idempotente.
2. Canonicalizar payload y calcular hash.
3. Iniciar transacción.
4. Insertar registro idempotente; ante conflicto, comparar el hash existente.
5. Si clave y hash coinciden, devolver la respuesta persistida; si difieren, devolver IDEMPOTENCY_CONFLICT.
6. Bloquear la fila de instancia con SELECT FOR UPDATE.
7. Rechazar propietario vigente o estado unknown/reconciling.
8. Bloquear y volver a validar la capacidad del nodo candidato dentro de la transacción.
9. Incrementar epoch; asignar propietario, lease inicial y estado reserved.
10. Crear reserva, operación, evento de auditoría y evento outbox.
11. Guardar respuesta idempotente y confirmar la transacción.
12. Un dispatcher entrega el outbox; el agente valida identidad, operación y epoch.
13. Si el candidato pierde capacidad antes de reservar, revertir y evaluar otro candidato.

La selección inicial puede ocurrir fuera de la transacción, pero la elegibilidad y la capacidad deben volver a validarse al reservar.

## 5. Restricciones e índices

- PK/FK para IDs y relaciones.
- CHECK para recursos positivos, epochs no negativos y estados válidos.
- UNIQUE para ámbito y clave idempotente.
- Índice para eventos outbox pendientes por antigüedad.
- Índices para nodo/estado, instancia/epoch y última observación.
- Restricción transaccional que impida dos propietarios activos de una instancia.
- Si se usa índice único parcial, incluir como bloqueantes reserved, starting, running, stopping, unknown y reconciling.

El DDL final debe probarse contra la versión concreta de PostgreSQL. Este documento no es una migración SQL.

## 6. Aplicación de resultados del agente

Cada resultado debe autenticar el agente, comprobar que es el propietario registrado, verificar epoch y operación, validar la transición, actualizar estado y auditoría en una transacción. Un epoch antiguo o un mensaje de un nodo no propietario se rechaza y registra. Un nodo no propietario nunca puede liberar reservas ni limpiar asignaciones.

## 7. Recuperación y outbox

- El dispatcher reclama eventos pendientes con bloqueo transaccional.
- La entrega puede repetirse y el agente debe responder idempotentemente.
- Un timeout no crea por sí solo otra asignación ni otro epoch.
- Tras reiniciar, el controlador lee asignaciones persistidas, procesa outbox y consulta agentes conectados.
- La observación local del agente no reemplaza la autoridad de asignación.
- La falta de evidencia conserva unknown.
- La caída de la Master pausa nuevas asignaciones. El MVP no tiene failover automático.

## 8. Consistencia

Propuesta inicial: transacciones cortas y bloqueos explícitos de filas de instancia/capacidad. Evaluar READ COMMITTED con locks y restricciones; usar SERIALIZABLE cuando sea necesario y manejar reintentos de serialización con idempotencia. La elección se debe confirmar con pruebas concurrentes.

No compartir una base SQLite activa entre hosts ni confiar en un lease temporal como fencing. No ejecutar dos Masters contra la misma base sin liderazgo y fencing probados.

## 9. Pruebas obligatorias

1. Dos solicitudes concurrentes asignan la misma instancia a nodos distintos: solo una confirma.
2. Misma clave/payload devuelve la misma operación.
3. Misma clave con payload distinto produce conflicto.
4. Caída tras commit y antes de envío: outbox recupera la orden.
5. Caída tras envío y antes de marcar despachado: agente deduplica.
6. Epoch antiguo no modifica el estado actual.
7. unknown bloquea nuevas asignaciones.
8. Vencimiento del lease no libera automáticamente al propietario.
9. Cargas concurrentes no comprometen más RAM/disco que lo reservable.
10. Reinicio conserva epochs, operaciones y auditoría.
11. Backup/restauración mantiene integridad y asignaciones.
12. Logs no contienen secretos ni payloads privados.

## 10. Coste y operación

PostgreSQL es software libre y puede operar localmente sin suscripción de base de datos. Persisten costes indirectos de hardware, electricidad, red y almacenamiento. Sin réplica ni segunda autoridad probada, la Master/base siguen siendo un punto de dependencia.

## 11. Criterios de aceptación

- DDL y migraciones probados localmente.
- Pruebas concurrentes demuestran ausencia de doble propietario.
- Outbox e idempotencia resisten los puntos de caída.
- Epoch, fencing y reconciliación tienen evidencia reproducible.
- Backup/restauración ejecutados y documentados.
- Manual operativo completo en español.
- Sin dependencia de servicio cloud ni pago obligatorio.

**Estado real:** diseño de persistencia; no hay migraciones, repositorio PostgreSQL ni pruebas de concurrencia implementadas.
