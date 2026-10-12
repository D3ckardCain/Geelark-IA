# ADR-005: autenticación local y enrolamiento de agentes

- **Estado:** aceptada por el usuario el 2026-10-09; implementación en curso y aún no habilitada en red.
- **Fecha:** 2026-10-10.
- **Relacionada:** ADR-003, ADR-004, `CONTRATO_API_CLUSTER.md`, `CONTRATO_MENSAJES_AGENTE_CLUSTER.md`, `MODELO_AMENAZAS_SEGURIDAD.md`.

## Contexto

Los agentes deben comunicarse con la Master sin servicios cloud, con credenciales individuales, revocables y rotables. La API no debe exponerse a Internet. El nodo no puede confiar en órdenes si no valida la identidad del controlador, y la Master no debe aceptar resultados de un nodo usando la identidad de otro.

## Decisión aceptada para el MVP

1. **HTTPS obligatorio**, TLS 1.2 como mínimo y preferencia por TLS 1.3. No ofrecer endpoint HTTP en la interfaz de red.
2. La Master usa un certificado de servidor firmado por una CA local del clúster. Los agentes confían explícitamente en el certificado de la CA/fingerprint distribuido durante la instalación; no aceptan cualquier certificado autofirmado.
3. Cada nodo tiene una credencial opaca aleatoria de al menos 256 bits. La Master almacena solo SHA-256 de la credencial; el secreto se entrega una sola vez y no aparece en logs, URLs ni mensajes de error.
4. Las credenciales de agente solo autorizan las rutas de agente. Nunca sirven para la UI administrativa ni para la API de administración.
5. La incorporación usa un token de enrolamiento aleatorio de un solo uso, con hash en base de datos, vencimiento de 10 minutos y consumo atómico. El token se vincula a una solicitud/identidad de nodo y no autoriza tareas.
6. Un nodo enrolado empieza en estado `pending`. Hasta la aprobación administrativa solo puede informar heartbeat/capacidades y consultar el estado de su enrolamiento; no recibe asignaciones.
7. La credencial normal se vincula a un solo `node_id`, se puede revocar inmediatamente y se rota mediante una operación auditada. La rotación no devuelve la credencial anterior ni la escribe en logs.
8. El agente almacena la credencial en un archivo local con permisos restrictivos (POSIX 0600 o ACL equivalente en Windows). La CA privada de la Master tiene permisos restrictivos y copia de respaldo cifrada fuera de la red.
9. La Master escucha solo en la interfaz privada configurada; el firewall permite acceso únicamente desde los nodos autorizados. No abrir port-forwarding ni publicar la API en Internet.
10. Las operaciones mutables requieren `request_id`, `operation_id` y clave idempotente. Se aplican límite de cuerpo, timeout, rate limit y redacción de secretos. Un nonce único y timestamp pueden ayudar a rechazar la repetición exacta de solicitudes, pero no sustituyen la revocación de una credencial robada.

## Por qué no elegir mTLS en esta primera implementación

mTLS es una alternativa válida y puede reducir la exposición de credenciales bearer, pero la extracción y validación de identidad del certificado cliente debe integrarse correctamente con el servidor ASGI/FastAPI y la política de revocación. No se debe declarar mTLS activo solo por configurar un certificado TLS del servidor. Se reconsiderará cuando exista una prueba de extremo a extremo del certificado cliente, revocación y rotación. La decisión actual mantiene una credencial fuerte, individual y revocable sobre TLS validado.

## Enrolamiento propuesto

1. Un administrador autenticado crea un token aleatorio para un nodo esperado; solo se guarda su hash y fecha de expiración.
2. El agente valida el certificado de la Master y envía el token por HTTPS.
3. La Master consume el token en una transacción con condición `consumed_at IS NULL AND expires_at > now()`; dos usos concurrentes no pueden tener éxito.
4. La Master registra el nodo como `pending`, crea la credencial individual y la devuelve una sola vez.
5. El agente guarda la credencial localmente y confirma la instalación. El administrador revisa y aprueba el nodo.
6. Si se pierde la respuesta que contiene el secreto, no se vuelve a mostrar; se genera una credencial nueva o se repite el enrolamiento con un token nuevo.
7. La revocación invalida la credencial inmediatamente en la Master. Las órdenes pendientes de un nodo revocado no se despachan.

## Modelo de datos necesario

La siguiente migración debe añadir tablas equivalentes a:
- `node_enrollments`: token_hash, node_id/solicitud esperada, expires_at, consumed_at, created_by y auditoría.
- `node_credentials`: credential_id, node_id, token_hash, created_at, expires_at, revoked_at, last_used_at.
- `agent_request_nonces` (opcional): node_id, nonce, seen_at/expiry con unicidad para bloquear replays exactos.

No almacenar tokens en claro. Limpiar hashes/nonce vencidos mediante un trabajo de mantenimiento con retención definida. La autorización debe consultar el estado actual del nodo y rechazar nodos `pending`, `quarantined` o `revoked` para cualquier operación de escritura.

## Riesgos y controles

| Riesgo | Control |
|---|---|
| Robo de credencial del agente | TLS, token de alta entropía, permisos locales, rotación y revocación inmediata |
| Token de enrolamiento reutilizado | Consumo atómico, un solo uso y expiración corta |
| Token de un nodo usado como otro nodo | Credencial ligada a node_id y autorización por recurso |
| Certificado de servidor falso | CA local/fingerprint explícito; rechazar certificados no confiables |
| Nodo enrolado aún no aprobado | Estado `pending`; sin asignaciones |
| Replay exacto de petición | Idempotencia, request ID/nonce y retención de nonces |
| Secretos en logs | Redacción automática y pruebas que inspeccionan logs/respuestas |
| Caída/revocación parcial | Transacción de revocación, auditoría y prueba de que la siguiente petición se rechaza |

## Pruebas de aceptación antes de abrir la red

- HTTP plano rechazado en interfaz de red.
- Certificado Master incorrecto o CA no confiable rechazado por el agente.
- Token de enrolamiento vencido/reutilizado rechazado incluso con dos solicitudes concurrentes.
- Token de nodo A no puede actuar como nodo B.
- Nodo `pending` no recibe órdenes.
- Credencial revocada no puede enviar heartbeat de control ni resultados de operación.
- Rotación/re-enrolamiento no deja la credencial anterior activa fuera de la ventana expresamente definida.
- No hay tokens en logs, trazas, respuestas posteriores ni exportaciones.
- Rate limit y límite de cuerpo probados.
- Toda prueba se ejecuta localmente/CI sin API de pago.

## Consecuencias

La implementación necesita una CA local y un procedimiento de respaldo/rotación documentado. La Master puede seguir administrándose offline; el enrolamiento y la comunicación remota requieren conectividad dentro de la red privada. No se requiere proveedor externo ni servicio cloud de autenticación.

Esta ADR no autoriza todavía endpoints de red ni instalación en las PC físicas.