# ADR-001: Stack principal y sistema operativo de referencia

- **Estado:** propuesta de stack para prototipo; **sistema operativo anfitrión pendiente de decisión y prueba**.
- **Fecha:** 2026-10-09; revisión documental en curso 2026-10-10.
- **Contexto:** GeeLark-IA debe operar sin costes obligatorios, localmente, con Android virtualizado, automatización, API/CLI y opción offline. El usuario permite elegir el mejor hardware y sistema operativo; no hace falta optimizar para un equipo existente. El usuario pidió comparar Debian 13 Stable directo y Proxmox VE antes de decidir; la auditoría detectó que también debe compararse Ubuntu LTS, nombrado en la versión previa de esta ADR.
- **Decisiones provisionales de stack:**
  1. Mantener **Linux x86_64 como requisito candidato para el anfitrión Android**, pero no seleccionar todavía una distribución. Los candidatos documentales son Ubuntu 26.04 LTS directo, Debian 13 Stable directo y Proxmox VE con una VM Linux dedicada. Ver [evaluación de SO del clúster](../EVALUACION_SO_BASE_CLUSTER_0USD.md), [matriz de decisión](../MATRIZ_DECISION_SO_CLUSTER.md) e [Issue #64](https://github.com/D3ckardCain/Geelark-IA/issues/64).
  2. Usar **Tauri 2 + React + TypeScript + Vite** para la aplicación de escritorio de control.
  3. Usar **Python + FastAPI + Pydantic** para la API y el dominio local.
  4. Mantener SQLite con migraciones como opción para una instalación mononodo; la persistencia autoritativa distribuida se define aparte, no asumir que SQLite mononodo sirve automáticamente para el clúster.
  5. Mantener **Android Emulator oficial como baseline de compatibilidad** y probar **redroid como candidato de ejecución multiinstancia**. La selección final de motor requiere pruebas y revisión de licencias.
  6. Encapsular ADB detrás de una lista de operaciones permitidas; no exponer puertos ADB ni la API administrativa a redes públicas.
  7. Crear el RPA como motor propio de estados, con acciones tipadas, límites, pausas, cancelación, reintentos idempotentes y trazabilidad. Usar Appium/UIAutomator2 para pruebas y Playwright para la UI web.

**Condición de aprobación del SO:** no se instalará ni cambiará nada en PCs físicas, BIOS/UEFI o discos hasta que la comparación documental, la matriz de pruebas y la autorización explícita del usuario estén completas. El candidato ganador debe superar puertas de coste obligatorio $0, actualizaciones de seguridad aceptables, licencias claras, ADB aislado, compatibilidad Android y recuperación reproducible.
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
