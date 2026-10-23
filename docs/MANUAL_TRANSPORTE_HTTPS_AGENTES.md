# Manual de transporte HTTPS privado para agentes

**Estado:** guía técnica preliminar. No ejecutar en las PC físicas ni activar el listener hasta aprobar la revisión de seguridad y validar la integración del adaptador de dominio.

## 1. Principios y límites

- El transporte se limita a la LAN privada; no se configura port forwarding ni exposición a Internet.
- El listener debe enlazarse a una IP privada concreta, no a `0.0.0.0`.
- HTTP plano se rechaza a nivel ASGI; el servidor debe tener TLS configurado con certificado y clave separados.
- La CA raíz firma certificados, pero **su clave privada no debe quedarse en el Master**. Los agentes reciben solo el certificado público de la CA por un canal confiable.
- Cada nodo conserva una credencial bearer individual; no compartir tokens entre nodos.
- Un nodo `pending` puede reportar heartbeat/capacidades y consultar su propio estado; no acepta tareas.
- Ninguna instrucción de este manual abre puertos ni inicia servicios por sí misma.

## 2. Instalar los paquetes locales de forma coherente

El transporte utiliza la política canónica del paquete `cluster-agent-auth`; instala ambos paquetes desde la raíz del repositorio y verifica dependencias. No instales `cluster-agent-transport` aislado.

```sh
python -m pip install -e "packages/cluster-agent-auth[test]"
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pip check
```

La autenticación PostgreSQL devuelve el vencimiento real de la credencial. La política canónica vuelve a validar ese timestamp antes de autorizar cada operación. Las credenciales expiradas, revocadas o con estados incoherentes se rechazan.

## 3. Preparar una CA local (equipo administrativo confiable)

Usar una estación administrativa controlada, no el Master ni un agente. Se requiere OpenSSL, software libre local.

```sh
umask 077
mkdir -p geelark-pki
cd geelark-pki
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out geelark-agent-ca.key
openssl req -x509 -new -sha256 -days 3650 \
  -key geelark-agent-ca.key -out geelark-agent-ca.crt \
  -subj "/CN=GeeLark-IA Local Agent CA"
chmod 600 geelark-agent-ca.key
chmod 644 geelark-agent-ca.crt
```

- La clave `geelark-agent-ca.key` es secreta y debe permanecer fuera del Master y de los agentes.
- Respaldar la clave CA cifrada en almacenamiento offline y controlar quién puede usarla.
- El certificado `geelark-agent-ca.crt` es público; su integridad debe verificarse al distribuirlo.
- Definir antes de usarla un registro de propietario, fecha de creación, vencimiento y procedimiento de revocación.

## 4. Generar la clave y CSR del servidor en el Master

Sustituir `192.168.1.10` por la IP privada fija que se haya reservado para el Master. No usar una IP pública ni un nombre que el helper actual no permita.

```sh
umask 077
mkdir -p /etc/geelark/pki
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:3072 -out /etc/geelark/pki/agent-server.key
openssl req -new -sha256 \
  -key /etc/geelark/pki/agent-server.key \
  -out /etc/geelark/pki/agent-server.csr \
  -subj "/CN=GeeLark-IA Agent API"
chmod 600 /etc/geelark/pki/agent-server.key
```

Copiar únicamente el CSR a la estación administrativa por un canal controlado. No copiar la clave privada del servidor.

## 5. Firmar el certificado del servidor fuera del Master

En la estación administrativa, crear un archivo de extensiones con la IP privada real:

```ini
basicConstraints=critical,CA:FALSE
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=IP:192.168.1.10
```

Firmar el CSR:

```sh
openssl x509 -req -sha256 -days 397 \
  -in agent-server.csr \
  -CA geelark-agent-ca.crt -CAkey geelark-agent-ca.key -CAcreateserial \
  -out agent-server.crt -extfile agent-server.ext
openssl verify -CAfile geelark-agent-ca.crt agent-server.crt
```

Verificar que el SAN coincide exactamente con la IP de conexión. Transferir al Master solo `agent-server.crt`; mantener su clave privada en el Master con permisos restrictivos. Renovar antes de vencer.

## 6. Distribuir confianza y restringir red

1. Instalar el certificado público `geelark-agent-ca.crt` en cada agente mediante un canal autenticado.
2. Usar el cliente `AgentHTTPSClient` del paquete `cluster_agent_transport`: valida cadena y SAN, exige TLS 1.2+, rechaza HTTP, redirects, hosts fuera de la LAN privada y rutas con caracteres de control, backslashes o traversal, incluso con codificación URL anidada. En POSIX comprueba que el archivo CA y su directorio pertenezcan al usuario actual o a root y no permitan escritura a grupo/otros; en Windows, proteger ambos con ACL NTFS para que otras identidades no puedan sustituir la raíz de confianza. El cuerpo JSON de cada solicitud se limita a 16 KiB, igual que el límite del servidor agente. No desactivar la verificación TLS ni aceptar certificados autofirmados arbitrarios.
3. El listener valida en POSIX que la clave privada pertenezca al usuario del proceso y no conceda permisos a grupo/otros; el certificado y sus directorios deben pertenecer al usuario actual o a root, y no pueden ser modificables por grupo/otros. En Windows, proteger clave, certificado y directorios con ACL NTFS.
4. Permitir en el firewall solo el puerto privado elegido desde las IP de los agentes autorizados.
5. No configurar NAT/port forwarding, túneles públicos ni DNS público para este listener.
6. Comprobar que el proceso no escucha en interfaces adicionales.
7. Registrar la huella SHA-256 del certificado CA y verificarla por un canal independiente.

Ejemplo de uso del cliente HTTPS (reemplazar IP, ruta de CA y placeholders por valores autorizados; nunca poner tokens reales en el repositorio):

```python
from cluster_agent_transport import AgentHTTPSClient

client = AgentHTTPSClient(
    base_url="https://192.168.1.10:8443",
    ca_cert="/etc/geelark/pki/geelark-agent-ca.crt",
    timeout_seconds=5,
)
response = client.request(
    "POST",
    "/agent/v1/heartbeat",
    payload={
        "schema_version": 1,
        "agent_version": "0.1.0",
        "health_state": "healthy",
        "cpu_load_percent": 10,
        "memory_total_bytes": 1024,
        "memory_available_bytes": 512,
        "storage_available_bytes": 2048,
    },
    headers={
        "Authorization": "Bearer <token-de-ejemplo>",
        "X-Agent-Nonce": "<uuid-unico>",
        "X-Agent-Timestamp": "<fecha-ISO-8601-con-zona>",
        "X-Request-ID": "<uuid-de-solicitud>",
        "Idempotency-Key": "<clave-unica-de-al-menos-16-caracteres>",
    },
)
print(response.status)
```

El ejemplo ilustra la interfaz del cliente; no se ejecuta automáticamente ni constituye un agente completo. El runtime del agente todavía debe integrar esta llamada con el journal local y el flujo de reconciliación.

## 7. Enrolamiento y estado pending

1. Un administrador emite un token de enrolamiento de un solo uso con vencimiento corto.
2. Entregarlo una sola vez al nodo esperado; nunca incluirlo en logs, tickets ni commits.
3. El nodo consume el token y recibe una credencial individual; nodo y credencial quedan en estado `pending`.
4. En `pending`, solo se autorizan heartbeat, capacidades y consulta de estado. Aceptación/progreso/resultado de tareas y reconciliación quedan denegados.
5. Aprobar manualmente el nodo después de verificar identidad, versión y capacidades.
6. Rotar o revocar la credencial cuando haya sospecha de exposición o al retirar un nodo.

## 8. Rotación y recuperación

- Renovar el certificado del servidor antes de su vencimiento; generar una clave nueva y firmar una nueva CSR.
- Mantener una ventana de transición documentada si se cambia la CA, confiando temporalmente en la CA antigua y nueva solo durante el periodo necesario.
- Si la clave CA se compromete, dejar de confiar en ella, generar CA nueva y volver a emitir certificados; renovar los certificados del servidor no basta.
- La revocación de tokens de agente es independiente de la revocación de certificados TLS.
- Mantener copias de seguridad cifradas y pruebas periódicas de restauración de la CA offline; no respaldar claves privadas en el repositorio.

## 9. Diagnóstico sin filtrar secretos

Comprobar la cadena y el SAN con OpenSSL. No imprimir bearer tokens, claves privadas, payloads sensibles ni URLs con credenciales. Las respuestas HTTP deben ser genéricas y llevar un request ID; los detalles internos se registran saneados.

## 10. Bloqueos antes de operación real

- Integrar los handlers con la persistencia transaccional y la tabla de outbox.
- CI ejecuta un handshake TLS real contra un servidor temporal con CA local: el cliente que confía en la CA conecta y el cliente sin esa CA es rechazado. El helper cliente ya valida TLS/CA; sigue pendiente integrarlo en el runtime del agente junto al journal local y la reconciliación.
- Validar timeouts, concurrencia y el límite de solicitudes en el modelo de despliegue elegido.
- Revisar autorización por ruta, idempotencia, revocación y recuperación.
- Revisar el manual con el usuario antes de instalar o habilitar el listener.

Este paquete no inicia el listener automáticamente. La configuración debe revisarse antes de llamar a `make_uvicorn_config` y arrancar Uvicorn.


## 11. Adaptador de runtime y reintento offline

El paquete incluye `AgentTransportRuntime`, un puente entre `AgentHTTPSClient` y cualquier journal compatible con la interfaz de `AgentJournal`. No importa ni instala automáticamente el paquete de guardián para mantener separados los módulos.

1. Inicializar el journal SQLite local y pasar esa instancia a `AgentTransportRuntime`.
2. Antes de reportar progreso o resultado, el adaptador llama a `journal.record_result`. El resultado queda durable antes de intentar la red.
3. Si el controlador responde 2xx, la entrega terminó. Si hay timeout, desconexión o error HTTP, el adaptador devuelve un error genérico y el recibo permanece en SQLite.
4. Cuando vuelva la conexión, llamar a `runtime.sync_pending_receipts(limit=100)`. El adaptador pide al journal un lote acotado y ordenado de recibos aún no confirmados; se detiene ante el primer error de red para no agotar recursos sin conexión.
5. Para progreso y resultados, el journal marca esa versión del recibo sincronizada solo después de recibir una respuesta HTTP 2xx. Una actualización posterior elimina el ACK anterior y vuelve a poner el recibo en la cola; así el progreso antiguo no bloquea resultados más recientes. El ACK se guarda en SQLite y sobrevive a un reinicio. Si el controlador recibió el resultado pero se perdió la respuesta, el agente lo reenvía con la misma clave idempotente y un nonce/request ID nuevos.
6. No reenviar resultados de otra instancia, nodo o epoch: el journal local valida propietario y epoch antes de guardar el resultado.

Ejemplo de construcción del adaptador (valores sensibles deben proceder del almacén protegido del sistema operativo, no del código):

```python
from uuid import UUID
from cluster_agent_transport import AgentHTTPSClient, AgentTransportRuntime
from geelark_cluster_agent_guard import AgentJournal

node_id = UUID("00000000-0000-4000-8000-000000000001")  # reemplazar por UUID provisionado
journal = AgentJournal("/var/lib/geelark-agent/journal.sqlite3", node_id)
journal.initialize()

https_client = AgentHTTPSClient(
    base_url="https://192.168.1.10:8443",
    ca_cert="/etc/geelark/pki/geelark-agent-ca.crt",
)
runtime = AgentTransportRuntime(
    client=https_client,
    bearer_token="<token-protegido-del-nodo>",
    journal=journal,
    local_node_id=node_id,
)
```

**Límites offline actuales:**
- El guardián SQLite conserva fencing, recibos pendientes y ACK terminales sin red.
- El adaptador puede sincronizar lotes acotados con `sync_pending_receipts()`, pero el bucle principal del agente todavía debe invocarlo al iniciar y cuando detecte reconexión.
- Heartbeat, capacidades y consulta de estado requieren conectividad; no se encolan localmente.
- La entrega de tareas y la reconciliación del lado controlador permanecen deshabilitadas hasta integrar/revisar servicio transaccional y outbox.
- No se ejecuta Android, ADB ni shell remoto; no desplegar en nodos reales hasta completar el bucle de agente, la entrega de tareas y la revisión de outbox.


## Inventario versionado de módulos — fase de revisión

La API añade `PUT /agent/v1/modules` con `schema_version: 1` y hasta 32 módulos sin duplicados. Los IDs se validan contra el registro cerrado del paquete: `agent-supervisor`, `agent-transport`, `agent-guard`, `task-journal` y `android-engine`. Cada elemento declara solo `module_id`, `state`, `version` y `error_code`; el servidor añade `checked_at` (hora del Master) y `source`. No se aceptan logs ni mensajes libres.

**Autorización:** solo nodos `active` pueden publicar el inventario. Un nodo `pending` no obtiene permisos nuevos y recibe 403. Los módulos no alteran la autorización ni habilitan tareas.

**Frescura:** si no hay heartbeat reciente (90 s) o el reporte supera 5 min, el estado se convierte en `unknown`, con origen `master-check` y código `NODE_STALE` o `REPORT_STALE`. La ausencia de un módulo nunca se interpreta como `operational`. Los datos recuperados de PostgreSQL también se sanean al responder: IDs fuera del registro se omiten, estados/orígenes/campos inesperados no se reenvían y un timestamp futuro se convierte en `unknown` (`REPORT_TIME_SKEW`).

La migración `db/migrations/0004_worker_module_inventory.sql` crea la columna JSONB acotada. Esta rama se apila sobre la PR #48; no se ha fusionado, desplegado ni probado en hardware físico.


### Contrato del payload

El esquema JSON formal y el ejemplo están en [worker-module-inventory-v1.schema.json](contracts/worker-module-inventory-v1.schema.json) y [worker-module-inventory-v1.example.json](contracts/examples/worker-module-inventory-v1.example.json). La lista cerrada del esquema se prueba contra el registro del código para evitar divergencias. El timestamp `checked_at` y `source` son generados por el Master; el Worker no puede falsificarlos. La lectura de estado propio no equivale todavía a un snapshot administrativo para PC-MASTER.


## ACK durable y compatibilidad del journal (21-oct-2026)

La sincronización de recibos debe confirmar exactamente el estado y el resultado enviados. El runtime pasa `expected_status` y `expected_result` al journal y conserva el recibo pendiente si la versión local cambió durante la petición. La CI de integración fija el commit del journal que implementa esa API; no debe sustituirse por un commit anterior que solo admita ACK por `operation_id`.
