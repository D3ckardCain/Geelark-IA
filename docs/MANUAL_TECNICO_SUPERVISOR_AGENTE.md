# Manual técnico: supervisor del agente

## Responsabilidad

AgentNodeSupervisor coordina dos componentes ya construidos:
- AgentTransportRuntime: heartbeat y publicación de capacidades por HTTPS.
- AgentReceiptSyncLifecycle: envío de recibos ya persistidos en SQLite.

El supervisor no contiene lógica de dominio de tareas, no reclama asignaciones, no ejecuta adaptadores Android, no utiliza ADB/shell y no abre un listener. Las dependencias se inyectan desde el proceso que lo integre.

## Secuencia de arranque

1. El llamador crea el journal SQLite persistente y obtiene la identidad UUID del nodo.
2. El llamador construye AgentHTTPSClient con URL HTTPS privada, CA explícita, verificación de certificado/hostname y timeout finito.
3. El llamador obtiene el token bearer de un almacén seguro del sistema operativo y crea AgentTransportRuntime.
4. Crea AgentReceiptSyncLifecycle(runtime=runtime, ...).
5. Crea `AgentNodeSupervisor(runtime=runtime, receipt_sync=lifecycle, agent_version=..., capabilities=..., metrics_provider=...)`.
6. Llama a start(). El sincronizador de recibos se inicia primero; luego el supervisor arranca el ciclo periódico de heartbeat/capacidades en un hilo separado.
7. La primera iteración es inmediata. Los valores predeterminados son 30 s para heartbeat, 300 s para capacidades y 60 s para consulta de estado; cada intervalo debe ser finito y de al menos 1 segundo. Ajustarlos a la política del controlador y su rate limit.
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
- STATUS_FAILED

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


## Proveedor de credenciales systemd (opcional)

El paquete exporta CredentialProvider (protocolo) y SystemdCredentialProvider (adaptador Linux/systemd). El adaptador lee un archivo entregado por systemd en CREDENTIALS_DIRECTORY; no guarda secretos, no usa red y no implementa cifrado propio. Rechaza directorios/archivos con permisos de grupo/otros, symlinks, archivos no regulares, tokens no ASCII o demasiado grandes.

Cuando se apruebe Linux/systemd, la integración prevista es:
1. Crear un token desde el flujo de enrolamiento autorizado; no copiarlo a un ticket ni a un repositorio.
2. Usar systemd-creds para crear un archivo cifrado, con el nombre de credencial esperado, y guardar el artefacto en una ruta protegida del host.
3. Configurar el servicio con LoadCredentialEncrypted=geelark-agent-token:/ruta/protegida/geelark-agent-token.cred.
4. En el proceso, crear SystemdCredentialProvider() y llamar load_bearer_token(); el runtime usa el valor en memoria.
5. Rotar/revocar el token por el controlador y reiniciar el servicio para cargar la nueva credencial.
6. No imprimir el token ni conservar copias de texto plano. Verificar el soporte de systemd-creds, el mecanismo de clave de host/TPM y recuperación antes de usarlo.

Esta secuencia es documentación de diseño, no un procedimiento ya ejecutado. No hay un unit file ni un instalador y no se ha elegido definitivamente el sistema operativo. No activar este adaptador hasta aprobar la decisión de arquitectura.


## Fábrica de componentes

El paquete exporta build_agent_components(), que devuelve un AgentComponents con client, runtime, receipt_lifecycle y supervisor. La fábrica:
1. valida la configuración del cliente HTTPS y la CA antes de leer el token;
2. llama a credential_provider.load_bearer_token();
3. crea AgentTransportRuntime con el journal y UUID del nodo;
4. crea AgentReceiptSyncLifecycle y AgentNodeSupervisor con las funciones de payload suministradas;
5. devuelve los objetos sin iniciar ningún hilo.

El llamador es responsable de mantener el journal en una ruta persistente, definir versión/capacidades, llamar supervisor.start() y comprobar supervisor.stop(timeout=...) al apagar. La fábrica no inicia hilos, no crea un servicio ni un CLI y no selecciona el almacén de credenciales.

CI de la rama combinada debe verificarse en el HEAD exacto antes de integrar; la suite de PR #67 cubre supervisor, configuración, conectividad y sincronización durable. No se han hecho pruebas en hardware físico.


## Evidencia de validación en la pila canónica

El HEAD `879f57fbd4d546002d65bdcfd21f234d2e873da5` pasó GitHub Actions run 38124601844: 131 pruebas, una advertencia deprecatoria Starlette/httpx y `pip check` correcto. El supervisor se ejecuta sobre PR #57 → #52 y mantiene el API de bandeja canónico. La actualización de documentación/base requiere validar el nuevo HEAD antes de integrar. No se han realizado pruebas en PCs físicas.
