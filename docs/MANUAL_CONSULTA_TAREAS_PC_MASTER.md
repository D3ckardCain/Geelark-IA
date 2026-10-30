# Manual — Consulta de tareas en PC-MASTER

## Alcance
La pestaña Tareas consulta la bandeja real mediante GET /admin/v1/tasks, con sesión local válida. No crea, reclama, acepta, reintenta, cancela ni ejecuta tareas.
Se conservan Windows para PC-MASTER, Debian 13 para workers y redroid como motor previsto. Esta implementación no despliega servicios ni modifica una base real.

## Uso
1. Abre Tareas: se consulta la primera página de metadatos.
2. Introduce opcionalmente el UUID de un worker y elige un estado. Pulsa Aplicar filtros para volver a la primera página.
3. Usa Anterior/Siguiente para recorrer páginas de 50 registros, ordenadas por fecha de creación y UUID descendentes.
4. Pulsa el identificador de una tarea para abrir su detalle. Cerrar detalle elimina la selección.
5. Actualizar tareas vuelve a consultar la página actual.

Los estados disponibles son en cola, entregada, aceptada, en curso, completada, rechazada, fallida, desconocida y cancelada. Son estados persistidos; no prueban por sí solos actividad física ni aceptación del módulo Android.

## Datos visibles
IDs de tarea/operación/worker/instancia, epoch, estado, intentos de entrega, fechas y código de error acotado.
El resultado visible es estado y código de error. Se omiten deliberadamente payload y result_summary porque pueden contener datos de aplicaciones o secretos.
No hay listado de órdenes, tokens, logs libres ni credenciales. Los datos no se guardan en el navegador.

## Permisos y preparación
Reaplicar el script MASTER_ADMIN_READONLY_ROLE.sql como administrador sobre la base elegida tras instalar la migración 0005, y verificar con verify_readonly_role.sql conectado como lector.
El lector conserva SELECT de nodes y obtiene SELECT exclusivamente de trece columnas de metadatos de agent_tasks. No recibe SELECT de la tabla completa, payload, result_summary ni permisos de escritura.
Estos cambios de permisos solo se ejecutan automáticamente en PostgreSQL desechable de CI; no se aplican a la base del usuario desde esta sesión.

## Límites y errores
- La API permite páginas de 1 a 100 registros; la pantalla usa 50. Offset máximo 10000 (hasta 10050 registros mediante la pantalla). Filtra por worker/estado para acotar historiales mayores.
- La paginación no congela la base: nuevas tareas pueden desplazar registros entre páginas. No es una exportación histórica consistente.
- No se obtiene un conteo total. La pantalla muestra página y cantidad recibida.
- 401/403: se limpia la bandeja y se solicita sesión.
- Fallo de servicio: se elimina el listado anterior y se muestra error, sin inventar tareas.
- UUID o estado inválidos: se rechazan antes de consultar PostgreSQL.
- Sin Internet funciona mientras el Master y PostgreSQL locales estén disponibles; consultar GitHub requiere Internet.
- La aceptación manual Windows sigue pendiente en #77 y redroid sigue bloqueado por #27.

## Validación
Pruebas API de sesión/revocación, filtros parametrizados, límites, paginación y sanitización; PostgreSQL real con lector de columnas y rechazo de payload/resultados/escrituras; JavaScript de filtros, detalle, escape y respuesta tardía tras perder sesión. Resultados del SHA publicados en #139.
