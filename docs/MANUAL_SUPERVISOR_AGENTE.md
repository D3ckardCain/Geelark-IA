# Manual de usuario: supervisor del agente

## Estado y alcance

El módulo AgentSupervisor está en desarrollo en la rama feat/agent-supervisor y se propone para el PR borrador #59. Es una biblioteca de coordinación, no un instalador ni un servicio del sistema ya desplegado. No ejecutar ni instalar en las PCs físicas durante esta fase.

El supervisor coordina dos ciclos independientes:
- Heartbeat y publicación de capacidades.
- Sincronización de recibos persistidos mediante AgentReceiptSyncLifecycle.

No reclama tareas ni ejecuta Android, ADB o shell. No abre listeners. No almacena credenciales.

## Qué necesita para funcionar

La aplicación que lo integre debe construir y proporcionar:
1. Un AgentTransportRuntime con cliente HTTPS configurado con CA de confianza, validación de certificado/hostname y timeout finito.
2. Un journal SQLite local persistente con permisos privados.
3. Un proveedor de credenciales protegido por el sistema operativo. Existe un adaptador opcional SystemdCredentialProvider para servicios Linux/systemd; todavía no hay unit file ni entry point que lo active. En Windows se necesitaría un adaptador específico.
4. Una función que produzca el payload de heartbeat y otra que produzca capacidades actuales.
5. Un AgentReceiptSyncLifecycle asociado al mismo runtime.

El supervisor no crea estas dependencias ni elige dónde se guardan las credenciales. SystemdCredentialProvider solo lee el archivo que systemd entrega en CREDENTIALS_DIRECTORY; no descifra ni crea credenciales por sí mismo. El punto de entrada instalable, el unit file y la decisión de SO siguen pendientes en la Issue #58 y la evaluación de arquitectura.

## Ciclo de operación previsto

1. Construir el runtime y el sincronizador de recibos.
2. Crear AgentSupervisor con ambos objetos y los proveedores de payloads.
3. Llamar a start() una sola vez. Arranca la sincronización durable y ejecuta heartbeat/capacidades en un hilo separado.
4. El heartbeat se envía inmediatamente y luego con el intervalo configurado. El intervalo permitido por el módulo es de 0.1 a 3600 segundos; el valor predeterminado es 30 segundos. Para operación real debe elegirse un intervalo compatible con los límites del servidor y la política de heartbeat.
5. Si el heartbeat falla, el supervisor registra solo HEARTBEAT_FAILED y continúa el ciclo. Si las capacidades fallan, registra CAPABILITIES_FAILED. El callback de errores no debe recibir tokens, excepciones ni cuerpos HTTP.
6. Cuando un heartbeat vuelve a tener éxito después de un fallo, el supervisor notifica la reconexión al sincronizador de recibos.
7. Si un detector externo confirma reconexión, puede llamar a notify_reconnected() para despertar tanto heartbeat como sincronización.
8. Al apagar, llamar a stop(timeout=5). El método devuelve True solo si ambos hilos terminaron dentro del presupuesto temporal. Si devuelve False, investigar la llamada bloqueada y no afirmar que el apagado terminó limpiamente.

## Comportamiento offline

- El journal conserva recibos ya persistidos aunque no haya conectividad.
- El supervisor sigue intentando heartbeat y capacidades según el intervalo, siempre que el proceso esté activo.
- Los recibos se reintentan mediante el sincronizador cuando arranca o se detecta reconexión.
- Sin conexión no se puede confirmar al controlador el estado actual ni realizar operaciones remotas.
- El supervisor no implica que el clúster entero funcione offline ni resuelve por sí solo estados inciertos de tareas.

## Seguridad

- No introducir tokens en argumentos de línea de comandos, código fuente, registros o tickets.
- No desactivar la validación TLS para corregir fallos de conexión.
- Mantener heartbeat/capacidades separados de cualquier futuro worker de tareas.
- Los nodos pending conservan únicamente heartbeat, capacidades y consulta de estado; no pueden reclamar ni ejecutar tareas.
- No activar ejecución Android/ADB/shell ni abrir puertos a Internet mediante el supervisor.

## Diagnóstico

- HEARTBEAT_FAILED: revisar conectividad, dirección privada del controlador, certificado, credencial y reloj del sistema.
- CAPABILITIES_FAILED: revisar el proveedor de capacidades y la respuesta del controlador sin registrar el cuerpo HTTP.
- stop() devuelve False: revisar timeouts de red y comprobar si el hilo está bloqueado; no iniciar una segunda instancia para ocultar el problema.
- No se reanudan recibos: comprobar que AgentReceiptSyncLifecycle comparte el runtime correcto y que notify_reconnected() se llama tras recuperar conectividad.

## Pendientes antes de uso real

- [x] CI del commit ejecutable 7b452538faf7da595f5cb30efe7f3ee5cf933ed1 aprobado: run 136, 70 pruebas aprobadas y pip check correcto. El supervisor sigue sin entry point instalable.
- [ ] Conectar el supervisor a un punto de entrada de proceso instalable.
- [ ] Aprobar el sistema operativo base. Si se elige Linux/systemd, revisar SystemdCredentialProvider y configurar LoadCredentialEncrypted; si se elige otro SO, implementar y probar su proveedor nativo.
- [ ] Añadir detector de conectividad apropiado al sistema operativo final, si se requiere además del heartbeat.
- [ ] Probar arranque/parada, desconexión, recuperación y reinicio del proceso.
- [ ] Revisar la reconciliación de estados unknown y el fencing del propietario.
- [ ] Completar revisión de seguridad y rollback.
- [ ] Autorizar explícitamente cualquier prueba en hardware físico.

## Coste

El módulo usa dependencias open source y no requiere APIs de pago. El objetivo de coste de software y servicios obligatorios sigue siendo $0 USD; no incluye electricidad ni hardware local.
