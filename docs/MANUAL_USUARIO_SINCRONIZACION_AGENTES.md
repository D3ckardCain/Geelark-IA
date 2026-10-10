# Manual de usuario: sincronización de recibos del agente

## 1. Estado del módulo

Este módulo es una pieza interna de software para desarrolladores y operadores del clúster. El código y sus pruebas están en revisión en el PR borrador https://github.com/D3ckardCain/Geelark-IA/pull/56.

**Importante:** todavía no existe un comando de usuario, pantalla de configuración ni instalador que active esta función en las PCs. Este manual explica cómo debe operarse cuando se integre en el proceso del agente; no significa que ya esté desplegada. No instalar ni conectar nodos físicos como parte de esta fase.

## 2. Para qué sirve

Cuando el agente ya guardó un recibo de progreso o resultado en el journal local SQLite, el sincronizador intenta enviarlo al controlador por el transporte HTTPS existente. Si no hay conexión, el recibo permanece local para volver a intentarlo más tarde.

El sincronizador no crea tareas, no las reclama, no ejecuta aplicaciones Android, no utiliza ADB ni shell y no abre puertos de escucha.

## 3. Procedimiento previsto al iniciar el agente

Estos pasos corresponden a la integración del software, no a comandos que el usuario pueda ejecutar hoy:

1. Inicializar el journal SQLite local usando una ruta persistente y permisos privados.
2. Configurar el cliente HTTPS con la dirección privada del controlador, la CA local de confianza y validación de certificado/nombre del servidor. Mantener un timeout de red finito.
3. Obtener la credencial del nodo desde un almacén protegido del sistema operativo; no escribirla en el código, archivos de configuración compartidos ni registros.
4. Construir el runtime del transporte con el journal, cliente y credencial.
5. Crear AgentReceiptSyncLifecycle con un tamaño de lote entre 1 y 1000. El valor predeterminado es 100.
6. Llamar a start() una sola vez durante el arranque. El sincronizador intenta enviar los recibos pendientes en un hilo separado.
7. Mantener el heartbeat y la publicación de capacidades en un ciclo independiente; un fallo de sincronización no debe detener ese ciclo.
8. Conectar el detector de red para que llame a notify_reconnected() al confirmar que volvió la conectividad.
9. En el apagado ordenado, llamar a stop(timeout=5). Si devuelve False, el hilo no terminó en el plazo indicado; registrar el evento con un código genérico y no afirmar que terminó limpiamente.

## 4. Comportamiento esperado

| Situación | Comportamiento |
|---|---|
| Arranque con recibos pendientes | Intenta sincronizarlos inmediatamente |
| Controlador responde HTTP 2xx | El runtime registra el ACK en el journal según su contrato |
| Pérdida de red o respuesta no exitosa | Mantiene el recibo pendiente y aplica reintentos con backoff y jitter |
| Lote completo entregado | Continúa con el siguiente lote acotado |
| Cola vacía | Espera una notificación de reconexión; no hace sondeo continuo |
| Recuperación de conectividad | notify_reconnected() despierta el sincronizador |
| Apagado ordenado | Solicita detener el hilo y espera hasta el timeout configurado |
| Callback de telemetría falla | No debe impedir que el hilo continúe con los reintentos |

## 5. Qué funciona sin Internet o sin controlador

**Puede funcionar localmente:**
- Guardar recibos en el journal SQLite persistente.
- Mantener esos recibos después de reiniciar el proceso, siempre que el archivo y el disco sigan disponibles.
- Preparar recibos para sincronizarlos posteriormente.

**Requiere conectividad con el controlador:**
- Entregar recibos y recibir su confirmación.
- Enviar heartbeat y capacidades.
- Consultar el estado remoto del nodo.
- Consultar o reclamar tareas y cualquier otra operación remota.

No se afirma que el clúster completo funcione offline. Sin red, el estado local puede quedar pendiente o desactualizado hasta la siguiente sincronización.

## 6. Diagnóstico

1. **Hay recibos pendientes:** comprobar conectividad LAN y que la dirección del controlador sea correcta.
2. **Falla TLS:** verificar que se usa HTTPS, que la CA configurada es la correcta y que el certificado del controlador no está vencido y coincide con la IP/identidad validada.
3. **Se repiten los reintentos:** revisar la disponibilidad del controlador y el estado de la credencial por los canales administrativos autorizados. No copiar tokens ni cuerpos HTTP en tickets.
4. **El sincronizador no despierta tras volver la red:** verificar que el detector de conectividad llama a notify_reconnected().
5. **El apagado devuelve False:** no forzar una segunda instancia del sincronizador; revisar si el cliente HTTPS tiene timeout finito y si la llamada en curso se bloqueó.
6. **Aparece RECEIPT_SYNC_FAILED:** es un código genérico deliberado. Consultar métricas operativas sin registrar bearer tokens, contenido sensible del recibo ni cuerpos de respuesta.

## 7. Seguridad y límites

- No guardar ni compartir credenciales en texto claro.
- No desactivar validación de certificado/hostname ni recurrir a HTTP plano para resolver errores TLS.
- No marcar un recibo sincronizado antes de una respuesta HTTP 2xx válida.
- No interpretar un timeout como prueba de que el controlador no recibió la solicitud; la idempotencia del runtime es necesaria para reintentar.
- No habilitar ejecución de tareas, Android, ADB, shell ni listeners mediante este módulo.
- No desplegar en las PCs físicas hasta revisar el conjunto de PRs apilados, validar seguridad e integración y aprobar expresamente una prueba física.

## 8. Validación antes de habilitarlo en un agente real

- [ ] CI del commit exacto aprobado.
- [ ] Integración SQLite→HTTPS→PostgreSQL validada en infraestructura desechable.
- [ ] Pruebas de desconexión, ACK perdido, repetición idempotente y reinicio completadas.
- [ ] Procedimiento de certificados, rotación/revocación de credenciales y permisos locales revisado.
- [ ] Integración con el ciclo real del agente revisada; heartbeat independiente.
- [ ] Backup/recuperación y observabilidad sin secretos probados.
- [ ] Aprobación de seguridad y plan de rollback documentados.
- [ ] Autorización explícita antes de probar en hardware físico.

## 9. Costo

El módulo no requiere una API de pago. Las pruebas de CI utilizan dependencias open source y PostgreSQL desechable. El objetivo de coste obligatorio de software y servicios sigue siendo **$0 USD**; el consumo eléctrico y el hardware local no están incluidos en esa cifra.
