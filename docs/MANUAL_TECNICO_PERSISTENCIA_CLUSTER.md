# Manual técnico: persistencia del plano de control del clúster

**Estado:** primera migración de esquema propuesta; la lógica de dominio todavía no está implementada.  
**Coste obligatorio:** 0 USD en software/servicios; PostgreSQL se autoalojará en la PC Master.  
**Ámbito:** metadatos de control, asignaciones, reservas, operaciones, idempotencia, auditoría y outbox. No contiene discos Android ni perfiles privados de ejecución.

## 1. Qué hay y qué no hay

Incluido en esta entrega:
- Migración PostgreSQL versionada: `db/migrations/0001_cluster_control.sql`.
- Pruebas de humo de restricciones: `db/tests/0001_cluster_control_smoke.sql`.
- Workflow CI con PostgreSQL desechable: `.github/workflows/cluster-persistence-postgres.yml`.

Todavía NO incluido:
- Servicio de dominio/API para mutar las tablas.
- Repositorios Python, gestor de migraciones o configuración de producción.
- Autenticación mTLS de agentes, rotación/revocación de credenciales.
- Dispatcher del outbox, leases/fencing ejecutados por el agente, ni reconciliación.
- Copias de seguridad y restauración verificadas.
- Prueba de concurrencia real entre dos solicitudes.
- Instalación en la PC Master o conexión con los nodos físicos.

Una migración correcta solo demuestra que el esquema se crea y que algunas restricciones funcionan. No demuestra por sí misma consistencia distribuida.

## 2. Tablas

| Tabla | Responsabilidad |
|---|---|
| `nodes` | Identidad lógica, estado administrativo, salud y capacidades declaradas. No almacena secretos de autenticación. |
| `node_resource_capacity` | Capacidad reservable conservadora de cada nodo, márgenes de seguridad y confianza de la medición. |\n| `instances` | Fila autoritativa por instancia; propietario actual, epoch, estado observado/deseado, lease, motor e imagen Android (API/ABI/digest). |
| `resource_reservations` | CPU, RAM y disco reservados. `held` y `uncertain` bloquean una segunda reserva de esa instancia. |
| `operations` | Historial de operaciones solicitadas y su resultado saneado. |
| `idempotency_records` | Clave única por ámbito, hash SHA-256 del payload canónico y respuesta/operación original. |
| `assignment_events` | Auditoría de cambios de propietario, epoch y estado. |
| `outbox_events` | Órdenes que se deben despachar después del commit, con reintentos y deduplicación. |
| `schema_migrations` | Registro para que un futuro gestor de migraciones almacene versión y checksum aplicado. |

## 3. Regla de oro para asignar una instancia

La futura capa de dominio debe ejecutar una única transacción para:
1. Insertar/reservar la clave idempotente; si ya existe, comparar el hash del payload canónico.
2. Si el hash coincide, devolver la respuesta previamente persistida. Si difiere, responder conflicto.
3. Bloquear la fila de instancia con `SELECT ... FOR UPDATE`.
4. Rechazar propietario vigente y cualquier estado distinto de `pending/stopped`; `unknown/reconciling` bloquean explícitamente la reasignación.
5. Bloquear y volver a validar la capacidad del nodo candidato.
6. Incrementar `assignment_epoch` de forma monotónica y asignar el propietario.
7. Crear reserva, operación, evento de auditoría y evento outbox.
8. Persistir la respuesta idempotente y confirmar.

El orden exacto de inserción de la clave y operación debe resolver la carrera entre peticiones iguales: la restricción primaria de `(scope, idempotency_key)` es la autoridad final; las colisiones se gestionan dentro de la transacción. No hacer comprobación-antes-de-inserción sin manejar la carrera.

No enviar órdenes al agente antes del commit. El dispatcher lee el outbox después del commit y puede entregar un evento más de una vez. Por eso el agente debe deduplicar operaciones y comprobar identidad, instancia y epoch.

## 4. Estados inciertos, leases y fencing

- `lease_expires_at` es información de vigencia, no prueba de que el proceso Android haya parado.
- La expiración de un lease no libera la reserva ni el propietario automáticamente.
- `unknown` y `reconciling` bloquean la reasignación hasta resolver el estado.
- Cada nueva asignación incrementa el epoch en la misma transacción que cambia el propietario.
- Cada orden y resultado debe incluir epoch. El agente rechaza órdenes con epoch menor que el último aceptado.
- Un epoch en la base de datos no basta si el propietario antiguo puede seguir ejecutándose sin validar fencing; no activar failover automático.

## 5. Migración y pruebas

### CI
El workflow crea una base temporal PostgreSQL 16, aplica la migración y ejecuta las comprobaciones SQL. La contraseña del workflow es de prueba y no debe reutilizarse.

### En local, solo en una base desechable
Con PostgreSQL instalado y `psql` disponible:

```sh
createdb geelark_schema_test
psql -v ON_ERROR_STOP=1 -d geelark_schema_test -f db/migrations/0001_cluster_control.sql
psql -v ON_ERROR_STOP=1 -d geelark_schema_test -f db/tests/0001_cluster_control_smoke.sql
dropdb geelark_schema_test
```

No ejecutar estas instrucciones contra una base de producción. La prueba SQL abre una transacción y hace rollback; la migración de esquema sí queda aplicada en la base desechable.

Antes de una instalación real:
- crear roles separados para migración y aplicación;
- limitar escucha y firewall a la red local;
- evitar exponer PostgreSQL a Internet;
- definir permisos que impidan a la aplicación borrar/modificar eventos de auditoría;
- configurar copias de seguridad y probar restauración;
- fijar y documentar versión exacta de PostgreSQL y procedimiento de actualización;
- registrar el checksum de migración con el gestor que se implemente.

## 6. Limitaciones conocidas que deben resolverse antes de producción

1. Las restricciones SQL no calculan por sí solas la capacidad total por nodo; la capa de dominio debe bloquear `node_resource_capacity` y sumar reservas en una transacción.
2. La tabla de auditoría es append-only por convención, no por una política de permisos ya desplegada.
3. Los campos `updated_at` los debe actualizar la aplicación o triggers futuros.
4. El registro de migraciones existe, pero todavía no hay ejecutor que registre automáticamente versión/checksum.
5. La política de retención de claves idempotentes debe ser explícita. No borrar una clave mientras una operación asociada pueda repetirse.
6. La prueba de humo verifica restricciones clave, pero no sustituye pruebas de concurrencia, caídas entre commit y despacho, reinicios, backups ni fencing.
7. PostgreSQL local no proporciona alta disponibilidad. Si Master/base caen, pausar nuevas asignaciones hasta recuperación.

## 7. Seguridad y coste

La migración no contiene credenciales, tokens ni datos personales. No guardar secretos en `capabilities`, `resource_profile`, `result_summary` ni payloads del outbox. Los payloads deben ser mínimos y saneados.

PostgreSQL es software libre y el esquema no depende de una API cloud. El coste de software/servicio puede mantenerse en 0 USD si se autoaloja; el hardware, la electricidad, la administración y los respaldos siguen teniendo costes indirectos. GitHub Actions tiene cuotas/condiciones del plan y no forma parte del requisito de ejecución local: las pruebas también se deben poder correr en una instalación local de PostgreSQL.
