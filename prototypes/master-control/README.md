# Centro de operaciones — vista previa local

Este prototipo permite revisar visualmente el panel de GeeLark-IA sin instalar dependencias ni conectar sistemas reales.

## Abrirlo en Windows

1. En GitHub, abre `prototypes/master-control/index.html`.
2. Usa **Raw** y guarda el archivo como `index.html`, o descarga el repositorio como ZIP y extrae la carpeta.
3. En el Explorador de archivos, abre `index.html` con Edge, Chrome o Firefox.
4. Recorre **Resumen**, **Nodos Worker**, **Módulos** y **Auditoría y CI**. Prueba las búsquedas y filtros.
5. Usa **Descargar resumen** para guardar el informe ficticio de ejemplo.

## Alcance real

- Es una maqueta estática con datos ficticios; no representa el estado real de equipos.
- No necesita Internet después de descargar el archivo y no carga bibliotecas ni recursos externos.
- No llama a GitHub, Cloudflare ni Supabase; no transmite datos ni controla Workers.
- No tiene autenticación real, ejecución de tareas, ADB, shell ni reconciliación de estados `unknown`.
- No se debe usar la maqueta para tomar decisiones operativas.

## Verificación

Las pruebas automatizadas de esta rama comprueban regresiones, renderizado del HTML real en Chrome/Chromium en tamaños de escritorio y móvil, y sintaxis JavaScript. Que la CI pase no equivale a una auditoría WCAG completa ni a pruebas en hardware.

## Siguiente hito visible

Convertir esta maqueta en una pantalla de solo lectura con datos reales exige, antes, integrar de forma segura el proveedor de snapshots, autenticar y autorizar al operador, y comprobar los permisos efectivos de lectura de PostgreSQL. Ese trabajo sigue en las PR #73/#74 y no está desplegado. No introducir credenciales en este prototipo.
