# Manual de operación — bandeja de tareas de agentes

**Estado:** módulo en borrador. Estas instrucciones describen el comportamiento previsto; no habilites el listener ni uses nodos físicos hasta que el PR sea revisado y aceptado.

## 1. Para qué sirve

La bandeja conserva las asignaciones que el controlador debe entregar a un nodo. El agente pregunta al controlador por HTTPS saliente; el controlador no abre conexiones entrantes hacia los equipos.

La bandeja **no ejecuta** una instancia Android. Solo entrega la asignación y registra la aceptación, el progreso y el resultado que comunica un agente autorizado.

## 2. Condiciones previas

- PostgreSQL operativo con todas las migraciones aprobadas.
- Servicio de autenticación de agentes y credenciales individuales activas.
- Certificado del servidor firmado por la CA local confiable y cliente HTTPS configurado con esa CA.
- Firewall limitado a la LAN privada; sin exposición a Internet ni port forwarding.
- Nodo aprobado por administrador y con estado `active`, credencial `active` y salud `healthy`.
- No compartir bearer tokens entre nodos; revocar inmediatamente un token expuesto.

## 3. Estados y significado

| Estado | Significado para operación |
|---|---|
| `queued` | Asignación persistida y lista para entregarse. |
| `delivered` | Se envió al agente; la lease de entrega dura 30 segundos. |
| `accepted` | El agente confirma recepción; todavía no significa que Android esté listo. |
| `running` | El agente reporta que el trabajo está en curso. |
| `succeeded` | Resultado de éxito comunicado por el agente; requiere validación del adaptador en una fase posterior. |
| `rejected` | El agente rechazó la asignación antes de ejecutarla. |
| `failed` | Error conocido comunicado por el agente. |
| `unknown` | Resultado incierto; requiere reconciliación, no debe convertirse automáticamente en éxito o fallo. |
| `cancelled` | Estado reservado para un flujo de cancelación autorizado futuro. |

## 4. Flujo de operación

1. El servicio transaccional crea la operación, reserva recursos, evento outbox y tarea en una sola transacción.
2. Un nodo activo reclama una tarea por `POST /agent/v1/tasks/claim` con clave idempotente.
3. Si no hay tareas, la respuesta contiene `task: null`.
4. El agente confirma recepción por `POST /agent/v1/tasks/{task_id}/accept`.
5. El agente informa progreso y resultado por las rutas tipadas correspondientes.
6. El controlador valida propietario, epoch, lease, estado de credencial e idempotencia antes de aceptar cada cambio.

## 5. Reintentos y problemas comunes

- **No aparecen tareas:** verifica que el nodo esté `active/active`, saludable y que la instancia conserve el mismo propietario/epoch y lease vigente.
- **Se devuelve `task: null`:** no significa error; no hay una tarea elegible en ese momento.
- **Conflicto idempotente (409):** una clave se reutilizó con otro payload. Genera una clave nueva para una operación lógica nueva; conserva la clave original para reintentar la misma petición.
- **Resumen rechazado (422):** el progreso/resultado contiene una clave sensible (por ejemplo, token, contraseña, cookie o credencial). No envíes secretos; transmite códigos de error y métricas redactadas.
- **Tarea no elegible o epoch obsoleto (409):** no fuerces la transición. Consulta estado y reconcilia.
- **Rate limit (429):** reduce la frecuencia de polling y aplica espera progresiva.
- **HTTPS/CA fallida:** no desactives la verificación de certificado ni uses HTTP plano. Comprueba la CA, SAN/IP del certificado y reloj.
- **Estado `unknown`:** no reasignes la instancia solo porque venció una lease o falta heartbeat. Primero hay que verificar el estado real y resolver la incertidumbre.

## 6. Offline y recuperación

- Sin conexión no se pueden reclamar tareas nuevas ni confirmar resultados al controlador.
- El journal local puede conservar resultados para sincronización posterior, pero el bucle principal y la reconciliación automática aún están pendientes de integración.
- Si se pierde la respuesta de claim, reintenta con la misma clave idempotente. Una clave nueva representa otra reclamación.
- La lease de entrega de 30 segundos solo controla la retransmisión del mensaje; no sustituye la lease de asignación ni demuestra que la instancia esté detenida.

## 7. Límites de seguridad

- Los nodos `pending` solo envían heartbeat, capacidades y consultan su propio estado.
- La bandeja no acepta comandos arbitrarios, shell remoto ni ADB.
- Los handlers de reconciliación permanecen deshabilitados hasta que exista su máquina de estados y pruebas específicas.
- No se habilita un listener automáticamente y no se despliega en PCs físicas desde este módulo.
- Coste operativo objetivo: **$0 USD**; la base PostgreSQL ya forma parte de la arquitectura y las bases de CI son desechables.
