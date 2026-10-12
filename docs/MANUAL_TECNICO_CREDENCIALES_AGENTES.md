# Manual técnico: esquema de enrolamiento y credenciales de agentes

**Estado:** migración de datos propuesta; no existe API de enrolamiento ni autenticación implementada.  
**Base de diseño:** ADR-005, PR #40.

## 1. Tablas de la migración 0002

- `node_enrollments`: guarda el hash SHA-256 del token de alta, nodo esperado, creador, vencimiento y timestamps de consumo/revocación. No guarda el token en claro.
- `node_credentials`: credenciales individuales por nodo con hash, estado, vencimiento, último uso y referencia a la credencial sustituida.
- `agent_request_nonces`: nonce único por nodo para rechazar una repetición exacta mientras el nonce siga retenido.

## 2. Alta de un nodo (flujo futuro)

1. Un administrador autenticado genera un token aleatorio de alta y lo entrega al operador del nodo por un canal seguro.
2. La Master guarda solo el hash, vincula el token al UUID esperado y fija una expiración corta (propuesta: 10 minutos).
3. El agente verifica el certificado HTTPS de la Master y presenta el token de alta.
4. El servicio consume el token con una sola operación condicional/transaccional que exige no consumido, no revocado y no vencido.
5. En la misma transacción crea el nodo como `pending` y una credencial individual. El secreto de la credencial se devuelve una sola vez.
6. El administrador revisa y aprueba el nodo. Hasta entonces no puede recibir asignaciones.

La migración proporciona las restricciones de datos, pero no implementa esos pasos.

## 3. Rotación de credenciales

La estructura permite mantener una credencial activa mientras se prepara una nueva credencial en estado `pending`, ligada a la anterior. La confirmación futura debe ejecutar una transacción que:
1. verifique que la nueva credencial pertenece al mismo nodo y que sigue pendiente/no vencida;
2. revoque la anterior;
3. active la nueva;
4. registre auditoría;
5. confirme el commit.

El orden es importante: activar la nueva antes de revocar la anterior viola el índice de una sola credencial activa por nodo. No mostrar de nuevo el secreto antiguo ni registrar el nuevo en logs.

## 4. Autorización y replay

- Cada petición autentica una credencial individual y consulta su estado, vencimiento y el estado administrativo actual del nodo.
- Una credencial válida no autoriza operaciones administrativas ni puede actuar como otro nodo.
- Los nonces son únicos por `(node_id, nonce)`; una repetición exacta se rechaza. Un nonce no protege frente a una credencial robada: TLS, revocación, permisos locales e idempotencia siguen siendo necesarios.
- Los nonces vencidos se pueden eliminar después de la ventana de replay documentada.
- No guardar secretos en `created_by`, request IDs, capabilities ni logs.

## 5. Pruebas

`db/tests/0002_agent_auth_smoke.sql` verifica:
- una sola credencial activa por nodo;
- una sola rotación pendiente por nodo;
- consumo único de un token de enrolamiento;
- nonce duplicado rechazado por el mismo nodo y permitido en otro nodo.

La CI aplica las migraciones ordenadas y ejecuta los tests SQL contra PostgreSQL desechable. Antes de habilitar endpoints faltan pruebas de consumo concurrente real en el servicio de dominio, expiración, revocación inmediata, rotación transaccional y redacción de logs.

## 6. Limitaciones

Esta migración no crea endpoints, certificados, CA ni tokens reales. No abre puertos, no autentica agentes y no autoriza tareas. La ADR-005 sigue siendo propuesta en revisión. No desplegar en las PC físicas ni exponer la API hasta implementar y probar la capa de transporte.
