# ADR-004 — Resolución segura de operaciones `unknown`

- **Fecha:** 2026-10-10
- **Estado:** aceptado por el usuario; implementación pendiente.
- **Ámbito:** protocolo de tareas del agente, bandeja durable, controlador y procedimientos operativos de GeeLark-IA.

## Contexto

Una operación puede quedar en estado `unknown` si el agente pierde conectividad o se interrumpe la comunicación cuando no es posible determinar con certeza si la acción llegó a ejecutarse. Reintentar o reasignar a ciegas puede duplicar efectos; marcarla automáticamente como éxito o fallo puede falsear el estado real.

## Decisión

1. `unknown` significa **resultado incierto**, no éxito, fallo ni autorización para reintentar.
2. No reintentar, reclamar de nuevo, reasignar ni volver a ejecutar automáticamente una operación `unknown`.
3. No convertir automáticamente `unknown` a `succeeded`, `failed` o `rejected`.
4. La reconciliación remota permanece deshabilitada (HTTP 503) hasta que el protocolo, la autorización y las pruebas de seguridad estén implementados.
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
- La decisión no activa ejecución de tareas ni modifica el despliegue actual.

## Seguimiento

- [Issue #50 — bandeja durable y protocolo de reconciliación](https://github.com/D3ckardCain/Geelark-IA/issues/50)
- [Issue #65 — integración y auditoría de autorización de nodos pendientes](https://github.com/D3ckardCain/Geelark-IA/issues/65)
- [PR #54 — bandeja durable de tareas](https://github.com/D3ckardCain/Geelark-IA/pull/54)
