# Manual de usuario — Panel de control PC-MASTER

**Versión:** panel de solo lectura v0.2  
**Estado:** interfaz preparada para API de snapshots; el endpoint backend aún no está implementado ni desplegado. No debe considerarse operativo con Workers reales hasta completar esa integración.

## 1. Abrir el panel

1. Abre la rama de la propuesta en GitHub y descarga la carpeta del panel, o clona/descarga el repositorio.
2. Abre prototypes/master-control/index.html en Edge, Chrome o Firefox.
3. La interfaz intenta consultar GET /admin/v1/status/snapshots en el mismo origen. Si se abre como archivo local, el endpoint no estará disponible y aparecerá “Sin conectar”; es el comportamiento esperado.
4. Para ver la distribución de la interfaz sin equipos reales, pulsa **Ver ejemplo ficticio**. El modo de muestra está separado de los datos reales.
5. Pulsa **Volver a datos reales** para abandonar la muestra y volver a consultar el servicio.

No necesita bibliotecas JavaScript externas. La pantalla no está desplegada ni conectada a PCs Worker.

## 2. Conexión y mensajes de estado

- **Esperando al servicio / Sin conectar:** no se recibieron snapshots reales.
- **Conectado al servicio de solo lectura:** el endpoint respondió correctamente y el contrato básico fue validado en el cliente.
- **Autenticación/autorización requerida:** el backend respondió 401/403. Inicia sesión por el mecanismo oficial del sistema; la interfaz no pide ni guarda tokens.
- **Servicio no disponible:** el backend devolvió error, timeout o JSON inválido. No se reemplazan los datos reales por ejemplos automáticamente.
- **Ejemplo ficticio:** datos locales solo para revisar navegación; no son evidencia del estado de equipos.

El endpoint definido está documentado en docs/contracts/MASTER_CONTROL_STATUS_API_V1.md. Su implementación y las verificaciones de autenticación/autorización aún son una puerta pendiente.

## 3. Navegación

- **Resumen:** contadores derivados de los snapshots recibidos y tabla de nodos.
- **Nodos Worker:** busca por nombre o ID, consulta autorización, salud, heartbeat, versión y capacidades.
- **Módulos:** consulta módulos reportados, estado, versión, fecha y fuente.
- **Auditoría y CI:** muestra el estado de integración y enlaza a GitHub Actions para revisar ejecuciones reales.

Los contadores muestran “—” antes de tener datos reales. No se inventan cifras por defecto.

## 4. Significado de estados

- **Saludable:** estado derivado por el Master con evidencia fresca.
- **Degradado:** hay un problema reportado o derivado.
- **Desconectado:** el heartbeat está obsoleto.
- **Pendiente:** el nodo no está autorizado para aceptar tareas.
- **Revocado:** credencial o autorización revocada.
- **Desconocido:** no hay evidencia suficiente.
- **Fresco / obsoleto / ausente:** estado de frescura del heartbeat.
- **No instalado:** solo debe mostrarse si el contrato de estado tiene evidencia explícita; un módulo ausente no se considera operativo.

La autorización y la salud son campos distintos. Los estados desconocidos no se resuelven automáticamente.

## 5. Consultar y actualizar

Pulsa **Consultar ahora** para hacer un GET al endpoint del mismo origen. La solicitud no contiene mutaciones, se realiza con credenciales de sesión same-origin y desactiva la caché. No hay una URL arbitraria ni un campo para introducir tokens.

Si la solicitud falla, se vacía la lista real para no dejar información obsoleta presentada como actual. El mensaje de estado explica el error.

## 6. Modo de ejemplo

Pulsa **Ver ejemplo ficticio** para inspeccionar la interfaz sin un backend. El ejemplo se genera localmente, está rotulado como ficticio y no se mezcla con la respuesta del servicio. No se guarda en almacenamiento persistente del navegador.

## 7. Seguridad y limitaciones

- El único endpoint de administración consultado por la interfaz es GET /admin/v1/status/snapshots.
- El backend debe autenticar y autorizar al operador y usar una conexión PostgreSQL de solo lectura.
- No hay botones para iniciar, detener, reasignar o ejecutar tareas.
- No ejecuta shell, ADB ni acciones en Workers.
- No habilita reconciliación ni cambia operaciones unknown.
- No guarda tokens, credenciales ni snapshots en localStorage o sessionStorage.
- Los valores remotos se escapan antes de renderizarse.
- La validación de forma JSON en el navegador no sustituye la validación completa del servidor contra el esquema.
- La CI no sustituye la revisión manual de seguridad ni las pruebas autorizadas en hardware.

## 8. Resolución de problemas

**Aparece “Sin conectar” al abrir el archivo local:** normal; el endpoint no se ejecuta dentro del HTML. El backend debe estar instalado y servido en el mismo origen.

**Aparece 401/403:** el servicio requiere autenticación o el operador no tiene permiso. No añadas tokens al HTML ni desactives el control de acceso.

**Aparece 503 o JSON inválido:** el servicio todavía no está listo, o no cumple el contrato. No uses el modo ficticio para tomar decisiones operativas.

**No aparecen nodos:** el servicio devolvió una lista vacía o no hay snapshots autorizados. Un inventario vacío no se interpreta como que todo esté saludable.

## 9. Funciones offline y funciones que requieren conexión

| Función | Offline |
|---|---|
| Abrir el HTML descargado | Sí |
| Navegar por las cuatro vistas | Sí |
| Buscar y filtrar el ejemplo ficticio | Sí |
| Ver ejemplo ficticio | Sí |
| Consultar snapshots reales | No |
| Consultar estado actual de GitHub Actions | Requiere Internet |
| Ejecutar acciones administrativas | No implementado |

## 10. Validación automatizada y accesibilidad

La CI prueba el documento HTML, las referencias DOM, navegación accesible, estado vacío seguro, modo de muestra explícito, escape de valores remotos, sintaxis JavaScript y renderizado con Chrome/Chromium en escritorio y móvil. Esto no equivale a una auditoría WCAG completa ni a una evaluación con lector de pantalla.

## 11. Contrato de datos

Los snapshots individuales siguen docs/contracts/master-worker-status-v1.schema.json. La envoltura HTTP está definida en docs/contracts/MASTER_CONTROL_STATUS_API_V1.md. Debe incluir schema_version 1.0, generated_at y snapshots[] con un límite máximo de 500 elementos. Los datos sensibles, credenciales, logs libres y payloads de tareas quedan excluidos.

## 12. Comparación funcional con GeeLark

GeeLark ofrece un dashboard para cloud phones Android, gestión por grupos, colaboración/permisos y automatización mediante herramientas/API. Esta pantalla está orientada al estado de Workers físicos locales y solo cubre una parte del plano de control. No ofrece paridad funcional con GeeLark. La comparación de brechas debe mantenerse actualizada en el manual técnico.

## 13. Integración con datos reales: pendiente

El proveedor interno de snapshots está en PR #74 y el inventario de módulos en PR #73; ambas propuestas siguen en borrador y sin fusionar. El proveedor actual es un puerto interno de solo lectura por nodo, no una API HTTP de administración. Antes de considerar operativo este panel, falta implementar el endpoint del Master, integrar autenticación/autorización humana, verificar permisos efectivos de PostgreSQL, probar 401/403/503 y payloads inválidos, y completar revisión de seguridad. No desplegar ni probar en PCs físicas sin autorización explícita.
