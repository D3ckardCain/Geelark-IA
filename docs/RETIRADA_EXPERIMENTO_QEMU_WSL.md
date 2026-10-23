# Retirada controlada del experimento QEMU + Android-x86 + VNC en WSL2

**Estado:** experimento retirado del proyecto; limpieza local pendiente de ejecución manual del usuario.  
**Fecha de preparación:** 2026-10-23  
**Importante:** este documento prepara la limpieza. No se ha detenido ningún proceso local, borrado ningún archivo ni desinstalado ningún paquete desde GitHub.

## Alcance exacto conocido

- Distro WSL usada en el experimento: Debian 13.
- Imagen ISO del experimento: `/var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso`.
- QEMU se ejecutó en WSL. El último diagnóstico histórico vio un proceso con PID 19, pero **el PID puede haberse reutilizado** y debe verificarse de nuevo antes de actuar.
- VNC escuchaba en el puerto TCP 5900.
- TigerVNC Viewer se instaló en Windows y también se probó/instaló en Debian.
- La pantalla negra no se resolvió; esta ruta queda retirada y no debe retomarse.
- No se conocen con certeza los nombres exactos de todos los paquetes instalados ni de los archivos de log. No purgar paquetes ni borrar directorios completos por conjetura.

## Procedimiento manual seguro

### 1. Identificar el proceso actual (solo lectura)

En la terminal de Debian/WSL, ejecutar:

```bash
pgrep -a -f '[q]emu-system|[a]ndroid-x86_64-9.0-r2.iso'
ps -fp 19
ss -ltnp | grep ':5900'
```

- Revisar la línea de comando completa de cada PID encontrado.
- Solo considerar el proceso que sea realmente `qemu-system-*` y que use la ISO indicada.
- Si no existe ese proceso, no intentar terminar el PID histórico 19.
- Si el puerto 5900 pertenece a otra aplicación, no detenerla.

### 2. Detener solo el QEMU confirmado

Después de identificar y verificar el PID real, enviar primero una terminación normal:

```bash
kill -TERM <PID_QEMU_VERIFICADO>
```

Sustituir `<PID_QEMU_VERIFICADO>` por el PID comprobado, no copiar literalmente el marcador. Verificar después con `pgrep -a -f '[q]emu-system|[a]ndroid-x86_64-9.0-r2.iso'` y `ss -ltnp | grep ':5900'`. No usar `kill -9` salvo que el proceso siga activo y se haya vuelto a confirmar su identidad.

### 3. Verificar y eliminar únicamente la ISO del experimento

Primero comprobar la existencia y el tamaño:

```bash
stat /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso
```

Si la ruta corresponde exactamente a la ISO retirada y el usuario confirma su eliminación, borrar **solo ese archivo**:

```bash
sudo rm -- /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso
```

No borrar `/var/lib/geelark-ia`, `/var/lib/geelark-ia/images` ni otros archivos de esas carpetas. No eliminar datos ajenos al experimento.

### 4. Inventariar paquetes antes de desinstalar

En Debian/WSL, listar los paquetes relacionados:

```bash
dpkg-query -W -f='${binary:Package}\n' | grep -Ei 'qemu|tigervnc|vncviewer'
```

Revisar cada resultado y confirmar que se instaló exclusivamente para este experimento antes de desinstalarlo. No ejecutar un `apt purge` con una lista inferida. Si se decide desinstalar, usar solo nombres verificados y revisar el plan de APT antes de confirmar. No ejecutar `autoremove` sin revisar primero qué dependencias propone eliminar.

### 5. Revisar TigerVNC en Windows

- Abrir **Configuración → Aplicaciones → Aplicaciones instaladas**.
- Localizar TigerVNC Viewer y confirmar que es la instalación usada para el experimento.
- Desinstalarlo solo si no se utiliza para otros equipos o proyectos.
- No borrar manualmente carpetas de programas ni claves de registro.

### 6. Verificación final

Después de la limpieza:

```bash
pgrep -a -f '[q]emu-system|[a]ndroid-x86_64-9.0-r2.iso'
ss -ltnp | grep ':5900'
test ! -e /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso && echo 'ISO retirada'
```

Un resultado vacío de `pgrep` y del filtro de puerto es lo esperado solo si no hay otras aplicaciones que coincidan. Si el puerto 5900 sigue ocupado, identificar su proceso antes de tomar medidas. La línea `ISO retirada` solo confirma la ausencia de ese archivo exacto.

## Qué no se debe hacer

- No volver a iniciar QEMU ni Android-x86 para depurar el experimento retirado.
- No borrar directorios completos ni archivos no identificados.
- No desinstalar paquetes por coincidencia de nombre sin revisar su origen y uso.
- No tocar los discos ni la configuración de los WORKERS físicos.
- No instalar redroid todavía: la issue [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27) sigue bloqueando cualquier ejecución física hasta demostrar mitigación sobre una imagen/digest exactos.
- No se requieren copias de seguridad para esta limpieza; limitarse a los artefactos identificados y confirmados.

## Resultado esperado

Una vez que el usuario complete los pasos, QEMU ya no estará ejecutándose para este experimento, la ISO indicada habrá sido retirada si existía y se habrán desinstalado únicamente los paquetes/clientes confirmados como exclusivos de la prueba. Hasta que se ejecute y compruebe manualmente, el repositorio solo registra la preparación de la limpieza, no su finalización.
