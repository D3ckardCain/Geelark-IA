# Reconciliación de ASGI y reloj tras bloqueos

## Base y procedencia
Base: `9369dca016ab3040edfba15e5965c03ebc23c645`.
- PR #129: `663da44515a0343118c1d8724bdad6fcd2de1624`.
- PR #130: `9b2072c4721cfa33cc5d7bf988b6ac43cbb92df3`.
- PR #131: `bc23de09dac6e7a088ef8a17b804b35ba9a28f06`.
- PR #132: `d1006ff041f38a89cbdf69a25eed288eded69179`.
Los nueve archivos afectados coinciden byte a byte con las bases correspondientes antes de aplicar las correcciones. Se portan sus blobs exactos, sin fusionar PR ni arrastrar archivos de otras ramas.

## Cambios
- #129: el middleware del transporte reproduce el cuerpo una vez y propaga la desconexión ASGI. La implementación administrativa existente se conserva.
- #130: credencial, lease de instancia, heartbeat y lease de entrega se revalidan con clock_timestamp() después de adquirir los bloqueos; reconciliación usa reloj actual por elemento.
- #131: enrolamiento, autenticación y rotación revalidan vencimientos tras las esperas por filas.
- #132: la asignación rechaza leases vencidas durante la espera y conserva respuesta idempotente de rechazo.
- Se mantienen las pruebas originales de cada corrección, incluidas esperas reales por bloqueos PostgreSQL.

## Validación y límites
Validar este commit mediante suite raíz con PostgreSQL 16, transporte HTTPS, migraciones y pruebas Windows. Los resultados concretos se registrarán en #139 tras revisar Actions.
Se preservan panel, ACL, lanzador y workflows. No se inicia hardware ni Android. Las PR fuente siguen abiertas.
Pendientes separados: lectura administrativa agregada de snapshots, aceptación manual #77 y bloqueo redroid #27.
