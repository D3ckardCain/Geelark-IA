# Estado del proyecto Geelark-IA

**Actualizado:** 2026-10-09  
**Fase:** A — inventario funcional de GeeLark y preparación de auditoría de hardware  
**Implementación:** no hay módulos declarados como terminados o verificados.

## Objetivo acordado

Replicar desde cero todas las funciones de GeeLark que puedan reproducirse en una plataforma local orientada exclusivamente a Android, usando dispositivos Android físicos y recursos informáticos locales, con software gratuito y sin servicios de pago obligatorios. iOS queda excluido. La paridad se comprobará mediante pruebas; no se promete equivalencia total antes de la investigación.

## Principios acordados

1. Objetivo de costo operativo de 0 USD; evitar pagos obligatorios, tarjetas requeridas, pruebas temporales, cobros automáticos y APIs de pago.
2. Priorizar software libre, local o autoalojado y reducir dependencia de proveedores.
3. Operación offline cuando sea técnicamente viable, documentando limitaciones.
4. GeeLark es la referencia funcional; la equivalencia requiere evidencia y pruebas.
5. Avanzar por fases pequeñas, terminadas, probadas, documentadas y aceptadas.
6. Cada módulo tendrá manual de usuario completo y documentación técnica.
7. GitHub registrará requisitos, decisiones, tareas, problemas, soluciones, pruebas y cambios.
8. No afirmar que una función existe, que una prueba pasó o que una capacidad está garantizada sin evidencia.
9. No copiar código, marca ni activos propietarios; implementar de forma independiente a partir de requisitos observables.

## Documentación principal

- [Plan maestro de paridad funcional](PLAN_PARIDAD_GEELARK.md)
- [Requisitos](REQUISITOS.md)
- [Plan de trabajo resumido](PLAN_TRABAJO.md)

## Investigación pública inicial

El Centro de ayuda de GeeLark lista Profile, Proxies, Library, AIGC, Analytics, Applications, Automaton, Synchronizer, GeeHub, Resources, Referral, Billing, Members y Logs; también presenta documentación de grupos, ADB y conexión de dispositivos locales. La web pública de automatización describe plantillas, sincronizador, RPA visual y API. La revisión es inicial: el inventario debe ampliarse y validarse función por función.

Fuentes:
- https://help.geelark.com/
- https://www.geelark.com/features/automation/
- https://www.geelark.com/features/rpa/
- https://www.geelark.com/features/api/
- https://www.geelark.com/pricing/

## Fase actual: entregables pendientes

- [ ] Inventariar funciones y flujos observables de GeeLark.
- [ ] Clasificar viabilidad local, adaptaciones, dependencias externas y funciones no confirmadas.
- [ ] Recopilar especificaciones del equipo anfitrión y teléfonos Android disponibles.
- [ ] Definir criterios de aceptación para la prueba técnica de un dispositivo.
- [ ] Ejecutar y documentar la prueba técnica antes de elegir stack definitivo.

## Decisiones aún pendientes

No están aprobados el sistema operativo anfitrión, stack, base de datos, motor de control, método de virtualización/emulación, cantidad de dispositivos simultáneos ni funciones de IA local. La prioridad es hardware físico Android; la emulación local solo se incluirá si aporta valor y pasa una prueba técnica.

## Registro

- 2026-10-09: se confirma como objetivo del usuario la paridad funcional con GeeLark en Android, usando hardware local/físico y soluciones gratuitas.
- 2026-10-09: se crea `docs/PLAN_PARIDAD_GEELARK.md` con módulos objetivo, orden de ejecución, riesgos, criterios de aceptación y fuentes iniciales.
