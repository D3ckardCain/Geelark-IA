# Auditoría de continuidad GitHub — 2026-10-22

**Estado:** actualización documental; no implica fusión ni aceptación de implementación.  
**Coste:** no se lanzaron workflows manuales durante esta actualización.  
**Alcance vigente:** PC-MASTER Windows + redroid en PC-WORKERS Debian 13 + componentes de control distribuido.

## Decisiones vigentes

- PC-MASTER es el panel web central; el lanzador/configurador es un componente separado.
- redroid es el único motor Android en preparación.
- La prueba física permanece bloqueada por la issue #27, que exige evidencia verificable de mitigación del riesgo /proc/sys/kernel/modprobe.
- El agente, enrolamiento, autenticación/autorización, transporte HTTPS, persistencia, despacho durable, reconciliación y automatización son agregados necesarios.
- Una PR abierta o CI verde no sustituye aceptación manual del panel ni prueba en el hardware real.
- No se han instalado paquetes ni modificado discos de los WORKERS en esta fase documental.

## Estado de cambios documentales

- PR #108: fusionada; preparación de WORKER-01 y diagnóstico de solo lectura integrados.
- PR #109: fusionada; README, ADRs, arquitectura, plan de trabajo y documentos de alcance actualizados.
- Issue #8: cerrada como decisión de alcance completada.
- Issue #27: abierta y bloqueante.
- PR #86: cerrada anteriormente; su historial se conserva y no se considera una fuente operativa vigente.

## Continuidad y CI

- Revisar cada PR sobre su SHA actual; no reutilizar resultados de un commit anterior si la rama cambió.
- Verificar dependencias entre PRs antes de fusionar.
- Evitar workflows manuales redundantes para conservar el objetivo de coste 0 USD.
- Mantener pruebas locales reproducibles, manuales en español y registro de fallos/soluciones.
- No borrar ramas divergentes ni eliminar historial para ocultar decisiones anteriores.

## Siguiente secuencia

1. Revisar enlaces y referencias internas de la rama de limpieza.
2. Confirmar que la limpieza no borra contratos ni tareas necesarias para el plano de control.
3. Revisar CI y dependencias de las PR relevantes.
4. Mantener bloqueada la prueba física de redroid hasta cerrar la issue #27 con evidencia reproducible.
5. Después de aprobar seguridad, ejecutar diagnóstico de solo lectura y validar primero una instancia y luego dos.

No se declara ningún worker configurado, redroid instalado, seguridad aprobada ni densidad de instancias validada.