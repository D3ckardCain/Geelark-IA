# Manual técnico-operativo — Proveedor de snapshots PC-MASTER

**Versión:** 0.1 (revisión)  
**Estado:** componente interno; no conectado a una interfaz ni expuesto por HTTP.  
**Requiere:** PostgreSQL local con migraciones 0001–0004 aplicadas y rol de lectura mínimo.  
**Coste:** 0 USD en dependencias obligatorias; no requiere servicios cloud.

## 1. Qué hace

El proveedor lee el estado persistido de un nodo y lo convierte en un snapshot compatible con master-worker-status-v1. Es una pieza interna para que una futura capa administrativa lea la fuente de verdad del controlador sin consultar directamente a los Workers.

No administra nodos, no cambia permisos, no crea tareas y no modifica registros.

## 2. Límites de seguridad

- La función no autentica personas. El controlador HTTP/UI que la invoque deberá autenticar y autorizar al operador primero.
- La conexión PostgreSQL debe pertenecer a un rol con permisos SELECT únicamente.
- El proveedor ejecuta una consulta de lectura y no inicia listeners.
- Un nodo pending sigue siendo pending; nunca recibe autorización por aparecer en un snapshot.
- Los estados draining, maintenance y quarantined se representan como unknown porque el contrato v1 no los equipara con active.
- La salud reportada por el Worker se conserva separada de la salud derivada por el Master.

## 3. Cómo usarlo desde código

1. Instala el paquete local packages/cluster-persistence en el entorno del servicio de PC-MASTER.
2. Crea una función de conexión con credenciales de solo lectura para la base de datos local.
3. Construye PostgresStatusSnapshotProvider(connect).
4. Tras comprobar los permisos del operador, llama get_node_snapshot(UUID_del_nodo).
5. Si devuelve None, el nodo no existe; no se debe inventar un registro ni asumir que está desconectado.
6. Valida el snapshot contra el esquema docs/contracts/master-worker-status-v1.schema.json antes de presentarlo.
7. No expongas esta llamada directamente en una ruta HTTP sin añadir autenticación, autorización, límites de consulta y auditoría.

El módulo exporta también build_status_snapshot(row, now=...), destinado a convertir y probar filas de estado. La aplicación normal debe preferir el proveedor y no fabricar filas a partir de datos arbitrarios.

## 4. Significado de frescura

| Situación | Frescura | Salud derivada |
|---|---|---|
| Heartbeat de menos de 90 s y reporte saludable | fresh | healthy |
| Heartbeat de menos de 90 s y reporte degradado/no saludable | fresh | degraded |
| Heartbeat con 90 s o más | stale | offline |
| Nunca hubo heartbeat | missing | offline |
| Timestamp del heartbeat demasiado adelantado | unknown | unknown |
| Reporte de módulo ausente, inválido o viejo | — | Módulo unknown |

La salud del nodo y la salud de un módulo son conceptos distintos. Que un Worker esté healthy no prueba que cada módulo esté operativo.

## 5. Compatibilidad y saneamiento

- snapshot_id se genera para cada lectura; generated_at usa el reloj del Master.
- Solo se emiten capacidades conocidas por el contrato. Los valores desconocidos no se reenvían a la UI.
- Los datos de módulo se limitan a identificador, estado, versión, hora, origen y código de error normalizado.
- Los nombres de nodo que no cumplen el formato v1 se reemplazan por WORKER- más los primeros ocho caracteres del UUID.
- Si se amplía el contrato, actualizar el esquema, las pruebas, el manual y la matriz de brechas en el mismo cambio.

## 6. Offline y conectividad

Este adaptador requiere acceso a PostgreSQL. No tiene caché ni cola offline. Una futura caché debe ser separada, etiquetar source=master-cache, conservar la hora de observación y no presentar un snapshot viejo como actual. La pérdida de GitHub/Internet no afecta una lectura local si PostgreSQL y PC-MASTER siguen disponibles.

## 7. Pruebas y diagnóstico

La suite packages/cluster-persistence/tests/test_status_snapshot.py cubre conversión, frescura, timestamps futuros, saneamiento y consulta SQL. Además, cuando TEST_DATABASE_URL está configurado (como en GitHub Actions), crea un rol temporal con SELECT solamente y verifica contra PostgreSQL real que puede leer y que un UPDATE falla por falta de privilegios. La prueba se omite explícitamente si no existe TEST_DATABASE_URL.

- Si falla una prueba de contrato, revisa el esquema v1 y no relajes las invariantes para forzar que pase.
- Si un módulo aparece como unknown, revisa checked_at, last_seen_at, el código seguro de error y la hora del Master.
- Si get_node_snapshot devuelve None, comprueba el UUID y el inventario persistido.
- Si la base de datos no está disponible, la función propagará el error de conexión; una capa superior deberá informar fallo de lectura sin marcar al nodo como saludable.
- La prueba de rol real pasó en GitHub Actions en el run 38105454312. Antes de integrar el servicio en un entorno distinto, repite la comprobación con el rol de lectura y los permisos efectivos de ese entorno; la prueba de CI no inspecciona permisos de una base de datos de producción.

## 8. Pendiente antes de integrar

- Revisar permisos efectivos del rol de lectura en PostgreSQL.
- Añadir validación completa contra JSON Schema en la capa de integración.
- Definir identidad y permisos del operador humano.
- Diseñar caché local y política de retención si se requiere lectura offline.
- Conectar al panel solo después de aprobar la revisión de seguridad.
- No instalar ni probar en PCs físicas sin autorización explícita.
