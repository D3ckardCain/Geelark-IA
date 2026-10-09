# Geelark-IA

Proyecto de referencia funcional inspirado en GeeLark para administrar entornos Android virtualizados de uso personal. La implementación debe avanzar por módulos terminados y verificables, con documentación y trazabilidad en GitHub.

> **Estado:** planificación y definición de requisitos. Las capacidades descritas aquí son objetivos, no funciones ya implementadas ni verificadas.

## Principios obligatorios

- **Costo operativo objetivo: 0 USD.** No usar tarjeta bancaria obligatoria, pruebas temporales, servicios con cobro automático, APIs pagadas ni dependencias críticas de pago. Verificar límites y condiciones antes de elegir cada servicio.
- Priorizar software libre, open source, local y autoalojable; evitar vendor lock-in y permitir migrar componentes.
- Implementar funcionamiento offline o con conectividad limitada cuando sea viable, indicando claramente qué requiere conexión.
- Trabajar paso a paso: terminar, probar, documentar y validar un módulo antes de avanzar al siguiente.
- Comparar continuamente flujos, opciones, configuraciones y resultados con GeeLark como referencia funcional. No afirmar equivalencia sin pruebas.
- Mantener en GitHub requisitos, decisiones, tareas, incidencias, soluciones, pruebas, cambios y manuales.
- Cada módulo debe tener manual de usuario y documentación técnica.

## Alcance objetivo

- Administrar inicialmente hasta 50 instancias Android, con capacidad de ampliar la escala tras validar recursos y rendimiento.
- Admitir distintas versiones de Android.
- Evaluar una infraestructura distribuida con nodos PC y administración central.
- Considerar Proxmox como opción preferente de virtualización, sujeto a pruebas de viabilidad, compatibilidad Android, aceleración gráfica y consumo de recursos.
- Permitir administración remota desde PC y móvil, con seguridad y autenticación.
- Diseñar tolerancia a la caída del nodo de administración cuando sea viable: los nodos no deben depender de una conexión permanente al controlador para seguir ejecutando trabajos ya iniciados.

## Infraestructura conocida

- Equipos disponibles o previstos: PCs con Intel Core i5 de 10.ª/11.ª generación o superior.
- RAM mencionada: 32 GB por equipo en los equipos actuales; el mínimo de planificación indicado es 16 GB.
- Almacenamiento de ejemplo: SSD M.2 NVMe de 500 GB.
- Cantidad de equipos flexible; el diseño debe escalar por nodos.
- Sistema operativo/hipervisor por evaluar: Linux directo frente a Proxmox.

Estos datos son referencias iniciales, no una garantía de que 50 instancias funcionen simultáneamente. Se requiere una prueba de carga real.

## Operación offline

Evaluar PWA, Service Workers, caché local, IndexedDB, cola de operaciones, sincronización posterior, idempotencia, identificadores únicos y resolución de conflictos. Las tareas locales podrán funcionar sin conexión según el módulo; la administración remota, descargas y servicios externos requerirán conexión.

## Organización

- `docs/ESTADO_PROYECTO.md`: estado, decisiones y preguntas abiertas.
- `docs/REQUISITOS.md`: requisitos y criterios de aceptación.
- `docs/PLAN_TRABAJO.md`: fases y entregables.
- GitHub Issues: tareas, dudas, incidencias y soluciones.
- Cada módulo futuro: especificación, pruebas, validación frente a GeeLark, manual de usuario y guía técnica.

## Fuera de alcance por ahora

No se ha confirmado la arquitectura final, el mecanismo técnico de virtualización Android, el stack de desarrollo ni la viabilidad de ejecutar 50 instancias en los equipos descritos. No se debe implementar infraestructura irreversible antes de probar alternativas.

## Seguridad y uso responsable

Proteger credenciales y sesiones, aplicar mínimo privilegio y evitar registrar secretos en issues, commits o documentación. Automatizaciones y aplicaciones deberán respetar las condiciones de servicio de las plataformas utilizadas.
