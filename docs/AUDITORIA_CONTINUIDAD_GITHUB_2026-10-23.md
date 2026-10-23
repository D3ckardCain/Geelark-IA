# Auditoría de continuidad GitHub — 2026-10-23

## Alcance y criterio

Revisión de solo lectura de `D3ckardCain/Geelark-IA` para priorizar limpieza e integración sin fusionar cambios inseguros ni ejecutar workflows redundantes. Coste objetivo: **0 USD**. No se autorizan instalaciones en WORKERS físicos ni cambios destructivos de infraestructura.

## Decisiones vigentes

- PC-MASTER: Windows; panel web y lanzador/configurador son componentes distintos.
- PC-WORKERS: Debian 13 previsto.
- Android: **redroid es el primer y único motor en preparación**.
- La issue #27 es una puerta de seguridad obligatoria. No ejecutar redroid en hardware físico hasta demostrar mitigación reproducible para una imagen/digest exactos.
- QEMU + Android-x86 + VNC en WSL2 está retirado. No reintroducirlo.
- Cuttlefish solo puede reconsiderarse como contingencia si redroid falla la puerta de seguridad o viabilidad.
- Objetivo operativo: 0 USD; no añadir servicios de pago, runners facturables ni dependencias temporales.

## Fotografía de GitHub

La consulta inicial del día devolvió 21 PR abiertas; la revalidación posterior del 2026-10-23 devuelve **38 Issues abiertas, 10 cerradas y 23 PR abiertas**, todas en draft. Estos números son fotografías temporales. Estos números son una fotografía y pueden cambiar. La búsqueda de Issues puede incluir elementos históricos/actualizados; el estado debe confirmarse antes de cualquier cierre.

## Bloqueos principales

### 1. Cadena de control/Worker

Orden de dependencia documentado: **#101 → #74 → #52 → #57 → #67 → #85**.

- #101, #52 y #67 aparecen con conflictos/no mergeables en la última auditoría registrada.
- El HEAD registrado de #101 (`b84da93881f5866e8832e5888e5dce02433e85cc`) no tenía workflow asociado en la consulta previa. No reutilizar CI de otro SHA como prueba del HEAD actual.
- No fusionar descendientes ni actualizar sus bases a ciegas.
- Siguiente paso técnico: inspeccionar el diff y la base exacta de #101; corregir conflicto en su rama, comprobar que el contrato de ACK/inventario coincide con la persistencia actual y dejar que la CI normal valide el nuevo HEAD. Después seguir en orden, una PR cada vez.

### 2. Línea PC-MASTER Windows

- #104 contiene el panel web autenticado de solo lectura y correcciones de seguridad Windows; sigue en draft.
- #103 y #87 forman una línea separada y su ascendencia debe reconciliarse con cuidado; #87 no es el panel web.
- Issue #77 mantiene la aceptación manual de Windows; #88 mantiene la comparación con el artefacto local. CI no sustituye estas comprobaciones.
- No fusionar solo porque los jobs anteriores estén verdes: validar el SHA exacto y revisar el diff completo tras resolver bases.

### 3. Redroid y workers físicos

- #27 permanece abierta y bloqueante.
- #10 no debe estimar densidad de instancias antes de medir hardware real.
- #24 es la caché local de artefactos verificados; #92 es el aprovisionamiento Debian 13. Mantener sus responsabilidades separadas.
- No instalar ni ejecutar redroid durante esta auditoría documental.

### 4. Paridad funcional

- #3 coordina la Fase A y la aceptación de la matriz.
- #6 profundiza en el catálogo de perfiles, RPA, Synchronizer, Library y API.
- #4 define el método de paridad/evidencia.
- No cerrar estas tareas porque los documentos existan: el corte de fuentes original es del 2026-10-09 y la revisión funcional exhaustiva sigue pendiente.

## Higiene y cierre de trabajo

- No cerrar Issues de implementación por tener documentación o CI histórica.
- No borrar documentos históricos complementarios ni ramas/PR sin confirmar que sus cambios únicos están integrados.
- La issue #29 describe brechas de contrato que se solapan parcialmente con #15/#16, pero no debe cerrarse como duplicada hasta reconciliar cada criterio pendiente; su cuerpo conserva tareas no marcadas completas.
- La issue #89 describe una corrección candidata en #104, pero no debe cerrarse antes de integrar la corrección o confirmar formalmente que el criterio de issue está satisfecho.
- No lanzar re-runs manuales solo para refrescar una auditoría. Usar resultados existentes únicamente para el SHA exacto al que pertenecen.

## Próxima secuencia recomendada

1. Resolver el conflicto de sincronización #112, revisar los 10 archivos afectados y validar el SHA resultante; no escoger un `runtime.py` entero sin reconciliar las funciones exclusivas.
2. Revalidar la cadena #101 → #74 → #52 → #57 → #67 → #85; #101 y #74 tienen CI verde en sus SHA actuales, pero #52 y #67 siguen con conflicto.
3. En paralelo, inspeccionar #104/#103/#87 y definir una reconciliación explícita de ascendencia; no cambiar bases automáticamente.
4. Mantener #27 como bloqueo hasta evidencia reproducible de mitigación de redroid para imagen/digest exactos.
5. Continuar la auditoría de Issues y cerrar únicamente decisiones ya resueltas o duplicados demostrados, registrando el motivo y el enlace canónico.
6. Actualizar el manual técnico y el registro español de problemas/soluciones al completar cada módulo; no marcar aceptación de hardware sin pruebas físicas autorizadas.

## Limitaciones de esta auditoría

Esta nota registra el estado observado y la secuencia segura. No afirma que los conflictos de PR estén resueltos, que las ramas se hayan fusionado, que redroid sea seguro, ni que el panel o los workers estén operativos.


## Revalidación posterior de la auditoría — 2026-10-23

- Se verificaron enlaces relativos de README, estado, plan, comparación de motores, ADR-002 y esta auditoría: **no se encontraron enlaces relativos rotos** en esos seis documentos.
- Se actualizaron Issues #50, #63, #71, #72, #89, #91 y #93 con evidencias de SHA/CI y dependencias actuales. #105 permanece cerrada: la colisión ADR-005 ya no existe; el nombre actual de PC-MASTER en la rama #104 es ADR-007 (ADR-006 queda en la rama histórica cerrada #70).
- PR #112 no es mergeable; se dejó comentario y no se fusionó. PR #113 pasó transporte y la prueba PostgreSQL afectada después de ampliar el workflow para ejecutar `test_task_inbox_postgres.py` ante cambios en `cluster-agent-transport`.
- El HEAD actual consultado de #104 es `75764c435f488f617a07c0003ce088829e6dbd41`, con transporte #473 y persistencia #602 `success`; siguen pendientes aceptación manual #77 y comparación local #88.
- No se cerraron issues de implementación con criterios pendientes; #64 es la única decisión de sistema base cerrada en esta pasada. No se ejecutó Android ni se modificó hardware físico.
