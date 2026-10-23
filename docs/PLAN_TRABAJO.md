# Plan de trabajo — GeeLark-IA

**Actualizado:** 2026-10-23  
**Alcance:** PC-MASTER Windows + PC-WORKERS Debian 13 previsto + adaptador Android agnóstico + agregados necesarios.  
**Coste obligatorio objetivo:** 0 USD.

## Estado vigente

- PC-MASTER es el panel web central; el lanzador/configurador de escritorio es separado.
- AOSP Cuttlefish es el primer candidato de laboratorio, aún no aprobado. El adaptador Android debe permanecer agnóstico; Android Emulator es referencia de compatibilidad y redroid sigue bloqueado por #27.
- Las rutas técnicas retiradas no forman parte del alcance vigente.
- No desplegar ningún motor Android en WORKERS físicos hasta aprobar selección, licencias, seguridad y plan de pruebas. La issue #27 mantiene un bloqueo específico para redroid.
- Los componentes de agente, enrolamiento, autenticación/autorización, HTTPS privado, heartbeat, persistencia, despacho, reconciliación, observabilidad y automatización siguen dentro del alcance.
- Una PR abierta no significa que el código esté integrado ni aceptado.

## Fases y puertas

### Fase 1 — Alcance, auditoría y documentación
- [x] Definir PC-MASTER Windows y Debian 13 previsto para WORKERS.
- [x] Retirar la ruta manual QEMU + Android-x86 + VNC en WSL2.
- [ ] Reconciliar todos los documentos de `main` con el adaptador Android agnóstico y el estado de candidatos.
- [ ] Revisar enlaces internos, documentación duplicada y referencias obsoletas en Issues/PR.
- [ ] Actualizar el registro de decisiones, problemas, soluciones y evidencias.

### Fase 2 — Selección y seguridad del motor Android
- [ ] Evaluar Cuttlefish como primer candidato: requisitos de host, KVM, licencias, imágenes, operación multiinstancia y control visual.
- [ ] Mantener el adaptador agnóstico y documentar capacidades realmente demostradas.
- [ ] Revisar Android Emulator como referencia de compatibilidad/licencias, sin asumir que sus imágenes son redistribuibles.
- [ ] Mantener redroid bloqueado por #27 hasta revisar imagen/digest y demostrar mitigación.
- [ ] Definir privilegios mínimos, aislamiento, ADB, red y recuperación para el candidato seleccionado.
- **Regla:** no arrancar ningún runtime Android en WORKER físico hasta aprobar la puerta correspondiente.

### Fase 3 — Preparación del primer worker
- [ ] Aprobar el procedimiento de instalación automatizable de Debian 13.
- [ ] Preparar WORKER-01; no modificar discos ni particiones antes de aprobar el procedimiento.
- [ ] Ejecutar el diagnóstico de solo lectura: CPU, RAM, disco, kernel, Binder/BinderFS, red y puertos.
- [ ] Fijar versiones, hashes, licencias y registro de instalación.

El plan de aprovisionamiento Debian 13 está en PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md. El diagnóstico de solo lectura es independiente del motor. Las guías específicas de redroid no autorizan su instalación y no se han ejecutado en hardware físico.

### Fase 4 — Pruebas Android controladas
Solo tras aprobar la fase 2:
1. Una instancia: ciclo de vida, ADB restringido, APK autorizada, captura/entrada, archivos, persistencia y métricas.
2. Dos instancias simultáneas: independencia de datos, puertos, almacenamiento y control.
3. Reinicio y fallo: recuperación, reconciliación y ausencia de efectos duplicados.
4. Medición de CPU, RAM, almacenamiento, arranque, latencia y estabilidad.
5. No estimar 50 instancias ni ampliar a 4/6 hasta disponer de métricas.

### Fase 5 — Integración PC-MASTER/Worker
- [ ] Enrolamiento con credenciales individuales y revocables.
- [ ] Nodo pendiente limitado a telemetría/consulta; bloqueo de tareas hasta autorización.
- [ ] HTTPS privado, autorización por operación, límites y protección contra repetición.
- [ ] Heartbeat y capacidades con distinción entre salud reportada y salud derivada.
- [ ] Órdenes tipadas, outbox durable, idempotencia, fencing y reconciliación.
- [ ] Panel de nodos, instancias, tareas, errores y registros.

### Fase 6 — Funciones de producto
- [ ] Gestión de perfiles/instancias, persistencia y operaciones por lote.
- [ ] Instalación de APK autorizadas y gestión de archivos.
- [ ] Captura/entrada remota con canal autenticado.
- [ ] RPA tipado con límites, cancelación, recuperación y resultados por paso.
- [ ] Synchronizer, Library, API local y registros según requisitos confirmados.
- [ ] Manual de usuario y documentación técnica en español para cada módulo.

## Reglas de aceptación

- Pruebas reproducibles y asociadas al commit exacto.
- Cero secretos en logs/artefactos.
- Fallos seguros: sin duplicar operaciones ni reasignar estados inciertos.
- Licencias y coste documentados antes de adoptar dependencias.
- No cerrar Issues ni aceptar módulos sin evidencia.
- No declarar paridad con GeeLark sin comparación funcional y pruebas reales.

## Documentos de referencia

- [Alcance vigente](ALCANCE_PC_MASTER_REDROID.md)
- [Estado del proyecto](ESTADO_PROYECTO.md)
- [Evaluación de redroid](COMPARATIVA_MOTORES_ANDROID.md)
- [Arquitectura del clúster](ARQUITECTURA_CLUSTER_HETEROGENEO.md)
- [Contrato del adaptador Android](CONTRATO_ADAPTADOR_ANDROID.md)
- [Modelo de amenazas](MODELO_AMENAZAS_SEGURIDAD.md)
- [Inventario de licencias y costes](INVENTARIO_LICENCIAS_COSTE.md)


## Continuidad de auditoría — 2026-10-23

- PR #106, #108 y #109 están integradas en `main`; consultar `docs/AUDITORIA_GITHUB_CONTINUIDAD_2026-10-22.md` y `docs/AUDITORIA_REPOSITORIO_GITHUB_2026-10-21.md` para evidencia y límites.
- PR #86 se cerró sin merge por cambio de alcance. No usar su plan antiguo para reemplazar este archivo; rescatar contenido solo si reaparece como necesidad explícita.
- Recuento observado: 22 PR abiertas y 38 Issues abiertas. No fusionar PR apiladas fuera de orden ni cerrar una tarea solo por CI verde.
- La issue #27 sigue bloqueando cualquier ejecución física de redroid. #24 cubre caché de artefactos; #92 cubre aprovisionamiento Debian 13.
- La aceptación manual de PC-MASTER en Windows (#77) y la identificación del artefacto local (#88) siguen pendientes; no declarar el panel operativo hasta resolverlas.
