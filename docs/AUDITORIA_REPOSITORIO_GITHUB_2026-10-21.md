# Auditoría de higiene del repositorio GitHub — actualización 2026-10-22

## Objetivo

Mantener el repositorio GeeLark-IA alineado con el alcance vigente: panel web PC-MASTER Windows, redroid en PC-WORKERS Debian 13 y agregados necesarios para administrar los nodos. El objetivo operativo obligatorio es 0 USD.

## Estado y reglas

- No confundir una PR abierta con código integrado o aceptado.
- No cerrar un bloqueo de seguridad por tener documentación escrita; exigir evidencia reproducible.
- No borrar ramas o historial de commits para ocultar decisiones anteriores. La documentación operativa sí debe reflejar el alcance actual.
- Las tareas de autenticación, enrolamiento, transporte, persistencia, despacho, reconciliación, observabilidad y automatización permanecen porque son componentes necesarios del plano de control.
- La selección de motores Android queda cerrada como línea documental: redroid es el único motor en preparación; la issue #27 bloquea la prueba física.
- No se han instalado paquetes ni modificado discos de los WORKERS durante esta limpieza documental.

## Cambios realizados en la rama de limpieza

- README actualizado con el alcance y los enlaces vigentes.
- ADR-001 y ADR-002 alineados con PC-MASTER Windows, Debian 13 y redroid.
- Arquitectura tecnológica y de clúster actualizadas.
- Plan de trabajo actualizado con fases y puertas de aceptación.
- Evaluación de redroid centrada en seguridad, digest, kernel, Binder/BinderFS, ADB, aislamiento y pruebas.
- Catálogo funcional y matriz de paridad conservados como documentación de funciones públicas de GeeLark, no como selección de motores.
- Issue #8 cerrada como decisión de alcance completada; la issue #27 permanece abierta.
- PR #108 conserva la preparación del worker y el diagnóstico de solo lectura; PR #109 contiene la limpieza de alcance.

## Criterios antes de integrar

1. Revisar que todos los enlaces internos resuelvan en el árbol final de main.
2. Revisar diff completo para asegurar que no se han eliminado contratos, tareas o documentación necesaria del plano de control.
3. Ejecutar comprobaciones de formato/enlaces localmente cuando el árbol esté disponible; no lanzar workflows solo para reconstruir resultados ya registrados.
4. Revisar CI del HEAD exacto y dependencias de PR apiladas.
5. Mantener la issue #27 abierta hasta que exista evidencia de mitigación sobre la imagen redroid exacta.
6. No declarar redroid instalado, seguro, probado en hardware físico ni escalable hasta que esas pruebas se ejecuten y documenten.

## Registro

Esta actualización reemplaza recuentos históricos de Issues/PR que podrían haber cambiado. El historial de GitHub conserva las decisiones anteriores; los documentos operativos actuales deben seguir esta actualización.