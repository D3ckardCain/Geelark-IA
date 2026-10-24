# ADR-001: Stack principal y sistema operativo de referencia

- **Estado:** propuesta adoptada para prototipo, pendiente de validación experimental.
- **Fecha:** 2026-10-09
- **Contexto:** Geelark-IA debe operar sin costes obligatorios, localmente, con Android virtualizado, automatización, API/CLI y opción offline. El usuario permite elegir el mejor hardware y sistema operativo; no hace falta optimizar para un equipo existente.
- **Decisión:**
  1. Usar **Linux Ubuntu LTS x86_64 como sistema operativo de referencia para el anfitrión Android**. Permite controlar kernel, virtualización, contenedores, ADB y aislamiento con herramientas abiertas. La versión exacta LTS se fijará al preparar la imagen reproducible.
  2. Usar **Tauri 2 + React + TypeScript + Vite** para la aplicación de escritorio de control.
  3. Usar **Python + FastAPI + Pydantic** para la API y el dominio local.
  4. Usar **SQLite con migraciones** para la instalación de un solo anfitrión; no introducir PostgreSQL, Redis ni servicios adicionales hasta que pruebas de concurrencia justifiquen la complejidad.
  5. Mantener **Android Emulator oficial como baseline de compatibilidad** y probar **redroid como candidato de ejecución multiinstancia** en Linux. La selección final de motor es un ADR separado y requiere pruebas.
  6. Encapsular ADB detrás de una lista de operaciones permitidas; no exponer puertos ADB ni la API administrativa a redes públicas.
  7. Crear el RPA como motor propio de estados, con acciones tipadas, límites, pausas, cancelación, reintentos idempotentes y trazabilidad. Usar Appium/UIAutomator2 para pruebas y Playwright para la UI web.
- **Consecuencias positivas:** stack portable, poco acoplamiento, costes de licencia bajos/nulos, API documentada, operación local y capacidad de cambiar el motor Android sin rehacer la UI.
- **Costes/riesgos:** hay que empaquetar dependencias; Linux es el anfitrión de referencia y no garantiza por sí mismo compatibilidad de cada app Android; redroid puede requerir permisos elevados y revisión de seguridad; Tauri necesita un proceso de instalación/actualización bien diseñado.
- **Alternativas descartadas por ahora:**
  - Supabase Cloud como backend obligatorio: añade dependencia de servicio externo y límites de free tier.
  - n8n como motor de RPA embebido: su licencia limita ofrecer el editor/automatización como parte de un producto para clientes.
  - Un microservicio/broker por cada función desde el día uno: complejidad prematura.
  - Elegir redroid como motor final sin pruebas: riesgo de asumir seguridad, compatibilidad y rendimiento.
- **Condiciones de validación:** crear e iniciar una instancia, persistir datos tras reinicio, instalar APK de prueba, ejecutar ADB local, capturar pantalla, respaldar/restaurar, probar dos instancias aisladas, verificar puertos escuchando y registrar recursos.
- **Revisión:** actualizar esta ADR cuando las pruebas comparativas indiquen que otro stack o motor ofrece mejor resultado.


## Aclaración posterior: la aplicación debe operar sobre varios nodos

La propuesta original de backend local se mantiene para el dominio y la API, pero el producto no se limitará a un único anfitrión. ADR-003 establece un plano de control distribuido y agentes por nodo. La base de datos local de una instalación mononodo no se considera automáticamente válida como almacén distribuido autoritativo. La decisión sobre persistencia, leases, quorum y recuperación se tomará junto con la implementación del clúster.

Referencias:
- [ADR-003 — Arquitectura distribuida](ADR-003-ARQUITECTURA-DISTRIBUIDA-CLUSTER.md)
- [Contrato de agente y planificador](../CONTRATO_AGENTE_NODO_PLANIFICADOR.md)
- [Comparativa de infraestructura](../COMPARATIVA_INFRAESTRUCTURA_CLUSTER.md)

Ubuntu LTS/Linux directo queda como opción de nodo candidata, no como decisión final para todos los equipos. Proxmox VE también se evaluará. La interfaz, API y modelo de dominio deben mantenerse desacoplados de ambos.

## Reconciliación de decisiones posteriores — 2026-10-24

Este ADR conserva la propuesta inicial del 2026-10-09; los puntos siguientes aclaran su vigencia y no implican que el despliegue esté aceptado:

- **PC-MASTER:** el panel administrativo en desarrollo se ejecuta en Windows. La aceptación física/manual continúa pendiente en [issue #77](https://github.com/D3ckardCain/Geelark-IA/issues/77).
- **PC-WORKERS:** Debian 13 Stable es la base de la primera prueba de nodos Linux. Ubuntu LTS queda como alternativa histórica, no como sistema ya instalado ni como requisito. Proxmox VE no está descartado; se comparará por aislamiento, operación, consumo, actualización y recuperación antes de decidir si conviene usarlo como hipervisor.
- **Android:** redroid es el primer candidato para evaluación multiinstancia, no un motor aprobado para producción. No instalar módulos ni arrancar contenedores hasta resolver [bloqueo de seguridad #27](https://github.com/D3ckardCain/Geelark-IA/issues/27) y fijar/auditar el digest exacto.
- **Persistencia:** SQLite sigue siendo adecuado para almacenamiento local acotado, como el journal del agente y sesiones del panel; no se debe confundir con la persistencia transaccional compartida del plano de control distribuido, que en la integración candidata usa PostgreSQL autohospedado.
- **Integración:** la PR [#117](https://github.com/D3ckardCain/Geelark-IA/pull/117) sigue en draft y sin fusionar. Los resultados CI no sustituyen la aceptación manual del equipo ni autorizan ejecución de tareas reales.

Cualquier cambio de estas decisiones debe quedar en un ADR versionado y enlazado desde el estado del proyecto. El objetivo de coste obligatorio continúa siendo 0 USD; no se añade una dependencia cloud ni un servicio de pago.
