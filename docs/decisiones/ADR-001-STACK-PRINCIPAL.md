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
