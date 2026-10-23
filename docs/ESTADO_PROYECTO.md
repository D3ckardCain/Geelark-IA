# Estado del proyecto GeeLark-IA

**Actualizado:** 2026-10-23  
**Alcance vigente:** PC-MASTER Windows + redroid en PC-WORKERS Debian 13 + agregados del plano de control.  
**Estado:** preparación y auditoría; redroid bloqueado para despliegue físico por la issue #27. No declarar producción ni capacidad validada.

## Objetivo

Construir una plataforma local que administre instancias Android ejecutadas en PCs WORKER físicos desde el panel web PC-MASTER Windows. GeeLark es la referencia funcional pública; la implementación será independiente. iOS queda fuera del alcance. El objetivo obligatorio de coste de software/servicios es 0 USD.

## Decisiones vigentes

1. PC-MASTER significa el panel web central, no su lanzador/configurador de escritorio.
2. redroid es el único motor Android en preparación.
3. Debian 13 es el sistema base previsto para los workers; no se ha instalado ni aprobado aún mediante este registro.
4. Se retira la ruta la ruta experimental anterior y no se mantienen motores alternativos como opciones activas.
5. Se conservan agente, enrolamiento, autenticación/autorización, HTTPS privado, heartbeat, capacidades, estado, persistencia, despacho durable, auditoría, reconciliación, captura/entrada y automatización.
6. Los nodos pendientes pueden enviar telemetría y consultar estado limitado; no reciben ni ejecutan tareas hasta ser autorizados.
7. No arrancar redroid en hardware físico hasta que #27 documente una mitigación de seguridad verificable para la imagen exacta.
8. No estimar densidad de instancias sin pruebas medidas en el hardware real.
9. Coste obligatorio objetivo: 0 USD; mantener alternativas locales y evitar servicios críticos de pago.

## Estado comprobable

- El plan de aprovisionamiento Debian 13 está en [PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md](PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md); la preparación de redroid y el diagnóstico de solo lectura están en [PREPARACION_WORKER_REDROID.md](PREPARACION_WORKER_REDROID.md) y [GUIA_DIAGNOSTICO_PREVIO_REDROID.md](GUIA_DIAGNOSTICO_PREVIO_REDROID.md), integrados mediante la PR #108.
- La limpieza de alcance/documentación se integró mediante la PR #109.
- El bloqueo de seguridad sigue abierto: [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27).
- No se ha instalado redroid en los workers físicos ni se han modificado sus discos durante esta preparación.
- Las PR abiertas no equivalen a cambios integrados; revisar dependencia, CI del HEAD actual y aceptación manual antes de cerrar módulos.

## Próximas etapas

1. Completar la limpieza de referencias y enlaces obsoletos en GitHub.
2. Verificar etiqueta/digest, init y mitigación del riesgo de `/proc/sys/kernel/modprobe`.
3. Cerrar #27 únicamente con evidencia reproducible; si no hay mitigación efectiva, mantener el bloqueo.
4. Aprobar el procedimiento de aprovisionamiento Debian 13 para WORKER-01.
5. Ejecutar diagnóstico de solo lectura en el worker ya preparado.
6. Probar una instancia y después dos, solo tras aprobar seguridad.
7. Integrar el agente autenticado con PC-MASTER y validar enrolamiento, heartbeat, despacho y reconciliación.
8. Medir capacidad y actualizar manuales y registro de problemas/soluciones.

## Documentos principales

- [Alcance PC-MASTER + redroid](ALCANCE_PC_MASTER_REDROID.md)
- [Evaluación de redroid](COMPARATIVA_MOTORES_ANDROID.md)
- [Contrato del adaptador Android](CONTRATO_ADAPTADOR_ANDROID.md)
- [Arquitectura del clúster físico](ARQUITECTURA_CLUSTER_HETEROGENEO.md)
- [Modelo de amenazas](MODELO_AMENAZAS_SEGURIDAD.md)
- [Inventario de licencias y costes](INVENTARIO_LICENCIAS_COSTE.md)
- [Plan de trabajo](PLAN_TRABAJO.md)