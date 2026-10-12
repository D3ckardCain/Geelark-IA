# Registro de implementación: panel PC-MASTER

Fecha: 2026-10-11. PR: #76 (borrador).

## Avance
- Autenticación local gestionada por PC-MASTER; no se usa proveedor externo.
- Panel HTML servido en el mismo origen, login/logout y API de snapshots de solo lectura.
- Sesiones locales SQLite con token opaco, hash PBKDF2 para contraseña y cookie protegida.
- Arranque TLS con loopback por defecto; bind remoto bloqueado salvo override explícito.
- Rol PostgreSQL dedicado `geelark_master_reader`, SQL de creación y script de verificación de privilegios.
- Corregida consulta del provider: la columna real es `health_state`; se proyecta como `reported_health_state` para el contrato del snapshot.
- Añadidas pruebas para consulta SQL sin base de datos y para bloquear el bind remoto.

## Estado de validación
- Una ejecución anterior aprobó 10 pruebas, pero corresponde a un commit anterior a la integración final del panel/runtime y a las pruebas recientes.
- Se amplió el workflow de integración existente para ejecutar los tests administrativos y comprobar el rol de solo lectura en PostgreSQL desechable.
- CI aprobada en el HEAD `8e0b47c564a0c4db287c01b62878f810f7f2ade4`: 33 tests de persistencia, 12 de guardia, 54 de autenticación de agentes, 20 de API administrativa, verificación de grants y `pip check`. [Ejecución 38186772500](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38186772500).
- Advertencia no bloqueante: deprecación del uso de `httpx` en `starlette.testclient`; se registra para resolver en una actualización posterior.
- No se ejecutó en PC-MASTER, no se abrió ningún puerto, no se desplegó ni se fusionó.
- No se han verificado grants en una base real. El proyecto Supabase vinculado aparece inactivo y no se reactivó ni modificó.

## Bloqueos antes de producción
1. Confirmar una base de datos que permita operación real a $0; preferir PostgreSQL local para no depender de una instancia remota.
2. Instalar/configurar el servicio en PC-MASTER y confiar el certificado TLS local.
3. Ejecutar `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql` con una cuenta administradora y después `packages/cluster-master-admin/sql/verify_readonly_role.sql` como `geelark_master_reader`.
4. Revisar la ejecución del workflow de integración que incluye tests administrativos y verificación de grants; después probar el flujo en PC-MASTER.
5. Probar login, sesión, snapshots y logout en la máquina real; realizar revisión de seguridad.

## Coste
No se incorporan APIs de pago ni autenticación SaaS. Los tests administrativos usan el workflow de integración existente, sin crear un workflow paralelo. No se afirma coste cero de proveedores de base de datos externos; PostgreSQL local es la alternativa de coste controlable.


## Revisión de seguridad adicional
- El SQL de preparación crea el rol dentro de un bloque DO usando ejecución dinámica, evitando depender de soporte de comandos DDL estáticos en PL/pgSQL.
- El inicializador de credenciales restringe ACL NTFS del directorio y del archivo en Windows; si no puede aplicar la ACL al archivo, lo elimina y falla cerrado.
- El script de prueba de grants es `packages/cluster-master-admin/sql/verify_readonly_role.sql` (no ejecutar como administrador: debe ejecutarse como el rol lector).
- Las pruebas del HEAD citado finalizaron correctamente. El último cambio de documentación posterior quedó en `47ef79d4d2ef873af6a72b64e9b799416f23d898`; no cambia el código ejecutado por CI. La siguiente actualización de código deberá volver a validarse.
