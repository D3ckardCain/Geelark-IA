# ADR-004 — Persistencia y consistencia del plano de control distribuido

**Fecha:** 2026-10-09  
**Estado:** propuesta para el MVP; requiere validación en la prueba de concepto.  
**Decisores:** proyecto Geelark-IA.

## Contexto

El planificador coordina nodos heterogéneos. Una asignación duplicada puede hacer que dos nodos ejecuten la misma instancia Android. El vencimiento de un heartbeat o lease no demuestra que el proceso anterior se haya detenido. Por tanto, la persistencia debe soportar transacciones atómicas, idempotencia, epochs monotónicos, auditoría y reconciliación tras reinicios o particiones de red.

El requisito de coste obligatorio de software/servicios es 0 USD. No se debe depender de una base de datos cloud, tarjeta, trial o suscripción.

## Opciones evaluadas

### A. SQLite independiente en la PC Master
Ventajas: muy simple, embebido, local y sin servicio separado.  
Riesgos: no proporciona por sí solo un protocolo de consenso entre controladores ni coordina automáticamente escrituras distribuidas. No colocar una base SQLite activa sobre un recurso de red para fingir que es distribuida.

### B. PostgreSQL local en la PC Master, con un solo escritor autorizado
Ventajas: software libre, transacciones, restricciones únicas, bloqueos y herramientas de backup; puede instalarse y mantenerse sin servicio cloud obligatorio.  
Riesgos: la base/controlador central sigue siendo un punto de dependencia para nuevas asignaciones; requiere administración, actualizaciones y restauración. No da alta disponibilidad por sí solo.

### C. Base de datos replicada o consenso distribuido desde el inicio
Ventajas: puede permitir mayor resiliencia del plano de control si se diseña correctamente.  
Riesgos: complejidad de operación, quorum y recuperación; con pocos nodos, una partición puede dejar el sistema sin quorum. No debe afirmarse que evita split-brain sin pruebas de fencing y consistencia.

### D. Servicio cloud administrado
No elegido: introduce dependencia externa y puede imponer límites, condiciones o costes incompatibles con el objetivo permanente de 0 USD.

## Propuesta para el MVP

Adoptar provisionalmente **PostgreSQL local en la Master como almacén autoritativo de metadatos**, con un único controlador activo y sin failover automático durante el MVP. La elección final queda condicionada a la prueba de concepto y a revisar el esfuerzo de operación.

Reglas:
1. Las reservas y cambios de propietario se escriben en transacciones; imponer restricciones únicas para impedir dos asignaciones vigentes de la misma instancia.
2. Cada cambio de asignación incrementa un epoch monotónico almacenado de forma durable.
3. La API de control valida claves de idempotencia y registra auditoría.
4. Los agentes conservan estado local mínimo y reportan estado observado; no pueden crear una nueva asignación por iniciativa propia.
5. Si la Master o la base no están disponibles, los nodos mantienen las instancias ya ejecutándose cuando sea seguro, pero suspenden nuevas asignaciones y acciones administrativas que necesiten autoridad central.
6. La reconexión desencadena reconciliación; los estados dudosos se mantienen como unknown hasta resolverlos.
7. No se reasigna una instancia solo porque expire un lease: se requiere fencing verificable del propietario anterior.
8. Hacer backups consistentes, probar restauración y definir RPO/RTO observados; no prometerlos antes de medir.
9. El acceso a PostgreSQL se limita a la red local/controlador, con credenciales separadas, firewall y copias de seguridad protegidas.
10. No se usa una base SQLite sobre NFS ni se comparte directamente el archivo de base de datos entre nodos.

## Qué significa para la disponibilidad

Este diseño **no es alta disponibilidad**. Si la Master falla, la gestión central y el scheduling quedan pausados hasta recuperar el controlador/base. La meta del MVP es preservar de forma segura las instancias que siguen ejecutándose y evitar asignaciones duplicadas. La recuperación manual es aceptable solo si está documentada y probada.

Una fase futura podrá evaluar controlador redundante y consenso/quorum, pero únicamente si la topología disponible y las pruebas justifican su complejidad. No se activará failover automático sin fencing, quorum y pruebas de partición de red.

## Condiciones para confirmar o rechazar la propuesta

- La licencia de PostgreSQL y dependencias es compatible con el uso previsto.
- Se puede instalar/actualizar sin pago obligatorio ni cuenta externa.
- Una transacción concurrente no permite dos propietarios de una misma instancia.
- Reiniciar controlador/base conserva epochs y asignaciones.
- Al perder la Master, los agentes no aceptan asignaciones contradictorias.
- Al recuperar la Master, reconciliación distingue running/stopped/unknown y no duplica cargas.
- Backup y restauración pasan pruebas con integridad verificada.
- Los procedimientos de operación y recuperación caben en el manual del módulo.

Si alguna condición no se cumple, revisar el diseño antes de implementar la coordinación distribuida.

## Consecuencias

- El MVP será más simple y seguro que introducir consenso distribuido prematuramente.
- La Master seguirá siendo dependencia para nuevas asignaciones; se declara explícitamente.
- No se afirmará alta disponibilidad, failover automático ni recuperación transparente.
- La capa de persistencia debe quedar detrás de interfaces para facilitar migración futura.
- Las pruebas de clúster deben validar el comportamiento de seguridad bajo caída de la Master.

**Estado real:** ADR propuesto; todavía no se ha implementado PostgreSQL ni ejecutado la prueba de concepto.
