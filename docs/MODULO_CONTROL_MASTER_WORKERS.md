# Módulo de control central PC-MASTER / Workers

**Estado:** diseño y prototipo visual inicial; no conectado a agentes ni a GitHub en tiempo real.  
**Issue:** [#69 — Control central](https://github.com/D3ckardCain/Geelark-IA/issues/69)  
**Coste obligatorio:** 0 USD.  
**Modo actual:** solo lectura, datos ficticios y sin acciones remotas.

## 1. Propósito

La PC-MASTER alojará el plano de control de GeeLark-IA. Desde una sola interfaz se debe poder observar el estado de los nodos Worker, sus agentes y módulos, las alertas, y la evidencia de pruebas y auditorías del software. La finalidad es reducir el tiempo invertido en reconstruir el estado del proyecto a partir de múltiples PR, issues y ejecuciones de CI.

## 2. Separación de responsabilidades

- **Interfaz de control:** presentación, búsqueda, filtros, alertas y enlaces a evidencia. No es autoridad de seguridad.
- **Servicio de control en PC-MASTER:** valida identidad y permisos, conserva el estado autoritativo, aplica reglas de dominio y registra auditoría.
- **Agente Worker:** informa heartbeat, versión y capacidades no sensibles; recibe solo operaciones tipadas y autorizadas cuando esa fase esté aprobada.
- **GitHub:** registro de cambios, issues, PR, commits y CI. La lectura de GitHub requiere conectividad; no debe bloquear la observación local de los últimos datos guardados.
- **Persistencia local:** caché/snapshot con marca temporal y origen, para que la interfaz pueda mostrar la última información disponible durante una desconexión.

## 3. Vistas iniciales

1. **Resumen:** cantidad de nodos, alertas, antigüedad de datos y puertas de validación.
2. **Nodos Worker:** autorización, salud, último heartbeat, versión de agente y capacidades reportadas.
3. **Módulos:** módulo, nodo, estado, versión, última comprobación y origen de la evidencia.
4. **Auditoría y CI:** resultado por workflow/commit, pruebas pendientes, PR/issues relacionadas, última revisión manual y estado de validación física.
5. **Detalle de nodo (fase posterior):** historial de heartbeat, capacidades, errores redactados y cambios auditados.

## 4. Modelo de estado recomendado

### Autorización del nodo
- `pending`: incorporado pero no aprobado para tareas.
- `active`: aprobado, sujeto a permisos y controles por operación.
- `revoked`: credenciales o autorización revocadas.

### Salud del nodo
- `reported_health_state`: declaración recibida del Worker (`healthy`, `degraded`, `unhealthy`, `unknown` o ausente); es evidencia no autoritativa.
- `health_state`: estado derivado por el Master a partir del reporte, la frescura calculada por el Master y comprobaciones independientes. Nunca copiar el reporte del Worker directamente a este campo.
- `healthy`: datos recientes y comprobaciones requeridas correctas.
- `degraded`: datos recientes, pero una o más comprobaciones fallan.
- `offline`: se superó el umbral de frescura o no se puede contactar.
- `unknown`: evidencia insuficiente o contradictoria.

### Estado del módulo
- `operational`, `degraded`, `not-installed`, `unknown`.
- Debe incluir versión, timestamp de observación, versión de contrato, fuente y motivo de error seguro.
- Nunca asumir que un módulo funciona solo porque aparece en el inventario.
- Nunca tratar datos antiguos como salud actual; el contrato v1 rechaza `healthy` cuando la frescura es `stale`, `missing` o `unknown`.

### Puertas de validación independientes
- CI automatizada.
- Revisión manual de seguridad.
- Validación en hardware.
- Aprobación de despliegue.

Una puerta no implica la aprobación de otra.

La implementación actual de heartbeat en la rama de transporte persiste el estado enviado por el Worker; esa discrepancia está registrada en [issue #71](https://github.com/D3ckardCain/Geelark-IA/issues/71) y debe resolverse antes de exponer snapshots reales.

## 5. Seguridad no negociable

- El nodo `pending` solo puede enviar heartbeat, publicar capacidades no sensibles y consultar su propio estado; no acepta ni ejecuta tareas.
- `unknown` no se reintenta, reasigna ni convierte automáticamente en éxito/fallo.
- La interfaz no puede eludir la autorización del servidor.
- Sin shell arbitrario, ADB remoto ni comandos libres.
- No abrir listeners entrantes en Worker por defecto ni exponer APIs a Internet.
- No guardar secretos, tokens ni datos privados de aplicaciones en logs, snapshots o GitHub.
- Las acciones administrativas futuras requieren autenticación, autorización por operación, confirmación explícita y evento de auditoría.
- No desplegar ni modificar PCs físicas sin autorización explícita.

## 6. Coste, operación offline y portabilidad

El prototipo actual es un HTML autocontenido que funciona localmente sin bibliotecas, CDN ni API. Sus datos son de demostración. En la futura aplicación:
- la vista podrá mostrar el último snapshot local durante pérdida de Internet;
- los datos en tiempo real de Workers requieren conectividad con PC-MASTER/LAN;
- la actualización de PR, issues y CI requiere conexión a GitHub;
- cualquier caché debe indicar cuándo se actualizó y no presentar información obsoleta como actual;
- usar interfaces de repositorio/servicio desacopladas para migrar la persistencia sin reescribir la UI;
- no asumir que GitHub Actions, Cloudflare o Supabase son requisitos de ejecución del control local.

## 7. Prototipo existente

Ruta: `prototypes/master-control/index.html`.

Incluye:
- navegación Resumen / Nodos / Módulos / Auditoría;
- filtros y búsqueda;
- estados visuales diferenciados;
- generación de un resumen de auditoría de muestra;
- aviso persistente de datos ficticios;
- cero llamadas de red y cero acciones de control de equipos.

La información de CI que aparece en la maqueta es una muestra documentada para validar la presentación, no una consulta en vivo.

## 8. Fases siguientes

1. Validar la utilidad y comprensión de las vistas con el usuario.
2. Añadir pruebas automáticas básicas del HTML/JS y revisión de accesibilidad.
3. Definir contrato versionado de salud de módulos y freshness.
4. Diseñar un adaptador de lectura para el servicio local del Master, sin mutaciones.
5. Diseñar un adaptador de lectura de GitHub para PR/issues/CI con límites y errores explícitos.
6. Añadir persistencia de snapshots y política de retención.
7. Integrar telemetría real solo después de revisar el stack HTTPS, la autenticación y los permisos.
8. Mantener acciones remotas deshabilitadas hasta aprobación específica y pruebas de seguridad.

## 9. Criterios de aceptación del primer prototipo

- Abre localmente sin Internet ni dependencias externas.
- La pantalla indica inequívocamente que usa datos ficticios.
- Búsqueda y filtros no realizan solicitudes de red.
- Ningún botón ejecuta tareas ni modifica nodos.
- Se diferencian CI, revisión de seguridad y validación física.
- El diseño es utilizable en móvil y escritorio.
- El manual describe los límites reales y no afirma integración todavía.


## 10. Contrato versionado de estado

El esquema propuesto para snapshots de solo lectura está en [`docs/contracts/master-worker-status-v1.schema.json`](contracts/master-worker-status-v1.schema.json), con un ejemplo ficticio y un contrato explicativo. Distingue autorización Master, salud derivada y frescura calculada en el Master. No incluye tareas, comandos, credenciales ni logs arbitrarios. Sigue sin estar conectado a la API operativa.


## 11. Comparación funcional con GeeLark (referencia oficial consultada el 10-oct-2026)

Fuentes de referencia: [GeeLark Cloud Phone](https://www.geelark.com/product/cloud-phone/) y [GeeLark API](https://www.geelark.com/features/api/). Esta comparación es funcional y de alcance; no afirma que GeeLark-IA tenga paridad de producto.

| Área | GeeLark según su documentación pública | GeeLark-IA en esta rama | Brecha / decisión |
|---|---|---|---|
| Panel e inventario central | Gestiona múltiples cloud phones desde un dashboard, con grupos y acceso remoto. | Maqueta local con 3 Workers ficticios; aún no consulta nodos reales. | Conectar inventario real de PC-MASTER solo después de cerrar autenticación y contrato de lectura. |
| Salud y estado | La documentación del producto menciona estado/health checks para configuraciones por dispositivo, además de consultas de estado por API. | Contrato v1 separa autorización, salud de nodo, estado de módulos y frescura. | Acordar el mapeo de estados con evidencia real; no equiparar estado del módulo con autorización del nodo. |
| Colaboración y auditoría | GeeLark describe roles/permisos de equipo y registros de actividad. | La vista Auditoría/CI es una muestra; no existe todavía un registro operativo conectado. | Diseñar RBAC y auditoría persistente antes de habilitar operaciones administrativas. |
| Automatización y API | GeeLark publica APIs para gestionar cloud phones y tareas; su documentación también describe operaciones Android/ADB. | No hay ejecución de tareas, shell ni ADB remoto habilitados. | Mantener la restricción actual; cualquier operación futura debe ser tipada, allowlisted, autorizada y auditada, nunca shell arbitrario. |
| Entorno Android | GeeLark ofrece entornos Android alojados en la nube. | Este proyecto coordina PCs físicas locales como Workers; no crea cloud phones. | Diferencia arquitectónica explícita: no prometer equivalencia con cloud Android. |
| Coste y conectividad | La referencia pública describe un producto cloud; sus condiciones comerciales y cuotas son independientes de este proyecto. | Requisito propio: coste operativo obligatorio de 0 USD y operación local/offline cuando sea viable. | No depender de GeeLark ni de APIs cloud de pago; documentar qué capacidades locales son posibles y qué funciones requieren LAN/Internet. |

### Criterio de paridad

El panel actual solo cubre el primer esqueleto visual de observabilidad. Antes de declarar una capacidad equivalente, registrar en GitHub la función de GeeLark observada, evidencia/referencia, implementación de GeeLark-IA, pruebas y brecha restante. No implementar funciones por imitación si violan el coste $0, la operación local o las reglas de seguridad del proyecto.


## 12. Decisión de integración de solo lectura

La arquitectura propuesta y sus puertas de seguridad están documentadas en [ADR-005](decisiones/ADR-005-LECTURA-ESTADO-CLUSTER.md). Este ADR no autoriza conectar datos reales ni añadir listeners; la interfaz sigue usando datos ficticios hasta confirmar la fuente de verdad y la identidad del operador.
