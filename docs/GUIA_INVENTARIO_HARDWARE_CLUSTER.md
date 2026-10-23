# Inventario inicial de hardware para el clúster GeeLark-IA

**Estado:** procedimiento de descubrimiento; solo lectura. No instala agentes ni cambia configuraciones.  
**Objetivo:** recopilar datos suficientes para decidir qué PC puede actuar como Master y cuáles como Workers heterogéneos.  
**Coste:** comandos integrados del sistema operativo; no requiere SaaS ni API de pago.

> **Relación con la guía de equipo individual:** este documento es la ficha del clúster (PC-MASTER y varios WORKERS, roles y capacidades). Para un diagnóstico detallado de CPU/GPU/RAM/virtualización de un solo anfitrión, consultar [Guía de inventario del equipo anfitrión](GUIA_INVENTARIO_EQUIPO.md). No son dos procedimientos de instalación; ambos son de inventario/solo lectura.

## Principios

- No ejecutar scripts descargados ni comandos como administrador/root para este inventario.
- No recopilar números de serie, claves, tokens, perfiles de navegador ni contenido personal.
- No cambiar BIOS/UEFI, particiones, firewall, antivirus ni configuración de virtualización durante el inventario.
- Guardar una ficha por PC con un alias (PC-01, PC-02…), no hace falta publicar nombres personales ni IP públicas.
- La capacidad útil depende también de refrigeración, estabilidad, virtualización disponible, disco libre y red; el modelo de CPU por sí solo no basta.

## Datos que hay que registrar por equipo

1. Alias del equipo y ubicación aproximada dentro de la red (por ejemplo, oficina/habitación; no dirección pública).
2. Sistema operativo y versión.
3. CPU: modelo, núcleos físicos e hilos.
4. RAM total y, si es posible, RAM disponible en reposo.
5. Discos: tipo (SSD/NVMe/HDD si se puede identificar), capacidad total y espacio libre; no compartir números de serie.
6. GPU: modelo si existe. No es requisito previo para toda carga.
7. Soporte de virtualización y si ya se utiliza un hipervisor.
8. Conexión: Ethernet o Wi-Fi y velocidad del enlace si el sistema la muestra.
9. Restricciones: si debe conservar Windows, si puede reiniciarse, horas de disponibilidad y si el equipo se usa a diario.

## Windows: comandos de solo lectura

Abrir **PowerShell normal** (no hace falta ejecutarlo como administrador) y ejecutar los bloques siguientes por separado.

### Sistema operativo
```powershell
Get-CimInstance Win32_OperatingSystem |
  Select-Object Caption, Version, OSArchitecture
```

### CPU
```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed
```

### Memoria RAM
```powershell
Get-CimInstance Win32_ComputerSystem |
  Select-Object @{Name='RAM_GB';Expression={[math]::Round($_.TotalPhysicalMemory / 1GB, 2)}}
```

### Discos y espacio libre
```powershell
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" |
  Select-Object DeviceID, FileSystem,
    @{Name='Size_GB';Expression={[math]::Round($_.Size / 1GB, 1)}},
    @{Name='Free_GB';Expression={[math]::Round($_.FreeSpace / 1GB, 1)}}
```

Este comando muestra unidades lógicas y espacio libre, no siempre identifica si el dispositivo físico es SSD, NVMe o HDD. No usar comandos que impriman números de serie.

### GPU
```powershell
Get-CimInstance Win32_VideoController |
  Select-Object Name, DriverVersion
```

### Virtualización y tipo de enlace de red
```powershell
Get-CimInstance Win32_ComputerSystem |
  Select-Object HypervisorPresent, HypervisorVendor
Get-NetAdapter |
  Select-Object Name, Status, LinkSpeed, InterfaceDescription
```

Si una propiedad no aparece en la versión de Windows, anotar “no disponible”; no es necesario instalar utilidades para completar la primera ficha.

## Linux: comandos de solo lectura

Ejecutar desde una terminal con usuario normal.

### Sistema operativo y CPU
```bash
cat /etc/os-release
lscpu
```

### RAM
```bash
free -h
```

### Discos y espacio libre
```bash
lsblk -o NAME,SIZE,TYPE,ROTA,TRAN,FSTYPE,MOUNTPOINTS
df -h
```

En `lsblk`, `ROTA=0` suele indicar almacenamiento no rotacional (SSD/NVMe), y `ROTA=1` suele indicar HDD; puede haber excepciones según controladores y máquinas virtuales.

### GPU y virtualización (si las herramientas están disponibles)
```bash
lspci | grep -Ei 'vga|3d|display'
systemd-detect-virt
```

Si `lspci` no está instalado o no muestra GPU, no instalar nada todavía. `systemd-detect-virt` puede devolver `none` en un sistema físico.

### Enlaces de red
```bash
ip -br link
```

## Plantilla para entregar el inventario

Copiar esta ficha y repetirla por cada equipo:

| Campo | Valor |
|---|---|
| Alias | PC-01 |
| Sistema operativo/versión | |
| CPU / núcleos / hilos | |
| RAM total | |
| RAM disponible en reposo (opcional) | |
| Discos: tipo, tamaño y espacio libre | |
| GPU (si existe) | |
| Virtualización/hipervisor actual | |
| Red: Ethernet/Wi-Fi y velocidad | |
| ¿Debe conservar Windows? | Sí/No |
| ¿Se puede reiniciar cuando sea necesario? | Sí/No |
| Disponibilidad aproximada | |
| Observaciones de estabilidad/temperatura | |

## Qué no se debe decidir todavía

No elegir aún una distribución definitiva de instancias, límites de concurrencia, tamaño de almacenamiento por instancia ni necesidad de GPU. Primero se deben conocer los requisitos de cada instancia Android y medir consumo real en una prueba controlada.

## Fase posterior

Una vez revisado el inventario:
1. Clasificar nodos por capacidad y fiabilidad.
2. Reservar recursos para el sistema operativo de cada PC.
3. Seleccionar Master y Workers candidatos.
4. Verificar compatibilidad del motor de virtualización/Android.
5. Instalar un agente firmado o verificable solo después de revisar el código, permisos, actualizaciones y mecanismo de desinstalación.
6. Ejecutar pruebas de carga progresivas con límites y botón de parada.
