# Inventario de licencias y coste — GeeLark-IA

**Actualizado:** 2026-10-22  
**Estado:** inventario de alcance activo; pendiente verificar versiones/digests exactos antes de distribuir o desplegar.  
**Objetivo obligatorio:** 0 USD en software y servicios esenciales.

## Criterios

- Sin cuota obligatoria, tarjeta ni prueba temporal.
- Registrar licencia, versión, procedencia, dependencias transitivas, coste, límites y condiciones de redistribución.
- No asumir que código abierto autoriza redistribuir imágenes Android, APK, marcas o contenido.
- Fijar versiones y hashes; evitar etiquetas flotantes en pruebas reproducibles.
- No declarar una dependencia aprobada para producción sin revisión y prueba.

## Componentes dentro del alcance actual

| Componente | Uso | Estado/coste | Verificación pendiente |
|---|---|---|---|
| Python | Lanzador Windows y servicios locales | Sin cuota de licencia | Fijar versión por entorno y auditar dependencias transitivas |
| FastAPI | API local de PC-MASTER/servicios | MIT; sin cuota obligatoria | Revisar versiones y dependencias en lockfile |
| Pydantic | Validación de contratos/mensajes | MIT; sin cuota obligatoria | Fijar versión compatible y auditar transitivas |
| PostgreSQL | Persistencia transaccional propuesta para el clúster | PostgreSQL License; sin cuota de software | Validar migraciones, operación local, coste de almacenamiento y pruebas de concurrencia |
| Debian 13 | Sistema base previsto de PC-WORKERS | Software libre; sin cuota obligatoria | Fijar imagen/repositorios, versión de kernel y política de actualizaciones |
| redroid | Runtime Android previsto en workers Linux | Código principal Apache-2.0 según repositorio; imágenes/componentes requieren revisión individual | Verificar etiqueta/digest, licencia de componentes, procedencia y bloqueo de seguridad #27 |
| redroid kernel modules | Funciones Binder/BinderFS y módulos requeridos según kernel | Repositorio de módulos indica GPL-2.0 | Confirmar si hacen falta módulos adicionales y compatibilidad exacta del kernel |
| Runtime de contenedores | Ejecutar redroid en worker | No aprobado para despliegue hasta completar revisión | Elegir versión y fuente oficial; verificar licencia, capacidades y seguridad |
| HTTPS/CA local | Transporte privado de agentes | Sin proveedor cloud obligatorio | Documentar generación, rotación, revocación y recuperación |
| pytest | Pruebas locales reproducibles | Open source; sin cuota obligatoria | Fijar versión y evitar CI redundante para conservar el objetivo $0 |

## Controles de coste

- No usar servicios cloud de teléfonos como dependencia operativa.
- No usar APIs comerciales obligatorias para administración, automatización o captura.
- Descargar artefactos una vez y distribuirlos por LAN cuando la licencia lo permita.
- Revisar cuotas, almacenamiento, ancho de banda, minutos CI y límites antes de activar cualquier servicio.
- Ejecutar pruebas pesadas localmente cuando sea viable; no lanzar workflows solo para repetir resultados ya documentados.

## Bloqueo

redroid no está aprobado para hardware físico. La issue #27 (https://github.com/D3ckardCain/Geelark-IA/issues/27) debe contener evidencia de mitigación para la imagen exacta, privilegios mínimos, ADB restringido y recuperación antes de cualquier arranque.

## Registro de cambios

- 2026-10-22: se limita el inventario a componentes dentro del alcance actual; las propuestas de UI/ejecución que no forman parte del stack vigente dejan de presentarse como candidatas.