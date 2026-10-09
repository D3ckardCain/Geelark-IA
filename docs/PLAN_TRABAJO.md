# Plan de trabajo — Geelark-IA

Plan provisional para un proyecto nuevo. Cada fase se completa con acuerdos y evidencia; no solo con código.

## Fase 0 — Definición conjunta

- [ ] Acordar el objetivo principal de la primera versión.
- [ ] Definir qué funciones de GeeLark son prioritarias.
- [ ] Confirmar el hardware y las restricciones reales.
- [ ] Definir criterios de aceptación y pruebas.
- [ ] Registrar los acuerdos en GitHub.

**Salida:** alcance inicial pequeño, entendido por ambas partes y documentado.

## Fase 1 — Prueba técnica mínima

- [ ] Elegir una sola hipótesis técnica para probar.
- [ ] Preparar un entorno de prueba reversible.
- [ ] Medir compatibilidad, rendimiento, estabilidad y costo.
- [ ] Registrar instrucciones para repetir la prueba y sus resultados.

**Salida:** decisión técnica respaldada por evidencia.

## Fase 2 — Arquitectura mínima

- [ ] Definir componentes solo a partir de los requisitos acordados.
- [ ] Definir autenticación, permisos, logs y manejo de secretos.
- [ ] Documentar fallos, recuperación y límites offline.
- [ ] Revisar costo y posibilidad de migración.

**Salida:** arquitectura mínima aprobada antes de ampliar el alcance.

## Fases posteriores — Construcción por módulos

Para cada módulo:
- [ ] Acordar alcance y criterios de aceptación.
- [ ] Registrar la tarea en GitHub.
- [ ] Implementar un cambio pequeño.
- [ ] Probar el funcionamiento y los errores.
- [ ] Comparar con GeeLark cuando corresponda.
- [ ] Crear manual de usuario y documentación técnica.
- [ ] Registrar resultados, limitaciones y decisiones.
- [ ] Cerrar el módulo antes de empezar el siguiente.

## Reglas para avanzar

1. Explicar el objetivo y por qué se hace.
2. Dar instrucciones paso a paso y señalar qué debe ejecutar el usuario.
3. No asumir acceso a equipos, cuentas o configuraciones que no se hayan confirmado.
4. No afirmar que una acción fue realizada si no existe evidencia.
5. No elegir un servicio antes de revisar que respete el objetivo de costo.
6. Mantener en GitHub los acuerdos, problemas y soluciones.

## No decidido aún

No se eligen todavía hipervisor, stack, base de datos, método Android ni número máximo de instancias. Primero se define el objetivo inicial y se valida la viabilidad técnica.
