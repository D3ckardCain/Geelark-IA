# Comparativa de motores Android locales

**Actualizado:** 2026-10-21  
**Estado:** investigación documental ampliada; ningún motor aprobado ni validado en WORKERS físicos.  
**Decisión de alcance:** se retira la vía manual QEMU + Android-x86 9.0-r2 + VNC. No se continuará depurando ese prototipo ni se usará como base del producto.

La investigación completa, incluidos componentes de automatización, fuentes, licencias, riesgos y puertas de validación, está en [INVESTIGACION_MOTOR_AUTOMATIZACION_ANDROID.md](INVESTIGACION_MOTOR_AUTOMATIZACION_ANDROID.md).

## Comparación ejecutiva

| Candidato | Evidencia de multiinstancia | Control | Riesgo/bloqueo | Prioridad |
|---|---|---|---|---|
| AOSP Cuttlefish | Documentación explícita: `cvd create --num_instances=N`, discos overlay por instancia y puertos ADB separados | WebRTC desde navegador, con control y ADB web documentados | Requiere Linux/KVM, imagen y dependencias compatibles; no garantiza Google Play ni compatibilidad universal de apps | **Primera prueba documental/técnica** |
| redroid | Proyecto diseñado para Android en contenedores y múltiples instancias | ADB y visor externo como scrcpy | Requiere funciones del kernel; ejemplo oficial usa `--privileged`; bloqueo de seguridad interno #27 sin resolver | **Candidato bloqueado** |
| Android Emulator oficial | AVD independientes; CLI/ADB/KVM documentados | Herramientas del emulador; la variante de contenedores es experimental | Revisar términos del SDK e imágenes, redistribución y densidad | Referencia de compatibilidad |
| Waydroid | No se ha demostrado la topología multiinstancia requerida | Principalmente integración de escritorio Linux | Headless, aislamiento y control independiente pendientes | Secundario |
| Android-x86/Bliss OS + QEMU manual | Posible una VM por instancia, pero no demuestra densidad ni paridad | El prototipo local con VNC mostró pantalla negra y no se validó | Imagen Android-x86 9.0-r2 antigua; ruta manual no validada | **Retirado** |
| Genymotion Desktop gratuito | No apto para nuestro uso de servidor/automatización profesional bajo licencia personal | Variable | Condiciones de licencia requieren pago para usos relevantes | Descartado |
| Anbox clásico | No se recomienda | — | Repositorio archivado | Descartado |

## Conclusiones

1. **Cuttlefish** es el primer candidato para una prueba controlada de una y dos instancias, porque la documentación oficial contempla multiinstancia y acceso por navegador mediante WebRTC.
2. **redroid** podría tener ventajas de densidad, pero no se ejecutará en hardware físico hasta resolver el bloqueo de seguridad de [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27), verificar la mitigación upstream y definir aislamiento y red con privilegios mínimos.
3. **Android Emulator oficial** se mantiene como referencia separada para compatibilidad de APK/UI/ADB; no se debe confundir con la receta manual Android-x86 + QEMU retirada, y no se aprobará para redistribución sin revisar licencias.
4. **Waydroid** queda secundario por falta de evidencia para una flota multiinstancia independiente.
5. No hay estimación validada de instancias por WORKER. Se medirá en Debian físico; no extrapolar a 50 instancias a partir de documentación.
6. El motor debe ser intercambiable detrás de un contrato común. RPA y Synchronizer no dependerán directamente de comandos específicos de un motor.

## Automatización que debe evaluarse

- **ADB/platform-tools:** operaciones Android permitidas, instalación de APK, archivos y capturas, siempre detrás de un adaptador con lista permitida, límites, timeout y auditoría.
- **Appium + UiAutomator2:** automatización de UI por selectores; Apache-2.0 para el driver; fijar versiones compatibles.
- **UI Automator oficial:** referencia Android para interacción y árbol semántico.
- **scrcpy:** visor/control libre y multiplataforma; no crea instancias ni reemplaza un motor RPA.
- **Maestro:** framework de flujos UI declarativos en YAML; evaluar como herramienta auxiliar, no asumir que sustituye un RPA completo de producto.
- **Desarrollo propio:** Instance Manager, perfiles, RPA Builder/Runner, Synchronizer, API local/Webhooks, Library, logs y scheduler de recursos.

## Puertas de validación

1. **Licencia/seguridad:** fijar versiones e imágenes; auditar componentes, puertos, privilegios y distribución.
2. **Una instancia en Debian físico de laboratorio:** inicio/parada/reinicio, ADB, captura/entrada, APK, red, archivos, persistencia y métricas.
3. **Dos instancias simultáneas:** aislamiento de datos/red/ADB, operación independiente, RPA con resultados separados.
4. **Automatización:** flujo con selectores, condiciones, bucle limitado, timeout, cancelación, recuperación y resultados.
5. **Escalado:** medir 4, 6 y más instancias solo si las métricas lo permiten.
6. **Integración:** conectar el adaptador aprobado con PC-MASTER/WORKERS y aprovisionamiento por LAN.

No instalar en WORKERS físicos ni cerrar la selección hasta completar las pruebas y documentar sus resultados. Coste obligatorio de software/servicios: 0 USD.

## Fuentes principales

- Cuttlefish multiinstancia: https://source.android.com/docs/devices/cuttlefish/multi-tenancy
- Cuttlefish WebRTC: https://source.android.com/docs/setup/create/cuttlefish-ref-webrtc
- redroid: https://github.com/remote-android/redroid-doc
- Bloqueo redroid: https://github.com/D3ckardCain/Geelark-IA/issues/27
- Android Emulator: https://developer.android.com/studio/run/emulator-commandline
- Términos SDK: https://developer.android.com/studio/terms
- Android Emulator en contenedores (experimental): https://github.com/google/android-emulator-container-scripts
- Waydroid: https://github.com/waydroid/waydroid
- Genymotion: https://www.genymotion.com/legal-terms-and-conditions/
- Appium UiAutomator2: https://github.com/appium/appium-uiautomator2-driver
- UI Automator: https://developer.android.com/training/testing/other-components/ui-automator
- scrcpy: https://github.com/Genymobile/scrcpy
- Maestro: https://docs.maestro.dev/get-started/what-is-maestro
- GeeLark RPA/API/Synchronizer: https://www.geelark.com/features/rpa/ · https://www.geelark.com/features/api/ · https://www.geelark.com/features/automation/

## Registro de cambios

- 2026-10-21: se retira Android-x86 9.0-r2 + QEMU manual + VNC como ruta de producto.
- 2026-10-21: Cuttlefish pasa a primera prioridad documental por multiinstancia y WebRTC.
- 2026-10-21: redroid permanece bloqueado por seguridad; Android Emulator es referencia; Waydroid queda secundario.
- 2026-10-21: automatización se amplía a RPA Builder/Runner, Synchronizer, API/Webhooks, ADB y visor de control.
