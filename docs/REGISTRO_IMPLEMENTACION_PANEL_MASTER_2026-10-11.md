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
- No se ejecutó una nueva CI para no consumir minutos sin confirmar que no habrá cargos.
- La validación automatizada del HEAD actual está pendiente.
- No se ejecutó en PC-MASTER, no se abrió ningún puerto, no se desplegó ni se fusionó.
- No se han verificado grants en una base real. El proyecto Supabase vinculado aparece inactivo y no se reactivó ni modificó.

## Bloqueos antes de producción
1. Confirmar una base de datos que permita operación real a $0; preferir PostgreSQL local para no depender de una instancia remota.
2. Instalar/configurar el servicio en PC-MASTER y confiar el certificado TLS local.
3. Ejecutar `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql` con una cuenta administradora y después `packages/cluster-master-admin/sql/verify_readonly_role.sql` como `geelark_master_reader`.
4. Ejecutar pruebas automatizadas solo después de comprobar la cuota de Actions.
5. Probar login, sesión, snapshots y logout en la máquina real; realizar revisión de seguridad.

## Coste
No se incorporan APIs de pago ni autenticación SaaS. El workflow de esta API es manual. No se afirma coste cero de proveedores de base de datos externos; PostgreSQL local es la alternativa de coste controlable.
