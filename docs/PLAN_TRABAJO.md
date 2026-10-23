# Plan de trabajo — GeeLark-IA

**Actualizado:** 2026-10-23  
**Alcance:** PC-MASTER Windows + PC-WORKERS Debian 13 previsto + adaptador Android agnóstico + agregados necesarios.  
**Coste obligatorio objetivo:** 0 USD.

## Estado vigente

- PC-MASTER es el panel web central; el lanzador/configurador de escritorio es separado.
- redroid es el primer candidato a evaluar; la ejecución física sigue bloqueada por #27 hasta demostrar mitigación para la imagen/digest exactos. El adaptador Android debe permanecer agnóstico; Cuttlefish es alternativa de contingencia y Android Emulator referencia de compatibilidad.
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
- [ ] Evaluar redroid primero: requisitos Debian/kernel/Binder, licencia, imagen/digest, seguridad, compatibilidad y rendimiento de una instancia aislada; no instalar en Workers físicos hasta resolver #27.
- [ ] Mantener el adaptador agnóstico y documentar capacidades realmente demostradas.
- [ ] Revisar Android Emulator como referencia de compatibilidad/licencias, sin asumir que sus imágenes son redistribuibles.
- [ ] Mantener la puerta de seguridad #27 cerrada hasta documentar mitigación reproducible de redroid sobre imagen/digest exactos; si no es posible, registrar descarte y pasar a contingencia.
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

- PR #106, #108 y #109 están integradas en `main`; la auditoría más reciente es `docs/AUDITORIA_CONTINUIDAD_GITHUB_2026-10-23.md`. Las notas del 22-oct y 21-oct se conservan como historial, no como estado actual.
- PR #86 se cerró sin merge por cambio de alcance. No usar su plan antiguo para reemplazar este archivo; rescatar contenido solo si reaparece como necesidad explícita.
- Recuento observado en la revalidación del 2026-10-23: 23 PR abiertas y 38 Issues abiertas. Todas las PR abiertas están en draft. No fusionar PR apiladas fuera de orden ni cerrar una tarea solo por CI verde.
- Bloqueo activo del stack de control: #101 HEAD `043a4e23efd063949577f758eacc326d74bb7ce5` y #74 HEAD `406936ecef181eb4a7a34d6e25316079ee8b29ea` tienen CI verde y `mergeable=true`; #52 y #67 siguen `mergeable=false`. La PR auxiliar #112 para sincronizar proveedor→bandeja también es `mergeable=false` y tiene 8 archivos solapados con #52, incluido `runtime.py`; resolver la integración explícitamente, sin reemplazar archivos completos a ciegas. #113 corrigió la lease de entrega: HEAD `21a5b4915086959eaf7dece15b6095de333612ce`, transporte #482 y persistencia #609 `success` (63 tests de transporte y prueba PostgreSQL de bandeja 1 passed, `pip check` limpio). Después revalidar la cadena #101 → #74 → #52 → #57 → #67 → #85 en orden y sobre cada SHA nuevo. La CI de SHA anteriores es histórica.
- La issue #27 sigue bloqueando cualquier ejecución física de redroid. #24 cubre caché de artefactos; #92 cubre aprovisionamiento Debian 13.
- La aceptación manual de PC-MASTER en Windows (#77) y la identificación del artefacto local (#88) siguen pendientes; no declarar el panel operativo hasta resolverlas.
