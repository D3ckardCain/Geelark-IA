# Plan de aprovisionamiento automatizado de PC-WORKER — Debian 13

**Actualizado:** 2026-10-22  
**Estado:** diseño documental; no se ha creado USB, instalado Debian ni modificado ningún disco.  
**Alcance:** WORKER-01 como piloto; después, replicar el procedimiento en WORKER-02/03.  
**Coste obligatorio objetivo:** 0 USD.

## 1. Objetivo

Reducir al mínimo la configuración manual de cada worker. PC-MASTER Windows prepara y distribuye los artefactos por LAN; cada worker recibe una instalación reproducible de Debian 13, con nombre de nodo único, acceso administrativo controlado y diagnóstico local. La instalación del runtime Android queda separada y bloqueada hasta que la issue #27 demuestre una mitigación efectiva de seguridad para la imagen redroid exacta.

## 2. Base técnica verificada

El instalador oficial de Debian 13 (Trixie) permite automatizar la mayoría de las respuestas con preseed. Debian documenta tres métodos: initrd, archivo local y red. El preseed de initrd ofrece mayor cobertura, pero requiere preparar el medio de instalación. La automatización no elimina la necesidad de definir cuidadosamente el disco objetivo: una configuración de particionado automático puede borrar datos.

Fuentes:
- Debian 13, automatización con preseed: https://www.debian.org/releases/trixie/amd64/apb
- Introducción y métodos de preseed: https://www.debian.org/releases/trixie/amd64/apbs01.en.html
- Ejemplo oficial de preseed: https://www.debian.org/releases/trixie/example-preseed.txt
- Requisitos de despliegue redroid: https://github.com/remote-android/redroid-doc/blob/master/deploy/README.md
- Guía Debian redroid (consultada; cubre Debian 11/12, no confirma Debian 13): https://github.com/remote-android/redroid-doc/blob/master/deploy/debian.md

**Importante:** la guía pública redroid para Debian consultada no confirma por sí sola compatibilidad de Debian 13. Por eso, el kernel y Binder/BinderFS se inspeccionan en el worker real antes de instalar el runtime.

## 3. Flujo propuesto

### Fase A — Preparar artefactos en PC-MASTER (no destructiva)

1. Descargar una sola vez la ISO oficial de Debian 13 desde un origen oficial.
2. Verificar la suma SHA-256 contra el valor publicado por Debian y registrar versión/fecha.
3. Guardar la ISO en una caché local de PC-MASTER y servirla por LAN o preparar un medio USB por worker.
4. Crear una plantilla preseed sin contraseñas, tokens, claves privadas ni credenciales reutilizables.
5. Mantener fuera de GitHub cualquier configuración local con secretos y cualquier valor específico del equipo.
6. Definir nombre de nodo único, método de red y acceso administrativo de cada worker.
7. Probar la plantilla en un entorno desechable antes de usarla en un equipo físico.

### Fase B — Confirmación del disco por worker (puerta destructiva)

Antes de habilitar el particionado automático, registrar para ese equipo:
- Identificador estable del disco objetivo (preferir /dev/disk/by-id cuando esté disponible).
- Modelo y capacidad esperada.
- Confirmación física de que el disco está destinado al clúster y no contiene datos que deban conservarse.
- Nombre único del nodo (WORKER-01, WORKER-02, etc.).

No seleccionar el primer disco detectado de forma ciega. No activar borrado automático hasta que el disco objetivo haya sido identificado y aprobado. No ejecutar esta fase desde PC-MASTER sobre un disco remoto sin confirmación física.

### Fase C — Instalar Debian 13 con configuración mínima

Después de la aprobación del procedimiento:
1. Arrancar el instalador oficial desde USB o el método local elegido.
2. Aplicar preseed para idioma/teclado, red, zona horaria, hostname, usuario administrativo, particionado del disco aprobado y selección mínima de paquetes.
3. Instalar un sistema sin entorno gráfico, con herramientas estándar y acceso remoto seguro si se necesita.
4. No almacenar contraseñas en el repositorio. Usar credenciales únicas y/o claves generadas localmente; documentar rotación y revocación.
5. Configurar actualizaciones de seguridad y política de reinicio de forma explícita.
6. Reiniciar y comprobar versión de Debian, kernel, hostname, red y acceso administrativo.
7. Registrar logs de instalación sin datos sensibles.

### Fase D — Diagnóstico posterior a instalación (solo lectura)

Ejecutar en cada worker:
- Sistema y kernel exactos.
- CPU, núcleos/hilos, RAM y espacio libre.
- Modelo de disco y puntos de montaje.
- Soporte de Binder/BinderFS y módulos ya presentes.
- Valor inicial de /proc/sys/kernel/modprobe.
- Interfaces, rutas, puertos en escucha y firewall.
- Runtime de contenedores, si existe; no instalarlo durante el diagnóstico.

La guía reproducible está en [GUIA_DIAGNOSTICO_PREVIO_REDROID.md](GUIA_DIAGNOSTICO_PREVIO_REDROID.md). La salida se revisa antes de compartirla y no debe contener secretos.

### Fase E — Instalar runtime Android (bloqueada)

No instalar Docker/Podman para ejecutar redroid ni iniciar contenedores hasta que la issue [#27](https://github.com/D3ckardCain/Geelark-IA/issues/27) documente:
- Etiqueta y digest exactos.
- Inspección del init y parches de esa imagen.
- Mitigación reproducible del riesgo de /proc/sys/kernel/modprobe.
- Capacidades, dispositivos y montajes mínimos.
- ADB restringido y socket de administración no expuesto.
- Plan de recuperación probado en un entorno aislado.

Después de cerrar la puerta, fijar el runtime de contenedores y paquetes con versiones, hashes y licencias; no usar etiquetas flotantes ni ejecutar el ejemplo privilegiado upstream sin una revisión de seguridad específica.

## 4. Seguridad de red y enrolamiento

- El worker inicia como pendiente.
- Antes de adopción, solo informa heartbeat/capacidades y consulta un estado limitado.
- No recibe tareas ni inicia Android hasta aprobación desde PC-MASTER.
- La comunicación de control usa HTTPS privado, credenciales individuales revocables y autorización por operación.
- No publicar ADB a Internet ni a la LAN general.
- No exponer el socket Docker al panel ni ofrecer shell arbitrario por la API.
- No incluir tokens, contraseñas, cookies ni claves en logs, preseed o commits.

## 5. Caché LAN y coste

- Mantener un artefacto por versión, arquitectura y hash.
- Descargar una vez desde el origen oficial y distribuir por LAN solo después de validar integridad y licencia.
- Separar ISO Debian, paquetes del sistema, imagen redroid y APK objetivo.
- Conservar metadatos de procedencia, licencia, fecha y hash; documentar cómo retirar una versión.
- Objetivo obligatorio: 0 USD; sin servicio cloud, API de pago ni almacenamiento externo obligatorio.

## 6. Aceptación del piloto WORKER-01

- [ ] ISO oficial verificada por SHA-256.
- [ ] Preseed probado en un entorno desechable.
- [ ] Disco físico objetivo identificado y aprobado explícitamente.
- [ ] Debian 13 instalado con hostname único y acceso administrativo seguro.
- [ ] Diagnóstico de solo lectura completo y redactado.
- [ ] Kernel/Binder/BinderFS y compatibilidad documentados.
- [ ] No se ha iniciado redroid antes de cerrar #27.
- [ ] Instalación reproducible y recuperación documentadas en español.

Solo después de aceptar el piloto se adapta la plantilla a WORKER-02/03. No se infiere capacidad de instancias a partir de la instalación del sistema operativo.

## 7. Registro de cambios

- 2026-10-22: primera versión del plan de aprovisionamiento Debian 13 con preseed, caché LAN, puerta de disco y bloqueo de seguridad redroid.
