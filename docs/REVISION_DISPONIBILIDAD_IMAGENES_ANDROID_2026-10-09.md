# Revisión de disponibilidad de imágenes Android para el clúster
**Fecha:** 2026-10-09  
**Estado:** investigación documental; ningún motor instalado ni probado.

## Resumen ejecutivo
La hipótesis de usar Bliss OS en QEMU/KVM como alternativa a redroid necesita matizarse: **Bliss OS no publica actualmente una ISO oficial nueva**. Su página de descargas indica que las imágenes archivadas no reciben actualizaciones ni soporte y no tendrán ruta OTA a la nueva generación. El proyecto informa que las imágenes públicas están pausadas desde agosto de 2026, sin fecha estimada de regreso.

Android-x86 tampoco parece una base actual para producción: su página lista versiones estables antiguas y el changelog indica que la rama Android 11 estaba preparada para desarrolladores en abril de 2022. No se debe inferir que tenga soporte de seguridad actual.

Android Emulator oficial sigue siendo una opción mantenida para pruebas de desarrollo y dispone de imágenes AVD AOSP, Google APIs y Google Play según variante. Sin embargo, la licencia del SDK concede uso del SDK para desarrollar aplicaciones para implementaciones compatibles de Android. No debemos asumir que permite operar una granja comercial de dispositivos virtuales de propósito general ni redistribuir imágenes. Su uso como runtime del producto requiere revisar los términos vigentes y medir carga real.

## Matriz preliminar

| Opción | Disponibilidad observada | Ventajas | Riesgos / límites | Decisión |
|---|---|---|---|---|
| redroid | Proyecto activo; kernel compatible y ejemplo privilegiado | Posible mayor densidad; Android en contenedores | Issue upstream #932 sobre escritura en `/proc/sys/kernel/modprobe`; kernel compartido; compatibilidad de apps/GMS no garantizada | **Bloqueado** hasta demostrar mitigación para la versión concreta |
| Bliss OS en QEMU/KVM | No hay ISO oficial actual; builds públicos antiguos archivados | VM completa y kernel huésped separado | Builds archivados sin soporte/actualizaciones; gráficos y entrada en VM pueden fallar | No usar como base permanente; solo prueba desechable condicionada |
| Android-x86 | Releases públicos antiguos; rama Android 11 preparada para desarrolladores en 2022 | x86/x86_64 y posible arranque en QEMU | Mantenimiento actual insuficiente por demostrar | No seleccionar sin evidencia de mantenimiento actual |
| Android Emulator oficial | Herramienta oficial de desarrollo con imágenes AVD | Documentación vigente; variantes x86_64, Google APIs/Play según imagen | Licencia SDK enfocada a desarrollo; uso continuo multiinstancia y finalidad del producto deben validarse | Candidato para pruebas; runtime de producción pendiente de licencia y carga |

## Recomendación por fases
1. No comprometer el producto con una imagen Android archivada. Mantener el motor desacoplado detrás de una interfaz de runtime/agent para poder sustituirlo sin rehacer panel, cola, asignación y auditoría.
2. Mantener la prueba de seguridad de redroid bloqueada hasta obtener commit/parche, versión y digest de imagen, y prueba de que no modifica el host.
3. Una imagen archivada de Bliss podría evaluarse en una VM desechable de laboratorio, documentando que carece de soporte; no promoverla a producción.
4. Evaluar Android Emulator oficial para confirmar el flujo de control (crear AVD, iniciar/detener, ADB local, persistencia y métricas), pero no aprobarlo como runtime de producción hasta revisar licencia y medir carga.
5. Si ninguna imagen gratuita y mantenida cumple los requisitos y licencia, declarar ese bloqueo claramente y continuar la capa de control con adaptador intercambiable; no prometer una flota Android operativa sin una base técnica y legal válida.

## Costos y licencias
- QEMU/KVM, libvirt y herramientas del sistema están disponibles en Debian sin cuota obligatoria, pero el host libre no vuelve automáticamente libre cualquier imagen Android o servicio Google.
- Las imágenes con Google Play, Google APIs, GMS y componentes de terceros tienen condiciones específicas. No redistribuir imágenes ni APKs sin verificar licencias.
- El objetivo es $0 USD de pagos obligatorios; electricidad, desgaste, conexión y mantenimiento son costes indirectos.
- No se propone API ni servicio de nube de pago.

## Fuentes oficiales consultadas
- Bliss OS descargas: https://blissos.org/download.html
- Estado de Bliss OS (agosto de 2026): https://blissos.org/status.html
- Bliss OS VM docs: https://docs.blissos.org/installation/install-in-a-virtual-machine/
- Android-x86 releases: https://www.android-x86.org/releases
- Android-x86 changelog: https://www.android-x86.org/changelog
- Android Emulator: https://developer.android.com/studio/run/emulator
- AVDs y variantes Google Play/Google APIs: https://developer.android.com/studio/run/managing-avds
- Licencia del Android SDK: https://developer.android.com/studio/terms
- Debian QEMU/KVM: https://wiki.debian.org/QEMU
- Issue de seguridad redroid #932: https://github.com/remote-android/redroid-doc/issues/932

## Estado final
No se ha elegido todavía un runtime Android de producción. La capa de control del clúster puede continuar con contratos desacoplados; ejecutar aplicaciones Android reales sigue siendo un requisito por demostrar, no una función desplegada.
