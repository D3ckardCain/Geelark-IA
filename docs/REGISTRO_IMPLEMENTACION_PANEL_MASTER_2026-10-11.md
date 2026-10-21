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

## Incidencia y correcciones de arranque/cierre de PC-MASTER — 2026-10-14

### Sintoma investigado

La aplicacion parecia permanecer en el estado de inicio y era necesario confirmar que el backend realmente respondia y que el cierre no dejaba procesos o puertos ocupados.

### Cambios implementados y revisados

- Se redirigio la salida estandar y de error del backend a `runtime.log`, conservando entradas anteriores.
- Se sustituyo la comprobacion basada solo en abrir un socket por una solicitud HTTPS local al endpoint de sesion.
- Se incorporo un canal privado por entrada estandar para solicitar el cierre ordenado del servidor Uvicorn mediante `STOP`.
- Se incorporo una alternativa de terminacion del arbol de procesos en Windows cuando la parada ordenada no termina a tiempo.
- La interfaz conserva la referencia al proceso y no se cierra si no puede confirmar la parada.
- Se incorporaron pruebas de regresion para parada ordenada, errores del mecanismo de emergencia, cierre de ventana y registro de salida del backend.

### Evidencia de validacion

- Pruebas combinadas de `packages\cluster-master-admin\tests` y `apps\pc-master-windows\tests\test_pc_master.py`: 39 aprobadas.
- Comprobacion HTTPS local: HTTP 200.
- Prueba de cierre: no quedaron procesos identificados como PC-MASTER/backend y el puerto 8765 quedo libre.
- `git diff --check`: sin errores de formato; solo avisos de conversion LF/CRLF.
- Durante la comprobacion registrada, el numero de lineas del log no aumento por la solicitud de disponibilidad. El log ya contenia entradas historicas que coincidian con patrones de error; no se atribuye su causa sin investigacion adicional.

### Riesgos y tareas pendientes

- La comprobacion HTTPS del lanzador utiliza un contexto que no valida la identidad del certificado. Solo confirma que el endpoint local responde; la validacion TLS del navegador sigue siendo obligatoria.
- Los tests unitarios del cierre no prueban todos los escenarios posibles de un proceso real de Windows. Debe repetirse el ciclo completo tras cambios posteriores.
- Pendiente completar la verificacion del certificado, ACL NTFS, permisos efectivos de PostgreSQL y flujo real de login/logout/snapshots contra la base objetivo.
- Mantener la escucha en loopback. No habilitar acceso LAN como parte de esta correccion.
- No se realizaron commit, push, reset, reversion ni eliminacion de backups durante esta tarea.

### Resultado

**Parcialmente validado:** las pruebas automatizadas y el ciclo local de inicio/respuesta/cierre han pasado. La aceptacion completa de seguridad y de la integracion con la base de datos sigue pendiente.

## Validación local del módulo PC-MASTER — cierre de comprobaciones (2026-10-19)

**Resultado: comprobaciones locales enumeradas completadas para el alcance comprobado.** Esto no equivale a la aceptación completa de producción ni confirma la CI de los cambios locales actuales.

### Comprobaciones aprobadas

- Backend local HTTPS accesible y panel de control con respuesta HTTP 200.
- Endpoint de snapshots protegido: una solicitud sin autenticación respondió HTTP 401, como se esperaba.
- Panel abierto y nodos visibles, confirmado durante la comprobación manual.
- Base SQLite de sesiones accesible después de corregir los permisos de acceso.
- PostgreSQL local accesible; lectura de la tabla de nodos comprobada con el usuario de solo lectura previsto.
- Pruebas del panel Windows: 10 aprobadas, según la ejecución registrada previamente.
- Pruebas del runtime de administración: 14 aprobadas, según la ejecución registrada previamente.
- Prueba específica de heartbeat ausente o antiguo: 1 aprobada en 0,20 segundos.
- Acción «Diagnosticar» de la interfaz: resultado correcto confirmado manualmente por el usuario.

### Límites y pendientes

- La prueba automatizada de heartbeat valida el tratamiento de estados ausentes o antiguos; no demuestra que se haya desconectado físicamente un nodo worker real durante esta comprobación.
- No se declara completada una validación integral de producción ni del flujo completo de autenticación, inicio y cierre de sesión.
- La verificación de CI correspondiente al conjunto más reciente de cambios sigue pendiente de comprobación independiente.
- Antes de la aceptación de producción deben completarse y documentarse las pruebas integrales pendientes, sin considerar las pruebas automatizadas como sustituto de la validación operativa y de seguridad.

### Alcance de los cambios

Esta entrada documenta resultados de validación local. No implica cambios en el código, la configuración, la base de datos, los certificados ni las credenciales.

## Actualización documental y suite completa — 2026-10-20

### Resultados de esta sesión

- Se creó un respaldo actualizado de los cambios locales: `geelark-ia-respaldo-20261020-090130.patch`.
- SHA-256 del respaldo: `B641612BFDFB696960F964BDAC5B3906F68C09E8AF1C925531C6919FE14DCB85`.
- Las pruebas específicas de `apps/pc-master-windows/tests/test_pc_master.py` y `packages/cluster-master-admin/tests/test_runtime.py` terminaron con 24 aprobadas.
- La suite completa del repositorio terminó con 133 aprobadas, 39 omitidas y 0 fallidas en 11,29 segundos.
- `git diff --check` se había ejecutado previamente y no detectó errores de formato.
- Los ocho archivos modificados siguen en el árbol de trabajo sin confirmar. No se aplicó el parche antiguo ni se realizó commit o push.

### Interpretación y límites

Los resultados de la suite completa pertenecen a la ejecución del 20 de octubre de 2026. Las cifras de pruebas de las entradas anteriores se conservan como evidencia histórica de sus respectivas ejecuciones y alcances.

**Estado: validación automatizada local aprobada; aceptación integral de producción pendiente.** Esta ejecución no demuestra por sí sola la confianza TLS en el navegador, las ACL NTFS efectivas, todos los permisos negativos de PostgreSQL ni el flujo completo de autenticación en la instancia objetivo. Mantener el servicio en loopback y completar la lista de aceptación de la issue #77 antes de habilitar acceso remoto o declarar el módulo listo para producción.
