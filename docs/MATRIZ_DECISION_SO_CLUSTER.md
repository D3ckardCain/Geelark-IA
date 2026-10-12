# Matriz de decisión del sistema operativo del clúster GeeLark-IA

**Estado:** Debian 13 Stable directo es la primera plataforma de prueba solicitada por el usuario; no equivale a aprobación de instalación ni selección para producción. Proxmox VE se conserva para una fase comparativa posterior cuando el usuario la solicite.  
**Regla:** no instalar ni cambiar hardware, BIOS, particiones o sistemas hasta autorización explícita.  
**Objetivo de coste:** $0 USD de costes obligatorios de software/servicios.

## 1. Candidatos y orden de trabajo

1. **Primera fase:** Debian 13 Stable instalado directamente en un solo equipo de prueba, solo después de autorización específica y verificación de recuperación.
2. **Fase posterior:** Proxmox VE con una VM Linux dedicada, cuando el usuario indique que desea iniciar esa comparación. No se descarta Proxmox.
3. **Referencia comparativa:** Ubuntu 26.04 LTS directo, para interpretar diferencias relevantes si la compatibilidad o soporte de Debian no resulta adecuado.

La preferencia por Debian se limita al orden de pruebas; no es un resultado de benchmark ni una decisión de producción.

## Candidatos técnicos

- Ubuntu 26.04 LTS directo sobre el host Linux.
- Debian 13 Stable directo sobre el host Linux.
- Proxmox VE como hipervisor, con una VM Linux dedicada para el motor Android. LXC solo se evaluará si se puede demostrar aislamiento suficiente y configurar binder/dispositivos sin ampliar privilegios innecesarios.

No se deben comparar resultados de configuraciones diferentes. El mismo motor Android, imagen, APK de prueba, límites de CPU/RAM, resolución, conjunto de acciones y número de repeticiones deben usarse en cada candidato. Si un motor no funciona en una plataforma, se registra como incompatibilidad; no se oculta ni se cambia la carga para favorecerlo.

## 2. Puerta cero: validaciones documentales

| Verificación | Ubuntu 26.04 LTS | Debian 13 | Proxmox VE |
|---|---|---|---|
| Versión exacta y origen oficial registrados | Pendiente | Pendiente | Pendiente |
| Política de actualizaciones de seguridad sin pago obligatorio documentada | Pendiente | Pendiente | Pendiente |
| Kernel, binder/binderfs y módulos requeridos comprobados en documentación | Pendiente | Pendiente | Pendiente |
| Licencia de motor, imagen Android y APK de prueba revisadas | Pendiente | Pendiente | Pendiente |
| Método de acceso ADB local/aislado definido | Pendiente | Pendiente | Pendiente |
| Método de backup y recuperación definido | Pendiente | Pendiente | Pendiente |

No avanzar a una instalación de prueba hasta resolver las licencias y el método de recuperación. La descarga de una imagen no implica que pueda redistribuirse por la LAN: se debe registrar la licencia y respetar sus condiciones.

## 3. Protocolo de medición

Cuando el usuario autorice la prueba, ejecutar en un único equipo de prueba desechable y registrar la versión exacta de cada componente:

1. Inventario previo de solo lectura: CPU completa, RAM, discos, GPU/controlador, BIOS/UEFI, virtualización disponible, interfaces de red y espacio libre.
2. Instalar una configuración limpia siguiendo la documentación oficial y guardar los pasos exactos.
3. Crear una instancia Android con una imagen fijada por versión y digest/checksum, cuando esté disponible.
4. Repetir tres veces el arranque en frío y registrar tiempo hasta ADB listo, tiempo hasta UI lista y errores.
5. Ejecutar un guion de prueba autorizado: captura de pantalla, toque, deslizamiento, escritura de texto, abrir/cerrar una aplicación de prueba y reiniciar la instancia.
6. Registrar uso de RAM en reposo y bajo la misma carga, CPU media/pico, espacio ocupado, estabilidad y temperatura si está disponible.
7. Confirmar que ADB no escucha en interfaces públicas ni en la LAN general; documentar sockets y reglas de red.
8. Verificar persistencia de datos tras reinicio, backup y restauración.
9. Solo después de aprobar una instancia, repetir con 2 instancias aisladas. El ensayo con 5 o más instancias queda como fase posterior y depende de la capacidad medida y del objetivo funcional que se confirme.
10. Si se compara Proxmox, medir por separado coste de RAM de host/VM, acceso a iGPU, comportamiento de snapshots y recuperación. Una VM Linux dedicada es la comparación principal; no asumir que passthrough/compartición de iGPU funciona.
11. Repetir los casos de desconexión y recuperación del agente: no duplicar instancias ni repetir operaciones externas de resultado incierto.

## 4. Métricas y evidencia obligatorias

| Métrica | Cómo registrarla | Criterio |
|---|---|---|
| Compatibilidad de arranque | Log, versión de imagen y resultado | Debe arrancar de forma reproducible |
| Tiempo de arranque | 3 repeticiones; mediana y rango | Registrar, sin umbral inventado antes de conocer el uso |
| RAM y CPU por instancia | Reposo y carga fija | Determinar densidad posible con margen para el host |
| Aceleración gráfica | Driver, renderer y prueba visual | No declarar aceleración solo porque existe iGPU |
| ADB | Dirección/puerto de escucha y prueba desde interfaz no autorizada | Cualquier exposición no prevista es fallo de seguridad |
| Aislamiento | Intento de acceso cruzado entre instancias y datos | No debe existir acceso no autorizado |
| Persistencia | Reinicio y restauración de backup | Datos de prueba deben recuperarse íntegros |
| Red desconectada | Arranque de la instancia y agente sin WAN | Documentar qué funciona offline y qué no |
| Recuperación del nodo | Desconexión/reconexión y estado de tareas | Sin duplicados ni ejecución incierta automática |
| Actualizaciones | Fuentes, firma/hash y rollback | Reproducible y sin dependencia de repositorio de pago |
| Mantenimiento | Pasos manuales y errores frecuentes | Procedimiento documentado y recuperable |

## 5. Registro de resultados

Por cada ejecución, crear una issue o comentario de GitHub con:
- ID de prueba y fecha.
- Host y configuración (sin números de serie ni secretos).
- SO, kernel, paquetes, motor, imagen y APK de prueba.
- Comandos ejecutados y resultado redactado.
- Logs relevantes, métricas y hashes.
- Incidentes, causa, solución y resultado de repetición.
- Decisión: aprobado, rechazado o inconcluso, con evidencia.

No adjuntar credenciales, claves, tokens, seriales ni datos personales. Mantener los artefactos de prueba con licencia compatible y no subir APK propietarias ni imágenes redistribuibles sin permiso.

## 6. Regla de decisión

No se asignan puntuaciones de antemano. Primero se aplican puertas eliminatorias: coste obligatorio $0, actualizaciones de seguridad aceptables, licencias claras, ADB aislado, arranque estable y recuperación verificable. Entre los candidatos que superen esas puertas se comparan rendimiento medido, aislamiento, complejidad, mantenibilidad y facilidad de migración.

Si ningún candidato satisface seguridad y actualización sin pagos obligatorios, no se autoriza producción; se documenta el bloqueo y se busca una alternativa libre/local. El documento no autoriza la instalación ni la modificación de hardware.
