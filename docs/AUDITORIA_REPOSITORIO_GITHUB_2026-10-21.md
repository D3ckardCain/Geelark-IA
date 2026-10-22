# Auditoría de higiene del repositorio GitHub — 2026-10-21

## Resumen ejecutivo

Esta auditoría revisa el estado visible del repositorio `D3ckardCain/Geelark-IA` en GitHub. El objetivo es reducir duplicados, corregir referencias envejecidas y separar trabajo terminado, candidato en rama, integrado y pendiente de aceptación.

**No confundir una PR con código integrado.** La rama predeterminada `main` contiene actualmente README y documentación; no contiene todavía paquetes de implementación, pruebas, migraciones ni workflows. La implementación técnica que se está validando vive en ramas de PR. Por tanto, el código de una PR abierta no se debe describir como integrado ni como producto aceptado.

## Inventario observado

- Rama predeterminada: `main`.
- Árbol recursivo de `main` al inicio de la auditoría: 28 archivos de texto/Markdown contando README y documentos; no aparecen `.github/workflows/`, `packages/`, `db/`, `tests/` ni `prototypes/`.
- Issues abiertos encontrados en la consulta inicial: 43; el Issue #2 se cerró como completado tras confirmar que el alcance/reglas generales están documentados. Issues abiertos restantes en la instantánea: 42.
- PR abiertas encontradas antes de esta limpieza: 32.
- PR cerradas durante esta auditoría por duplicación/supersesión documentada: #25, #90, #99 y #102.
- PR abiertas tras esas cuatro acciones: 28, pendiente de volver a consultar el estado global al terminar la auditoría.
- No se han fusionado PR, eliminado ramas, borrado archivos ni cambiado configuraciones de facturación.

## Acciones realizadas

### PR #102 — cerrada como supersedida

- Era la versión v2 de la corrección de ACL NTFS/ciclo ASGI para la rama PC-MASTER Windows.
- La PR #103 conserva la misma línea de trabajo en v3.
- Cierre: https://github.com/D3ckardCain/Geelark-IA/pull/102

### PR #90 — cerrada como supersedida

- Era la versión inicial de la misma corrección de ACL NTFS/suite integral.
- La PR #103 es la versión posterior.
- Cierre: https://github.com/D3ckardCain/Geelark-IA/pull/90

### PR #99 — cerrada como supersedida

- Era una rama anterior de endurecimiento del panel administrativo basada en el proveedor de snapshots.
- La PR #104 continúa esa línea con correcciones posteriores, pruebas y CI documentada para el HEAD actual.
- Cierre: https://github.com/D3ckardCain/Geelark-IA/pull/99

Los cierres conservan el historial de GitHub; no se borró el trabajo histórico.

### PR #25 — evaluación preliminar del motor Android, cerrada como supersedida

- La propuesta del 2026-10-09 se quedó obsoleta frente a la investigación y comparativa ampliadas, el ADR-002 y el Issue #8.
- La vía QEMU + Android-x86 + VNC está retirada; redroid sigue bloqueado por #27 y Cuttlefish es solo candidato de laboratorio.
- No se fusionó ni se borró la rama histórica.

## PR que deben seguir abiertas por ahora

### PR #104 — panel PC-MASTER autenticado, solo lectura y seguridad Windows

- Sigue en draft y **no está fusionada**.
- Su descripción registra CI verde en el HEAD `3b71c7979f068e5759d263dd9af13f65fc1161fd`: suite raíz 293 passed / 3 skipped, Windows ACL 50 passed / 8 skipped, y transporte HTTPS success.
- La propia PR declara pendientes revisión final de diffs y aceptación manual en el PC-MASTER real: TLS/certificados, login/logout y permisos efectivos contra PostgreSQL local desechable.
- Issue de aceptación manual: #77.
- No marcar el módulo como aceptado solo por CI.

### PR #103 — corrección Windows v3

- Sigue abierta como draft y es la línea actual de corrección de ACL NTFS/ciclo ASGI sobre la aplicación de escritorio Windows (#87).
- Las versiones v1/v2 (#90/#102) se cerraron como supersedidas.
- Mantener #103 abierta hasta verificar su CI/relación final con la rama PC-MASTER; no fusionar automáticamente.

### Otras PR abiertas

Las ramas de transporte, autenticación, persistencia, journal, supervisor y planificador están apiladas entre sí. No se cerraron automáticamente por antigüedad: varias declaran dependencias explícitas y cerrar una podría descartar trabajo que no está integrado en `main`. Se requiere una auditoría de grafo PR por PR, comparando bases, HEAD, archivos y referencias de supersesión antes de consolidarlas.

## Issues: criterio de limpieza

### Issue #2 — cerrado como completado

El acuerdo inicial (desarrollo desde cero, coste obligatorio $0, local/offline cuando sea viable, documentación/manuales, aceptación por módulo y registro en GitHub) ya está documentado en README, requisitos, estado y plan. Las tareas concretas de inventario/paridad siguen en #3, #4 y #6; se cerró únicamente el issue general de arranque.

No se cerró ninguna Issue únicamente por tener casillas marcadas, antigüedad o una prueba verde en una rama sin fusionar.

- #77 debe permanecer abierta: la aceptación manual del panel en el PC-MASTER real sigue pendiente.
- #89 y #91 describen defectos de ACL/ciclo ASGI y de suite pytest. Hay evidencia de corrección candidata y CI verde en #104, pero el cambio no está integrado; revisar de nuevo tras resolver las PR candidatas.
- #20 tiene pruebas de DDL marcadas, pero mantiene casillas abiertas para autenticación/roles y otros pasos; no está completa.
- #8 y #12 permanecen activas: motor Android y contrato agnóstico todavía no están validados en hardware.
- #27 permanece como bloqueo de seguridad para redroid.
- #6 mantiene la auditoría de paridad funcional pendiente; no declarar terminado el catálogo sin contrastar fuentes y registrar evidencias.

## Documentación envejecida detectada

- `docs/ESTADO_PROYECTO.md` y `docs/PLAN_TRABAJO.md` tenían encabezado de actualización del 2026-10-09 aunque había decisiones y pruebas posteriores hasta 2026-10-21.
- Los documentos centrales deben distinguir explícitamente:
  1. contenido presente en `main`;
  2. implementación en PR abierta;
  3. CI verificada para un SHA concreto;
  4. aceptación manual del usuario;
  5. despliegue en hardware físico.
- La vía manual QEMU + Android-x86 + VNC está retirada como estrategia de producto. La limpieza local de WSL sigue pendiente de ejecución manual del usuario; GitHub no puede confirmar que se hayan borrado procesos, ISO o paquetes del equipo.
- Cuttlefish es candidato de investigación, no motor aprobado. redroid sigue bloqueado por #27.

## Siguiente cola de auditoría

1. Revisar todas las PR abiertas en grupos de dependencia (PC-MASTER, snapshots, autenticación/transporte, bandeja/outbox/journal/supervisor, contratos/persistencia, documentos).
2. Cerrar PR adicionales solo cuando la descripción, los comentarios y los diffs demuestren inequívocamente que otra PR las sustituye o que no contienen cambios exclusivos.
3. Revisar Issues abiertos en relación con PR/CI: cerrar únicamente defectos corregidos e integrados; mantener bloqueos manuales y decisiones no resueltas.
4. Comparar documentos de main entre sí para localizar secciones repetidas, fechas contradictorias, nombres de contrato/ADR y enlaces rotos; fusionar contenido solo cuando no se pierda contexto.
5. Actualizar fechas de encabezado solo cuando el contenido se haya revisado realmente, no para ocultar antigüedad.
6. Confirmar al final el recuento de PR/Issues, las acciones realizadas y los pendientes que requieren al usuario.

## Límites de esta auditoría

La consulta de GitHub permite revisar el contenido del repositorio, metadatos, PR e Issues, pero no confirma el estado del PC-MASTER local, los procesos de WSL, la aceptación manual, el panel de facturación de la cuenta ni las pruebas que no tengan artefacto verificable. No se ha usado GitHub Actions para lanzar pruebas adicionales ni se ha habilitado ningún runner de pago.
