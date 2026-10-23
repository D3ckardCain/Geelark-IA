# Fase 2 — Auditoría de integración y deuda pendiente — 2026-10-23

## Resultado de inspección en vivo

Se consultaron metadatos de las PR apiladas, comparaciones de commits y Issues de aceptación. Esta revisión es de solo lectura; no se rebasaron ramas, no se fusionaron PR, no se cerraron Issues y no se lanzaron workflows nuevos.

### Cadena de control

| PR | Estado de merge reportado | Base → HEAD | Hallazgo |
|---|---|---|---|
| #101 | `mergeable=false` | base `da71c77a` → HEAD `b84da938` | Comparación divergente: HEAD 21 commits por delante y 5 por detrás. Debe reconciliarse antes de confiar en CI previa. |
| #74 | `mergeable=true` | base declarada en `f338d63a` → HEAD `df34e00e` | Es descendiente de #101. No integrarla hasta que #101 se resuelva y se valide el nuevo SHA; su base declarada no debe darse por actualizada automáticamente. |
| #52 | `mergeable=false` | base `c5bc7925` → HEAD `20e618aa` | 55 commits por delante, 0 por detrás, pero GitHub informa no mergeable. Esto puede deberse a conflictos de contenido y requiere inspección de diff; la topología por sí sola no resuelve el bloqueo. |
| #57 | `mergeable=true` | base `ea3e0d09` → HEAD `a27922c2` | Depende de #52; no integrar antes de resolver #52. |
| #67 | `mergeable=false` | base `ead30bd4` → HEAD `776a3d54` | Depende de #57; revisar conflictos tras estabilizar las bases anteriores. |
| #85 | `mergeable=true` | base `3bd09e4f` → HEAD `3ef9f065` | Depende de #67; no integrar antes de validar la cadena completa. |

Los SHA abreviados de la tabla sirven para orientación; usar SHA completos en operaciones. La propiedad `mergeable` es una observación de GitHub en el momento de la consulta y puede cambiar.

### CI exacta de #101

- HEAD consultado: `b84da93881f5869e8832e5888e5dce02433e85cc`.
- La consulta de workflows asociados a ese SHA devolvió una lista vacía; los estados combinados también devolvieron una lista vacía. Por tanto, no hay evidencia recuperada de CI de PR asociada a ese SHA en esta consulta.
- La PR incluye cambios reales en runtime, política, handlers, migración, contrato JSON Schema, pruebas PostgreSQL y workflow. No es una limpieza documental segura para integrar a ciegas.
- La comparación base/HEAD devolvió 21 commits por delante y 5 por detrás. Próximo paso: revisar los cinco commits de divergencia y reconciliar los cambios de autorización/transporte, preservar ACK durable y validar el SHA resultante.

### Línea Windows PC-MASTER

| PR | Estado observado | Conclusión |
|---|---|---|
| #104 | abierta, draft, mergeable=true | Mantener separada; falta aceptación manual #77 y verificación local #88. |
| #103 | abierta, draft, mergeable=true | Corregir ACL/runtime y validar contra su ascendencia real antes de integrar. |
| #87 | abierta, draft, mergeable=true | Es el lanzador/configurador, no el panel web. Mantener separados los criterios de aceptación. |
| #48 | abierta, draft, mergeable=true | Transporte HTTPS base de la línea de agentes; no asumir que esté fusionada. |

No usar `mergeable=true` como sustituto de revisión, CI del HEAD exacto, integración de dependencias y aceptación manual.

## Issues: evitar cierres incorrectos

- **#29 sigue abierta correctamente:** quedan pruebas negativas de contratos, unicidad, timestamps, semántica de recursos, compatibilidad de versiones y revisión de seguridad. CI histórica de #16 no satisface estos criterios.
- **#89 sigue abierta correctamente:** la incidencia de ACL de Windows no debe cerrarse hasta integrar y probar la corrección en la pila actual; la suite completa tiene un bloqueo separado por módulos de prueba duplicados en #91.
- **#77 y #88 siguen abiertas correctamente:** la primera requiere aceptación manual del panel Windows; la segunda requiere comparar el acceso directo/artefacto realmente ejecutado en el PC con los artefactos del repositorio. No pueden resolverse solo desde GitHub.
- **#3, #4 y #6 no son duplicados exactos:** #3 coordina la Fase A; #4 fija el método y criterios de paridad; #6 contiene el catálogo detallado.
- **#10, #24 y #92 tienen puertas distintas:** inventario/medición física, caché local verificada y aprovisionamiento Debian. No instalar redroid ni tocar discos mientras falte aprobación de seguridad/procedimiento.
- **#27 continúa siendo bloqueo obligatorio:** no se ha aportado evidencia de mitigación reproducible para un digest concreto.

## Optimizaciones seguras aplicadas a la estrategia

1. No ejecutar re-runs solo para refrescar estados; ejecutar CI únicamente cuando cambie el SHA o exista una regresión concreta.
2. No cerrar ni borrar PR/Issues por antigüedad. Primero identificar cambios exclusivos y destino canónico.
3. Tratar documentación, CI, integración y aceptación física como estados separados.
4. Resolver conflictos por orden de dependencia, sin cambiar bases automáticamente.
5. Mantener redroid como único motor en preparación y coste objetivo 0 USD.

## Siguiente tarea técnica

Inspeccionar los commits que divergen en #101 respecto de la base actual y determinar el conjunto mínimo de cambios que debe preservarse. Luego resolver únicamente #101 y validar CI del nuevo HEAD. No continuar a #74 hasta que #101 tenga base reconciliada y CI relevante en verde.


## Seguimiento de resolución de PR #101 — 2026-10-23

Se realizaron tres correcciones acotadas directamente en la rama `fix/worker-module-inventory-transport-ack-v2` para reducir solapamientos con la base:
- Commit `34004599821454e05b6380ed77f6bfaf50271772`: alinea `tests/test_runtime.py` con las pruebas actuales del contrato ACK (estado/resultado esperados y ACK fail-closed).
- Commit `f3c14ff2fbfd751cb80250b3507a4752f1a788ff`: separa la explicación del fencing ACK en README para conservar el inventario de módulos y reducir conflicto de línea.
- Commit `3123cd15e08c301860389abd00900e26b4c660a2`: reconcilia el comentario del workflow con la base y mantiene una nota separada sobre el fencing.

El código `runtime.py` fue comparado en ambas ramas y su contenido actual coincide. La base tiene siete commits posteriores al ancestro común que tocan workflow, README, runtime y tests. Aunque se reconciliaron los solapamientos visibles de esos cuatro archivos, GitHub sigue informando `mergeable=false` para la PR #101. La consulta de estados y workflows del HEAD `3123cd15e08c301860389abd00900e26b4c660a2` no devolvió checks ni ejecuciones asociados. Por tanto, **no se considera resuelta** ni se ha intentado fusionar.

Siguiente paso seguro: obtener/reconciliar la base exacta y resolver el conflicto restante con una operación Git de merge/rebase que preserve los cambios únicos de la PR; validar el nuevo HEAD con CI antes de quitar el draft. No se deben tratar los checks históricos como evidencia de esta revisión.

## Resolución de la divergencia de PR #101 — 2026-10-23 (seguimiento)

Se sincronizó realmente `feat/agent-https-transport` dentro de `fix/worker-module-inventory-transport-ack-v2` mediante la PR auxiliar #110, fusionada correctamente por GitHub en el commit `32797b1cce9714e332ff1bd9020fab8db482b1d5`. La comparación de ramas posterior confirmó `ahead 30 / behind 0` respecto de `feat/agent-https-transport`; la divergencia de siete commits quedó eliminada. Se restauraron después en el README de la rama los apartados del inventario v1 y el contrato de ACK cercado, commit `043a4e23efd063949577f758eacc326d74bb7ce5`.

Estado posterior: PR #101 sigue abierta y en draft. La consulta de workflows/status para el HEAD `043a4e23efd063949577f758eacc326d74bb7ce5` aún no devuelve ejecuciones ni checks, y el indicador `mergeable` de GitHub osciló tras los últimos cambios; no se declara resuelta hasta reconsultar la mergeabilidad y obtener CI del HEAD exacto. No fusionar #101 ni desplegar a hardware físico mientras falten esas verificaciones.
