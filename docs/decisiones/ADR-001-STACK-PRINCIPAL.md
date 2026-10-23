# ADR-001: Stack principal y sistema operativo de referencia

> **Nota de vigencia — 2026-10-22:** conservar este ADR como registro de la propuesta del 9-oct, pero no tratar todos sus puntos como decisiones vigentes. Tauri/React no está seleccionado; la candidata de escritorio es Python/Tkinter en PR #87 y el panel autenticado está en PR #104, ambos sin integrar. El plano de control y la persistencia PostgreSQL local se están validando en ramas/PRs separadas, por lo que la elección inicial de SQLite no debe imponerse a la arquitectura del clúster sin reconciliar ADR-004 y las pruebas. Android Emulator sigue siendo referencia de compatibilidad, redroid está bloqueado por #27 y Cuttlefish es candidato de laboratorio sin aprobación; QEMU + Android-x86 + VNC está retirado. No instalar ni desplegar por este ADR histórico.


- **Estado:** propuesta adoptada para prototipo, pendiente de validación experimental.
- **Fecha:** 2026-10-09
- **Contexto:** Geelark-IA debe operar sin costes obligatorios, localmente, con Android virtualizado, automatización, API/CLI y opción offline. El usuario permite elegir el mejor hardware y sistema operativo; no hace falta optimizar para un equipo existente.
- **Decisión:**
  1. Mantener **PC-MASTER como aplicación Windows** y utilizar **Debian 13 directamente en los PC WORKER físicos** como sistema base previsto para ejecutar Android. GeeLark-IA administrará los nodos y desplegará las herramientas locales necesarias desde PC-MASTER.
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

La decisión operativa vigente es Debian 13 directamente en los PC WORKER y PC-MASTER en Windows. El aprovisionamiento desatendido por red, la instalación del agente y la preparación del runtime Android requieren pruebas en hardware físico. La interfaz, API y modelo de dominio deben mantener contratos claros entre el plano de control y los agentes.
