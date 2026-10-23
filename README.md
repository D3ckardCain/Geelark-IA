# GeeLark-IA

Plataforma local para administrar instancias Android en equipos WORKER físicos desde el **panel web PC-MASTER Windows**. GeeLark se usa como referencia funcional pública; la implementación será independiente.

> **Alcance vigente:** PC-MASTER Windows + PC-WORKERS físicos con Debian 13 previsto + adaptador Android agnóstico + componentes de control distribuido. redroid es el primer candidato a evaluar, pero permanece bloqueado para ejecución física por la issue [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27) hasta demostrar mitigación en la imagen/digest exactos. Cuttlefish queda como contingencia, no como primera opción.

## Reglas obligatorias

- Coste operativo objetivo: **0 USD**; sin dependencia crítica de servicios de pago, tarjetas, pruebas temporales ni cargos automáticos.
- PC-MASTER significa el panel web de control, no el lanzador/configurador de escritorio.
- PC-MASTER Windows coordina workers físicos. Los workers usarán Debian 13 como base prevista; redroid es la primera opción a evaluar, aún bloqueada por #27 antes de ejecución física. Cuttlefish queda como contingencia; el motor solo se aprobará tras revisar licencia, seguridad y pruebas.
- La ruta manual QEMU + Android-x86 + VNC en WSL2 está retirada. redroid es la prioridad de evaluación, no una instalación autorizada; Android Emulator sirve como referencia de compatibilidad y Cuttlefish queda como contingencia si redroid no supera la puerta de seguridad.
- Conservar agente, enrolamiento, autenticación/autorización, transporte seguro, heartbeat, estado, persistencia, despacho, reconciliación, observabilidad y automatización: son agregados del producto, no motores alternativos.
- Los nodos pendientes solo pueden enviar telemetría y consultar estado limitado; no reciben ni ejecutan tareas hasta ser autorizados.
- No exponer ADB a Internet ni abrir el socket Docker al panel. No ejecutar shell arbitrario desde la API.
- No instalar ni arrancar ningún motor Android en WORKERS físicos hasta aprobar la selección, las licencias, la seguridad y el plan de pruebas.
- No afirmar capacidad, paridad o pruebas completadas sin evidencia del hardware real.
- Mantener documentación, incidencias, pruebas y manuales en español. Registrar costes y límites para sostener el objetivo de 0 USD.

## Estado actual

- PC-MASTER Windows v0.1 y sus componentes están en distintas PR; una PR abierta no significa que esté integrada ni aceptada.
- La preparación del worker y el diagnóstico de solo lectura son independientes del motor; las guías específicas de redroid se conservan solo como evaluación del candidato bloqueado.
- La limpieza de alcance y documentación se integró mediante la [PR #109](https://github.com/D3ckardCain/Geelark-IA/pull/109).
- La [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27) es un bloqueo real, no una tarea cosmética. El reporte upstream sobre `/proc/sys/kernel/modprobe` está cerrado, pero no prueba por sí solo que una imagen concreta esté corregida.
- No se ha instalado redroid ni se han modificado discos de los WORKERS durante esta preparación.

## Documentos principales

- [Alcance vigente PC-MASTER + motor intercambiable](docs/ALCANCE_PC_MASTER_REDROID.md)
- [Estado del proyecto](docs/ESTADO_PROYECTO.md)
- [Auditoría de continuidad GitHub (2026-10-23)](docs/AUDITORIA_CONTINUIDAD_GITHUB_2026-10-23.md)
- [Auditoría de integración Fase 2 (2026-10-23)](docs/FASE2_AUDITORIA_INTEGRACION_2026-10-23.md)
- [Requisitos](docs/REQUISITOS.md)
- [Plan de trabajo](docs/PLAN_TRABAJO.md)
- [Arquitectura del clúster físico](docs/ARQUITECTURA_CLUSTER_HETEROGENEO.md)
- [Contrato del adaptador Android](docs/CONTRATO_ADAPTADOR_ANDROID.md)
- [Contrato API del clúster](docs/CONTRATO_API_CLUSTER.md)
- [Contrato de mensajes de agente](docs/CONTRATO_MENSAJES_AGENTE_CLUSTER.md)
- [Modelo de amenazas](docs/MODELO_AMENAZAS_SEGURIDAD.md)
- [Inventario de licencias y costes](docs/INVENTARIO_LICENCIAS_COSTE.md)
- [Comparativa y priorización de motores Android](docs/COMPARATIVA_MOTORES_ANDROID.md)
- [Plan de aprovisionamiento automatizado Debian 13](docs/PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md)
- [Preparación del worker redroid](docs/PREPARACION_WORKER_REDROID.md)
- [Bloqueo de seguridad redroid #27](https://github.com/D3ckardCain/Geelark-IA/issues/27)
- [Limpieza manual segura del experimento QEMU retirado](docs/RETIRADA_EXPERIMENTO_QEMU_WSL.md)

## Secuencia de validación

1. Completar la auditoría de documentación y dependencias.
2. Completar la evaluación comparativa de licencias, requisitos y seguridad; mantener #27 como bloqueo específico de redroid.
3. Aprovisionar WORKER-01 con Debian 13 solo después de que se apruebe el procedimiento.
4. Ejecutar diagnóstico de solo lectura; fijar kernel, Binder/BinderFS, red y recursos.
5. Aprobar la seguridad del motor elegido antes de iniciar cualquier runtime Android.
6. Probar una instancia y luego dos: ciclo de vida, ADB restringido, captura/entrada, APK autorizada, persistencia, aislamiento y métricas.
7. Integrar el agente autenticado con PC-MASTER; validar enrolamiento, heartbeat, despacho y reconciliación.
8. Medir capacidad real antes de planificar 4, 6 o aproximadamente 50 instancias.

La documentación y las pruebas de laboratorio no equivalen a una aprobación de producción.