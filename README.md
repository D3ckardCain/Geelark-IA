# Geelark-IA

Proyecto nuevo que construiremos desde cero, paso a paso. GeeLark será la referencia funcional para las capacidades que decidamos implementar. Este repositorio documenta requisitos y decisiones confirmados durante este proyecto; no se importará código, arquitectura, datos ni soluciones de proyectos o conversaciones anteriores.

> **Estado actual:** inicio y definición del proyecto. No se considera implementada ni validada ninguna función hasta construirla y probarla.

## Reglas de trabajo

- **Objetivo de costo operativo: 0 USD.** No depender de tarjetas obligatorias, pruebas temporales, cobros automáticos, APIs de pago ni servicios críticos que exijan pagos. Verificar límites y condiciones antes de elegir cada dependencia.
- Priorizar software libre, open source, local o autoalojado; reducir dependencias y facilitar migraciones.
- Implementar operación offline o con conectividad limitada cuando sea viable y explicar qué requiere Internet.
- Trabajar en pasos pequeños y explicados. No avanzar al siguiente módulo hasta que el actual esté probado, documentado y aceptado.
- Comparar cada capacidad acordada con GeeLark y registrar resultados y diferencias. No afirmar paridad sin evidencia.
- Usar GitHub para registrar requisitos, preguntas, decisiones, tareas, incidencias, soluciones, pruebas, cambios y documentación.
- Cada módulo debe tener un manual de usuario completo y documentación técnica.
- No dar por confirmado ningún dato de hardware, tecnología o arquitectura hasta verificarlo con el usuario o mediante pruebas.

## Forma de trabajo

1. Aclarar el objetivo y los requisitos con preguntas concretas.
2. Registrar acuerdos y criterios de aceptación en GitHub.
3. Elegir una tarea pequeña y explicar cómo realizarla.
4. Implementar y probar.
5. Documentar el resultado, los problemas y sus soluciones.
6. Comparar la función con GeeLark cuando corresponda.
7. Solo entonces avanzar.

## Documentación

- `docs/ESTADO_PROYECTO.md`: etapa actual, acuerdos y preguntas abiertas.
- `docs/REQUISITOS.md`: requisitos confirmados y criterios de aceptación.
- `docs/PLAN_TRABAJO.md`: fases provisionales.
- GitHub Issues: tareas, dudas, incidencias y soluciones.

## Decisiones aún no tomadas

El alcance detallado, el inventario de hardware, el sistema operativo/hipervisor, el método para ejecutar Android, la arquitectura, las tecnologías y la capacidad real se decidirán y validarán paso a paso. Las metas preliminares no se consideran promesas de rendimiento.

## Seguridad

No guardar contraseñas, tokens, claves privadas ni otros secretos en el repositorio, commits o incidencias. Las automatizaciones deberán respetar las condiciones aplicables de los servicios y plataformas utilizados.
