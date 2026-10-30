# Aviso de conexión al cerrar sesión

En la revisión local de 9bf77cf se confirmó que salir eliminaba datos y sesión, pero conservaba el aviso anterior Master conectado / snapshots recibidos hasta recargar.

Mostrar el acceso ahora reemplaza el chip y el aviso por Sesión no iniciada e indica que hay que autenticarse para consultar el estado actual. Se conserva la limpieza de datos y el descarte de respuestas pendientes.

La regresión JavaScript comprueba el texto y la clase del aviso después del cierre, además de la protección frente a respuestas antiguas. Los resultados por SHA se registran en #139.

El nuevo inicio de sesión del usuario se comprobó en navegador: botón Cerrar sesión visible, Master conectado y una fila del fixture. La corrección visual requiere actualizar y reiniciar la laptop; no se modifica su proceso abierto automáticamente.
