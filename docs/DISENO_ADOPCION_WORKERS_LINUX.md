# Diseño de adopción segura de PC-WORKERS Linux

**Actualizado:** 2026-10-28  
**Estado:** propuesta documental; no implementada ni probada con hardware.  
**Issue fuente:** [#118 — adopción de nodos Linux independiente de redroid](https://github.com/D3ckardCain/Geelark-IA/issues/118)  
**Dependencias:** aceptación PC-MASTER [#77](https://github.com/D3ckardCain/Geelark-IA/issues/77), integración de transporte/autenticación y persistencia existentes.  
**Coste obligatorio:** 0 USD; sin SaaS, APIs de pago ni servicios que requieran tarjeta.

## 1. Objetivo y límites

Permitir que PC-MASTER registre un PC Linux como nodo candidato antes de instalar el motor Android. La identidad, conectividad, capacidades y autorización del worker son conceptos separados del estado de Redroid.

Este documento solo define el contrato. No instala Debian, no genera credenciales reales, no abre listeners, no adopta nodos ni habilita ejecución remota.

Fuera de alcance:
- Redroid, Android, ADB, shell remota o ejecución de tareas.
- Descubrimiento que otorgue confianza automática.
- Instalación/destrucción de discos sin aprobación explícita.
- Acceso público, dependencias cloud obligatorias o telemetría de terceros.

## 2. Máquina de estados

Separar el estado administrativo de adopción del estado de conectividad:

| Estado administrativo | Significado | Permisos |
|---|---|---|
| `pending` | Identidad aún no aprobada por PC-MASTER | Solo enrolamiento/heartbeat/capacidades/consulta propia, con credencial válida y rutas permitidas |
| `approved` | Un operador aprobó explícitamente la identidad | Solo operaciones enumeradas por política; no implica que Redroid esté instalado |
| `rejected` | El operador rechazó la solicitud | Sin operaciones autenticadas salvo flujo de re-enrolamiento explícito |
| `revoked` | Acceso retirado | Denegar inmediatamente; no aceptar tareas ni renovar credenciales antiguas |

Conectividad derivada, independiente: `online`, `stale`, `offline`. La salud reportada por el agente debe mostrarse por separado de la última señal recibida. No convertir una señal reciente en estado “saludable” automáticamente.

Capacidades separadas y explícitas: `linux_base`, `container_runtime`, `binderfs`, `redroid`, `adb`, `image_cache`. Ausente/desconocido no equivale a instalado. La fase de adopción inicial solo necesita reportar capacidades observadas; no las instala.

## 3. Identidad y enrolamiento

1. PC-MASTER crea una solicitud de enrolamiento de un solo uso, con caducidad, ligada a un identificador esperado. Solo se conserva un hash del secreto.
2. El operador entrega el secreto por un canal local controlado; nunca se incluye en Git, logs, capturas ni preseed.
3. El agente crea o recibe identidad criptográfica individual por nodo. La credencial queda vinculada al identificador estable y al estado de enrolamiento.
4. El worker inicia como `pending`; una señal de vida no lo aprueba.
5. PC-MASTER muestra hostname declarado, huella/identidad, arquitectura, sistema/kernel, capacidades y primera/última señal. El operador compara la identidad esperada y aprueba o rechaza explícitamente.
6. Revocar invalida la autorización en el servidor en cada petición; rotar credenciales invalida la anterior de forma transaccional.
7. Si se reinstala el sistema y cambia la identidad criptográfica, exigir revalidación manual. No confiar solo en hostname o dirección IP.

Las credenciales deben ser individuales, aleatorias, revocables y no recuperables en claro desde la base. La implementación debe reutilizar los contratos/servicios existentes de enrolamiento y autenticación; no crear un segundo sistema paralelo.

## 4. Transporte y autorización

- Comunicación iniciada por el worker hacia PC-MASTER; no requiere puertos entrantes en el worker.
- HTTPS con validación estricta de CA/identidad; sin fallback HTTP.
- Autenticar y comprobar estado actual del nodo en cada petición.
- Autorizar por ruta y operación; no usar únicamente un rol genérico “worker”.
- Para `pending`, permitir únicamente heartbeat, publicación limitada de capacidades y consulta del propio estado. Denegar tareas, aceptación/progreso/resultado, shell y ADB.
- Para `revoked`, credenciales expiradas, identidad desconocida, TLS inválido o estado incoherente: denegar por defecto.
- No exponer el socket del runtime de contenedores, ADB ni una consola administrativa al agente.
- Redactar secretos de URLs, headers, excepciones, métricas y logs.

## 5. Heartbeat, desconexión y modo offline

Cada heartbeat incluye un identificador de mensaje único, identidad del nodo, secuencia monotónica, versión del agente, timestamp y capacidades observadas. El servidor valida autenticación, secuencia y límites antes de actualizar el último contacto.

- Duplicado idéntico: respuesta idempotente sin duplicar efectos.
- Mismo ID con payload distinto: conflicto y registro saneado.
- Secuencia antigua: rechazar o ignorar sin retroceder el estado.
- Desconexión: marcar `stale` y luego `offline` según umbrales configurables; no revocar ni aprobar automáticamente.
- Reconexión: revalidar credencial/estado y enviar una nueva señal; no reproducir órdenes operativas almacenadas.
- La cola local, si se incorpora, solo puede conservar telemetría limitada con retención acotada. No guardar tareas ejecutables en un nodo pendiente.
- Indicador de conexión en UI y hora de última señal. No afirmar sincronización si no ocurrió.

El inventario local puede seguir visible sin conexión, pero aprobar/revocar nodos, rotar credenciales y recibir telemetría nueva requieren conectividad con PC-MASTER. La interfaz debe distinguir dato local cacheado de dato confirmado por servidor.

## 6. Contrato mínimo de datos

Campos propuestos para la vista de nodo:
- `node_id`: UUID estable asignado al enrolar.
- `display_name`: nombre editable por el operador, distinto de la identidad.
- `identity_fingerprint`: huella pública, nunca clave privada.
- `adoption_state`, `connectivity_state`, `reported_health`.
- `os_name`, `os_version`, `kernel_release`, `architecture`.
- `cpu_model`, `logical_cpu_count`, `memory_total_bytes`, `storage_free_bytes`.
- `agent_version`, `capabilities`, `last_seen_at`, `heartbeat_sequence`.
- `approved_at/by`, `revoked_at/by`, timestamps de auditoría.

Tratar los datos del agente como entrada no confiable: validar tipos, rangos, tamaño, campos permitidos y timestamps. No aceptar paths, comandos, variables de entorno ni texto que se vaya a ejecutar desde el payload.

## 7. Idempotencia y concurrencia

- Toda solicitud de escritura lleva `request_id` o clave de idempotencia y hash canónico del payload.
- Repetición de misma clave y mismo hash devuelve el resultado original; clave reutilizada con payload distinto produce conflicto.
- Aprobar/revocar/rotar credenciales son transacciones atómicas que actualizan estado y auditoría.
- Una carrera entre heartbeat y revocación no debe reactivar al nodo: comprobar estado actual dentro de la transacción/operación protegida.
- Nunca reasignar ni despachar tarea solo porque un nodo volvió a conectarse.
- Usar reloj del servidor para expiraciones y conservar tiempos reportados solo como dato no confiable.

## 8. Seguridad y privacidad

- Mínimo privilegio: agente sin permisos de administrador en operación normal; privilegios de instalación separados y explícitos.
- No ejecutar comandos arbitrarios, ADB, contenedores ni tareas durante adopción.
- No almacenar secretos en GitHub, archivos de ejemplo, CI logs o documentación.
- Limitar tamaño de peticiones, frecuencia, concurrencia, timeout y cardinalidad de direcciones rastreadas.
- Retención acotada de telemetría y auditoría sin secretos; evitar recopilar datos personales no necesarios.
- Un nodo rechazado/revocado no debe poder crear otra identidad aprobada usando el mismo hostname/IP.
- La UI debe mostrar estados verdaderos y no fabricar nodos o checks verdes.

## 9. Pruebas obligatorias antes de implementación física

1. Enrolamiento de un solo uso, expiración y doble consumo concurrente.
2. Identidad/huella incorrecta, nodo duplicado y reinstalación con nueva identidad.
3. Matriz de autorización pending/approved/rejected/revoked para cada ruta.
4. Credencial expirada/revocada, CA incorrecta y transporte no seguro.
5. Heartbeat duplicado, secuencia antigua, timestamp inválido y payload sobredimensionado.
6. Carrera heartbeat vs revocación y rotación de credenciales.
7. Pérdida de conexión, stale/offline, reconexión y caché UI obsoleta.
8. Reintentos e idempotencia con mismo y distinto hash.
9. Redacción de secretos en logs/respuestas y límite de rate limiter.
10. Pruebas contra PostgreSQL desechable, CI en Linux/Windows cuando corresponda y `pip check` limpio.

### Matriz mínima de autorización para convertir el contrato en pruebas

Esta matriz es normativa para las pruebas del transporte; cualquier ruta nueva debe incorporarse explícitamente antes de implementarse.

| Estado del nodo | Estado de credencial | Heartbeat/capacidades propias | Consulta de estado propio | Aceptar/progresar/resultado de tarea | Reconciliación operativa |
|---|---|---|---|---|---|
| `pending` | `pending` | Permitir solo tras autenticación limitada y validación de esquema | Permitir solo recurso propio | Denegar | Denegar |
| `active` | `active`, vigente | Permitir según contrato | Permitir según contrato | Permitir únicamente tareas asignadas y con fencing/lease vigentes | Permitir con idempotencia y validación de propiedad |
| `rejected` | cualquier estado | Denegar | Denegar | Denegar | Denegar |
| `revoked` o nodo revocado | cualquier estado | Denegar | Denegar | Denegar | Denegar |
| cualquier estado | `revoked` o expirada | Denegar | Denegar | Denegar | Denegar |
| nodo y credencial no coinciden | cualquiera | Denegar | Denegar | Denegar | Denegar |
| estado desconocido/inconsistente | cualquiera | Denegar (fail closed) | Denegar | Denegar | Denegar |

Pruebas negativas concretas:
- Una credencial `pending` no puede acceder a ninguna ruta de tarea aunque el cuerpo indique un `node_id` activo.
- Cambiar el `node_id` del payload no cambia la identidad autenticada ni el recurso de consulta propio.
- Credencial expirada o revocada durante una espera de lock no autoriza la escritura después de adquirir el lock.
- Si la revocación confirma primero, heartbeat debe fallar y no modificar `last_seen_at`, capacidades ni secuencia.
- Si heartbeat confirma primero, la revocación posterior debe dejar al nodo revocado; ningún retry puede volverlo activo.
- Repetir el mismo `request_id`/idempotency key con el mismo payload no duplica cambios; con payload distinto devuelve conflicto.
- Rutas no registradas y métodos HTTP no declarados se rechazan por defecto.
- Los logs y respuestas de denegación no incluyen bearer token, hash, nonce ni payload sensible.

## 10. Orden de implementación propuesto

1. Completar aceptación manual de PC-MASTER (#77) y revisar la pila existente antes de integrar.
2. Reconciliar los contratos existentes de nodo, credencial, nonce y autorización; evitar tablas/rutas duplicadas.
3. Implementar primero el registro/vista de nodos con fixtures de prueba únicamente en tests; sin workers físicos.
4. Añadir enrolamiento de un solo uso y estados administrativos con pruebas negativas.
5. Añadir heartbeat/capacidades y reconexión idempotente.
6. Revisar seguridad, logs y permisos antes de permitir una prueba física de solo telemetría.
7. Aprobar por separado cualquier instalación de Debian en hardware; confirmar el disco exacto antes de usar particionado automatizado.
8. Evaluar Redroid únicamente después de resolver #27 y sin inferir que adoptar un nodo lo autoriza a ejecutar Android.

## 11. Criterio de aceptación

- El diseño permite registrar un worker Linux sin Redroid instalado.
- El estado pendiente nunca recibe tareas.
- Identidad criptográfica, autorización por ruta, revocación e idempotencia tienen pruebas negativas reproducibles.
- Heartbeat, conectividad y salud son estados distintos.
- Documentación y decisiones se mantienen en español en GitHub.
- No hay dependencia obligatoria de pago ni cambio físico antes de la aprobación correspondiente.

## Registro de cambios

- 2026-10-28: primera especificación documental de adopción segura desacoplada del motor Android. No representa implementación ni prueba física.


## 12. Integración obligatoria con la autenticación ya existente

Esta propuesta no sustituye ni duplica la ADR-005, el esquema de credenciales o el servicio de dominio existente. La revisión de Issues #40, #44 y #46 detecta una decisión de integración que debe resolverse antes de implementar:

- ADR-005/#40 y transporte #46 describen que un nodo `pending` puede reportar heartbeat/capacidades y consultar su propio estado, sin recibir tareas.
- El servicio de dominio descrito en #44 autentica únicamente credenciales activas asociadas a nodos aprobados (`admin_state='active'`). Por ello, hoy no debe asumirse que un nodo pendiente pueda autenticarse por HTTP solo porque el contrato lo desea.
- No resolver esta diferencia creando un endpoint alternativo, saltándose el servicio de autenticación o marcando automáticamente el nodo como activo.

### Decisión de diseño para resolver la discrepancia

Se adopta la separación de responsabilidades descrita en el alcance de #46: **autenticar la identidad y el estado de la credencial no concede autorización para cualquier ruta**. El servicio existente debe conservar una ruta estricta para operaciones operativas y añadir una decisión explícita, testeable y limitada para la telemetría de nodos pendientes; no se debe convertir el nodo a activo ni relajar la política global.

Contrato de integración propuesto:
1. Validar token, hash, expiración, revocación e identidad vinculada usando el servicio de credenciales existente.
2. Obtener el estado administrativo actual del nodo desde la fuente autoritativa, no desde el payload del agente ni desde caché no invalidable.
3. Autorizar la operación por una política central explícita:
   - `pending`: solo heartbeat, publicación limitada de capacidades y consulta de su propio estado.
   - `approved/active`: solo las operaciones adicionales ya enumeradas por contrato.
   - `rejected`, `revoked`, credencial expirada o identidad inconsistente: denegar.
4. Mantener el camino de claim/accept/progress/result/reconcile separado y denegado para `pending`; no reutilizar el permiso de heartbeat como permiso de tarea.
5. Comprobar estado y aplicar la escritura de heartbeat bajo la protección transaccional/concurrencia apropiada para que una revocación concurrente no deje el nodo autorizado ni actualice su estado como si siguiera vigente.

**Hallazgo concreto del servicio actual:** `authenticate_bearer()` en `packages/cluster-agent-auth/src/cluster_agent_auth/service.py` exige simultáneamente `nodes.admin_state = 'active'` y `node_credentials.status = 'active'`. Por tanto, el transporte no puede reutilizar esa función para un nodo `pending` y esperar que funcione; hoy el rechazo es intencional y seguro.

Para implementar la política sin debilitar la función existente:
- Mantener `authenticate_bearer()` como camino de autenticación para operaciones de nodos aprobados.
- Añadir, dentro del mismo paquete y usando la misma fuente de credenciales, una operación de autenticación de alcance restringido para telemetría de enrolamiento, o un resultado autenticado neutral seguido de autorización central. No duplicar SQL/esquema/almacenamiento de secretos.
- El resultado neutral debe incluir `node_id`, estado administrativo actual y estado de credencial; el middleware debe pasar por una allowlist exacta de rutas y rechazar cualquier operación fuera de ella.
- No permitir que una credencial `pending` llegue a la autorización operativa por reutilización accidental del resultado; los handlers de tareas deben exigir estado/credencial aprobados de forma independiente.
- Bloquear nodo y credencial en un orden consistente y probar carrera con revocación/activación para evitar decisiones basadas en estado obsoleto.

**Estado de implementación revisado el 2026-10-28:** la rama de la [PR #48](https://github.com/D3ckardCain/Geelark-IA/pull/48) ya implementa `make_database_authenticator()` para pares `pending/pending` y `active/active`, la política por operación y handlers PostgreSQL que vuelven a validar el estado bajo bloqueo de filas antes de mutar. La PR documenta CI satisfactoria, incluida la prueba end-to-end de PostgreSQL y la denegación de tareas para `pending`. Esto significa que la vía restringida ya existe en una rama de propuesta, **no** que esté fusionada, desplegada o validada en PCs físicos.

Antes de integrar/habilitar el transporte, comprobar que la matriz estado × operación, credencial expirada/revocada, identidad A intentando actuar como B y carrera heartbeat-vs-revocación están cubiertas por tests de la versión exacta del HEAD. Si la persistencia no garantiza atomicidad suficiente, el endpoint debe permanecer deshabilitado; no se permite bypass ni API paralela. No abrir puertos ni desplegar agentes para validar esta decisión.

Este punto debe resolverse dentro de la cadena existente de transporte/auth, respetando sus bases y pruebas, no mediante una API paralela. Referencias: [#40](https://github.com/D3ckardCain/Geelark-IA/issues/40), [#44](https://github.com/D3ckardCain/Geelark-IA/issues/44), [#46](https://github.com/D3ckardCain/Geelark-IA/issues/46).
