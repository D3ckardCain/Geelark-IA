> **Aclaración de vigencia — 2026-10-22:** esta arquitectura se mantiene como objetivo propuesto. El motor Android no está aprobado; QEMU + Android-x86 + VNC está retirado, redroid bloqueado por #27 y Cuttlefish es candidato de laboratorio no aprobado. No implica implementación, integración ni prueba física.

# Arquitectura de clúster físico heterogéneo — Geelark-IA

**Fecha:** 2026-10-09  
**Estado:** requisito arquitectónico confirmado; diseño preliminar pendiente de pruebas.  
**Coste obligatorio de software/servicios:** 0 USD.  
**Alcance:** reunir varios PC físicos de distintas capacidades bajo una administración centralizada para ejecutar instancias Android virtualizadas localmente.

## 1. Corrección importante del diseño actual

La propuesta tecnológica inicial de `ARQUITECTURA_TECNOLOGICA_PROPUESTA.md` describía principalmente una aplicación local ejecutada en un solo anfitrión. Eso sirve para definir la interfaz, la API, los contratos y los módulos, pero **no representa todavía la arquitectura distribuida de varios PC** acordada preliminarmente.

El clúster de varios equipos debe ser parte de la arquitectura objetivo desde ahora. No se debe construir el producto como si una única PC fuera a ejecutar obligatoriamente todas las instancias Android.

## 2. Objetivo de arquitectura

- Reunir PC heterogéneas: CPU, RAM, GPU y discos de diferentes tamaños/rendimientos.
- Disponer de una PC principal o *Master* para administración y observabilidad.
- Permitir administrar desde la Master y, con autenticación, acceder de forma remota desde otra PC o teléfono.
- Distribuir instancias Android y trabajos RPA entre los nodos según recursos reales y capacidades requeridas.
- Poder agregar o retirar nodos sin rediseñar la aplicación.
- Evitar que la caída de la interfaz o del nodo Master detenga automáticamente todos los Android que ya estén ejecutándose, cuando la tecnología elegida lo permita.
- No usar cloud phones ni depender de servicios pagados.
- Mantener un plano de control y un registro de estado coherente, con recuperación documentada.

## 3. Separación de responsabilidades

### 3.1 Plano de administración

PC-MASTER permanece como aplicación Windows. La candidata de escritorio actual es Python/Tkinter en la PR #87, todavía draft y no integrada; el panel web autenticado de solo lectura está en la PR #104, también draft. Tauri/React fue una propuesta inicial y no está seleccionado ni autoriza una reescritura. La interfaz muestra el estado del clúster, nodos, instancias, tareas, recursos, alertas y registros cuando se integre y acepte. La API debe ser agnóstica al número de nodos.

### 3.2 Plano de control

Un servicio de control mantiene inventario, configuración deseada, asignaciones, cola de tareas, permisos, historial y estado conocido de cada nodo. La Master será el punto principal de administración, pero no se debe convertir por defecto en un punto único de fallo para las instancias ya ejecutándose.

Debe definirse antes de producción:
- dónde persiste el estado autoritativo;
- cómo se elige o recupera el controlador si la Master falla;
- cómo se evitan dos controladores activos que asignen la misma instancia;
- cómo se reconcilian estados tras una desconexión;
- qué funciones siguen disponibles durante una partición de red.

No se prometerá alta disponibilidad hasta implementarla y probarla.

### 3.3 Nodos de cómputo

Cada PC participante ejecuta un agente de nodo con identidad autenticada. El agente informa CPU, RAM, espacio libre, arquitectura, capacidades de virtualización, aceleración gráfica, versiones instaladas y estado de salud. Recibe únicamente trabajos autorizados y reporta resultados.

El agente no debe exponer ADB, Docker, sockets de administración ni shell arbitrario a la red. La comunicación se limita a una red privada autenticada, con permisos mínimos, validación de mensajes y protección contra repetición.

### 3.4 Ejecución Android

Las instancias pertenecen a un nodo en cada momento. La capa de abstracción del motor Android debe poder seleccionar un backend por nodo, pero la compatibilidad de imagen, CPU/ABI, kernel, GPU, almacenamiento y funciones se valida por motor y por nodo. No se supondrá que una instancia puede migrarse en vivo entre PC heterogéneas.

La primera versión debe preferir asignación, parada controlada, copia/backup y recuperación en otro nodo cuando sea compatible, antes de intentar migración en vivo.

## 4. Sistema base y aprovisionamiento de los nodos

- Los PC WORKER físicos utilizarán Debian 13 directamente como sistema operativo base previsto.
- PC-MASTER se mantiene como aplicación Windows y será el plano central para descubrir, adoptar, preparar, administrar y supervisar los WORKER.
- Para equipos sin sistema operativo, se diseñará el arranque por red y la instalación desatendida de Debian cuando el firmware, la tarjeta de red y la infraestructura LAN lo permitan.
- El descubrimiento será automático, pero la adopción requerirá aprobación explícita desde PC-MASTER. Los nodos pendientes no ejecutarán tareas de producción.
- Tras la adopción, PC-MASTER distribuirá y configurará el agente, instalará las herramientas locales de virtualización Android, obtendrá los artefactos autorizados y verificará el resultado.
- El agente y las herramientas de ejecución serán componentes locales del WORKER; el control y la orquestación propios corresponderán a GeeLark-IA. No se añade una plataforma externa de administración de infraestructura.
- La instalación por red depende de la compatibilidad UEFI/BIOS, el arranque PXE/iPXE y la configuración de la LAN; estas condiciones se probarán antes de prometer aprovisionamiento universal.

## 5. Planificador de recursos para PC heterogéneas

No asignar instancias solo por cantidad de núcleos. El planificador debe considerar como mínimo:
- RAM disponible y reserva de seguridad del sistema anfitrión;
- CPU disponible, carga y límites por instancia;
- espacio libre, latencia y rendimiento del disco;
- arquitectura de CPU y compatibilidad ABI de la imagen;
- aceleración gráfica y necesidades de cámara/sensores;
- motor Android y versión disponible en el nodo;
- límites de instancias medidos por nodo, no supuestos;
- estado de salud, temperatura/estrangulamiento cuando esté disponible;
- afinidad de perfil/datos y coste de mover respaldos;
- trabajos en ejecución, prioridades y ventanas de mantenimiento.

Cada nodo declara capacidad observada y capacidad segura recomendada. El sistema no debe sobreasignar RAM o almacenamiento por encima de límites configurados. Debe poder marcar nodos como drenados para impedir nuevas asignaciones antes de mantenimiento.

## 6. Datos y almacenamiento

Separar:
1. **Metadatos de control:** perfiles, grupos, configuración deseada, asignaciones, permisos, tareas y auditoría.
2. **Datos de ejecución Android:** discos/volúmenes de cada instancia.
3. **Artefactos compartidos:** APK autorizados, archivos importados, imágenes y respaldos.

Para el MVP, preferir almacenamiento local en cada nodo más backup/exportación controlada, sin requerir NAS ni servicios cloud. Si posteriormente se evalúa almacenamiento compartido (por ejemplo, NFS), debe ser opcional y probarse su efecto en rendimiento y disponibilidad. No se debe colocar una base SQLite activa sobre un sistema de archivos de red como sustituto improvisado de una base distribuida.

Definir política de backup, cifrado, retención, integridad, recuperación y prevención de dos escritores para una misma instancia antes de ofrecer recuperación entre nodos.

## 7. Red y acceso remoto

- Red privada entre nodos; preferir segmentación de red y firewall por defecto.
- Acceso remoto autenticado para administración desde PC/teléfono.
- No publicar directamente en Internet la API, ADB, el daemon del motor ni interfaces administrativas de los nodos.
- Una VPN autogestionada puede evaluarse si el acceso debe cruzar redes; revisar coste, requisitos y modo de operación. El sistema local debe seguir funcionando en LAN sin una cuenta cloud obligatoria.
- Registrar cambios administrativos y aplicar permisos por usuario/rol.
- Definir TLS/autenticación de nodo, rotación/revocación de credenciales y procedimiento para retirar un nodo comprometido.

## 8. Comportamiento ante fallos

Deben probarse por separado:
- caída de la UI/Master;
- pérdida de conectividad de un nodo;
- apagado abrupto de un nodo con Android activo;
- caída del controlador mientras los nodos siguen ejecutándose;
- disco lleno;
- corrupción de datos de una instancia;
- reaparición de un nodo con estado obsoleto;
- reintentos de tareas no idempotentes;
- partición de red que pueda producir asignaciones contradictorias.

La política por defecto debe ser segura: una tarea no idempotente no se repite automáticamente si no se puede saber si terminó; una instancia no se inicia en dos nodos simultáneamente; la pérdida de la Master no debe causar acciones destructivas automáticas.

## 9. Entregas por etapas

1. Definir el contrato del agente de nodo y modelo de recursos.
2. Hacer prueba de concepto con dos nodos Linux heterogéneos.
3. Medir un motor Android candidato en un nodo y después en ambos.
4. Probar distribución de instancias y tareas, desconexión y recuperación.
5. Implementar y probar el aprovisionamiento por red, la instalación de Debian, el enrolamiento seguro del agente y la preparación automática del entorno Android.
6. Implementar autenticación, permisos, auditoría y administración remota segura.
7. Documentar instalación, alta/baja de nodos, actualizaciones, backups, recuperación y resolución de problemas en español.
8. Actualizar la matriz de paridad de GeeLark: la arquitectura de clúster es infraestructura propia y no se marcará como función equivalente de GeeLark salvo que corresponda a una función observada.

## 10. Criterios de aceptación antes de aprobar el clúster

- Dos nodos heterogéneos se registran y muestran recursos reales.
- El planificador coloca una instancia únicamente en un nodo compatible y con capacidad suficiente.
- La instancia puede iniciarse, detenerse, respaldarse y recuperarse conforme a las capacidades comprobadas.
- Una desconexión no provoca duplicación de una instancia ni repetición insegura de acciones.
- La caída de la interfaz no destruye las instancias en ejecución.
- Acceso remoto protegido; ADB y consolas administrativas no están expuestos públicamente.
- Pruebas de recuperación reproducibles, logs redactados y manual completo en español.
- Sin servicios o licencias de software obligatorios de pago.
- Resultados de rendimiento medidos, no estimados ni inventados.

## 11. Estado y límites actuales

Este documento registra la dirección arquitectónica y los requisitos; no significa que el aprovisionamiento completo, el agente o el motor Android ya estén validados en hardware físico. La capacidad máxima de instancias se calculará después de medir cargas reales en los nodos disponibles.
