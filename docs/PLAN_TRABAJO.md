# Plan de trabajo — GeeLark-IA

**Actualizado:** 2026-10-22  
**Alcance:** PC-MASTER Windows + redroid en PC-WORKERS Debian 13 + agregados necesarios.  
**Coste obligatorio objetivo:** 0 USD.

## Estado vigente

- PC-MASTER es el panel web central; el lanzador/configurador de escritorio es separado.
- redroid es el único motor Android en preparación.
- Las rutas técnicas retiradas no forman parte del alcance vigente.
- El despliegue físico de redroid está bloqueado por la issue #27 hasta demostrar una mitigación efectiva para el riesgo de `/proc/sys/kernel/modprobe`.
- Los componentes de agente, enrolamiento, autenticación/autorización, HTTPS privado, heartbeat, persistencia, despacho, reconciliación, observabilidad y automatización siguen dentro del alcance.
- Una PR abierta no significa que el código esté integrado ni aceptado.

## Fases y puertas

### Fase 1 — Alcance, auditoría y documentación
- [x] Definir PC-MASTER Windows y redroid como alcance vigente en la rama de limpieza.
- [x] Retirar de la documentación operativa la selección de motores alternativos.
- [ ] Revisar enlaces internos, documentación duplicada y referencias obsoletas en Issues/PR.
- [ ] Actualizar el registro de decisiones, problemas, soluciones y evidencias.

### Fase 2 — Puerta de seguridad redroid
- [ ] Fijar etiqueta, digest y procedencia de imagen.
- [ ] Inspeccionar init y parches de la versión exacta.
- [ ] Identificar y probar una mitigación efectiva del riesgo `kernel.modprobe`.
- [ ] Definir capacidades, dispositivos, montajes y privilegios mínimos.
- [ ] Verificar que ADB no quede expuesto y que el panel no tenga acceso al socket Docker.
- [ ] Registrar evidencia en [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27).
- **Regla:** no arrancar redroid en WORKER físico mientras esta puerta siga abierta.

### Fase 3 — Preparación del primer worker
- [ ] Aprobar el procedimiento de instalación automatizable de Debian 13.
- [ ] Preparar WORKER-01; no modificar discos ni particiones antes de aprobar el procedimiento.
- [ ] Ejecutar el diagnóstico de solo lectura: CPU, RAM, disco, kernel, Binder/BinderFS, red y puertos.
- [ ] Fijar versiones, hashes, licencias y registro de instalación.

El plan de aprovisionamiento Debian 13 está en PLAN_APROVISIONAMIENTO_WORKER_DEBIAN13.md; la guía de redroid y el diagnóstico de solo lectura están en PREPARACION_WORKER_REDROID.md y GUIA_DIAGNOSTICO_PREVIO_REDROID.md. No se han ejecutado en el hardware físico.

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
