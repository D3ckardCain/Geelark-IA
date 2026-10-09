# ADR-002: Estrategia de selección del motor Android

- **Estado:** decisión provisional de evaluación; no aprueba todavía un motor para producción.
- **Fecha:** 2026-10-09

## Contexto

Geelark-IA necesita ejecutar instancias Android locales, persistentes, aisladas y automatizables. El objetivo no es simplemente probar una app Android, sino crear un gestor de perfiles y múltiples instancias. Un emulador de desarrollo y un motor de ejecución para producto no son equivalentes.

## Decisión

1. **Candidato principal para experimento de producto: redroid en Linux.** Se evaluará para crear múltiples instancias Android persistentes, cada una con almacenamiento y red aislados. La documentación pública muestra un modelo basado en contenedores y requisitos específicos del kernel.
2. **Baseline de compatibilidad: Android Emulator oficial.** Se usará como referencia de pruebas de instalación, ADB, UI y compatibilidad. No se asumirá que sus términos permitan redistribuirlo o usar sus imágenes como motor incluido en el producto.
3. **Alternativa de laboratorio: Waydroid.** Útil para evaluar Android containerizado en Linux, pero su modelo de escritorio no demuestra por sí mismo que cumpla requisitos de gestión de muchas instancias.
4. **Android-x86 no será candidato principal inicial.** Se conserva como referencia histórica/alternativa; su matriz de versiones y mantenimiento se debe revisar antes de invertir en un adaptador.
5. **No acoplar el producto a un motor.** El contrato del adaptador define una interfaz común y una matriz de capacidades.

## Riesgos que bloquean la aprobación de redroid

La guía de redroid usa un ejemplo con contenedor privilegiado y puerto ADB publicado, y advierte que no se debe exponer ADB a redes públicas. Por tanto, el ejemplo de inicio rápido no se copiará tal cual a producción.

Antes de aprobarlo, demostrar:
- ADB enlazado solo a loopback o a una red interna aislada, sin publicación LAN/WAN.
- El menor conjunto posible de privilegios y capacidades del contenedor; documentar cualquier excepción necesaria.
- Separación de directorios, puertos, procesos, datos y credenciales por instancia.
- Inicio/parada/reinicio y persistencia de datos.
- Instalación de APK y automatización básica.
- Backup/restauración y comportamiento después de fallos.
- Compatibilidad de ABI y aplicaciones de referencia.
- Licencia exacta de cada imagen y posibilidad de distribuirla.
- Recuperación de una instancia sin contaminar otras.
- Funcionamiento local sin servicios externos de pago.

## Pruebas comparativas obligatorias

| Criterio | redroid | Android Emulator | Waydroid |
|---|---|---|---|
| Ejecución multiinstancia | Pendiente de probar | Pendiente de probar | Pendiente de probar |
| Persistencia por instancia | Pendiente de probar | Pendiente de probar | Pendiente de probar |
| Aislamiento de red/ADB | Pendiente de probar | Pendiente de probar | Pendiente de probar |
| Instalación de APK | Pendiente de probar | Pendiente de probar | Pendiente de probar |
| Automatización UI | Pendiente de probar | Pendiente de probar | Pendiente de probar |
| Backup/restauración | Pendiente de probar | Pendiente de probar | Pendiente de probar |
| Seguridad de privilegios | Revisión obligatoria | Revisar configuración del host | Revisar permisos de host |
| Licencia/redistribución | Revisar imagen y componentes | Revisar términos del SDK e imágenes | Revisar imagen y componentes |
| Coste de licencia | Verificar dependencias exactas | Revisar condiciones; no asumir | Verificar dependencias exactas |

## Criterio de cierre

Se aprobará un motor solo si supera pruebas reproducibles, cumple requisitos de seguridad, tiene una ruta de distribución compatible con las licencias y no exige servicios de pago. Si ningún candidato cumple, se documentará el bloqueo y se evaluarán otras opciones sin prometer paridad.
