# Manual de transporte HTTPS privado para agentes

**Estado:** guía técnica preliminar. No ejecutar en las PC físicas ni activar el listener hasta aprobar la revisión de seguridad y completar el adaptador de dominio.

## 1. Principios y límites

- El transporte se limita a la LAN privada; no se configura port forwarding ni exposición a Internet.
- El listener debe enlazarse a una IP privada concreta, no a `0.0.0.0`.
- HTTP plano se rechaza a nivel ASGI; el servidor debe tener TLS configurado con certificado y clave separados.
- La CA raíz firma certificados, pero **su clave privada no debe quedarse en el Master**. Los agentes reciben solo el certificado público de la CA por un canal confiable.
- Cada nodo conserva una credencial bearer individual; no compartir tokens entre nodos.
- Un nodo `pending` puede reportar heartbeat/capacidades y consultar su propio estado; no acepta tareas.
- Ninguna instrucción de este manual abre puertos ni inicia servicios por sí misma.

## 2. Preparar una CA local (equipo administrativo confiable)

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

## 3. Generar la clave y CSR del servidor en el Master

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

## 4. Firmar el certificado del servidor fuera del Master

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

## 5. Distribuir confianza y restringir red

1. Instalar el certificado público `geelark-agent-ca.crt` en cada agente mediante un canal autenticado.
2. El agente debe validar cadena, vigencia y SAN del servidor; no desactivar verificación TLS ni aceptar certificados autofirmados arbitrarios.
3. Permitir en el firewall solo el puerto privado elegido desde las IP de los agentes autorizados.
4. No configurar NAT/port forwarding, túneles públicos ni DNS público para este listener.
5. Comprobar que el proceso no escucha en interfaces adicionales.
6. Registrar la huella SHA-256 del certificado CA y verificarla por un canal independiente.

## 6. Enrolamiento y estado pending

1. Un administrador emite un token de enrolamiento de un solo uso con vencimiento corto.
2. Entregarlo una sola vez al nodo esperado; nunca incluirlo en logs, tickets ni commits.
3. El nodo consume el token y recibe una credencial individual; nodo y credencial quedan en estado `pending`.
4. En `pending`, solo se autorizan heartbeat, capacidades y consulta de estado. Aceptación/progreso/resultado de tareas y reconciliación quedan denegados.
5. Aprobar manualmente el nodo después de verificar identidad, versión y capacidades.
6. Rotar o revocar la credencial cuando haya sospecha de exposición o al retirar un nodo.

## 7. Rotación y recuperación

- Renovar el certificado del servidor antes de su vencimiento; generar una clave nueva y firmar una nueva CSR.
- Mantener una ventana de transición documentada si se cambia la CA, confiando temporalmente en la CA antigua y nueva solo durante el periodo necesario.
- Si la clave CA se compromete, dejar de confiar en ella, generar CA nueva y volver a emitir certificados; renovar los certificados del servidor no basta.
- La revocación de tokens de agente es independiente de la revocación de certificados TLS.
- Mantener copias de seguridad cifradas y pruebas periódicas de restauración de la CA offline; no respaldar claves privadas en el repositorio.

## 8. Diagnóstico sin filtrar secretos

Comprobar la cadena y el SAN con OpenSSL. No imprimir bearer tokens, claves privadas, payloads sensibles ni URLs con credenciales. Las respuestas HTTP deben ser genéricas y llevar un request ID; los detalles internos se registran saneados.

## 9. Bloqueos antes de operación real

- Integrar los handlers con la persistencia transaccional y la tabla de outbox.
- Probar el handshake TLS real desde un agente que confíe en la CA local.
- Validar timeouts, concurrencia y el límite de solicitudes en el modelo de despliegue elegido.
- Revisar autorización por ruta, idempotencia, revocación y recuperación.
- Revisar el manual con el usuario antes de instalar o habilitar el listener.

Este paquete no inicia el listener automáticamente. La configuración debe revisarse antes de llamar a `make_uvicorn_config` y arrancar Uvicorn.
