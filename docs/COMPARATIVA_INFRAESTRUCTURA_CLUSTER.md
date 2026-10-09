# Comparativa de infraestructura del clúster: Proxmox VE frente a Linux directo

**Fecha:** 2026-10-09  
**Estado:** análisis documental; decisión pendiente de prueba de concepto.  
**Objetivo:** seleccionar la base de infraestructura para Geelark-IA sin costes obligatorios de software/servicios y sin limitar la arquitectura a un proveedor.

## 1. Conclusión provisional

No hay un ganador demostrado para ejecutar Android virtualizado en hardware heterogéneo. Se comparan dos opciones:

- **Proxmox VE:** aporta una capa de gestión de virtualización y clúster ya construida.
- **Linux directo:** reduce capas y deja que Geelark-IA gestione nodos y motores Android directamente, pero exige desarrollar más funciones de infraestructura.

Proxmox VE tiene licencia AGPLv3 y puede usarse sin comprar soporte; la suscripción comercial ofrece repositorio Enterprise y soporte, mientras que el repositorio no-subscription está disponible sin clave y la documentación oficial no lo recomienda para producción por su menor nivel de validación. Por tanto, la infraestructura puede operar sin una suscripción obligatoria, pero el coste cero implica aceptar la administración propia, el canal de actualizaciones elegido y la ausencia de soporte comercial. Revisar las condiciones actuales antes de desplegar.

Fuentes oficiales:
- Licencia y funciones: https://proxmox.com/en/products/proxmox-virtual-environment/features
- Planes/soporte: https://www.proxmox.com/en/proxmox-ve/pricing
- Repositorio no-subscription: https://github.com/proxmox/pve-docs/blob/master/pve-package-repos.adoc
- Requisitos de clúster y quorum: https://github.com/proxmox/pve-docs/blob/master/pvecm.adoc

## 2. Matriz comparativa

| Criterio | Proxmox VE | Linux directo |
|---|---|---|
| Coste obligatorio de licencia | 0 USD posible; soporte comercial opcional | 0 USD posible con distribución y herramientas seleccionadas |
| Gestión de máquinas virtuales | Integrada | Hay que elegir y operar herramientas propias |
| Gestión central de clúster | Incluida, multi-master a nivel Proxmox | La debe proporcionar Geelark-IA u otra herramienta validada |
| Quorum/particiones | Requiere comprender quorum y red estable; no basta con nombrar una PC Master | Geelark-IA debe diseñar autoridad, leases, reconciliación y fencing |
| Agentes de Geelark-IA | Siguen siendo necesarios para lógica de perfiles/RPA Android | Necesarios y con más responsabilidad operativa |
| Compatibilidad de Android | No garantizada por usar Proxmox; depende del motor, virtualización, kernel, GPU y ABI | No garantizada; depende del motor y kernel, pero puede reducir capas |
| Aislamiento | Buenas primitivas de VM/LXC; el diseño Android requiere pruebas propias | Depende de namespaces/cgroups/SELinux/AppArmor y configuración implementada |
| Heterogeneidad | Adecuado para administrar nodos; la migración entre CPU distintas puede tener restricciones | Scheduler propio puede filtrar por capacidad/compatibilidad |
| Rendimiento Android | Pendiente de medir; capas VM/contenedor y aceleración podrían influir | Pendiente de medir; potencialmente menos capas |
| Mantenimiento | Menos trabajo propio de infraestructura, más dependencia del modelo operativo Proxmox | Más código y mantenimiento de infraestructura propio |
| Copias de seguridad | Integración de backups de VM/CT; restauración Android debe probarse | Se debe diseñar backup por motor y estado de instancia |
| Bloqueo de proveedor | Moderado; API y formatos pueden crear acoplamiento si no se abstraen | Menor dependencia de hipervisor, mayor coste de desarrollo interno |
| Riesgo de actualización | Debe gestionarse el repositorio y compatibilidad de versiones | Se deben gestionar paquetes, kernel y versiones por nodo |

## 3. Aclaración sobre la PC Master

Proxmox VE documenta un clúster multi-master: cualquier nodo puede administrar el clúster. Eso es diferente del plano de control de Geelark-IA. La PC elegida como interfaz principal será una preferencia de operación, no necesariamente un controlador exclusivo del clúster Proxmox.

La disponibilidad de quorum depende de votos, nodos y red. La documentación recomienda al menos tres votos para un quorum estable y describe QDevice como opción para clústeres pequeños de dos nodos. Un QDevice necesita un equipo/servicio adicional independiente y no debe asumirse que cualquier PC Master puede actuar como árbitro sin analizar la topología. La prueba debe incluir una pérdida de nodo y una partición de red.

## 4. Decisión recomendada para el prototipo

No adoptar Proxmox para todos los nodos todavía. Implementar primero un contrato de agente y planificador que sea independiente de Proxmox. Ejecutar luego la misma carga Android de referencia en:

A. Linux directo + motor Android candidato.  
B. Proxmox VE + el motor Android viable en esa topología.

Medir con dos nodos heterogéneos:
- instalación y actualizaciones;
- arranque/parada de instancia;
- estabilidad durante 24 horas como prueba inicial, sin confundirla con certificación de producción;
- CPU, RAM, I/O y uso de GPU;
- instalación/ejecución de APK de prueba;
- ADB/captura/entrada;
- aislamiento entre instancias;
- pérdida de red y reinicio del nodo;
- backup/restauración;
- recuperación de metadatos;
- complejidad de operación y documentación.

## 5. Criterios de decisión

La opción elegida debe:
1. no imponer pagos ni suscripciones obligatorias;
2. permitir mantenimiento sin detener todo el clúster;
3. ejecutar Android con las capacidades mínimas requeridas;
4. aislar instancias y proteger ADB/administración;
5. tolerar la heterogeneidad mediante filtros de compatibilidad;
6. permitir backups/restauración comprobados;
7. exponer una interfaz de integración automatizable;
8. tener una ruta de salida sin reescribir perfiles/RPA/dominio;
9. superar pruebas reproducibles y documentadas.

## 6. Límites

Esta es una comparación documental basada en fuentes oficiales, no una prueba de rendimiento. No determina todavía el motor Android final ni la cantidad de instancias. El rendimiento, la compatibilidad de imágenes y las condiciones de licencia de cada componente deben verificarse antes de distribuir el producto.
