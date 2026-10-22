# Guía de limpieza manual del experimento QEMU + Android-x86 en WSL2

**Estado:** preparado para ejecución manual del usuario. No ejecutar automáticamente ni eliminar nada desde GitHub.

## Objetivo

Retirar el experimento descartado de QEMU + Android-x86 + VNC, sin afectar el proyecto GeeLark-IA, la distribución Debian13 de WSL2 ni otros servicios.

## Alcance conocido

- Distribución WSL: `Debian13`.
- ISO de prueba: `/var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso`.
- Se inició QEMU para Android-01 y se configuró VNC en `127.0.0.1:5900`.
- Se instalaron componentes de QEMU y TigerVNC durante el experimento; antes de desinstalarlos se debe consultar la lista real de paquetes.
- La ISO no llegó a instalar Android en un disco virtual persistente según el estado registrado.
- El código y la documentación del proyecto en GitHub se conservan; la ruta QEMU queda retirada como estrategia.

## Reglas de seguridad

1. No borrar ni reinstalar la distribución `Debian13`.
2. No borrar la carpeta del repositorio GeeLark-IA ni sus entornos de desarrollo.
3. No ejecutar comandos generales como `wsl --unregister Debian13`, `apt autoremove -y` sin revisar, ni eliminar directorios completos de `/var/lib/geelark-ia`.
4. Detener únicamente el proceso QEMU de la prueba; confirmar el comando/PID antes de enviar una señal.
5. Borrar la ISO solo después de comprobar la ruta exacta.
6. Desinstalar paquetes solo después de revisar qué paquetes se instalaron y cuáles son dependencias de otros usos.
7. El módulo KVM del kernel de WSL no se debe desinstalar como parte de esta limpieza.
8. No se debe limpiar ningún otro experimento, imagen o paquete no relacionado.

## Procedimiento manual

### 1. Confirmar distribución y localizar procesos de prueba

Desde PowerShell:

```powershell
wsl.exe -l -q
wsl.exe -d Debian13 -u root -- sh -lc 'pgrep -af qemu || true'
```

Revisa la línea completa de cada proceso. Si el proceso no corresponde claramente al Android-01 de esta prueba, no lo detengas.

### 2. Detener solo el QEMU de prueba

En Debian13, usa el PID exacto confirmado en el paso anterior. Primero solicita terminación normal:

```sh
kill PID_CONFIRMADO
```

Sustituye `PID_CONFIRMADO` por el número real; no escribas literalmente ese texto. Comprueba después:

```sh
pgrep -af qemu || true
```

Solo si el mismo proceso de prueba sigue activo, verifica de nuevo su PID y utiliza `kill -TERM PID_CONFIRMADO`. No uses `killall qemu` ni mates todos los procesos Python.

### 3. Confirmar y eliminar únicamente la ISO experimental

```sh
ls -lh /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso
sha256sum /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso
```

Si la ruta coincide exactamente con la ISO Android-x86 9.0-r2 de esta prueba y deseas retirarla, elimina solo ese archivo:

```sh
rm -- /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso
```

No borres el directorio `/var/lib/geelark-ia` ni otros archivos de `images`.

### 4. Identificar paquetes instalados relacionados con la prueba

```sh
dpkg-query -W -f='${binary:Package}\t${Version}\n' 'qemu*' '*tigervnc*' '*tightvnc*' 2>/dev/null || true
```

Revisa el resultado antes de desinstalar. Si QEMU u otro paquete se utiliza para otro trabajo, consérvalo. Si decides retirar un paquete, elimina solo los nombres confirmados como instalados y pertenecientes a esta prueba, sin `-y` en la primera ejecución para revisar el resumen de APT:

```sh
sudo apt-get remove NOMBRE_DE_PAQUETE
```

No ejecutes `autoremove` hasta revisar individualmente qué propone retirar; no es necesario para completar la limpieza del experimento.

### 5. TigerVNC en Windows

Comprueba **Configuración de Windows → Aplicaciones → Aplicaciones instaladas** y busca TigerVNC. Desinstálalo solo si la entrada corresponde al visor instalado para esta prueba y no lo necesitas para otra tarea. No elimines clientes VNC distintos.

### 6. Verificación final

```powershell
wsl.exe -d Debian13 -u root -- sh -lc 'pgrep -af qemu || true; test ! -e /var/lib/geelark-ia/images/android-x86_64-9.0-r2.iso && echo "ISO de prueba retirada" || echo "ISO todavía presente"; dpkg-query -W -f="${binary:Package}\t${Version}\n" "qemu*" "*tigervnc*" "*tightvnc*" 2>/dev/null || true'
```

Registra en el Issue #8 de GitHub qué se retiró, qué se conservó y cualquier error. No marques la limpieza como terminada hasta revisar los resultados.

## Después de la limpieza

La investigación del motor Android continúa por separado: validar primero AOSP Cuttlefish en hardware Debian físico, con pruebas progresivas de 1, 2, 4 y 6+ instancias, midiendo estabilidad, CPU, RAM, almacenamiento, arranque, aislamiento y control desde PC-MASTER. Redroid permanece bloqueado por la revisión de seguridad del Issue #27. La limpieza local no instala ni aprueba ningún motor alternativo.
