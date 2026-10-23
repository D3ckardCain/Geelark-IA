# ADR-001: Stack principal y sistema operativo de referencia

- **Estado:** decisión de alcance actualizada; la integración y aceptación se verifican por PR y pruebas.
- **Actualizado:** 2026-10-22.
- **Coste obligatorio objetivo:** 0 USD.

## Contexto

GeeLark-IA administra instancias Android locales desde PC-MASTER Windows y PC-WORKERS físicos. La solución debe ser local-first, operar con conectividad limitada cuando sea posible y no depender de servicios cloud pagados.

## Decisiones vigentes

1. **PC-MASTER:** el producto de administración es el panel web central en Windows. El lanzador/configurador de escritorio es un componente separado y no debe confundirse con el panel.
2. **Workers:** Debian 13 es el sistema base previsto para PC-WORKERS físicos.
3. **Motor Android:** redroid es el único motor en preparación. Su despliegue físico sigue bloqueado por la issue #27 hasta demostrar una mitigación de seguridad verificable para la imagen exacta.
4. **Backend/API:** Python, FastAPI y Pydantic se mantienen como stack del servicio local sujeto a pruebas de integración y seguridad.
5. **Persistencia:** usar el diseño transaccional de persistencia del clúster y reconciliar migraciones/decisiones con las PR actuales antes de integrar. No tratar una propuesta histórica de base de datos como decisión de producción sin validar el diseño distribuido.
6. **Comunicación:** transporte HTTPS privado, CA local, credenciales individuales revocables, autorización por operación, límites, idempotencia y protección contra repetición.
7. **Agente Worker:** identidad del nodo, heartbeat, inventario de capacidades, recepción de órdenes tipadas, ejecución limitada y reporte de resultados.
8. **Operación segura:** nodo pendiente solo informa telemetría/consulta limitada; no recibe ni ejecuta tareas hasta ser autorizado. No exponer ADB ni el socket Docker al panel.
9. **Automatización:** flujos tipados con timeout, límites, cancelación, recuperación y auditoría; no ejecutar shell arbitrario desde la API de producto.
10. **Coste/licencias:** cada dependencia, imagen y componente debe tener versión, procedencia, licencia y coste documentados. No asumir que una imagen gratuita autoriza su redistribución.

## Puerta de seguridad redroid

La incidencia upstream redroid-doc #932 (https://github.com/remote-android/redroid-doc/issues/932) describe una escritura de /proc/sys/kernel/modprobe que puede afectar al host desde un contenedor privilegiado. El cierre upstream no demuestra que la imagen elegida esté corregida. No ejecutar redroid en WORKER físico hasta que la issue interna #27 (https://github.com/D3ckardCain/Geelark-IA/issues/27) tenga evidencia reproducible de mitigación, privilegios mínimos, ADB restringido y recuperación.

## Estado de implementación

- La preparación de redroid y el diagnóstico de solo lectura están en la PR #108 (https://github.com/D3ckardCain/Geelark-IA/pull/108).
- La limpieza de alcance/documentación está en la PR #109 (https://github.com/D3ckardCain/Geelark-IA/pull/109).
- Las PR abiertas no equivalen a integración ni aceptación. Revisar CI del SHA actual y criterios manuales antes de cerrar módulos.
- No se declara instalación, prueba física ni densidad de instancias completada.

## Registro de cambios

- 2026-10-22: se alinea el stack con PC-MASTER Windows, workers Debian 13 y redroid como único motor en preparación; se elimina la vigencia de propuestas tecnológicas históricas no adoptadas.