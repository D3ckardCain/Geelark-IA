# Manual de usuario — Panel de control PC-MASTER

**Versión:** prototipo 0.1  
**Estado:** maqueta local con datos ficticios. No es todavía el panel operativo de la aplicación.

## 1. Abrir el prototipo

1. Abre el repositorio GeeLark-IA en GitHub.
2. En la rama de la propuesta, abre `prototypes/master-control/index.html`.
3. Usa la opción de visualizar/descargar el archivo y ábrelo en un navegador moderno. También puedes clonar la rama y abrir directamente el archivo en Firefox o Chromium.
4. No se necesita instalar paquetes ni tener conexión a Internet para utilizar la maqueta una vez guardado el archivo.

## 2. Aviso de demostración

La franja superior indica que todos los datos son ficticios. No existe conexión con las PCs Worker, la base de datos ni GitHub. No uses los estados mostrados para tomar decisiones operativas.

## 3. Navegación y accesibilidad

La navegación marca la vista activa con `aria-current="page"`, las tablas tienen títulos accesibles y encabezados que identifican sus columnas, y los iconos decorativos se ocultan a lectores de pantalla. Los controles muestran un indicador de foco para navegación con teclado.

## 3.1 Navegación

- **Resumen:** indicadores globales, nodos de muestra, alertas y puertas de validación.
- **Nodos Worker:** busca por nombre/rol y filtra por estado.
- **Módulos:** busca por nombre o nodo y filtra por estado operativo.
- **Auditoría y CI:** muestra resultados de ejemplo, distingue CI de revisión manual y validación física, y permite descargar un resumen de la muestra.

## 4. Significado de estados

- **Saludable:** la muestra considera reciente la telemetría y sin fallos reportados.
- **Degradado:** hay datos recientes, pero una comprobación presenta problemas.
- **Desconectado:** no llegó un heartbeat dentro del umbral de ejemplo.
- **Pendiente:** el nodo no está autorizado para aceptar tareas.
- **Desconocido:** no hay evidencia suficiente para determinar el estado.
- **No instalado:** no existe evidencia de que el módulo esté instalado.

En el sistema real, estos estados deberán derivarse de contratos y políticas versionados. No deben calcularse solo con valores visuales.

## 5. Actualizar la demostración

El botón **Actualizar demo** solo cambia la hora mostrada en pantalla. No consulta la red ni actualiza datos reales.

## 6. Descargar el resumen de auditoría

En la vista **Auditoría y CI**, pulsa **Descargar resumen**. El navegador descargará un archivo de texto con la síntesis de demostración. El archivo no contiene resultados nuevos ni credenciales.

## 7. Seguridad y limitaciones

- No hay botones para iniciar, detener ni reasignar instancias.
- No ejecuta shell, ADB ni tareas.
- No modifica el sistema operativo ni los agentes.
- No almacena credenciales ni realiza peticiones HTTP.
- La maqueta no reemplaza la auditoría de seguridad.
- CI aprobada no significa que el código haya sido validado en hardware.
- Las operaciones con estado `unknown` no se resuelven automáticamente.

## 8. Resolución de problemas

**La página se ve sin estilos:** comprueba que abriste el archivo HTML completo y que el navegador no lo truncó al guardarlo.

**No veo nodos reales:** es el comportamiento esperado; el prototipo usa datos ficticios.

**El botón Actualizar demo no cambia el estado de los nodos:** solo actualiza el reloj visual, no simula una conexión real.

**No se descarga el resumen:** permite descargas para el archivo local en el navegador e inténtalo de nuevo.

## 9. Funciones offline y funciones que requieren conexión

| Función | Offline |
|---|---|
| Abrir la maqueta guardada | Sí |
| Navegar, filtrar y buscar datos ficticios | Sí |
| Descargar resumen ficticio | Sí, si el navegador permite descargas locales |
| Consultar Workers reales | No en esta maqueta |
| Consultar PR/issues/CI en vivo | No en esta maqueta |
| Ejecutar acciones administrativas | No implementado |

## 10. Estado de validación y límites de accesibilidad

Se añadieron comprobaciones estáticas para la vista activa, los encabezados de columnas, los iconos decorativos y el indicador de foco. Estas pruebas no sustituyen una evaluación con lector de pantalla ni una auditoría WCAG completa.

## 11. Estado de validación

Este manual describe el prototipo visual. Antes de considerarlo módulo operativo hacen falta contrato de datos, servicio local de lectura, autenticación/autorización, pruebas automáticas, persistencia de snapshots, revisión de seguridad y validación autorizada.
