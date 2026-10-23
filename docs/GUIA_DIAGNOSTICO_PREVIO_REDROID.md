# Diagnóstico de solo lectura para preparar WORKER-01 antes de redroid

**Estado:** comandos preparados; aún no ejecutados.  
**Objetivo:** recopilar datos del worker después de instalar Debian 13, sin instalar paquetes ni cambiar configuración.  
**Restricción:** no ejecutar el contenedor redroid durante este diagnóstico. La puerta de seguridad de [issue #27](https://github.com/D3ckardCain/Geelark-IA/issues/27) sigue bloqueada.

Ejecutar como usuario normal desde una terminal local de WORKER-01. Estos comandos consultan información; no instalan, borran ni modifican configuración.

```bash
printf '\n===== 1. SISTEMA Y KERNEL =====\n'
cat /etc/os-release
uname -a
uname -m
printf '\n===== 2. CPU Y VIRTUALIZACION =====\n'
lscpu
printf '\n===== 3. MEMORIA =====\n'
free -h
printf '\n===== 4. DISCOS Y ESPACIO =====\n'
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
df -hT
printf '\n===== 5. CONFIGURACION DEL KERNEL: BINDER/BINDERFS =====\n'
if [ -r "/boot/config-$(uname -r)" ]; then
  grep -E 'CONFIG_ANDROID_BINDER_IPC|CONFIG_ANDROID_BINDERFS|CONFIG_ANDROID_BINDER_DEVICES|CONFIG_ASHMEM' "/boot/config-$(uname -r)" || true
else
  echo "No existe /boot/config-$(uname -r); no inferir soporte a partir de esta ausencia."
fi
printf '\n===== 6. MODULOS Y DISPOSITIVOS BINDER YA PRESENTES =====\n'
lsmod | grep -E 'binder|ashmem' || true
ls -ld /dev/binderfs /dev/binder /dev/hwbinder /dev/vndbinder 2>&1 || true
printf '\n===== 7. VALOR ACTUAL DE kernel.modprobe (SOLO LECTURA) =====\n'
cat /proc/sys/kernel/modprobe
printf '\n===== 8. RED E INTERFACES =====\n'
ip -brief address
ip route
printf '\n===== 9. PUERTOS EN ESCUCHA =====\n'
ss -lntup
printf '\n===== 10. RUNTIME DE CONTENEDORES SI YA EXISTE =====\n'
if command -v docker >/dev/null 2>&1; then
  docker --version
  docker info --format 'ServerVersion={{.ServerVersion}} CgroupDriver={{.CgroupDriver}} SecurityOptions={{json .SecurityOptions}}' 2>&1
else
  echo "Docker no está instalado; correcto para una fase de solo diagnóstico."
fi
if command -v podman >/dev/null 2>&1; then
  podman --version
else
  echo "Podman no está instalado."
fi
printf '\n===== FIN: NO SE HA INSTALADO NI INICIADO REDROID =====\n'
```

## Reglas para compartir los resultados

- Revisar la salida antes de pegarla en GitHub; eliminar direcciones públicas, nombres personales o datos que no sean necesarios.
- No incluir contraseñas, tokens, claves privadas, cookies ni archivos de configuración con secretos.
- No ejecutar `modprobe`, `apt install`, `docker run`, cambios de sysctl, firewall, BIOS ni particiones durante esta etapa.
- La salida no demuestra por sí sola que redroid sea seguro ni que el kernel sea compatible. Se debe revisar contra la documentación de la versión fijada.
- Si Debian todavía no está instalado en WORKER-01, no ejecutar este documento en PC-MASTER como sustituto: se trata de un inventario del worker físico.
