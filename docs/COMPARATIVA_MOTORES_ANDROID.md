# Comparativa preliminar de motores Android locales

**Actualizado:** 2026-10-09  
**Estado:** investigación documental; no se han ejecutado pruebas en el hardware anfitrión del usuario.  
**Decisión:** no seleccionar todavía un motor.  
**Objetivo:** identificar un camino reproducible, mantenible y con coste obligatorio de software/servicios de 0 USD para instancias Android locales y automatizables.

## 1. Reglas de evaluación

Un motor no se aprobará solo porque arranque Android. Debe evaluarse en: licencia del motor e imagen; sistema anfitrión; arquitecturas de APK; ADB; captura/entrada; persistencia y aislamiento; creación y eliminación de varias instancias; compatibilidad con automatización; red; GPU; cámara/sensores; seguridad; actualizaciones; espacio y rendimiento medido.

La gratuidad del software no significa coste físico cero: electricidad, almacenamiento, RAM, GPU y conectividad son costes indirectos. No se usarán servicios cloud ni funciones que requieran pagos como dependencia crítica.

## 2. Comparación documental

| Candidato | Enfoque / anfitrión | Evidencia pública | Ventajas potenciales | Riesgos / incógnitas | Estado |
|---|---|---|---|---|---|
| redroid | Android en contenedores Linux; Docker/Podman; arquitecturas amd64 y arm64 | README oficial enumera imágenes Android 8.1 y 9–16; requiere funciones de kernel como binderfs y ashmem/memfd; admite ADB | Diseñado para múltiples instancias; posible automatización por ADB; código base Apache 2.0 según proyecto | Requiere Linux y configuración del kernel; el ejemplo de despliegue usa `--privileged`; hay que auditar componentes de terceros, aislamiento, persistencia y gráficos. No exponer ADB a redes públicas | Candidato para prueba en Linux, no aprobado |
| Android Emulator oficial | AVD con hipervisor; Linux/KVM, Windows/WHPX o macOS/HVF según plataforma | Documentación oficial describe aceleración, control por línea de comandos y requisitos de arquitectura | Herramientas maduras, control de arranque, imágenes y automatización para pruebas; integración ADB | Revisar cuidadosamente el acuerdo del SDK y el alcance de uso antes de incorporarlo como motor de un producto; no asumir que toda imagen/Google API es redistribuible. Capacidad para múltiples instancias y personalización tipo GeeLark pendiente de prueba | Candidato condicionado a revisión de licencia y alcance |
| Waydroid | Contenedor Android sobre GNU/Linux, con acceso directo a hardware | Repositorio oficial indica sistema basado en LineageOS, actualmente Android 13 en la descripción consultada; licencia GPL-3.0 y componentes con licencias propias | Integración estrecha con Linux; software abierto; acceso a hardware anfitrión | No es una solución general para Windows/macOS; investigar multiinstancia, aislamiento, operación sin sesión gráfica y control independiente por instancia. Las opciones comerciales de licencia deben distinguirse de la vía GPL y de obligaciones de distribución | Candidato secundario para prueba Linux |
| Android-x86 / derivados | Android adaptado a x86/x86_64, normalmente en VM | Proyecto y derivados requieren revisión de estado, imágenes, arquitectura y licencia por versión | Aislamiento de VM tradicional; puede ser útil para una instancia Android completa | El estado de mantenimiento, versiones recientes, gráficos, ADB y compatibilidad de aplicaciones debe verificarse por distribución concreta; no asumir soporte uniforme | Candidato de reserva; investigar distribución concreta |

## 3. Fuentes oficiales revisadas

- redroid, documentación y licencias: https://github.com/remote-android/redroid-doc
- redroid, despliegue y requisitos de kernel: https://github.com/remote-android/redroid-doc/blob/master/deploy/README.md
- Android Emulator, aceleración: https://developer.android.com/studio/run/emulator-acceleration
- Android Emulator, línea de comandos: https://developer.android.com/studio/run/emulator-commandline
- Acuerdo de licencia del SDK Android: https://developer.android.com/studio/terms
- Waydroid, repositorio y licencia: https://github.com/waydroid/waydroid
- Waydroid, licencias de componentes: https://github.com/waydroid/docs/blob/master/licensing/licensing.md

Las fuentes son documentación de los propios proyectos. La revisión es preliminar; no sustituye una auditoría legal de cada componente e imagen.

## 4. Conclusiones provisionales

1. **redroid merece la primera prueba técnica en Linux** por su orientación a varias instancias y su disponibilidad de imágenes de varias versiones Android. Esto es una prioridad de prueba, no una selección definitiva.
2. Android Emulator debe mantenerse como referencia de automatización y candidato alternativo, pero no incorporarse a una arquitectura distribuible hasta revisar las condiciones del SDK, las imágenes y los componentes.
3. Waydroid puede ser útil como alternativa Linux, aunque su modelo de contenedor y su orientación a escritorio requieren probar el control de varias instancias independientes.
4. Android-x86 no se aprobará de forma genérica: primero hay que seleccionar una distribución concreta y verificar mantenimiento, licencia y compatibilidad.
5. Ninguna documentación pública prueba que alguno de estos motores reproduzca toda la huella de un teléfono físico, todos los sensores o todas las restricciones de GeeLark.

## 5. Prueba técnica reproducible requerida

Para cada candidato viable en el sistema anfitrión real:

1. Registrar sistema operativo, versión, CPU/arquitectura, RAM, GPU/controlador, almacenamiento libre y soporte de virtualización.
2. Registrar versiones de motor, imagen Android, runtime/hipervisor y ADB; guardar enlaces y checksums cuando estén disponibles.
3. Instalar desde fuentes oficiales y guardar el procedimiento completo.
4. Crear una instancia limpia, iniciarla, comprobar ADB, capturar pantalla y enviar toque, deslizamiento y texto.
5. Instalar una APK de prueba propia o legítima y ejecutar una acción de prueba.
6. Reiniciar el motor y comprobar persistencia de datos.
7. Crear una segunda instancia y comprobar que datos, archivos, estado y operaciones ADB están aislados.
8. Transferir un archivo en ambas direcciones y documentar límites.
9. Medir tiempo de arranque, RAM/CPU en reposo y durante actividad, tamaño en disco y estabilidad; no inventar cifras antes de medir.
10. Revisar puertos expuestos, privilegios, límites de red y recuperación ante cierre inesperado.
11. Probar cámara, GPS, audio, sensores y red por separado, registrando capacidades reales y no equivalentes.
12. Repetir después de detener/iniciar y reiniciar el anfitrión.

**Criterio de salida:** al menos un candidato debe completar el conjunto mínimo con resultados documentados; debe existir una tabla de diferencias y una decisión de arquitectura basada en evidencia. Las pruebas de rendimiento requieren las especificaciones del equipo anfitrión.

## 6. Información que falta del equipo anfitrión

Para realizar pruebas reales y escoger una arquitectura hace falta, cuando el usuario pueda facilitarlo:

- Sistema operativo anfitrión y versión.
- Modelo de CPU y arquitectura.
- RAM instalada.
- GPU y versión del controlador.
- Espacio libre en disco.
- Si la virtualización por hardware está habilitada.
- Cantidad de instancias Android simultáneas deseada.

Hasta tener estos datos, se puede continuar la investigación documental y especificar pruebas, pero no certificar rendimiento ni compatibilidad del equipo.

## 7. Registro de cambios

- 2026-10-09: creación de la comparativa preliminar de redroid, Android Emulator, Waydroid y Android-x86/derivados. No se elige motor; quedan pendientes auditoría de licencias y pruebas en hardware real.
