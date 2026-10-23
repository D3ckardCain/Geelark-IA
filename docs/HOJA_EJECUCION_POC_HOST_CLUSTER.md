> **No ejecutar sin reconciliación y autorización — 2026-10-22:** Esta hoja pertenece a una rama divergida. Antes de usarla, contrastar con el estado actual de `main`, verificar licencias y obtener autorización específica para el equipo y la operación. No instalar sistemas, borrar discos ni habilitar motores Android por inferencia. QEMU + Android-x86 + VNC está retirado; no hay motor aprobado.

# Hoja de ejecución de la POC del host y nodo Android

**Estado:** plantilla; no ejecutada.  
**Coste obligatorio permitido:** 0 USD.  
**Autorización:** ninguna instalación, cambio de BIOS/UEFI, particionado, borrado de disco ni modificación de hardware está autorizada por este documento.  
**Referencia:** [matriz de decisión](MATRIZ_DECISION_SO_CLUSTER.md) · [evaluación del SO](EVALUACION_SO_BASE_CLUSTER_0USD.md) · [guía de inventario](GUIA_INVENTARIO_EQUIPO.md)

## 1. Identificación de la ejecución

- ID de prueba:
- Issue de GitHub:
- Fecha y hora (con zona horaria):
- Responsable:
- Host de prueba (alias, no número de serie):
- Estado de autorización del propietario: pendiente / concedida para esta prueba específica
- Objetivo y alcance autorizado:
- ¿Se permite borrar el disco? sí / no. Si no, no instalar.
- ¿Existe copia de seguridad verificada? sí / no / no aplica
- Procedimiento de recuperación probado: sí / no

## 2. Puerta previa: no avanzar si algo está pendiente

- [ ] Confirmar por escrito el equipo exacto y la acción autorizada.
- [ ] Confirmar que los datos existentes pueden borrarse o que hay respaldo restaurable.
- [ ] Confirmar la licencia y procedencia de cada imagen, motor y APK.
- [ ] Registrar versión exacta, hash/digest y método de verificación de artefactos.
- [ ] Confirmar que la prueba no necesita tarjeta, prueba temporal ni servicio de pago.
- [ ] Definir red aislada y demostrar que ADB no estará expuesto a la LAN general ni a Internet.
- [ ] Definir cómo detener el proceso y restaurar el estado anterior.
- [ ] Confirmar que el agente de un nodo pendiente solo puede reportar heartbeat/capacidades/estado: no debe recibir tareas ni ejecutar operaciones.

**Cualquier casilla de seguridad sin resolver bloquea la instalación y la ejecución.**

## 3. Inventario de solo lectura

Ejecutar estos comandos únicamente cuando el usuario solicite recopilar inventario. No instalan paquetes ni modifican el sistema. Algunos datos pueden ser sensibles: revisar y redactar salidas antes de subirlas a GitHub.

### Linux

```bash
date -Is
cat /etc/os-release
uname -a
uname -m
lscpu
free -h
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
df -h
lspci | grep -Ei 'vga|3d|display|ethernet|network'
ip -br link
grep -Eoc '(vmx|svm)' /proc/cpuinfo
if test -e /dev/kvm; then echo 'KVM presente'; else echo 'KVM no detectado'; fi
```

Notas:
- No ejecutar `dmidecode`, lectura SMART, comandos con `sudo` ni utilidades adicionales salvo que se justifique y se autorice: pueden requerir privilegios o herramientas no instaladas.
- No compartir números de serie, UUID de discos, direcciones MAC, IP pública, nombres de usuario, tokens ni claves.
- La presencia de `vmx`/`svm` o de `/dev/kvm` no demuestra por sí sola que el motor Android o la aceleración gráfica funcionen.

### Windows

Usar PowerShell sin elevación cuando sea posible:

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture, CsTotalPhysicalMemory
Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, VirtualizationFirmwareEnabled, VMMonitorModeExtensions
Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion
Get-Volume | Select-Object DriveLetter, FileSystemLabel, Size, SizeRemaining
```

Revisar y redactar la salida antes de adjuntarla.

## 4. Configuración exacta bajo prueba

- Candidato: Ubuntu 26.04 LTS directo / Debian 13 directo / Proxmox VE + VM Linux
- Versión/build y origen oficial:
- Kernel del host/VM:
- CPU/RAM asignadas al host y al motor:
- Motor Android y versión:
- Imagen Android y digest/hash:
- APK de prueba y licencia:
- Driver gráfico y renderer observado:
- Red/bridge aislado:
- ADB: dirección y puerto local esperados:
- Paquetes y versiones:
- Cambios de configuración realizados (referencia al commit/issue):

## 5. Resultados repetibles

| Prueba | Repetición 1 | Repetición 2 | Repetición 3 | Evidencia |
|---|---|---|---|---|
| Arranque del host/VM | | | | |
| Motor listo | | | | |
| UI Android lista | | | | |
| Captura de pantalla | | | | |
| Entrada táctil/teclado | | | | |
| RAM en reposo | | | | |
| RAM bajo carga | | | | |
| CPU bajo carga | | | | |
| Persistencia tras reinicio | | | | |
| Backup y restauración | | | | |
| Operación sin WAN | | | | |
| ADB bloqueado desde red no autorizada | | | | |
| Aislamiento entre instancias | | | | |
| Nodo desconectado/reconectado | | | | |
| No duplicación de tareas/efectos | | | | |

No rellenar con estimaciones: usar valores observados o escribir “no medido”.

## 6. Criterios de seguridad y control del nodo

- [ ] ADB solo accesible desde la interfaz local/aislada expresamente autorizada.
- [ ] API administrativa no expuesta a Internet.
- [ ] Secretos fuera de logs, commits y capturas.
- [ ] El agente pendiente puede emitir heartbeat, capacidades y consultar estado.
- [ ] El agente pendiente no puede aceptar tareas, iniciar instancias ni ejecutar operaciones.
- [ ] La pérdida de conexión no provoca repetición automática de operaciones de resultado incierto.
- [ ] La reanudación requiere reconciliar el estado antes de aceptar nuevas tareas.
- [ ] Las operaciones son auditables y los identificadores de ejecución son idempotentes.

## 7. Incidentes y decisión

Para cada incidente: síntoma, pasos para reproducir, logs redactados, causa confirmada o hipótesis, solución, commit/PR asociado y resultado de repetir la prueba.

- Resultado: aprobado / rechazado / inconcluso
- Criterios que no se superaron:
- Riesgos abiertos:
- Coste obligatorio detectado: 0 USD / bloqueado
- Decisión propuesta y evidencia:
- Quién autorizó el siguiente paso:

## 8. Política offline

Registrar por separado qué funciona sin WAN:
- Arranque del host y del agente:
- Heartbeat dentro de LAN:
- Gestión local de instancias existentes:
- Inicio de nuevas instancias con artefactos ya almacenados:
- Login/activación o componentes que exijan Internet:
- Actualizaciones y descarga de artefactos:
- Sincronización de eventos al recuperar conexión:

No marcar una función como offline hasta probarla desconectando únicamente la WAN de forma controlada, sin romper la LAN de gestión.
