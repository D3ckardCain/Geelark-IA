# Arquitectura tecnológica objetivo — Geelark-IA

**Fecha:** 2026-10-09  
**Estado:** propuesta de arquitectura; no implica que el software esté implementado.  
**Objetivo:** maximizar funcionalidad local y extensible inspirada en las capacidades públicas de GeeLark, con coste obligatorio de operación de 0 USD, sin cloud phones ni APIs pagadas.

## 1. Decisión ejecutiva

Diseñar primero una aplicación **desktop-first, local-first y modular**, con una interfaz reutilizable, un servicio backend propio y adaptadores desacoplados para motores Android. No construir una plataforma SaaS dependiente de un proveedor.

### Combinación base recomendada

| Capa | Tecnología preferida | Motivo | Condición/alternativa |
|---|---|---|---|
| UI escritorio | Tauri 2 + React + TypeScript + Vite | Aplicación multiplataforma, UI moderna y puente al sistema | Revisar plugins/permisos; UI web local separada posible |
| Diseño UI | Tailwind CSS + componentes accesibles propios o Radix UI | Consistencia, velocidad y accesibilidad | Fijar versiones y revisar licencias |
| API y dominio | Python 3 + FastAPI + Pydantic | Ecosistema maduro para automatización, procesos y tooling Android | Mantener el dominio desacoplado del framework |
| Persistencia local inicial | SQLite + migraciones versionadas | Cero coste, local y transaccional | Evaluar PostgreSQL local si la concurrencia multiusuario lo exige |
| Estado de tareas | Cola persistente en SQLite, IDs idempotentes y recuperación | Evita añadir infraestructura prematura | Valorar PostgreSQL o Valkey solo si pruebas lo justifican |
| Contrato API | OpenAPI generado desde FastAPI | Contratos verificables y cliente UI desacoplado | Versionar API y errores |
| Motor Android baseline | Android Emulator oficial | Referencia de compatibilidad y pruebas Android | No necesariamente el motor final |
| Motor de densidad candidato | redroid en Linux | Android en contenedores, potencialmente eficiente | Riesgos de privilegios/ADB; no aprobar sin endurecimiento |
| Motor Linux alternativo | Waydroid | Android containerizado en Linux | No asumir equivalencia con un gestor multiinstancia |
| Control de dispositivos | ADB oficial/platform-tools detrás de adaptador interno | Estándar para dispositivos autorizados | Nunca exponer ADB públicamente |
| RPA | Motor propio de máquina de estados + adaptadores ADB/UIAutomator2 | Control, límites, recuperación y trazabilidad | Appium como apoyo de pruebas, no dependencia ciega |
| Pruebas UI web | Playwright | Pruebas E2E reproducibles | No usar como motor RPA Android de producción |
| Pruebas Android | ADB + UIAutomator2/Appium según caso | Acciones y verificaciones | Fijar versiones compatibles |
| Entorno | uv/venv para Python; pnpm y lockfile para UI | Reproducibilidad | Docker solo opcional, no requisito del producto |
| Calidad | Ruff, mypy/pyright, pytest, ESLint, TypeScript strict, Vitest, Playwright | Detectar errores temprano | La ejecución local de pruebas no depende de CI pago |
| Registro | Logs estructurados locales con redacción y rotación | Diagnóstico sin filtrar secretos | Sin telemetría obligatoria |
| Distribución | Instaladores por SO y compilación reproducible | Descarga sencilla | Debe ser posible compilar localmente |

## 2. Decisión sobre Android virtualizado

No hay un motor ganador hasta probarlo. Se recomienda una estrategia de dos candidatos:

1. **Baseline:** Android Emulator oficial para validar instalación de apps, ADB, capturas, entradas, persistencia, versiones Android y automatización.
2. **Experimento de densidad:** redroid en Linux para medir recursos, arranque, persistencia y aislamiento.

La selección final comparará compatibilidad con apps/ABI, versiones Android, persistencia, proxy por instancia, configuración admitida, aislamiento, ADB/captura, sensores/cámara, privilegios, licencias y seguridad.

No se promete reproducción exacta de identidad física ni compatibilidad universal de aplicaciones. No se implementarán técnicas para falsificar claves de hardware, attestation o evadir controles de seguridad.

## 3. Arquitectura de procesos

En el MVP pueden compartir un backend modular; separar procesos solo cuando una frontera de seguridad o pruebas lo justifiquen.

- **desktop-ui:** interfaz Tauri; no ejecuta shell arbitrario.
- **geelark-api:** FastAPI local con autenticación y autorización por recurso.
- **instance-manager:** adaptador de ciclo de vida para cada motor.
- **adb-manager:** lista permitida de comandos, selección explícita, timeout y salida limitada.
- **rpa-runner:** cola persistente, estado por paso, timeout, límite de iteraciones, pausa/cancelación y auditoría.
- **importer:** lectura selectiva desde Android físico, sin escritura al origen.
- **artifact-manager:** archivos/APK, checksums, nombres y rutas normalizadas.
- **audit-log:** eventos estructurados redactados.

### Contratos y adaptadores

El dominio no dependerá de comandos específicos de un motor. La interfaz de cada adaptador debe contemplar: listar imágenes, crear/iniciar/detener/reiniciar/eliminar instancias, consultar estado, capturar pantalla, instalar aplicación, ejecutar acciones permitidas y respaldar/restaurar datos.

Cada adaptador declara capacidades soportadas, no soportadas y no probadas. Operaciones peligrosas requieren confirmación explícita.

## 4. Modelo de datos inicial

- Perfiles con UUID, nombre, grupo, estado y versión de esquema.
- Configuración versionada separando identidad sintética de campos de hardware protegidos.
- Instancias de motor, versión, ruta de datos, estado y capacidades.
- Grupos y pertenencia de perfiles.
- Proxies; credenciales separadas y protegidas.
- Aplicaciones/artefactos con origen, checksum, versión y ABI.
- Archivos multimedia y etiquetas.
- Flujos RPA, versiones, ejecuciones y pasos.
- Cola de tareas con payload validado, clave idempotente, intentos, estado y error redactado.
- Sesiones de sincronización y acciones.
- Dispositivos físicos con alias, fabricante/modelo/versión y serial enmascarado.
- Sesiones de importación, campos y resultados.
- Eventos de auditoría, respaldos y migraciones.

Los secretos no se guardan en logs ni como texto plano en tablas genéricas. Definir el mecanismo de cifrado antes de guardar credenciales reales.

## 5. API, tareas y sincronización

- API versionada y documentada por OpenAPI.
- Validación estricta de esquemas, límites de cuerpo, timeout y concurrencia.
- UUID y claves idempotentes para tareas y reintentos seguros.
- Estados de tarea: queued, running, paused, cancel_requested, succeeded, failed, cancelled.
- Resultado por instancia/paso sin almacenar secretos.
- Recuperación tras reinicio según política explícita; no repetir automáticamente acciones no idempotentes.
- Eventos por WebSocket/SSE solo en loopback, con polling como alternativa.
- Importación/sincronización con vista previa, confirmación, diferencias y registro por campo.

## 6. Offline

Debe funcionar sin Internet: abrir la UI local; gestionar perfiles/configuración; crear grupos; consultar historial/logs locales; editar RPA y tareas pendientes; importar archivos locales y exportar respaldos.

Requiere motor instalado: iniciar/detener instancias, instalar APK y automatizar apps.

Requiere conectividad: descargar imágenes/actualizaciones o APK remotos; proxies externos; integraciones remotas. No declarar sincronización entre equipos offline-first hasta implementar reconciliación de conflictos, versionado y pruebas de idempotencia.

## 7. Licencias y coste

- Preferir licencias permisivas (MIT, Apache-2.0, BSD, PostgreSQL License y dominio público) cuando la funcionalidad sea comparable.
- Revisar por separado código, dependencias, imágenes Android, aplicaciones y derechos de redistribución.
- Evitar n8n como motor RPA integrado: su Sustainable Use License restringe ofrecer su editor de flujos o automatización como parte de un producto para clientes.
- No depender de Supabase Cloud, Firebase, APIs de IA de pago, almacenamiento externo ni teléfonos en la nube. Supabase podría ser una integración futura opcional, nunca el único almacenamiento ni requisito local.
- El software local puede no tener tarifa de licencia; hardware, electricidad, conectividad y dominios opcionales pueden tener costes indirectos. La meta es no imponer pagos de software/servicios.
- Las cuotas gratuitas de GitHub Actions pueden cambiar; compilar localmente debe seguir siendo posible.

## 8. Secuencia recomendada

### Fase 0 — decisiones y contratos
- [ ] Fijar licencias y versiones principales.
- [ ] Registrar ADR de arquitectura y motor.
- [ ] Definir capacidades del adaptador y matriz de soporte.

### Fase 1 — núcleo mínimo
- [ ] Esqueleto Tauri + React + TypeScript.
- [ ] Backend FastAPI local.
- [ ] SQLite y migraciones.
- [ ] Autenticación local y permisos.
- [ ] Logs redactados y pruebas reproducibles.

### Fase 2 — primera instancia Android
- [ ] Probar Android Emulator como baseline.
- [ ] Crear, iniciar, detener, reiniciar y eliminar instancia.
- [ ] Captura, entrada básica, ADB y persistencia.
- [ ] Backup/restauración.
- [ ] Documentar diferencias respecto a GeeLark.

### Fase 3 — gestión de perfiles
- [ ] Perfiles, grupos, clonación segura y operaciones masivas.
- [ ] Proxy con credenciales protegidas.
- [ ] Instalación/actualización de APK.
- [ ] Logs e historial de tareas.

### Fase 4 — RPA/Synchronizer
- [ ] Editor visual de flujos con bloques tipados.
- [ ] Ejecutor persistente, pausa, cancelación, límites y resultados.
- [ ] Sincronización entre instancias con acciones seleccionadas explícitamente.
- [ ] Pruebas de flujos interrumpidos y recuperación.

### Fase 5 — importación física
- [ ] Detección ADB progresiva para múltiples fabricantes/versiones.
- [ ] Inventario de campos realmente legibles.
- [ ] Vista previa por campo y exclusión sensible por defecto.
- [ ] Aplicar campos compatibles a instancia virtual.
- [ ] Verificar persistencia y registrar diferencias.

### Fase 6 — motor alternativo, Library, API/CLI y distribución
- [ ] Probar redroid en Linux aislado.
- [ ] Comparar compatibilidad y recursos contra baseline.
- [ ] API/CLI local estable.
- [ ] Library de archivos/medios.
- [ ] Empaquetado reproducible para los sistemas operativos incluidos en alcance.

No comenzar la fase siguiente hasta que la fase actual tenga pruebas, manual en español, matriz actualizada y aceptación documentada.

## 9. Decisiones pendientes de evidencia

1. Motor Android final y versiones soportadas.
2. Aislamiento para múltiples instancias.
3. Estrategia de secretos/cifrado.
4. Campos de configuración aplicables por motor.
5. Permisos de shell/ADB.
6. Alcance de distribución: escritorio o UI web local adicional.
7. Redistribución de imágenes y APK.

## 10. Criterio de aprobación

La arquitectura se acepta cuando las licencias son compatibles; no hay pago ni servicio cloud obligatorio; se prueba el flujo crear/iniciar/detener/persistir/respaldar; ADB/API no quedan expuestos por defecto; existen pruebas automatizadas; y las diferencias frente a GeeLark y el manual del módulo inicial están documentados.


## 11. Requisito transversal: clúster heterogéneo de varios PC

**Esta arquitectura queda corregida para contemplar varios equipos desde el inicio.** La UI Tauri/React y la API FastAPI pueden seguir siendo el plano de administración, pero no se presupone que el backend y todas las instancias Android residan en un único anfitrión.

Documentos que definen esta parte:
- [Arquitectura de clúster heterogéneo](ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- [ADR-003 — Arquitectura distribuida](decisiones/ADR-003-ARQUITECTURA-DISTRIBUIDA-CLUSTER.md).
- [Contrato del agente de nodo y planificador](CONTRATO_AGENTE_NODO_PLANIFICADOR.md).
- [Arquitectura de clúster físico heterogéneo](ARQUITECTURA_CLUSTER_HETEROGENEO.md).
- [Issue #14 — Integrar clúster y planificador](https://github.com/D3ckardCain/Geelark-IA/issues/14).

El diseño se separa en plano de administración, plano de control, agentes por nodo, planificador de recursos y adaptadores de motor Android. Cada nodo anuncia capacidades observadas y probadas; el planificador filtra por compatibilidad, RAM, disco, CPU y capacidades de motor. No se supone migración en vivo entre nodos heterogéneos.

La decisión operativa es mantener PC-MASTER como aplicación Windows y utilizar Debian 13 directamente en los PC WORKER físicos. La administración central, el descubrimiento, la adopción, el despliegue del agente y la preparación de Android serán responsabilidad de GeeLark-IA. El aprovisionamiento desde equipos sin sistema operativo se implementará mediante arranque por red cuando el hardware y la LAN sean compatibles, y se validará con pruebas reproducibles.

No se aprobará la infraestructura hasta probar dos nodos heterogéneos, registrar métricas, comprobar recuperación y revisar licencias/versiones. El objetivo de 0 USD para software/servicios obligatorios se mantiene.
