# Evaluación del sistema operativo base del clúster GeeLark-IA

**Fecha de revisión:** 2026-10-10  
**Estado:** recomendación técnica preliminar; no aprobada para instalación física.  
**Restricción:** coste operativo obligatorio de software/servicios de 0 USD, sin tarjeta ni suscripción obligatoria.

## Resumen ejecutivo

**Recomendación para la primera prueba de concepto: Debian 13 Stable instalado directamente en dos PCs**, sin Proxmox inicialmente. Mantener Proxmox VE como alternativa si la prueba demuestra que la administración de máquinas virtuales aporta una ventaja imprescindible.

Motivos:
- Debian Stable es una distribución libre sin suscripción obligatoria, con una base conservadora y un ciclo de soporte documentado.
- Linux directo reduce capas y complejidad mientras se valida el motor Android, los módulos de kernel, la GPU integrada y el rendimiento real.
- Proxmox VE es software libre y puede instalarse sin una suscripción, pero su documentación indica que el repositorio no-subscription es para pruebas/no producción y no lo recomienda para servidores de producción; el repositorio Enterprise y soporte forman parte de sus planes de suscripción. Esto entra en tensión con la regla de coste $0 para producción.
- No hay resultados de rendimiento todavía. La recomendación no demuestra que una imagen Android específica vaya a funcionar.

No instalar ningún sistema operativo hasta que se apruebe expresamente el plan de prueba de concepto y se comprueben las licencias de cada componente.

## Comparativa

| Criterio | Debian 13 Stable directo | Proxmox VE sin suscripción |
|---|---|---|
| Coste obligatorio del SO | 0 USD | 0 USD para descargar/usar; suscripción opcional |
| Repositorio de actualizaciones | Repositorios oficiales de Debian | Repositorio no-subscription disponible sin clave |
| Adecuación de actualizaciones gratuitas a producción | Debian Stable con soporte de seguridad/LTS documentado | Proxmox declara que no-subscription es para pruebas/no producción y no lo recomienda para producción |
| Complejidad inicial | Menos capas: Linux, motor Android y agente | Más capas: Proxmox, VM/CT, red/almacenamiento y motor Android |
| Aislamiento | Depende de contenedores, usuarios, cgroups, namespaces y política local | Puede aportar aislamiento/gestión de VM; la configuración sigue requiriendo auditoría |
| Gestión centralizada de nodos | La implementa GeeLark-IA | Proxmox aporta su propia administración de infraestructura, con requisitos de quorum/cluster |
| Rendimiento Android | Debe medirse; evita una capa de hipervisor | Debe medirse; VM/CT, passthrough y aceleración añaden variables |
| Riesgo de bloqueo tecnológico | Menor si el agente usa interfaces Linux estándar y backends abstractos | Mayor si la automatización depende de APIs específicas de Proxmox |
| Recomendación actual | **Candidato preferido para la POC $0** | Candidato comparativo; no preferido para producción con $0 estricto |

## Requisitos de Android que deben verificarse

El proyecto redroid documenta soporte para hosts Linux x86_64/amd64 y arm64, pero requiere características del kernel y módulos como binder; algunas configuraciones históricas también requieren ashmem. Sus ejemplos usan contenedores privilegiados y advierten expresamente que ADB no debe exponerse a redes públicas.

Antes de seleccionar un motor:
1. Verificar licencia del código y de cada módulo de terceros.
2. Separar la licencia del motor de la licencia de la imagen Android, aplicaciones Google, servicios propietarios y APK de terceros.
3. Confirmar compatibilidad con la CPU/ABI y versión del kernel.
4. Probar si la GPU integrada disponible ofrece aceleración útil; no asumirlo por el nombre de CPU.
5. No exponer el puerto ADB a la LAN general ni a Internet. En la POC debe quedar en loopback/red aislada y ser accesible solo por el adaptador local autorizado.
6. No usar una etiqueta de imagen mutable como versión reproducible; registrar digest, versión, origen y licencia.

redroid declara que su propio código está bajo Apache 2.0 y sus módulos de kernel bajo GPL v2, pero también advierte que incluye componentes de terceros cuyas licencias deben revisarse. Esto no equivale a autorización automática para redistribuir Google Mobile Services ni cualquier APK.

## Propuesta de POC reversible

### Fase 0 — solo inventario, sin instalar

- Registrar modelo exacto de cada PC, CPU completa (incluido sufijo), RAM, disco, firmware/BIOS, soporte VT-x/VT-d, NIC y GPU integrada/dedicada.
- Verificar que no hay información que deba conservarse y confirmar el consentimiento para borrar el disco del equipo de prueba.
- Descargar ISO desde fuente oficial y verificar firma/checksum desde otra máquina.
- Elegir dos equipos distintos para medir heterogeneidad.
- Crear una incidencia GitHub por cada instalación, comando, resultado y fallo; redactar secretos.

### Fase 1 — Debian directo en un solo equipo desechable

1. Instalar Debian 13 Stable con particiones simples y cifrado de disco si el equipo admite recuperación de clave documentada.
2. Aplicar actualizaciones de seguridad y deshabilitar servicios/puertos innecesarios.
3. Instalar solo las herramientas de contenedor necesarias, evitando Docker Desktop y cualquier producto que requiera licencia comercial.
4. Probar el motor Android con una imagen y APK de prueba autorizadas.
5. Medir arranque, RAM, CPU, almacenamiento, estabilidad, captura de pantalla y entrada.
6. Confirmar que ADB solo escucha en loopback o en una interfaz aislada y que no es accesible desde redes no autorizadas.
7. Repetir al menos tres veces y registrar fallos.

### Fase 2 — segundo nodo y red aislada

- Repetir en un segundo PC con capacidades diferentes.
- Registrar ambos agentes y validar heartbeat/capacidades.
- Ejecutar una carga compatible y otra incompatible para comprobar la política de colocación.
- Desconectar/reconectar un nodo; verificar que el controlador no duplica instancias ni repite acciones externas de resultado incierto.
- Probar restauración de un respaldo en un nodo compatible, no migración en vivo.

### Fase 3 — evaluar Proxmox solo si existe una razón medible

Proxmox se prueba únicamente si Debian directo no ofrece el aislamiento/operación necesarios. La comparación debe usar la misma carga, imagen, reserva de RAM y protocolo de medición. No activar suscripciones ni repositorios de pago. Documentar claramente el riesgo de usar el repositorio no-subscription en producción; si el coste cero impide una política de actualización aceptable, descartar Proxmox para producción.

## Criterios de decisión

La decisión se toma con datos, no por preferencia:
- compatibilidad Android real;
- aceleración gráfica efectiva;
- rendimiento y estabilidad medidos;
- aislamiento y superficie de ataque;
- recuperación tras pérdida de red/controlador;
- complejidad operativa;
- soporte de seguridad disponible sin suscripción;
- licencias comerciales/redistribución;
- facilidad de migrar a otro host.

**No se aprobará producción** si una función crítica requiere una licencia de pago, una cuenta con tarjeta, un trial, un servicio externo permanente o si no puede mantenerse actualizado de forma segura con coste $0.

## Fuentes oficiales consultadas

- Debian — releases y ciclo de soporte: https://www.debian.org/releases/index.en.html
- Debian Stable — versión estable actual: https://wiki.debian.org/DebianStable
- Proxmox — repositorio no-subscription y limitación para producción: https://github.com/proxmox/pve-docs/blob/master/pve-package-repos.adoc
- Proxmox — suscripciones, repositorio Enterprise y soporte: https://www.proxmox.com/en/proxmox-ve/pricing
- redroid — arquitectura, módulos de kernel, seguridad ADB y licencias: https://github.com/remote-android/redroid-doc
- Android Open Source Project — licencias y excepciones de componentes: https://source.android.com/docs/setup/contribute/licenses?hl=es-419

## Estado real

Esta es una evaluación documental basada en fuentes oficiales. No se ha instalado ningún sistema operativo, no se ha ejecutado redroid, no se ha probado aceleración GPU y no existen mediciones de rendimiento. La elección final debe esperar a la POC reversible y a la aprobación explícita del usuario.
