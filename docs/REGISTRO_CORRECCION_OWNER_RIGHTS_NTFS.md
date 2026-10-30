# Corrección OWNER RIGHTS en verificación NTFS

## Evidencia local
Laptop de pruebas i7 de 12.ª generación, 16 GB RAM, SSD M.2 512 GB; Python 3.12 y PostgreSQL 16.15.
La suite administrativa produjo 19 fallos, 37 aprobadas y 6 omitidas. El diagnóstico devolvió UNTRUSTED_WRITE_ACE sobre una carpeta temporal de pytest con ACE de DERECHOS DE PROPIETARIO, SYSTEM y Administradores.

## Causa y corrección
El SID OWNER RIGHTS (S-1-3-4) representa al propietario efectivo. El verificador ya valida ownerSid antes de recorrer las ACE, pero trataba OWNER RIGHTS como escritor ajeno.
Se reconoce esa ACE únicamente después de validar el propietario. No se añade el SID a trustedSids ni se omiten otros escritores.
El verificador permanece de solo lectura y falla cerrado si no puede verificar propietario o ACL. No se modifican permisos de Temp, no se deshabilitan controles y no se cambia la política de sesiones.

## Pruebas
- Windows/NTFS real: propietario válido con ACE OWNER RIGHTS admitido.
- La misma carpeta con OWNER RIGHTS y escritura de Users sigue rechazada.
- PowerShell con ACL en memoria: propietario Users y ACE OWNER RIGHTS rechazados como UNTRUSTED_OWNER.
- Suites administrativas, Windows, raíz e integración PostgreSQL del commit; resultados en #139.

La validación en la laptop del usuario requiere actualizar la rama con fast-forward y repetir las pruebas. No se considera resuelto localmente hasta recibir ese resultado.
