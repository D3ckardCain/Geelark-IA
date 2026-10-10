# Manual técnico: supervisor del agente

## Responsabilidad

AgentSupervisor coordina dos componentes ya construidos:
- AgentTransportRuntime: heartbeat y publicación de capacidades por HTTPS.
- AgentReceiptSyncLifecycle: envío de recibos ya persistidos en SQLite.

El supervisor no contiene lógica de dominio de tareas, no reclama asignaciones, no ejecuta adaptadores Android, no utiliza ADB/shell y no abre un listener. Las dependencias se inyectan desde el proceso que lo integre.

## Secuencia de arranque

1. El llamador crea el journal SQLite persistente y obtiene la identidad UUID del nodo.
2. El llamador construye AgentHTTPSClient con URL HTTPS privada, CA explícita, verificación de certificado/hostname y timeout finito.
3. El llamador obtiene el token bearer de un almacén seguro del sistema operativo y crea AgentTransportRuntime.
4. Crea AgentReceiptSyncLifecycle(runtime=runtime, ...).
5. Crea AgentSupervisor(runtime=runtime, receipt_lifecycle=lifecycle, heartbeat_payload=..., capabilities_payload=...).
6. Llama a start(). El sincronizador de recibos se inicia primero; luego el supervisor arranca el ciclo periódico de heartbeat/capacidades en un hilo separado.
7. La primera iteración es inmediata. El intervalo predeterminado es 30 segundos; el intervalo admitido por la clase va de 0.1 a 3600 segundos. En un despliegue real, el intervalo debe fijarse según la política del controlador y su rate limit.
8. Al apagar, el llamador debe llamar a stop(timeout=5) y comprobar el booleano devuelto.

## Máquina de estados simplificada

- **Inicializado:** aún no se ha llamado start().
- **Ejecutando:** heartbeat/capacidades y sincronización de recibos tienen hilos independientes.
- **Degradado/offline:** heartbeat falló; se informa HEARTBEAT_FAILED y se conserva el ciclo periódico.
- **Recuperación:** un heartbeat exitoso después de fallo notifica notify_reconnected() al sincronizador.
- **Apagado:** stop() fija la señal de cancelación, despierta la espera y comparte un presupuesto de tiempo entre ambos hilos.
- **Apagado incompleto:** stop() devuelve False si alguno de los hilos sigue vivo al agotarse el presupuesto. No se debe declarar una parada limpia ni iniciar una segunda instancia para ocultar el problema.

## Errores y observabilidad

Los únicos códigos enviados al callback son:
- HEARTBEAT_FAILED
- CAPABILITIES_FAILED
- RECEIPT_SYNC_WAKE_FAILED

El callback no recibe excepciones, token bearer, cuerpos HTTP ni contenido del recibo. Si el callback mismo falla, el supervisor no debe terminar por esa razón.

Un fallo de capacidades no debe impedir el siguiente heartbeat. Un fallo del aviso de reconexión no debe clasificarse como fallo del heartbeat; el supervisor conserva la marca offline para volver a intentar el aviso en la siguiente respuesta exitosa.

## Concurrencia y cancelación

- La clase evita iniciar más de un hilo supervisor en la misma instancia.
- Una instancia detenida no puede reiniciarse.
- notify_reconnected() despierta la espera del heartbeat y notifica el sincronizador de recibos.
- Los timeouts de red pertenecen al cliente HTTPS y son obligatorios: el timeout de stop() no puede cancelar de forma segura una llamada de red que no tenga timeout propio.
- Las funciones proveedoras de payload deben ser rápidas y no realizar operaciones de red bloqueantes.

## Seguridad y límites

- El supervisor no implementa almacén de credenciales. No pasar tokens desde argumentos de línea de comandos ni escribirlos en logs.
- El supervisor no implementa el entry point del sistema operativo ni servicio systemd/Windows Service.
- La elección del sistema operativo base y del almacén de credenciales está pendiente en la arquitectura del clúster.
- El heartbeat y las capacidades permitidas a nodos pending no implican permiso para reclamar/aceptar tareas.
- El supervisor no resuelve estados unknown ni reemplaza fencing/reconciliación del controlador.
- Coste obligatorio de software/servicios: $0 USD. No hay API de pago requerida.

## Pruebas

La suite test_supervisor.py cubre arranque, heartbeat/capacidades, recuperación, fallo del callback, error de notificación de reconexión, fallo de capacidades, validación de intervalo y apagado. El resultado de CI debe asociarse siempre al SHA exacto; una prueba en CI no demuestra que el módulo esté instalado en PCs físicas.
