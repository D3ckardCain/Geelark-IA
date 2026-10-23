# Estado del proyecto GeeLark-IA

**Actualizado:** 2026-10-23  
**Alcance vigente:** PC-MASTER Windows + PC-WORKERS Debian 13 previsto + adaptador Android agnóstico + agregados del plano de control.  
**Estado:** preparación y auditoría; redroid bloqueado para despliegue físico por la issue #27. No declarar producción ni capacidad validada.

## Objetivo

Construir una plataforma local que administre instancias Android ejecutadas en PCs WORKER físicos desde el panel web PC-MASTER Windows. GeeLark es la referencia funcional pública; la implementación será independiente. iOS queda fuera del alcance. El objetivo obligatorio de coste de software/servicios es 0 USD.

## Decisiones vigentes

1. PC-MASTER significa el panel web central, no su lanzador/configurador de escritorio.
2. El contrato del motor Android es agnóstico; redroid es el primer candidato a evaluar, todavía bloqueado por seguridad #27 y no aprobado para ejecución física.
3. Debian 13 es el sistema base previsto para los workers; no se ha instalado ni aprobado aún mediante este registro.
4. La ruta manual QEMU + Android-x86 + VNC en WSL2 está retirada. redroid es la prioridad de evaluación, pero no se ejecuta en Workers físicos hasta resolver #27. Android Emulator queda como referencia de compatibilidad y Cuttlefish como contingencia.
5. Se conservan agente, enrolamiento, autenticación/autorización, HTTPS privado, heartbeat, capacidades, estado, persistencia, despacho durable, auditoría, reconciliación, captura/entrada y automatización.
6. Los nodos pendientes pueden enviar telemetría y consultar estado limitado; no reciben ni ejecutan tareas hasta ser autorizados.
7. No arrancar ningún motor Android en hardware físico hasta aprobar la selección, licencias, seguridad y plan de pruebas; #27 sigue bloqueando específicamente redroid.
8. No estimar densidad de instancias sin pruebas medidas en el hardware real.
9. Coste obligatorio objetivo: 0 USD; mantener alternativas locales y evitar servicios críticos de pago.

## Estado comprobable

- El plan de aprovisionamiento Debian 13 está en [PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md](PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md). La preparación base del worker y el diagnóstico de solo lectura son independientes del motor; las guías específicas de redroid no autorizan instalarlo.
- La limpieza de alcance/documentación se integró mediante la PR #109.
- El bloqueo de seguridad sigue abierto: [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27).
- No se ha instalado redroid en los workers físicos ni se han modificado sus discos durante esta preparación.
- Las PR abiertas no equivalen a cambios integrados; revisar dependencia, CI del HEAD actual y aceptación manual antes de cerrar módulos.

## Recuento de auditoría GitHub — 2026-10-23

La consulta final registra **38 Issues abiertas, 10 cerradas y 21 PR abiertas**, todas las PR abiertas en draft. Son conteos dinámicos, no un criterio de aceptación. La auditoría documental más reciente está en [AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md](AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md). No se han fusionado las PR de la cadena del agente/panel; no confundir CI de ramas con integración o aceptación en hardware.

## Próximas etapas

1. Completar la limpieza de referencias y enlaces obsoletos en GitHub.
2. Evaluar redroid primero: seguridad de la imagen/digest, requisitos kernel/Binder, licencia, compatibilidad de APK, operación multiinstancia y recursos. Cuttlefish solo si redroid se descarta.
3. Mantener #27 abierta mientras redroid no tenga mitigación verificable para la imagen exacta.
4. Aprobar el procedimiento de aprovisionamiento Debian 13 para WORKER-01.
5. Ejecutar diagnóstico de solo lectura cuando el worker esté preparado.
6. Probar una instancia y después dos, solo tras aprobar el motor elegido.
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