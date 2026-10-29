# Panel PC-MASTER: interfaz alineada con la vista previa

Fecha: 2026-10-24

## Qué cambia
- La página que sirve la API en `/` adopta la identidad visual oscura con acentos cian de la vista previa móvil.
- La navegación principal pasa a las pestañas **Nodos**, **Tareas** y **Sistema**.
- La pestaña Nodos muestra únicamente snapshots obtenidos de `GET /admin/v1/status/snapshots` tras validar la sesión local.
- La pestaña Tareas explica que la ejecución todavía no está integrada. No crea ni envía tareas.
- La pestaña Sistema documenta autenticación, exposición local, PostgreSQL de solo lectura, objetivo de coste y enlaces al repositorio/CI.
- Redroid se presenta como planificado y sujeto a adopción, compatibilidad y aprobación del worker.

## Seguridad y límites
- Se conserva el formulario de inicio de sesión, la comprobación de sesión, el cierre de sesión y la revocación del lado servidor.
- No se guardan contraseñas, cookies ni snapshots en `localStorage` o `sessionStorage`.
- Si la API falla, se vacía la lista y se muestra un error; no se sustituyen los datos por trabajadores ficticios.
- Los nodos pendientes no pueden recibir tareas; esta interfaz no ofrece acciones de escritura ni ejecución remota.
- El objetivo de coste sigue siendo 0 USD; no se añade ningún proveedor o servicio externo obligatorio.
- El panel continúa siendo una página web local servida por el backend existente, por lo que la consulta de datos necesita el backend y la base de datos disponibles. El HTML está empaquetado en la aplicación, pero los datos reales no están disponibles offline.

## Pruebas
La prueba `test_panel_matches_preview_tabs_without_fabricating_real_workers` comprueba las pestañas, el estado planificado de Redroid y la ausencia de datos demo preinsertados. También se conservan las pruebas existentes de sesión y política CSP. Ejecutar la suite de `packages/cluster-master-admin/tests` en el entorno del proyecto antes de integrar.
