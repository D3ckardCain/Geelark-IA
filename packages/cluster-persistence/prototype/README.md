# Prototipo de persistencia del clúster

**No es una migración de producción ni una API lista para exponer.** Todo el contenido de este directorio se valida únicamente en una base PostgreSQL desechable.

## Archivos

- `001_schema.sql`: esquema de nodos, capacidad utilizable, instancias, reservas, operaciones, idempotencia, auditoría y outbox.
- `002_assign_instance.sql`: función SQL transaccional de asignación.
- `003_apply_agent_result.sql`: función de prototipo que valida propietario, operación y epoch antes de aplicar un resultado del agente.
- `test_constraints.sql`: restricciones básicas.
- `test_assignment_function.sql`: asignación, repetición idempotente, conflicto de hash, capacidad insuficiente y ACL de la función.
- `test_agent_result.sql`: resultado válido, reintento terminal, epoch antiguo y nodo no propietario.
- `test_concurrency.sh`: dos inserciones concurrentes de reserva.
- `test_concurrent_assignments.sh`: dos transacciones que intentan asignar una misma instancia a nodos diferentes.

## Ejecutar pruebas

El método recomendado es el workflow de GitHub Actions `.github/workflows/cluster-persistence-prototype.yml`, que crea un servicio temporal PostgreSQL 16 y destruye el contenedor al terminar.

Para una ejecución local, usar una base desechable recién creada y exportar variables estándar de libpq (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`). No apuntar a producción ni a Supabase.

```bash
psql -v ON_ERROR_STOP=1 -f packages/cluster-persistence/prototype/001_schema.sql
psql -v ON_ERROR_STOP=1 -f packages/cluster-persistence/prototype/002_assign_instance.sql
psql -v ON_ERROR_STOP=1 -f packages/cluster-persistence/prototype/003_apply_agent_result.sql
psql -v ON_ERROR_STOP=1 -f packages/cluster-persistence/prototype/test_constraints.sql
psql -v ON_ERROR_STOP=1 -f packages/cluster-persistence/prototype/test_assignment_function.sql
psql -v ON_ERROR_STOP=1 -f packages/cluster-persistence/prototype/test_agent_result.sql
bash packages/cluster-persistence/prototype/test_concurrency.sh
bash packages/cluster-persistence/prototype/test_concurrent_assignments.sh
```

Los dos scripts de concurrencia insertan fixtures de forma persistente en la base de prueba. Por eso, para repetir todo desde cero, hay que recrear la base desechable.

## Contrato simplificado de `assign_instance`

La función recibe IDs generados por la capa de aplicación, clave de idempotencia, SHA-256 del payload canónico y cantidades de RAM, disco y CPU. Devuelve `operation_id`, `assignment_epoch` y `replayed`.

Garantías que sí se prueban:
- una transacción asigna la instancia, aumenta el epoch y escribe reserva, operación, evento y outbox;
- la clave repetida con el mismo hash devuelve la operación existente;
- la misma clave con otro hash produce conflicto;
- capacidad insuficiente es rechazada;
- dos transacciones simultáneas no asignan la misma instancia a dos nodos;
- la función de asignación no concede permiso EXECUTE a PUBLIC;
- resultados con epoch antiguo o de un nodo no propietario se rechazan; un resultado terminal repetido no duplica auditoría.

## Límites

Todavía no existen el servicio HTTP/de dominio, autenticación real de agentes, permisos de roles de producción, actualización autenticada de capacidad, verificación de compatibilidad Android, dispatcher del outbox, reconciliación automática ni procedimientos de backup/restauración probados. La función de resultados es una primitiva SQL experimental y depende de que el servicio le pase una identidad autenticada correctamente.

No conceder permisos amplios para compensar esas carencias. Antes de producción, crear un rol de servicio dedicado, limitarlo a las operaciones necesarias, revisar RLS si se elige Supabase y mantener la base autoritativa local como alternativa sin pagos obligatorios.
