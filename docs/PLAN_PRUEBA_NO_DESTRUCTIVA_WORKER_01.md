# Plan de prueba no destructiva: WORKER-01

**Fecha:** 2026-10-09  
**Estado:** propuesta documental; pendiente de revisión y aprobación antes de cualquier instalación.  
**Objetivo:** inventariar el hardware y comprobar la virtualización en WORKER-01 sin instalar ni modificar el sistema del disco interno.

## 1. Decisión técnica provisional

- Usar WORKER-01 (Intel Core i5-11400, 32 GB RAM, NVMe 500 GB) como primer equipo de laboratorio. No usar PC-MASTER para el primer experimento.
- Primera opción de sistema host a evaluar: **Ubuntu Server 24.04.5 LTS**, instalación mínima, por madurez y soporte estándar de seguridad hasta 2029. Comparar con Debian Stable antes de fijar la versión definitiva. La elección no se considera cerrada hasta comprobar los requisitos exactos del motor Android y el hardware.
- Mantener **redroid bloqueado** mientras no exista evidencia reproducible de que la versión concreta evita modificar `/proc/sys/kernel/modprobe` del host.
- Alternativa prioritaria para el primer prototipo Android: una VM QEMU/KVM. Bliss OS es solo candidato; primero hay que verificar compatibilidad de la imagen y las aplicaciones objetivo. Una VM completa mejora el límite de aislamiento frente a compartir kernel, pero no garantiza compatibilidad ni seguridad por sí sola.

## 2. Fase A — preparación sin tocar discos

Antes de arrancar:
1. Descargar la ISO de una distribución Live/Server desde su sitio oficial y verificar el checksum publicado por el proyecto.
2. Crear el USB desde otra computadora, identificando con cuidado el dispositivo USB para no sobrescribir otro disco.
3. Tener disponible teclado, monitor y acceso físico a WORKER-01.
4. Confirmar que no hay discos USB conectados que puedan confundirse con el disco interno.
5. No cambiar BIOS/UEFI ni instalar todavía. Si la virtualización está deshabilitada, registrar el resultado y decidir después si se habilita desde firmware.

El usuario indicó que las cuatro PCs son equipos aislados, dedicados a pruebas y sin datos sensibles. Esto permite experimentación controlada, pero no elimina riesgos de arranque, firmware, kernel, red o pérdida de configuración.

## 3. Fase B — inventario desde un entorno Live

Arrancar en modo “Try”/Live si está disponible; **no seleccionar instalar**. Los comandos siguientes son de consulta y no deben escribir en el disco:

```bash
# Sistema y kernel
uname -a
cat /etc/os-release

# CPU, arquitectura y virtualización
lscpu
grep -m1 -E 'vmx|svm' /proc/cpuinfo || true

# Memoria y discos detectados
free -h
lsblk -o NAME,SIZE,TYPE,MODEL,RO,FSTYPE,MOUNTPOINTS
findmnt

# PCI: CPU gráfica, red y controladores visibles
lspci -nnk

# Módulos KVM ya presentes, si existen
lsmod | grep -E '(^kvm|i915|xe)' || true

# Mensajes relacionados con gráficos y virtualización
dmesg | grep -Ei 'kvm|vmx|i915|xe|drm|firmware' | tail -n 100
```

Notas:
- Que aparezca `vmx` indica que la CPU anuncia Intel VT-x; no demuestra por sí solo que esté habilitado en firmware ni que KVM funcione.
- La GPU integrada exacta y su controlador se deben confirmar con `lspci -nnk`; no asumir que existe aceleración gráfica utilizable solo por tratarse de un i5-11400.
- No ejecutar comandos de particionado, formateo, instalación, actualización de firmware ni escritura en sysctl en esta fase.
- Guardar la salida del inventario en un archivo de texto en otro USB o copiarla manualmente al equipo de desarrollo; no escribir en el NVMe interno.

## 4. Fase C — criterios para aprobar instalación del host

No instalar hasta que:
- Se identifique la CPU y GPU integrada exactas.
- VT-x esté disponible y KVM pueda inicializarse.
- Se elija una versión host soportada y se comprueben los requisitos del motor Android.
- Exista plan de recuperación y se haya comprobado el medio de arranque.
- Se confirme el esquema de disco previsto (usar todo el NVMe solo si el usuario confirma que se puede borrar; no inferirlo del hecho de que el PC sea dedicado).
- Se documente el plan de red: SSH solo desde LAN de administración, firewall activo, sin puertos administrativos/ADB publicados a Internet.

## 5. Fase D — primer prototipo en VM

Tras aprobación e instalación del host:
1. Instalar únicamente paquetes de repositorios oficiales de la distribución.
2. Verificar `/dev/kvm`, permisos y aceleración; no continuar si la VM cae silenciosamente a emulación por software.
3. Descargar una imagen Android/Bliss OS de fuente oficial, verificar hash/firma si el proyecto los publica y documentar licencia/versión.
4. Crear una única VM desechable con recursos limitados, disco virtual separado y red inicialmente aislada/NAT sin puertos entrantes.
5. Medir arranque, uso de RAM/CPU, renderizado, ADB local, reinicio, persistencia y estabilidad.
6. Probar solo aplicaciones legítimas de destino autorizadas por el usuario; no asumir que Play Store/GMS, ARM translation, notificaciones, cámara o apps que detectan emuladores funcionarán.
7. Apagar la VM y validar restauración desde una copia/snapshot antes de intentar varias instancias.

## 6. Seguridad y red

- No publicar ADB (5555) ni la consola de administración de QEMU/libvirt en Internet.
- Preferir administración SSH desde la LAN de gestión, con autenticación por clave y reglas de firewall restrictivas.
- No dar al agente del clúster acceso root irrestricto por defecto; separar control plane, agente y runtime.
- No instalar ni probar redroid privilegiado hasta cerrar el bloqueo de seguridad del issue #27 con evidencia técnica específica.
- La caché de paquetes puede reducir descargas WAN, pero debe respetar firmas, checksums, licencias y versiones; no cachear ni redistribuir automáticamente APKs de terceros.

## 7. Matriz de salida

| Prueba | Evidencia requerida | Criterio |
|---|---|---|
| CPU/VT-x | salida `lscpu`, flags CPU, KVM | VT-x disponible; KVM usable |
| GPU | salida `lspci -nnk`, controlador | controlador identificado; modo gráfico medible |
| RAM/disco | `free -h`, `lsblk` | capacidad confirmada; destino de instalación explícito |
| VM Android | versión/hash de imagen, logs | arranca y reinicia de forma repetible |
| Rendimiento | RAM/CPU/latencia en reposo y carga | margen de recursos; sin estimar densidad antes de medir |
| Red | reglas firewall y prueba desde otro host | ADB y administración no accesibles desde Internet |
| Recuperación | restauración probada | volver a estado conocido sin reinstalar a ciegas |
| Coste | lista de componentes y licencias | cero pagos obligatorios; sin prueba temporal ni tarjeta |

## 8. Límites

- Esta guía no es una autorización para instalar.
- La primera fase solo recopila información en Live USB.
- No se han modificado discos, BIOS/UEFI, Supabase ni el sistema en ninguno de los cuatro equipos.
- No hay todavía una cifra fiable de instancias Android por nodo; solo una prueba de carga puede establecerla.
- La electricidad, el desgaste, la conectividad y el tiempo de mantenimiento siguen siendo costes indirectos aunque no haya cuotas de software.
