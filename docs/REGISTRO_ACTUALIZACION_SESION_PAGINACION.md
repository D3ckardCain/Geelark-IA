# Actualización del panel: sesión y paginación

Base: 8e44693569f6af1dca2e4412e60ffc4a2b2904bf.

## Correcciones
- Las consultas de nodos comprueban la generación de sesión y petición después de fetch y después de leer el JSON.
- Una respuesta o un error de una sesión anterior se descarta; tampoco puede desbloquear una consulta nueva ni reemplazar datos de la sesión actual.
- Mostrar el acceso limpia fecha, selección y datos, e invalida consultas anteriores.
- Cambiar filtros de Tareas reinicia automáticamente la paginación al volver a consultar. Mantener los mismos filtros conserva la página.

## Validación
JavaScript real ejecutado con Node.js: respuesta tardía, JSON tardío, error tardío y consulta de una nueva sesión; filtros cambiados vuelven a offset 0 y filtros iguales conservan offset 50.
Se ejecutan suites administrativas Linux/Windows, raíz y PostgreSQL del SHA publicado. Resultados en #139.
La laptop ya abrió el panel HTTPS real y el usuario indicó que lo revisó. Esto no completa por sí solo toda la aceptación #77.
No se modifican permisos ni se activan workers/Android.
