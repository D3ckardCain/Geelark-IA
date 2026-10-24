# Investigación estática de imágenes Android ligeras para GeeLark-IA

**Fecha:** 2026-10-24  
**Estado:** investigación; ninguna imagen aprobada  
**Issue:** [#119](https://github.com/D3ckardCain/Geelark-IA/issues/119)  
**Bloqueo de seguridad:** [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27)  
**Restricciones:** coste operativo obligatorio $0 USD; no desplegar ni arrancar redroid antes de resolver #27 y aceptar PC-MASTER en #77.

## 1. Conclusión ejecutiva

No se elige todavía una imagen ganadora. El tamaño comprimido publicado favorece a Android 12/13 64only, pero no demuestra menor RAM, menor almacenamiento extraído ni mejor rendimiento por instancia. El catálogo consultado muestra que las tags Android 12/13/14 64only llevan más de dos años sin actualización indicada y Android 15/16 64only más de un año. Es una señal de mantenimiento que requiere evaluación, no prueba automática de vulnerabilidad.

Los candidatos de comparación inicial son Android 12, 13 y 14 64only; Android 15 queda como candidato condicional y Android 16 no se promueve hasta aclarar los reportes de compatibilidad/kernel. La compatibilidad real de APKs, las necesidades de Google services y la ABI todavía no están especificadas para las aplicaciones objetivo.

**Ningún candidato puede arrancarse en PC-MASTER o en un WORKER físico mientras #27 permanezca abierta.** No basta con que una incidencia upstream esté cerrada: se necesita inspeccionar la imagen exacta y demostrar una mitigación que impida que Android init modifique el host.

## 2. Catálogo público preliminar

Fuente: [Docker Hub — tags de redroid](https://hub.docker.com/r/redroid/redroid/tags). Tamaños publicados como comprimidos para linux/amd64; pueden cambiar.

| Tag | Prefijo de digest mostrado | Tamaño comprimido | Señal de antigüedad del catálogo | Estado para GeeLark-IA |
|---|---|---:|---|---|
| redroid/redroid:12.0.0_64only-latest | e6f799d56b9a | 616.13 MB | Más de 2 años | Comparador; no aprobado |
| redroid/redroid:13.0.0_64only-latest | 36d6d21bcf7e | 651.29 MB | Más de 2 años | Comparador; no aprobado |
| redroid/redroid:14.0.0_64only-latest | 68ae34dfbdb1 | 676.23 MB | Más de 2 años | Comparador; no aprobado |
| redroid/redroid:15.0.0_64only-latest | 58e548d78c48 | 695.98 MB | Más de 1 año | Condicional; ABI/compatibilidad por comprobar |
| redroid/redroid:16.0.0_64only-latest | 18eaf7058f1f | 739.72 MB | Más de 1 año | No promover hasta resolver reportes de kernel/arranque |

Los prefijos son referencias de catálogo para esta investigación, **no pinning operativo**. Antes de cualquier prueba se debe obtener el digest completo correspondiente a linux/amd64, guardar la fecha de consulta y fijar la imagen por digest. No usar latest como identificador reproducible.

Para contexto, el catálogo muestra Android 12 estándar ~769.48 MB, Android 13 estándar ~799.58 MB y Android 14 estándar ~832.88 MB comprimidos en amd64. Esto no demuestra que una variante estándar sea funcionalmente necesaria; debe decidirse a partir de las APKs objetivo.

## 3. Hallazgos de seguridad y compatibilidad

### 3.1 Escritura de /proc/sys/kernel/modprobe

La [incidencia upstream #932](https://github.com/remote-android/redroid-doc/issues/932) describe que AOSP init escribe una cadena vacía en /proc/sys/kernel/modprobe durante early-init. El informe reproduce el problema con Android 14 64only y señala que Android 16 conserva la instrucción en su base AOSP. Al ser un sysctl no namespaced, una ejecución privilegiada puede afectar al host.

La [fuente init.rc de redroid Android 14](https://raw.githubusercontent.com/remote-android/platform_system_core/redroid-14.0.0_r2/rootdir/init.rc) conserva la escritura en las líneas iniciales de early-init. Por tanto:
- No se puede considerar segura la tag Android 14 sin inspeccionar la imagen publicada exacta y sus capas.
- La incidencia no prueba por sí sola el comportamiento de cada digest Android 12/13/15; esos tags necesitan inspección individual.
- Restaurar el valor del sysctl después del arranque no es una mitigación preventiva suficiente.
- La receta de inicio de la documentación upstream usa --privileged; no copiarla a GeeLark-IA sin una revisión específica de capacidades, dispositivos, montajes y namespaces.

### 3.2 ABI ARM en imágenes x86_64

La [incidencia upstream #933](https://github.com/remote-android/redroid-doc/issues/933) informa de imágenes x86_64 desde redroid 15 que anuncian arm64-v8a aunque el traductor nativo necesario no esté presente. En ese escenario una APK ARM-only puede instalarse y fallar al abrirse. La documentación upstream también contiene una sección de soporte Native Bridge, pero no debe asumirse que esa documentación general prueba la presencia/funcionamiento en cada digest actual.

Reglas:
- Obtener las APKs objetivo y determinar sus ABI antes de elegir 64only.
- Probar por tag/digest exacto instalación, apertura y carga de bibliotecas nativas.
- No añadir ni redistribuir binarios propietarios de Google sin resolver procedencia y licencia.
- Si no existe traductor autorizado, preferir un fallo de compatibilidad claro a anunciar ABI que no se pueden ejecutar.

### 3.3 ADB, red y privilegios

La [guía oficial de redroid](https://github.com/remote-android/redroid-doc) muestra una receta de ejemplo con --privileged y puerto ADB 5555 publicado, y advierte que ADB no debe exponerse a redes públicas. Para GeeLark-IA:
- ADB no se publicará en LAN ni Internet por defecto.
- No exponer el socket Docker al panel ni al agente.
- No permitir que un nodo pendiente reciba tareas.
- No aceptar comandos remotos genéricos, shell arbitraria o ADB como parte del flujo de adopción.
- La prueba inicial, cuando se autorice, debe ser aislada, de una sola instancia, con rollback escrito y evidencia sanitizada.

## 4. Qué significa realmente “imagen ligera”

Se deben registrar por separado:

1. Tamaño comprimido descargado.
2. Tamaño de capas e imagen extraída en el host.
3. Tamaño inicial y crecimiento del directorio persistente /data.
4. RAM en reposo y con una carga de aplicación reproducible.
5. CPU en reposo, arranque, apertura de aplicación y carga sostenida.
6. Tiempo hasta ADB disponible y tiempo hasta aplicación utilizable.
7. Estabilidad, reinicios, errores del kernel y pérdida de conectividad.
8. Compatibilidad con APKs, ABI, WebView, notificaciones y Google services cuando correspondan.
9. Capacidad real con 1, 2 y varias instancias, sin extrapolar desde una instancia.
10. Efecto de resolución/DPI, FPS, animaciones y servicios en segundo plano.

La comparación debe mantener constante el worker, kernel, límites de CPU/RAM, resolución/DPI, datos, red y carga de aplicación. No declarar un ganador usando únicamente MB comprimidos.

## 5. Requisitos previos a cualquier descarga o prueba física

### Fase A — sin hardware y sin ejecutar contenedores
- Registrar la APK y sus ABI requeridas, Google services, notificaciones, WebView y funciones que necesita.
- Obtener digest completo, fecha y arquitectura de cada tag candidato.
- Revisar estáticamente init.rc, parches redroid aplicados, configuración de ABI y procedencia/licencias.
- Verificar requisitos del kernel Debian 13 previsto: binderfs, ashmem/memfd, soporte de páginas de 4 KiB y los módulos/recursos exactos requeridos por la versión elegida.
- Documentar la mitigación preventiva de kernel.modprobe; si no puede demostrarse, mantener bloqueado el despliegue.
- No instalar módulos DKMS ni cambiar el kernel por anticipado.

### Fase B — solo tras resolver #27 y aceptar #77
- Prueba controlada en WORKER-01, nunca primero en PC-MASTER.
- Una instancia, datos de prueba descartables, red restringida y ADB sin publicación externa.
- Registrar imagen/digest, kernel, configuración y resultados.
- Verificar que el host conserva el sysctl original y la carga automática de módulos; la comprobación posterior es evidencia adicional, no sustituto de la prevención.
- Ejecutar pruebas de regresión de APK/ABI y guardar logs sin secretos.
- Detener, retirar la instancia de prueba y verificar rollback antes de pasar a varias instancias.

### Fase C — rendimiento y distribución LAN
- Medir 0/1/2/múltiples instancias con límites comparables.
- Descargar cada digest una vez por worker cuando sea viable y distribuir artefactos por LAN.
- Verificar hash/digest después de distribuir y conservar una versión anterior para rollback.
- Evitar pulls repetidos en la conexión de 10 Mbps; la caché local no debe convertirse en una dependencia de proveedor.
- Registrar límites de Docker Hub y no asumir que la disponibilidad pública garantiza descargas ilimitadas.

### Fase D — imagen personalizada
Solo considerar una imagen personalizada después de medir la imagen oficial y demostrar un beneficio. Eliminar o deshabilitar componentes requiere pruebas de regresión. No retirar Package Manager, permisos, WebView, conectividad, entrada, audio/vídeo o servicios de Google si las aplicaciones los requieren. Mantener SBOM, licencias, procedencia y construcción reproducible.

## 6. Coste y dependencia externa

La investigación y las pruebas locales propuestas no requieren APIs de pago ni un servicio cloud de pago. Docker Hub es una fuente pública de imágenes, pero sus límites de descarga/disponibilidad deben comprobarse y no deben tratarse como garantía ilimitada. La arquitectura debe permitir almacenar y distribuir los digests por LAN y reconstruir o migrar sin depender de un proveedor único.

La compilación AOSP personalizada no se justifica en esta fase: requiere mucho almacenamiento, ancho de banda y CPU; primero hay que medir las imágenes existentes y sus requisitos reales.

## 7. Criterios de salida de la investigación

- [ ] APKs objetivo y ABI identificadas.
- [ ] Digest completo por plataforma y fecha registrados para cada candidato.
- [ ] Revisión estática de init/patches por digest.
- [ ] Mitigación preventiva del riesgo kernel.modprobe demostrada o despliegue bloqueado.
- [ ] Requisitos del kernel Debian 13 confirmados para el digest exacto.
- [ ] Licencias/procedencia/SBOM revisadas.
- [ ] Baseline de RAM/CPU/arranque/disco recogido con pruebas controladas.
- [ ] Compatibilidad funcional validada para las APKs reales.
- [ ] Procedimiento de distribución LAN, integridad y rollback documentado.

## Fuentes

- [Redroid — documentación upstream](https://github.com/remote-android/redroid-doc)
- [Docker Hub — tags y tamaños publicados](https://hub.docker.com/r/redroid/redroid/tags)
- [redroid-doc #932 — escritura de kernel.modprobe](https://github.com/remote-android/redroid-doc/issues/932)
- [redroid-doc #933 — ABI ARM anunciada sin traductor](https://github.com/remote-android/redroid-doc/issues/933)
- [init.rc de redroid Android 14](https://raw.githubusercontent.com/remote-android/platform_system_core/redroid-14.0.0_r2/rootdir/init.rc)
- [redroid-patches — ramas y parches](https://github.com/remote-android/redroid-patches)
- [Issue GeeLark-IA #27 — puerta de seguridad](https://github.com/D3ckardCain/Geelark-IA/issues/27)
- [Issue GeeLark-IA #77 — aceptación manual PC-MASTER](https://github.com/D3ckardCain/Geelark-IA/issues/77)
