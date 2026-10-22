# ADR-002: Estrategia de selección del motor Android

- **Estado:** decisión provisional de investigación; ningún motor aprobado para producción.
- **Actualizado:** 2026-10-21

## Contexto

GeeLark-IA debe reproducir de forma independiente las capacidades públicas de GeeLark, empezando por instancias Android locales independientes y automatización. No basta con arrancar una imagen: hacen falta ciclo de vida fiable, acceso visual y ADB, persistencia, aislamiento, compatibilidad de aplicaciones, RPA, Synchronizer, API/eventos y operación distribuida desde PC-MASTER Windows hacia WORKERS físicos Debian 13.

La meta de coste obligatorio de software/servicios es 0 USD. No se dependerá de cloud phones ni de APIs de pago. Toda afirmación de capacidad requiere evidencia y pruebas.

## Decisiones

1. **Retirada de la vía anterior:** no continuar con el prototipo manual QEMU + Android-x86 9.0-r2 + VNC probado en WSL2. No depurar más su pantalla negra ni construir el producto sobre esa combinación. La retirada se registra en [INVESTIGACION_MOTOR_AUTOMATIZACION_ANDROID.md](../INVESTIGACION_MOTOR_AUTOMATIZACION_ANDROID.md).
2. **Primera prioridad de evaluación: AOSP Cuttlefish.** La documentación oficial describe multiinstancia explícita, overlays de disco por instancia, puertos ADB diferenciados y control remoto WebRTC desde navegador. Es una prioridad de prueba, no una aprobación para producción.
3. **redroid: candidato de densidad bloqueado por seguridad.** No instalarlo en PC-MASTER ni en WORKERS físicos hasta resolver la [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27), verificar la versión/mitigación upstream y demostrar aislamiento con privilegios mínimos y ADB no expuesto.
4. **Android Emulator oficial: referencia de compatibilidad.** Puede ayudar a probar APK, ADB, versiones y automatización. Se revisarán los términos del SDK, los binarios e imágenes antes de redistribuir o incluirlo en un producto. La variante de contenedores es experimental. No confundirlo con el prototipo manual Android-x86/QEMU retirado.
5. **Waydroid: alternativa secundaria.** Su orientación al escritorio Linux no demuestra todavía la operación headless y la administración independiente de muchas instancias requeridas.
6. **No acoplar el dominio a un motor.** Definir un contrato común de capacidades, ciclo de vida, estado, captura, entrada, instalación de APK, archivos, persistencia y errores. Cada adaptador declara capacidades probadas, no soportadas y desconocidas.
7. **Separar motor de automatización.** ADB, Appium/UiAutomator2, UI Automator, scrcpy o Maestro son herramientas/componentes candidatos, no un sustituto automático del producto. GeeLark-IA necesita su propio RPA Builder/Runner, Synchronizer, API local, eventos, perfiles, Library, registros y scheduler.
8. **Coste y licencias:** revisar por separado el código, dependencias, imágenes, APK y permisos de redistribución. No asumir que una descarga gratuita autoriza cualquier uso comercial o distribución.

## Evidencia documental

- Cuttlefish multiinstancia: https://source.android.com/docs/devices/cuttlefish/multi-tenancy
- Cuttlefish WebRTC: https://source.android.com/docs/setup/create/cuttlefish-ref-webrtc
- redroid y requisitos: https://github.com/remote-android/redroid-doc
- Android Emulator CLI/aceleración: https://developer.android.com/studio/run/emulator-commandline
- Términos SDK: https://developer.android.com/studio/terms
- Android Emulator en contenedores (experimental): https://github.com/google/android-emulator-container-scripts
- Waydroid: https://github.com/waydroid/waydroid
- Appium UiAutomator2: https://github.com/appium/appium-uiautomator2-driver
- UI Automator: https://developer.android.com/training/testing/other-components/ui-automator
- scrcpy: https://github.com/Genymobile/scrcpy
- Maestro: https://docs.maestro.dev/get-started/what-is-maestro
- Catálogo de paridad GeeLark: https://www.geelark.com/features/automation/ · https://www.geelark.com/features/rpa/ · https://www.geelark.com/features/api/

## Pruebas obligatorias antes de elegir

| Criterio | Cuttlefish | redroid | Android Emulator | Waydroid |
|---|---|---|---|---|
| Una instancia: ciclo de vida | Pendiente | Bloqueado hasta revisión de seguridad | Pendiente | Pendiente |
| Dos instancias simultáneas | Pendiente | Bloqueado hasta revisión de seguridad | Pendiente | Pendiente |
| Captura y entrada | Pendiente en nuestro hardware | Pendiente | Pendiente | Pendiente |
| ADB restringido | Pendiente | Bloqueo crítico | Pendiente | Pendiente |
| Persistencia independiente | Pendiente | Pendiente | Pendiente | Pendiente |
| APK objetivo y compatibilidad | Pendiente | Pendiente | Pendiente | Pendiente |
| RPA y recuperación | Pendiente | Pendiente | Pendiente | Pendiente |
| Licencias de imagen/componentes | Revisar artefactos exactos | Revisar imagen y componentes | Revisar SDK/imágenes | Revisar imágenes/componentes |
| Densidad medida | Pendiente | Pendiente | Pendiente | Pendiente |

## Criterios de seguridad

- No exponer ADB en Internet ni abrir listeners de control por defecto.
- No ejecutar shell arbitrario desde la API de producto.
- Aislar datos, archivos, puertos y credenciales por instancia.
- Aplicar timeouts, límites, cancelación, idempotencia y auditoría a tareas.
- No permitir que nodos pendientes acepten o ejecuten tareas.
- No instalar en PCs físicos hasta superar revisión de licencias/seguridad y obtener aprobación para la prueba física.
- No declarar soporte de Google Play, ARM, sensores o identidad física sin pruebas.

## Criterio de cierre

Aprobar un motor solo después de una prueba reproducible en Debian físico de laboratorio: primero una instancia y luego dos, con captura/entrada, ADB, APK, persistencia, aislamiento, automatización, recuperación y métricas. La documentación sola no demuestra rendimiento ni paridad. Si ningún candidato pasa, registrar el bloqueo y buscar alternativas sin reactivar automáticamente la vía retirada.

## Registro de cambios

- 2026-10-09: se documentó inicialmente redroid como candidato de densidad, Android Emulator como baseline y Waydroid como alternativa.
- 2026-10-21: se retira explícitamente el prototipo manual QEMU + Android-x86 9.0-r2 + VNC.
- 2026-10-21: Cuttlefish pasa a primera prioridad de evaluación por multiinstancia y WebRTC documentados.
- 2026-10-21: redroid queda bloqueado hasta resolver la issue #27.
- 2026-10-21: se incorpora la arquitectura de automatización como parte esencial del motor, no como tarea posterior.
