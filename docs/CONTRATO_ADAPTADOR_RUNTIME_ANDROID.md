> **Nota de vigencia — 2026-10-22:** Este contrato es una propuesta histórica de diseño, no una selección de motor ni un permiso para instalarlo. Las referencias a redroid, Bliss OS y Android Emulator son ejemplos de motores desacoplables, no decisiones vigentes. La selección actual sigue abierta: QEMU/Android-x86/VNC retirado, redroid bloqueado por #27 y Cuttlefish candidato no aprobado. El contrato canónico vigente que debe compararse antes de reutilizar contenido es `docs/CONTRATO_ADAPTADOR_ANDROID.md` en `main`.

# Contrato del adaptador de runtime Android

**Fecha:** 2026-10-09  
**Estado:** propuesta de diseño; aún no es código ejecutable ni prueba de motor Android.  
**Objetivo:** permitir que GeeLark-IA desarrolle y pruebe la capa de control del clúster sin quedar atada a redroid, Bliss OS o Android Emulator.

## 1. Principio

El plano de control no debe depender de los comandos internos de un motor concreto. Cada worker expone un agente autenticado que implementa un contrato común; el agente traduce operaciones al runtime aprobado en ese nodo. La selección del motor se configura por worker y versión. Si un runtime deja de tener soporte o no pasa seguridad/licencias, se puede sustituir sin reescribir asignación, panel, cola, auditoría y estado de tareas.

**Este contrato no convierte todavía al clúster en operativo.** No existe runtime instalado ni agente desplegado en los equipos.

## 2. Entidades mínimas

- **Node:** identidad estable del worker, versión de agente/runtime, estado de salud, capacidades CPU/RAM/disco/gráficos, último latido y estado de mantenimiento.
- **RuntimeProfile:** tipo de runtime, versión exacta, digest/hash de imagen, ABI, política de red, límites de recursos, licencia revisada y estado de aprobación.
- **AndroidInstance:** UUID, nombre visible, nodo propietario, epoch/fencing token, perfil de runtime, estado deseado/observado, ID nativo del runtime y ubicación de datos persistentes.
- **Operation:** UUID, instancia, acción, clave de idempotencia, hash de petición, estado, intentos, tiempos, resultado normalizado y error clasificado.
- **Artifact:** nombre, versión, arquitectura, origen, SHA-256, firma si existe, licencia, tamaño, aprobación/revocación y nodos que lo tienen cacheado.

## 3. Operaciones del contrato

| Operación | Entrada principal | Resultado requerido |
|---|---|---|
| `capabilities` | ninguna | versión del agente/runtime, recursos disponibles, aceleración, límites y capacidades explícitas |
| `validate_profile` | perfil + versión/hash de artefactos | aprobado/rechazado con razones; no inicia nada |
| `create_instance` | UUID, perfil, recursos, clave idempotente | ID nativo y estado inicial; no crear duplicado en reintento |
| `start_instance` | UUID, epoch, clave idempotente | estado observado o operación pendiente |
| `stop_instance` | UUID, epoch, clave idempotente | parada confirmada o error clasificado |
| `restart_instance` | UUID, epoch, clave idempotente | resultado reconciliable; no repetir acción ciegamente |
| `delete_instance` | UUID, epoch, modo de datos, clave idempotente | instancia eliminada; borrado de datos requiere una política explícita |
| `inspect_instance` | UUID | estado, versión, salud, IP solo si aplica y métricas permitidas |
| `install_app` | UUID, artefacto aprobado, hash, clave idempotente | resultado; nunca aceptar APK de ruta arbitraria sin política |
| `collect_metrics` | UUID opcional | CPU/RAM/disco/estado/tiempo de arranque, con timestamp |
| `snapshot_or_export` | UUID, política de datos | solo si el runtime lo soporta; indicar formato, integridad y compatibilidad |
| `reconcile` | inventario esperado | diferencia entre estado deseado y observado, sin borrar/crear automáticamente de forma destructiva |

El agente debe responder con un esquema versionado y errores normalizados: `UNSUPPORTED`, `INVALID_PROFILE`, `CAPACITY_EXCEEDED`, `NOT_FOUND`, `NOT_OWNER`, `STALE_EPOCH`, `ARTIFACT_NOT_APPROVED`, `RUNTIME_UNAVAILABLE`, `TIMEOUT`, `RETRYABLE`, `PERMANENT_FAILURE`.

## 4. Estados y consistencia

- Estado de operación: `queued → claimed → running → succeeded | failed | cancelled`. El sistema puede tener `unknown`/reconciliation-required cuando el worker pierde conexión durante una acción.
- Estado de instancia: `requested → creating → stopped → starting → running → stopping → stopped`; estados de error/mantenimiento deben registrarse sin ocultar el último estado observado.
- Cada comando mutante lleva UUID de operación, clave de idempotencia, hash de petición, ID de instancia y epoch de propietario.
- La misma clave con el mismo hash devuelve el resultado original; la misma clave con hash diferente produce conflicto.
- El agente valida que el nodo es propietario y que el epoch no es antiguo antes de ejecutar. Un epoch viejo no puede alterar una instancia reasignada.
- No marcar una operación como completada solo porque se envió un comando. Requerir confirmación del runtime o reconciliar estado tras timeout.
- No reubicar una instancia a otro nodo como si su almacenamiento local fuera replicado. La migración requiere exportación/copia verificada o restauración explícita.

## 5. Seguridad del agente

- Identidad única por nodo, credenciales revocables/rotables y autenticación mutua o mecanismo equivalente.
- El agente no confía en un `node_id` recibido del cliente: deriva identidad del canal autenticado.
- Control plane y workers solo por red de gestión; firewall por allowlist. Sin puertos administrativos o ADB expuestos a Internet.
- ADB queda desactivado salvo operación explícita, con bind a loopback dentro del host o túnel de administración controlado.
- Separar proceso del agente de root; usar permisos mínimos y helper privilegiado limitado si el runtime lo exige.
- El agente no ejecuta shell arbitrario recibido desde la API. Las acciones se mapean a operaciones enumeradas y parámetros validados.
- Cada operación registra auditoría sin incluir secretos, tokens, contraseñas ni contenido privado de aplicaciones.

## 6. Capacidad y planificación

Cada runtime declara reservas de RAM, CPU, disco y memoria gráfica por instancia. El planificador aplica límites conservadores configurables y reserva recursos atómicamente antes de mandar la creación. Los límites iniciales son hipótesis, no promesas de densidad.

La primera prueba medirá una instancia, después carga sostenida y finalmente varias instancias. No escalar automáticamente hasta disponer de métricas de 24 horas, margen de memoria, comportamiento gráfico, reinicio y fallo de worker.

## 7. Offline y conectividad limitada

- El control plane registra operaciones con IDs únicos e idempotencia antes de entregarlas al worker.
- Un worker desconectado no se considera capaz de ejecutar órdenes nuevas. Las órdenes no destructivas pueden quedar en cola según su caducidad; acciones de borrado/instalación deben requerir validación reciente.
- Al reconectar, el agente reporta su inventario observado y la cola reintenta solo operaciones elegibles; primero reconciliar, luego mutar.
- Las descargas grandes se hacen a una caché local aprobada y se distribuyen por LAN con SHA-256 verificado.
- La interfaz debe mostrar online/offline, última comunicación y operaciones pendientes.
- No prometer operación Android completa offline: inicio/gestión local podría funcionar en el nodo, pero descargas, autenticación externa, APIs y sincronización dependen de conectividad.

## 8. Pruebas de aceptación del contrato

1. Crear una instancia dos veces con la misma clave no duplica recursos.
2. Repetir clave con hash distinto da conflicto.
3. Un worker no propietario no puede iniciar, detener ni borrar una instancia.
4. Un epoch antiguo es rechazado.
5. Timeout después de enviar una orden se resuelve por inspección/reconciliación, no por repetición ciega.
6. Un artefacto sin aprobación o con SHA-256 incorrecto se rechaza.
7. Una caída y reconexión no pierde operaciones ni duplica efectos.
8. Una operación destructiva no se ejecuta desde una cola caducada.
9. Un agente comprometido no obtiene shell arbitrario del host desde la API.
10. Los registros de auditoría no contienen credenciales ni datos privados de aplicaciones.

## 9. Integración por fases

**Fase 1 — contratos y simulador:** implementar un runtime simulado que devuelva estados y errores controlados; permite desarrollar el panel, cola, auditoría, fencing e idempotencia sin instalar Android.

**Fase 2 — agente de laboratorio:** agente mínimo con autenticación, capacidades y health check en WORKER-01; inicialmente no ejecutar operaciones privilegiadas.

**Fase 3 — runtime real de una instancia:** solo cuando imagen/licencia/seguridad estén aprobadas; ejecutar create/start/stop/inspect y recoger métricas.

**Fase 4 — apps y persistencia:** instalar únicamente aplicaciones objetivo autorizadas, medir compatibilidad, datos, reinicio, red y recuperación.

**Fase 5 — multiinstancia:** medir densidad, rendimiento, límites y fallos antes de habilitar escalado.

## 10. Decisiones abiertas

- Motor Android compatible, mantenido y legalmente utilizable para el propósito concreto.
- Versiones exactas de imagen, kernel, firmware y agente.
- Formato de almacenamiento persistente y política de snapshots.
- Mecanismo de identidad/certificados de workers.
- Aplicaciones objetivo y requisitos de Google Play/GMS, ABI ARM, notificaciones, sensores y detección de emulador.
- Límites medidos por instancia y objetivo de densidad.

## Fuentes de contexto

- Revisión de disponibilidad de imágenes Android: `docs/REVISION_DISPONIBILIDAD_IMAGENES_ANDROID_2026-10-09.md`
- Prototipo de persistencia y fencing: `packages/cluster-persistence/prototype/`
- Issue de seguridad redroid: https://github.com/D3ckardCain/Geelark-IA/issues/27

**Límite explícito:** este documento define un contrato propuesto, no código desplegado ni paridad con GeeLark. Cada operación debe implementarse y probarse por separado.
