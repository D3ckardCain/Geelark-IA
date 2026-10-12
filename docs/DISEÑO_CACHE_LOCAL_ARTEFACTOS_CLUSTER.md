# Diseño preliminar: caché local de artefactos del clúster

**Estado:** propuesta documental; no desplegada ni probada en los equipos físicos.  
**Objetivo económico:** coste obligatorio de operación de 0 USD.  
**Alcance:** reducir descargas repetidas por la conexión a Internet de 10 Mbps simétricos, distribuir versiones aprobadas por LAN Gigabit y conservar trazabilidad. No instala ni configura máquinas.

## 1. Inventario y restricciones conocidas

- PC-MASTER: 16 GB RAM, disco de 500 GB; CPU i7-11700 probable, pendiente de verificar.
- Tres workers: cada uno Intel Core i5-11400 confirmado, 32 GB RAM y SSD M.2 NVMe de 500 GB.
- Sin GPU dedicada confirmada en los cuatro equipos; la iGPU y sus controladores están pendientes de inventario.
- LAN Gigabit; Internet simétrico 10 Mbps.
- No hay sistema operativo instalado todavía.
- Los 2 TB declarados son capacidad bruta distribuida entre cuatro discos, no un volumen único ni almacenamiento redundante.
- El proyecto no debe modificar Supabase ni desplegarse en hardware sin aprobación y plan de recuperación.

## 2. Principio de diseño

La caché es una optimización, no una dependencia crítica. Si el servidor de caché está caído, los nodos autorizados deben poder descargar directamente cuando exista Internet, o usar artefactos ya descargados. La primera descarga desde Internet sigue limitada por los 10 Mbps; la LAN Gigabit solo acelera la redistribución posterior.

No se debe asumir que un artefacto es redistribuible: cada imagen, APK, paquete, imagen Android o archivo de Google debe tener procedencia, licencia y condiciones de uso revisadas. No se debe redistribuir software privativo ni eludir límites de proveedores.

## 3. Capas propuestas

### A. Paquetes del sistema operativo: apt-cacher-ng

Para una base Debian o Ubuntu, evaluar **apt-cacher-ng** en PC-MASTER como caché HTTP de paquetes APT. Es una opción pequeña, empaquetada por Debian y diseñada para que varias máquinas compartan descargas de repositorios. Referencias:
- Debian package information: https://packages.debian.org/stable/apt-cacher-ng
- Debian Handbook, sección sobre cachés APT: https://www.debian.org/doc/manuals/debian-handbook/apt.es.html

Condiciones:
- Solo atender a la LAN; nunca exponer el puerto de caché a Internet.
- Mantener la validación criptográfica habitual de APT; no desactivar comprobaciones de firmas.
- Medir el tamaño real del caché y definir limpieza, límites de disco y alertas.
- Documentar un modo de bypass para que un cliente pueda volver a usar el repositorio oficial si el proxy falla.
- No hacer que el sistema dependa de la caché para actualizaciones de seguridad.

### B. Imágenes OCI y componentes empaquetados: registry local opcional

Si la implementación final usa contenedores OCI, probar la distribución oficial **CNCF Distribution** como caché pull-through para un upstream concreto, o una registry local privada para artefactos construidos por el proyecto. La documentación oficial explica que el modo pull-through almacena localmente contenido solicitado, que puede requerir volver al upstream para comprobar etiquetas cambiantes y que el modo espejo tiene limitaciones. Referencia: https://distribution.github.io/distribution/recipes/mirror/

Condiciones:
- No dar por hecho que todas las imágenes Android se publican en Docker Hub; cada upstream se evaluará por separado.
- No depender de una cuenta de pago ni de una cuota externa para el funcionamiento crítico.
- Mantener caché y repositorio de producción separados.
- Para versiones aprobadas, preferir referencias inmutables por digest SHA-256 en vez de etiquetas mutables como `latest`.
- No usar credenciales de upstream que permitan acceder a contenido privado sin proteger la caché local.
- La limpieza debe respetar los artefactos fijados por despliegues activos y conservar un procedimiento de recuperación.
- Docker Hub y otros upstreams mantienen sus propias políticas y límites; una caché no los elimina para la primera descarga.

### C. Artefactos del proyecto y APK autorizados: repositorio de solo lectura

Mantener una carpeta o servicio interno para versiones **aprobadas**, independiente de la caché automática. Cada entrada debe tener un manifiesto con:
- identificador único y versión;
- URL/fuente original y fecha de adquisición;
- SHA-256 calculado al ingresar y comprobado al servir/instalar;
- arquitectura y plataforma de destino;
- licencia, autorización de redistribución y restricciones;
- revisión/estado: pendiente, aprobada, rechazada o retirada;
- tamaño, notas de compatibilidad y versión anterior para rollback.

El flujo de promoción debe ser explícito: descargar → verificar hash y firma cuando exista → revisar licencia/procedencia → probar en nodo de laboratorio → aprobar → publicar en LAN. Nunca ejecutar automáticamente archivos solo porque llegaron a la caché.

## 4. Ubicación y capacidad

PC-MASTER es candidato inicial por su función de control, pero el disco de 500 GB también tendrá sistema, logs, base de datos local si se decide, imágenes y otros componentes. Por eso:
1. No reservar un tamaño fijo hasta medir espacio libre y estimar el tamaño de las imágenes Android.
2. Separar directorios/volúmenes lógicos para sistema, datos de control, cachés recuperables y artefactos aprobados.
3. Aplicar cuotas/límites por directorio y alertas de uso (por ejemplo, aviso al 70 % y 85 %, con umbrales ajustables tras medición).
4. Mantener al menos una copia de seguridad de configuración, manifiestos y datos irremplazables fuera del disco principal. Los archivos de caché se pueden reconstruir; los manifiestos y la configuración no deben tratarse como desechables.
5. No contar el almacenamiento de los workers como almacenamiento compartido: cada SSD pertenece a su equipo salvo que se configure y pruebe explícitamente otro mecanismo.

## 5. Red y seguridad

- Asignar IP reservada o nombre estable al servicio de caché en la LAN.
- Escuchar únicamente en la interfaz LAN, limitar por firewall a la subred privada y no abrir puertos en el router.
- Los agentes del clúster deben autenticarse contra el plano de control; la caché no sustituye la autenticación del agente.
- Si la registry admite artefactos privados, habilitar autenticación y autorización; nunca exponerla sin protección.
- Registrar solicitudes, errores, espacio usado, aciertos/fallos de caché y procedencia de las promociones.
- Proteger el acceso administrativo y mantener actualizaciones de seguridad.
- No almacenar tokens, contraseñas ni claves dentro de manifiestos o repositorios Git.

## 6. Modo degradado y offline

| Función | Sin Internet, caché disponible | Sin Internet, caché vacía | Servicio de caché caído con Internet |
|---|---|---|---|
| Instalar paquetes ya almacenados | Puede funcionar si metadatos y paquetes requeridos siguen disponibles | No garantizado | Cliente puede usar repositorio oficial por bypass |
| Recuperar imagen OCI ya almacenada | Puede funcionar si el contenido está completo localmente | No | Se puede usar upstream si hay conectividad |
| Descargar artefacto nuevo | No | No | Sí, si el cliente tiene bypass autorizado |
| Instalar APK/imagen Android aprobada y ya replicada | Sí, sujeto a integridad y compatibilidad | No | Sí, desde copia local disponible |
| Actualizaciones de seguridad nuevas | No | No | Sí, por Internet |

El modo offline no garantiza que una aplicación Android funcione sin red: eso depende de la propia aplicación, licencias, autenticación, servicios de Google y sus servidores.

## 7. Pruebas de aceptación antes de instalar en producción

1. En laboratorio, solicitar el mismo paquete desde dos clientes y comprobar que el segundo se sirve desde caché sin repetir la descarga externa.
2. Registrar bytes transferidos por WAN y LAN; no inferir ahorros solo por tiempos.
3. Reiniciar el servicio y comprobar persistencia de los objetos y recuperación limpia.
4. Simular caché llena; verificar que no se llena el disco raíz ni se bloquea el plano de control.
5. Simular caché caída y verificar bypass explícito y seguro.
6. Corromper un artefacto de prueba y comprobar que el hash impide su promoción/instalación.
7. Confirmar que puertos de caché no son accesibles desde Internet.
8. Revisar licencias de cada artefacto Android y contenedor antes de replicarlo.
9. Documentar la recuperación desde cero y medir el tiempo de reconstrucción.
10. Repetir pruebas con una imagen de Android elegida; no asumir que el caché resuelve problemas de GPU, GMS, traducción ARM o compatibilidad de apps.

## 8. Decisiones todavía abiertas

- Sistema operativo definitivo: comparar Debian estable y Ubuntu Server LTS por compatibilidad con el motor Android elegido y mantenimiento.
- Motor Android: redroid, Android Emulator o Bliss OS/QEMU/KVM siguen siendo candidatos; falta prueba física.
- Caché de contenedores: decidir solo después de confirmar formato de distribución, upstream y términos de uso.
- Tamaño de caché: definir después de medir imágenes y espacio libre real.
- Backups: decidir destino físico/local y política de retención antes de instalar.
- GPU/iGPU, virtualización BIOS y rendimiento por instancia: requieren inventario de hardware y benchmark en un único worker de prueba.

## 9. Criterio de coste cero

Las herramientas propuestas son software libre/open source o paquetes de distribución sin licencia de pago obligatoria. Eso no elimina costes eléctricos, de hardware, Internet ya contratado ni obligaciones de licencias de los artefactos de terceros. No se recomienda un servicio cloud de pago ni una prueba temporal. Antes de adoptar cualquier servicio adicional se revisarán sus límites y si exige tarjeta o facturación automática.

## Fuentes primarias

- Debian package: https://packages.debian.org/stable/apt-cacher-ng
- Debian Handbook (español): https://www.debian.org/doc/manuals/debian-handbook/apt.es.html
- CNCF Distribution pull-through cache: https://distribution.github.io/distribution/recipes/mirror/
- CNCF Distribution configuration: https://github.com/distribution/distribution/blob/main/docs/content/about/configuration.md
