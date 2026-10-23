> **Nota de vigencia — 2026-10-22:** Este documento conserva la investigación histórica del riesgo de redroid. La recomendación antigua de probar QEMU/KVM con Bliss OS si redroid falla quedó retirada por decisión del proyecto; no ejecutar ni reactivar esa ruta. QEMU + Android-x86 + VNC en WSL2 se descartó y Bliss OS no es un sustituto aprobado. Redroid sigue bloqueado por la Issue #27 hasta demostrar mitigación específica; el motor Android sigue sin seleccionar.

# Actualización de seguridad: redroid y kernel.modprobe

**Fecha de revisión:** 2026-10-09  
**Proyecto:** GeeLark-IA  
**Estado:** investigación documental; no se ha instalado ni ejecutado redroid en los equipos físicos.

## Hallazgo confirmado en la fuente upstream

El issue [remote-android/redroid-doc #932](https://github.com/remote-android/redroid-doc/issues/932), abierto el 15 de julio de 2026 y cerrado el 25 de agosto de 2026, describe que el proceso init de Android puede escribir en `/proc/sys/kernel/modprobe` desde un contenedor redroid ejecutado con `--privileged`. Según el reporte, ese sysctl no está aislado por namespace y la escritura puede afectar al host. El autor indicó que observó el problema en redroid 14 y que también afectaba al código base de Android 16 revisado en el momento del reporte.

**Importante:** el issue aparece cerrado como “completed”, pero la página pública consultada no muestra una explicación de la solución, un commit de corrección, una versión corregida ni una prueba que demuestre la mitigación. Por tanto, no se puede concluir que el riesgo esté corregido solo por el estado cerrado.

La guía oficial actual de redroid continúa mostrando un ejemplo de ejecución con `--privileged` y publicación del puerto ADB `5555`; también advierte expresamente que ADB no debe exponerse a una red pública porque el contenedor —e incluso el host— podría verse comprometido.

## Decisión para GeeLark-IA

1. **No aprobar todavía redroid para una prueba física.** Mantenerlo bloqueado hasta verificar una corrección trazable para una combinación concreta de imagen y kernel.
2. No asumir que precargar módulos o restaurar manualmente el sysctl es una solución suficiente; son mitigaciones operativas reportadas por el usuario del issue, no una corrección demostrada para nuestra configuración.
3. Antes de reabrir la evaluación, exigir evidencia verificable: commit/parche upstream aplicable, versión de imagen construida con ese parche y una prueba controlada que confirme que el valor del host no cambia al iniciar Android.
4. Si no se obtiene esa evidencia, priorizar la evaluación de una VM completa QEMU/KVM (por ejemplo, Bliss OS) en un worker de laboratorio. La VM también requerirá endurecimiento y pruebas; no se considera automáticamente segura ni compatible.
5. Independientemente del motor, ADB y las interfaces administrativas permanecerán limitados a loopback o a una red de gestión aislada; no se publicarán en Internet.
6. Se puede usar uno de los tres workers existentes para las pruebas controladas cuando exista un plan revisado y aprobado; no hace falta comprar un quinto PC. No empezar en PC-MASTER.

## Evidencia consultada

- Issue upstream #932: https://github.com/remote-android/redroid-doc/issues/932
- Guía oficial redroid y advertencia sobre ADB: https://github.com/remote-android/redroid-doc
- Guía de Bliss OS en QEMU: https://docs.blissos.org/installation/install-in-a-virtual-machine/install-in-qemu/

## Próximos pasos

- Revisar la actividad/commit que motivó el cierre de #932 y los repositorios de código Android/parches de redroid para buscar una corrección verificable.
- Si se identifica una corrección, registrar hash del commit, versión/tag de imagen, digest de imagen y prueba reproducible.
- Si no se identifica, documentar la decisión de descartar redroid para este MVP y preparar una prueba Live USB + QEMU/KVM en WORKER-01, sin instalar nada hasta revisar el plan de recuperación.
