# ADR-004 — Resolución segura de operaciones `unknown`

- **Fecha:** 2026-10-10
- **Estado:** aceptado por el usuario; comparación remota read-only implementada en una rama de trabajo, resolución manual de `unknown` todavía pendiente.
- **Ámbito:** protocolo de tareas del agente, bandeja durable, controlador y procedimientos operativos de GeeLark-IA.

## Contexto

Una operación puede quedar en estado `unknown` si el agente pierde conectividad o se interrumpe la comunicación cuando no es posible determinar con certeza si la acción llegó a ejecutarse. Reintentar o reasignar a ciegas puede duplicar efectos; marcarla automáticamente como éxito o fallo puede falsear el estado real.

## Decisión

1. `unknown` significa **resultado incierto**, no éxito, fallo ni autorización para reintentar.
2. No reintentar, reclamar de nuevo, reasignar ni volver a ejecutar automáticamente una operación `unknown`.
3. No convertir automáticamente `unknown` a `succeeded`, `failed` o `rejected`.
4. La reconciliación remota puede comparar estados únicamente mediante una operación autenticada de solo lectura. No cambia estados ni permisos; cualquier endpoint de resolución con escritura permanece deshabilitado hasta contar con autorización de operador, auditoría inmutable y pruebas independientes.
5. La resolución requiere intervención de un operador autorizado, revisión de evidencia/auditoría y una acción explícita registrada. Si no hay evidencia suficiente, la operación permanece `unknown`.
6. Una decisión manual no debe permitir que un nodo con epoch obsoleto, lease vencido o credencial revocada cambie el estado del controlador.
7. Mantener idempotencia y fencing por `assignment_epoch`; nunca asumir que timeout o ausencia de heartbeat prueban que la tarea no se ejecutó.

## Requisitos antes de habilitar reconciliación

- Autorización específica de operador y auditoría inmutable de quién, cuándo, motivo, evidencia y decisión.
- Pruebas de reintentos, pérdida de ACK tras commit, caída del agente/controlador, desconexión, revocación de credenciales, epoch obsoleto, lease expirado y solicitudes concurrentes.
- Pruebas que demuestren que no existe autoéxito, autofallo, reejecución ni doble asignación desde `unknown`.
- Contrato/documentación del API y manual operativo en español.
- CI verde y revisión del stack completo. Ninguna prueba en hardware físico sin autorización explícita.

## Consecuencias

- Algunas operaciones pueden quedar bloqueadas hasta una revisión humana; es un coste deliberado para evitar efectos duplicados o estados inventados.
- El heartbeat y las métricas siguen siendo útiles para diagnóstico, pero no resuelven por sí solos el resultado de una tarea.
- La comparación read-only no activa ejecución de tareas ni modifica estados del controlador. La resolución manual aún no está implementada ni desplegada.

## Seguimiento

- [Issue #50 — bandeja durable y protocolo de reconciliación](https://github.com/D3ckardCain/Geelark-IA/issues/50)
- [Issue #65 — integración y auditoría de autorización de nodos pendientes](https://github.com/D3ckardCain/Geelark-IA/issues/65)
- [PR #54 — bandeja durable de tareas](https://github.com/D3ckardCain/Geelark-IA/pull/54)


## Revalidación del estado — 2026-10-12

La rama de la PR #52 contiene `POST /agent/v1/reconcile` como comparación de solo lectura: exige autorización específica, valida identidad/epoch/propiedad y devuelve `uncertain_review_required` cuando cualquiera de los lados es `unknown`. No modifica las tablas de tareas/operaciones. La prueba de integración de PR #67 ya no se omite y CI [#38193374440](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38193374440) terminó success con 130 pruebas de transporte y 18 pruebas del journal.

Esto no autoriza resolución automática ni manual con escritura. La acción que convierta `unknown` en otro estado sigue fuera de alcance; se requiere decisión de operador, evidencia y auditoría antes de diseñarla. Las PR continúan draft y no se han fusionado ni desplegado.
