# Guía de inventario del equipo anfitrión

**Objetivo:** reunir los datos mínimos para elegir y probar un motor Android local.  
**Estado:** pendiente de ejecutar en el equipo del usuario.  
**Seguridad:** los comandos de esta guía son de lectura; no instalan ni modifican nada. No enviar números de serie, claves, nombres de usuario, direcciones IP públicas ni otra información personal.

## 1. Qué necesitamos conocer

- Sistema operativo y versión.
- CPU y arquitectura (x86_64/AMD64 o ARM64).
- Memoria RAM instalada y disponible.
- GPU y controlador.
- Espacio libre en el disco donde se instalarían las imágenes Android.
- Soporte y estado de la virtualización por hardware.
- Número aproximado de instancias Android simultáneas deseado.
- Si se permite usar Linux como anfitrión o una máquina dedicada, si actualmente se usa Windows/macOS.

## 2. Windows 10/11

Abre **PowerShell** normal (no hace falta ejecutarlo como administrador) y ejecuta los comandos siguientes uno por uno.

### Sistema, CPU y RAM

    Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsArchitecture, CsTotalPhysicalMemory
    Get-CimInstance Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors, VirtualizationFirmwareEnabled, VMMonitorModeExtensions
    Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, TotalPhysicalMemory

### GPU

    Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM

### Espacio en disco

    Get-Volume | Select-Object DriveLetter, FileSystemLabel, Size, SizeRemaining

### Virtualización

En el menú Inicio busca **Información del sistema** y revisa la fila **Virtualización habilitada en firmware**. También puedes ejecutar systeminfo y revisar el bloque de requisitos de Hyper-V si aparece.

Copia solo las líneas relevantes. No envíes seriales ni datos de identificación personal.

## 3. Linux (Ubuntu/Debian u otra distribución)

Abre una terminal y ejecuta:

### Sistema y CPU

    cat /etc/os-release
    uname -m
    lscpu | grep -E 'Model name|Architecture|CPU\\(s\\)|Virtualization|Hypervisor vendor'

### RAM y almacenamiento

    free -h
    df -h

### GPU

    lspci | grep -Ei 'vga|3d|display'

### Virtualización

    grep -Eoc '(vmx|svm)' /proc/cpuinfo
    test -e /dev/kvm && echo "KVM disponible" || echo "KVM no detectado"

El primer comando de virtualización cuenta CPUs lógicas que exponen flags de virtualización; un resultado positivo no demuestra por sí solo que el firmware, permisos y KVM estén listos. La prueba definitiva se hará después, de forma controlada.

## 4. macOS

Abre Terminal y ejecuta:

### Sistema, CPU y RAM

    sw_vers
    uname -m
    system_profiler SPHardwareDataType

### GPU y almacenamiento

    system_profiler SPDisplaysDataType
    system_profiler SPStorageDataType

### Soporte de hipervisor

    sysctl kern.hv_support

No hace falta compartir número de serie del Mac ni otros identificadores.

## 5. Número de instancias objetivo

Indica una estimación inicial, por ejemplo:
- 1 instancia para la primera prueba.
- 2–5 instancias para uso inicial.
- 10 o más instancias como objetivo futuro.

No se prometerá un número de instancias antes de medir RAM, CPU, GPU, almacenamiento, estabilidad y el consumo real de la imagen Android elegida.

## 6. Cómo compartir los resultados

Puedes pegar en el chat el resultado relevante de los comandos, o enviar capturas de pantalla recortadas que oculten seriales y datos personales. No necesitas instalar herramientas ni comprar hardware para hacer este inventario.

Con esos datos se podrá elegir la primera prueba candidata y adaptar las instrucciones al sistema anfitrión real. Si se propone cambiar de sistema operativo, primero se explicarán ventajas, riesgos, requisitos y método de recuperación antes de pedir que se instale o cambie nada.
