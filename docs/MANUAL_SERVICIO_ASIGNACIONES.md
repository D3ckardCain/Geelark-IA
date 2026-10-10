# Manual técnico del servicio de asignación transaccional

**Estado:** implementación inicial en revisión; solo se ejecuta en pruebas contra PostgreSQL.  
**No usar en producción:** todavía no existe API autenticada, dispatcher del outbox ni agente con fencing implementado.

## 1. Objetivo

El paquete `packages/cluster-persistence` implementa el servicio de dominio que convierte una solicitud de asignación en una transacción persistente. No ejecuta Android, no contacta nodos y no abre puertos de red.

## 2. Qué hace la transacción

`assign_instance(connection, request)`:
1. Valida los tipos y campos críticos.
2. Canonicaliza el payload semántico y calcula SHA-256.
3. Inserta o recupera la clave idempotente.
4. Devuelve la respuesta original si la clave/hash ya fue completada; si el hash difiere, lanza `IdempotencyConflict`.
5. Bloquea la instancia con `FOR UPDATE`; rechaza estados inciertos o un propietario existente.
6. Bloquea la fila del nodo y la fila de `node_resource_capacity`.
7. Suma reservas `held/uncertain` y verifica CPU, RAM y disco con márgenes de seguridad.
8. Incrementa el epoch y crea propietario, reserva, operación, auditoría y outbox dentro de la misma transacción.
9. Persiste la respuesta idempotente y hace commit.

El bloqueo de `node_resource_capacity` serializa las reservas de un nodo. Todas las rutas futuras que creen reservas deben seguir el mismo protocolo de bloqueo; no basta con consultar capacidad sin bloqueo.

## 3. Errores de dominio

- `InvalidAssignmentRequest`: campos/tipos no válidos.
- `IdempotencyConflict`: misma clave, payload semántico distinto.
- `IdempotencyRecordIncomplete`: fila idempotente existente sin respuesta final; requiere reconciliación.
- `InstanceNotFound`: instancia no registrada.
- `InstanceAlreadyAssigned`: propietario vigente.
- `InstanceStateBlocked`: estado `unknown/reconciling`.
- `NodeNotEligible`: nodo no activo/saludable.
- `NodeCapacityNotConfigured`: falta capacidad medida/configurada.
- `InsufficientCapacity`: no caben recursos respetando límites.

Estos errores se deben mapear a respuestas HTTP tipadas en una etapa posterior; no devolver trazas SQL ni detalles internos.

## 4. Ejecución de pruebas

La CI usa PostgreSQL 16 desechable, aplica `db/migrations/0001_cluster_control.sql`, instala el paquete y ejecuta pruebas de integración. Para ejecutar localmente, define `TEST_DATABASE_URL` a una base desechable que ya tenga aplicada la migración y ejecuta:

```sh
python -m pip install -e "packages/cluster-persistence[test]"
TEST_DATABASE_URL=postgresql://usuario:clave@127.0.0.1:5432/geelark_test \
  python -m pytest packages/cluster-persistence/tests -q
```

La URL anterior es un formato de ejemplo, no una credencial del proyecto. No usar la base de producción ni subir credenciales al repositorio.

## 5. Limitaciones actuales

- La asignación crea un evento outbox, pero aún no existe dispatcher ni entrega al agente.
- La seguridad del propietario/epoch después del commit depende de un agente futuro que valide fencing; no se permite failover automático.
- Las excepciones esperadas hacen rollback; la persistencia de respuestas de rechazo idempotentes requiere una política explícita en una iteración posterior.
- La prueba concurrente debe ejecutarse en PostgreSQL real, no SQLite ni mocks.
- No hay API, autenticación, autorización ni controles de red; este paquete no debe exponerse directamente.
- No se ha instalado en las PC físicas del usuario.
