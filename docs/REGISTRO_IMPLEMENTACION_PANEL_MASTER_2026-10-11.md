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
- HEAD de código validado: `cfbc8873b052b67dffbebedb5e526da58cd8c81a`; [CI #38190869235](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38190869235) terminó en success.
- 33 pruebas de persistencia, 12 de guardia, 54 de autenticación de agentes y 26 pruebas administrativas aprobadas; `pip check` correcto.
- El workflow existente verifica el rol lector incluso cuando ya existía con `NOLOGIN`, y comprueba que falle si se le concede SELECT sobre una tabla ajena o CREATE/propiedad en otro esquema.
- Se añadió límite PBKDF2 de 600.000–2.000.000 iteraciones; PostgreSQL remoto exige `host=` explícito y `sslmode=verify-full`, detecta `hostaddr` remoto y rechaza DSN `service=`.
- Se sustituyó `httpx` por `httpx2` en las dependencias de prueba; la advertencia de Starlette desapareció en CI.
- No se ejecutó en PC-MASTER, no se abrió ningún puerto, no se desplegó ni se fusionó.
- No se han verificado grants en una base real. El proyecto Supabase vinculado aparece inactivo y no se reactivó ni modificó.
- La CI desechable valida comportamiento automatizado, no las ACL NTFS/TLS de Windows ni la configuración heredada de una base real. La lista de aceptación en Windows está registrada en [issue #77](https://github.com/D3ckardCain/Geelark-IA/issues/77).

## Bloqueos antes de producción
1. Confirmar una base de datos que permita operación real a $0; preferir PostgreSQL local para no depender de una instancia remota.
2. Instalar/configurar el servicio en PC-MASTER y confiar el certificado TLS local.
3. Ejecutar `packages/cluster-master-admin/sql/MASTER_ADMIN_READONLY_ROLE.sql` con una cuenta administradora y después `packages/cluster-master-admin/sql/verify_readonly_role.sql` como `geelark_master_reader`.
4. Completar en Windows la verificación real de ACL NTFS para el directorio, credenciales, PGPASSFILE, SQLite y clave TLS; comprobar certificado/SAN y escucha exclusiva en loopback.
5. Probar login, sesión, snapshots y logout en la máquina real; realizar revisión de seguridad.

## Coste
No se incorporan APIs de pago ni autenticación SaaS. Los tests administrativos usan el workflow de integración existente, sin crear un workflow paralelo. No se afirma coste cero de proveedores de base de datos externos; PostgreSQL local es la alternativa de coste controlable.


## Revisión de seguridad adicional
- El SQL de preparación crea el rol dentro de un bloque DO usando ejecución dinámica, evitando depender de soporte de comandos DDL estáticos en PL/pgSQL.
- El inicializador de credenciales restringe ACL NTFS del directorio y del archivo en Windows; si no puede aplicar la ACL al archivo, lo elimina y falla cerrado.
- El script de prueba de grants es `packages/cluster-master-admin/sql/verify_readonly_role.sql` (no ejecutar como administrador: debe ejecutarse como el rol lector).
- La última CI del código actual finalizó correctamente en `38190571137`. Cualquier cambio posterior en código debe volver a validarse; esta actualización documental no altera la ejecución ya verificada.


## Auditoría estática adicional de privilegios PostgreSQL — 2026-10-12

La revisión del rol `geelark_master_reader` encontró dos huecos que no estaban cubiertos por la comprobación inicial:

1. El verificador comprobaba propiedad de funciones, pero no `EXECUTE` efectivo en rutinas de esquemas de aplicación. Una función `SECURITY DEFINER` con permiso heredado de `PUBLIC` podría ampliar la capacidad del rol aunque no tuviera grants de tabla.
2. `has_table_privilege()` por sí sola no demuestra ausencia de grants a nivel de columna. Podían pasar inadvertidos `SELECT(column)` sobre tablas ajenas o `UPDATE(column)` en `geelark_control.nodes`.

La rama de PR #76 añade controles fail-closed para `has_function_privilege()` y `has_any_column_privilege()`, junto con pruebas negativas PostgreSQL desechables para una función `SECURITY DEFINER`, SELECT por columna en tabla ajena y UPDATE por columna en `nodes`. La documentación del módulo refleja el alcance ampliado.

**Estado:** cambios escritos en la rama `feat/master-control-readonly-api-local-auth`; CI del HEAD actualizado no está confirmada. La PR sigue en borrador y actualmente GitHub indica `mergeable=false` frente a su base apilada; no fusionar ni desplegar. Reconciliar la rama y obtener CI verde antes de declarar validado el verificador. No se han conectado grants reales ni restaurado Supabase.


## Reconstrucción limpia para CI — 2026-10-12

Se creó la rama `feat/master-control-readonly-api-local-auth-clean` desde la base actual `feat/master-status-snapshot-provider-v1` porque la PR #76 quedó `mergeable=false` tras divergir su historial apilado. Se copiaron los archivos específicos del módulo, workflow y prueba de regresión del proveedor sin duplicar la fuente `status_snapshot.py`, que ya existe en la base. El objetivo es obtener CI completo de API Python y verificador SQL en una rama mergeable, sin fusionar ni desplegar.

El SQL coincide exactamente con el verificado por [CI #38193499261](https://github.com/D3ckardCain/Geelark-IA/actions/runs/38193499261). La CI completa de esta rama aún está pendiente. Windows real sigue pendiente por issue #77.
