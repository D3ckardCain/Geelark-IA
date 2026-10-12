# Centro de operaciones — panel de solo lectura

## Estado actual

La interfaz ya tiene un adaptador para consultar snapshots reales mediante una API autenticada del mismo origen. **El endpoint backend aún no está implementado ni desplegado**, así que en este momento la pantalla debe mostrar “Sin conectar” y no presentar nodos ficticios como si fueran reales.

## Abrir la interfaz

1. Abre el archivo [index.html](index.html) en GitHub y descarga el HTML completo, o descarga la rama como ZIP.
2. Ábrelo en Edge, Chrome o Firefox. No requiere paquetes ni recursos externos.
3. El panel intenta consultar GET /admin/v1/status/snapshots en el mismo origen. Abrirlo directamente como archivo local no proporciona ese endpoint; la conexión fallará de forma visible.
4. Para probar la navegación visual, pulsa **Ver ejemplo ficticio**. Ese modo está claramente identificado y no representa equipos reales.
5. Pulsa **Volver a datos reales** para salir del modo de ejemplo y volver a intentar la conexión.

## Contrato de integración

Consulta [MASTER_CONTROL_STATUS_API_V1.md](../../docs/contracts/MASTER_CONTROL_STATUS_API_V1.md). El servicio debe autenticar y autorizar al operador, usar un rol PostgreSQL de solo lectura y devolver snapshots conforme al contrato Master/Worker v1. No se deben añadir tokens al HTML ni guardar credenciales en el navegador.

## Seguridad y límites

- El panel solo hace GET al endpoint de snapshots del mismo origen, con credenciales de sesión same-origin y caché desactivada.
- No incluye controles de mutación, tareas remotas, ADB, shell ni reconciliación.
- Los errores 401/403/503 o payloads inválidos no se sustituyen por datos ficticios.
- Los datos recibidos se escapan antes de insertarse en el DOM; no se guardan en localStorage ni sessionStorage.
- Sin conexión, el ejemplo ficticio es navegable; los estados reales requieren servicio y red.
- CI verde no equivale a revisión manual de seguridad ni a validación en hardware.

## Siguiente bloqueo

Implementar y probar el endpoint HTTP en el servicio Master, con autenticación/autorización humana y permisos efectivos de lectura, antes de llamar a esta pantalla operativa. No se ha desplegado ni conectado a PCs físicas.
