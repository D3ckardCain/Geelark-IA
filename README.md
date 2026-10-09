# Geelark-IA

Proyecto nuevo que construiremos desde cero, paso a paso. GeeLark será la referencia funcional para las capacidades que decidamos implementar. Este repositorio documenta requisitos y decisiones confirmados durante este proyecto; no se importará código, arquitectura, datos ni soluciones de proyectos o conversaciones anteriores.

> **Estado actual:** fase A — auditoría funcional de GeeLark y viabilidad de Android virtualizado local. La documentación y matriz están en construcción. No hay módulos implementados ni se ha seleccionado un motor Android.

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
- `docs/PLAN_TRABAJO.md`: fases, dependencias y orden de trabajo.
- `docs/CATALOGO_FUNCIONAL_GEELARK.md`: inventario funcional por módulos, evidencia, adaptaciones y límites.
- `docs/MATRIZ_PARIDAD_GEELARK.md`: requisitos de paridad, estados y pruebas pendientes.
- `docs/INVESTIGACION_FUNCIONAL_GEELARK.md`: fuentes y análisis documental.
- `docs/COMPARATIVA_MOTORES_ANDROID.md`: candidatos Android locales y protocolo de prueba; sin motor seleccionado.
- `docs/MODELO_AMENAZAS_SEGURIDAD.md`: controles de seguridad requeridos, aún no implementados.
- `docs/GUIA_INVENTARIO_EQUIPO.md`: guía opcional para validación final en hardware real.
- `docs/ARQUITECTURA_TECNOLOGICA_PROPUESTA.md`: combinación tecnológica local-first propuesta.
- `docs/decisiones/ADR-001-STACK-PRINCIPAL.md`: decisión inicial de stack y anfitrión de referencia.
- `docs/INVENTARIO_LICENCIAS_COSTE.md`: licencias, costes y restricciones de redistribución.
- `docs/CONTRATO_ADAPTADOR_ANDROID.md`: contrato agnóstico para motores Android.
- `docs/ESPECIFICACION_MOTOR_RPA.md`: diseño de automatización por bloques tipados.
- GitHub Issues: tareas, dudas, incidencias, decisiones y soluciones.

## Decisiones aún no tomadas

El alcance detallado, el inventario de hardware, el sistema operativo/hipervisor, el método para ejecutar Android, la arquitectura, las tecnologías y la capacidad real se decidirán y validarán paso a paso. Las metas preliminares no se consideran promesas de rendimiento.

## Seguridad

No guardar contraseñas, tokens, claves privadas ni otros secretos en el repositorio, commits o incidencias. Las automatizaciones deberán respetar las condiciones aplicables de los servicios y plataformas utilizados.


## Issues principales

- [#3 — Inventario funcional y matriz de paridad](https://github.com/D3ckardCain/Geelark-IA/issues/3)
- [#6 — Completar el catálogo funcional](https://github.com/D3ckardCain/Geelark-IA/issues/6)
- [#7 — Importación selectiva desde Android físico por USB/ADB](https://github.com/D3ckardCain/Geelark-IA/issues/7)
- [#8 — Comparar y validar motores Android locales](https://github.com/D3ckardCain/Geelark-IA/issues/8)
- [#9 — Controles de seguridad local, ADB, RPA e importación](https://github.com/D3ckardCain/Geelark-IA/issues/9)
- [#10 — Recopilar especificaciones del equipo anfitrión](https://github.com/D3ckardCain/Geelark-IA/issues/10)
- [#11 — Validar combinación tecnológica y arquitectura local-first](https://github.com/D3ckardCain/Geelark-IA/issues/11)

