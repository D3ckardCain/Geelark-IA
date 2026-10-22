# ADR-006: Integración de solo lectura del estado Master/Worker

- **Estado:** propuesta de arquitectura; no autoriza implementación operativa.
- **Fecha:** 2026-10-10
- **Relacionado:** issue #69, PR #70, contrato `master-worker-status-v1`. La ADR-005 queda reservada para autenticación de agentes (PR #40).
- **Coste objetivo:** 0 USD; no depender de servicios cloud de pago.

## Contexto

El panel actual es un HTML local con datos ficticios. El agente/supervisor, el transporte HTTPS, la autorización de nodos y la persistencia se desarrollan en PRs apiladas aún pendientes de revisión. Conectar la interfaz antes de confirmar la fuente de verdad y la autorización de lectura podría duplicar APIs o permitir que la interfaz mostrase estados no autoritativos.

## Decisión propuesta

1. **La interfaz nunca se conecta directamente a Workers ni a la base de datos.** Consulta un proveedor de snapshots de solo lectura en PC-MASTER.
2. **No crear un segundo canal de control.** El proveedor debe leer la fuente de estado autoritativa ya utilizada por el controlador existente. No duplicar autenticación, tablas, heartbeats ni lógica de autorización.
3. **No añadir listeners ni exposición WAN.** La interfaz seguirá siendo un archivo local hasta que se confirme cómo se sirve de forma segura en PC-MASTER. Cualquier servicio futuro debe estar ligado al plano de control aprobado, con TLS/autenticación y reglas de red revisadas.
4. **No inventar un endpoint antes de confirmar la API existente.** La primera implementación debe definir un puerto interno `StatusSnapshotProvider`; solo se añadirá una ruta HTTP si la arquitectura actual lo requiere y después de revisar autenticación humana/admin. Las credenciales de Worker no son credenciales de administrador.
5. **Serializar con el contrato v1.** Validar el snapshot antes de presentarlo. Una versión desconocida o un documento inválido se muestra como error/estado desconocido, nunca como saludable.
6. **Solo lectura real.** La ruta de datos no puede crear tareas, mutar asignaciones, aceptar recibos ni resolver `unknown`. No incluir botones de control remoto en esta fase.
7. **GitHub es evidencia complementaria.** Los enlaces a PR/CI pueden abrir GitHub; la consulta en vivo de GitHub es opcional y requiere Internet. La caída de GitHub no debe impedir mostrar el último snapshot local.

## Flujo de datos

```text
Worker --HTTPS saliente existente--> Controlador / persistencia autoritativa
                                          |
                                          v
                               StatusSnapshotProvider
                                          |
                                  contrato v1 validado
                                          |
                                          v
                                   Panel de solo lectura
                                          |
                             snapshot local con timestamp
```

La interfaz no hace solicitudes directas a Workers. El controlador determina autorización, salud y frescura; el agente no puede autodeclararse `active` ni `healthy`.

## Offline y datos obsoletos

- La maqueta HTML funciona sin Internet.
- En la integración futura, la última instantánea validada puede mostrarse desde caché local.
- Si no hay contacto reciente con el Worker, la frescura se calcula en PC-MASTER y el estado pasa a `stale`, `missing` u `unknown` según evidencia; no conservar `healthy` solo porque el último dato lo era.
- Si se pierde Internet, la vista local y la última instantánea siguen disponibles; las consultas actuales a GitHub no.
- Al ser lectura, no se crea cola de mutaciones offline ni se reintentan comandos.

## Puertas previas a implementar

- Revisar el stack apilado de autenticación/transporte (PR #44/#48) y persistencia/recibos (PR #54/#57), además del supervisor (PR #67) y la idempotencia (PR #68).
- Confirmar la fuente de verdad y el modelo de identidad/permisos del operador del panel.
- Mantener la corrección de salud reportada/derivada de [issue #71](https://github.com/D3ckardCain/Geelark-IA/issues/71) revisada e integrada en el stack antes de exponer el snapshot.
- Resolver [issue #72](https://github.com/D3ckardCain/Geelark-IA/issues/72): el backend aún no persiste un inventario de estados por módulo ni devuelve `modules[]` conforme al contrato v1; no inferir instalación/operatividad solo a partir de capacidades.
- Verificar que la autorización se vuelve a comprobar en el servidor y que los nodos `pending` solo pueden informar heartbeat/capacidades no sensibles/estado propio.
- Mantener handlers de tareas/reconciliación en 503 mientras sigan pendientes sus criterios de seguridad.
- Completar pruebas negativas y revisión manual de seguridad antes de integrar datos reales.
- No instalar agentes, cambiar SO ni probar sobre PCs físicas sin autorización explícita.

## Criterios de aceptación de la futura integración

- Un snapshot cumple contrato v1 y tiene fuente/tiempo de observación.
- `pending`, `revoked`, `unknown`, offline y datos caducados se muestran de forma distinta.
- La UI no puede escribir en la base de datos ni llamar operaciones de tarea.
- La ausencia de GitHub/Internet no bloquea el último snapshot local.
- Los logs no contienen tokens, payloads, datos privados ni errores sin redactar.
- Pruebas automáticas cubren estado fresco/obsoleto, nodo ausente, credenciales revocadas, contrato inválido y falta de permisos.
- No se añaden servicios ni APIs de pago; la integración sigue siendo migrable y local.

## Estado de auditoría (10-10-2026)

La revisión de PR #48 encontró una comprobación de frescura de 90 segundos en la elegibilidad de asignación y separación de `reported_health_state`/ `health_state` en el endpoint de estado. En el commit `2c58c3edf732de265235dae3dc683aa958e4208d`, los workflows de transporte, servicio de persistencia y esquema terminaron en success; se añadieron pruebas de derivación para heartbeat fresco, obsoleto y ausente. Evidencia: [CI transporte](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38085624799), [CI persistencia](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38085624804), [CI esquema](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38085624822).

Esto **no cierra automáticamente la issue #71**: PR #48 sigue abierta en borrador y la corrección aún debe revisarse dentro del stack apilado completo. Mantener la integración del panel bloqueada hasta que ese stack se integre y vuelva a validarse.

## Consecuencias

Esta decisión retrasa la telemetría real hasta que el stack de seguridad esté listo y exista un inventario de módulos autoritativo. El endpoint actual todavía no produce el snapshot v1 completo. Evita dos fuentes de verdad, endpoints duplicados y una falsa impresión de salud. La maqueta y el contrato pueden evolucionar sin abrir ejecución remota.


## Seguimiento de implementación (10-10-2026)

- La PR #73 implementa el reporte/persistencia de inventario de módulos Worker, apilada sobre la PR #48.
- La PR #74 implementa el puerto interno `StatusSnapshotProvider` y el adaptador PostgreSQL de solo lectura. En su HEAD `80e7f17865fc34f6f64832180ae4ad81d71a2042`, CI success: persistencia 26 pruebas, guard 12 y autenticación 26. [Ejecución](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38095051862).
- Este progreso **no elimina las puertas previas**: no hay endpoint administrativo, autenticación de operador ni conexión con el panel. El proveedor requiere una conexión con permisos SELECT solamente, que aún no se ha verificado con un rol PostgreSQL real.
- El esquema JSON v1 se comparte con la PR #70. La implementación debe permanecer en draft hasta revisar las PR apiladas, confirmar identidad/permisos humanos y completar la validación de seguridad.
