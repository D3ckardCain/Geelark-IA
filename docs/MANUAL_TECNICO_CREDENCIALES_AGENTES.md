# Manual técnico: enrolamiento y autenticación de agentes

**Estado:** servicio de dominio propuesto en PR #44; no existe listener HTTP ni API remota habilitada.  
**Diseño elegido:** bearer tokens individuales aleatorios de 256 bits por nodo, hashes SHA-256 en PostgreSQL, CA local y HTTPS obligatorio en la futura capa de transporte. El enrolamiento queda pendiente de aprobación administrativa.  
**Costo:** dependencias de software libre; no requiere APIs ni servicios de pago.

## 1. Componentes

- Migración `0002_agent_auth.sql`: hashes de tokens de enrolamiento y credenciales, estados, expiración y nonces.
- Paquete `packages/cluster-agent-auth`: servicio de dominio Python 3.11+ con psycopg 3.
- `create_enrollment`: genera token de alta de un solo uso (10 minutos por defecto, máximo una hora).
- `consume_enrollment`: bloquea el registro, valida vigencia/consumo/revocación, crea nodo `pending`, credencial `pending` y consume el token en una transacción.
- `authenticate_bearer`: solo acepta credenciales activas/no vencidas de nodos aprobados con estado administrativo `active`.
- `begin_credential_rotation` y `rotate_credential`: preparan una credencial pendiente y revocan la anterior/activan la nueva en una transacción.
- `revoke_credential`: revoca una credencial individual.

## 2. Secretos y transporte

- Los tokens usan `secrets.token_hex(32)`: 32 bytes de entropía, codificados como 64 caracteres hexadecimales.
- PostgreSQL almacena únicamente SHA-256 hexadecimal; nunca el secreto original.
- No incluir tokens en logs, telemetría, errores, issues ni artefactos CI.
- El secreto se devuelve solo una vez al emitirlo; el llamador debe entregarlo por canal seguro y almacenarlo de forma protegida.
- La futura API debe rechazar peticiones sin HTTPS y validar el certificado de la CA local. No se crean endpoints ni listeners en este PR.
- Las credenciales de agentes no otorgan permisos administrativos ni permiten elegir otro node_id.

## 3. Alta y aprobación

1. Un administrador autenticado crea un enrolamiento asociado al UUID esperado del nodo.
2. El operador entrega el token de alta por un canal seguro.
3. El agente verifica TLS de la Master y presenta el token.
4. El servicio bloquea la fila del token; los consumos concurrentes se serializan y solo uno puede completarse.
5. Se crea el nodo en estado `pending` y una credencial también `pending`.
6. Un flujo administrativo separado debe aprobar el nodo y activar la credencial antes de que la autenticación permita acceso.

## 4. Rotación y revocación

1. `begin_credential_rotation` crea una credencial pendiente ligada a la activa.
2. El operador instala el nuevo secreto de forma segura y confirma que puede usarlo.
3. `rotate_credential` revoca la anterior y activa la nueva dentro de la misma transacción.
4. Si falla una condición, la transacción se revierte.
5. Revocar una credencial no equivale a revocar administrativamente todo el nodo.

## 5. Desarrollo y pruebas

Desde la raíz del repositorio:

```bash
python -m pip install -e "packages/cluster-agent-auth[test]"
python -m pytest packages/cluster-agent-auth/tests -q
```

La CI instala el paquete y ejecuta pruebas unitarias y de integración contra PostgreSQL desechable. La suite actual cubre consumo único y concurrente del enrolamiento, estado pendiente, aprobación manual en fixture, autenticación, revocación y rotación básica. Aún faltan casos de expiración temporal real, rotación concurrente, revocación administrativa del nodo bajo carga y pruebas de transporte TLS/replay/rate limiting; estos últimos pertenecen a la siguiente fase de transporte y no deben darse por implementados.

## 6. Límites y próximos pasos

Este cambio no implementa API HTTP, CA/certificados, rate limiting ni endpoints administrativos. Tampoco despliega ni instala agentes en las PC físicas. Antes de habilitar la red hay que completar revisión de seguridad y pruebas de expiración/revocación bajo concurrencia; después se podrá implementar una capa ASGI con TLS obligatorio, límites de cuerpo, timeouts, rate limiting, redacción de secretos y autorización por operación. Mantener PR en draft hasta que CI y revisión de seguridad sean satisfactorias.
