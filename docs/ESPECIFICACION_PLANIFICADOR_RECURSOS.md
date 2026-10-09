# Especificación del planificador de recursos — Geelark-IA

**Fecha:** 2026-10-09  
**Estado:** especificación inicial; no implementada ni validada con cargas reales.  
**Objetivo:** asignar instancias Android y trabajos a PC heterogéneas sin superar reservas configuradas, explicando cada decisión y evitando duplicados ante fallos.

## 1. Principios
1. La compatibilidad es un filtro obligatorio, no una puntuación compensable.
2. No asignar por CPU/RAM nominales: usar capacidad observada, reservas y límites validados.
3. La puntuación será determinista para una misma instantánea de recursos y configuración.
4. Cada decisión tendrá explicación legible y datos reproducibles.
5. La pérdida de heartbeat vuelve incierto el estado; no prueba que una instancia se haya detenido.
6. Ningún nodo ejecutará una instancia con asignación vigente en otro nodo.
7. Una tarea no idempotente con resultado incierto requiere reconciliación; no reintentar a ciegas.
8. Umbrales, pesos y reservas son configuración versionada.
9. El planificador no presupone capacidades que el motor Android no soporte.
10. Coste obligatorio de software/servicios: 0 USD.

## 2. Entradas de planificación

### Solicitud
- Identificador único de carga y tipo de trabajo.
- Perfil de recursos: CPU estimada, RAM reservada, almacenamiento e I/O.
- Requisitos Android: versión/API, ABI, motor, imagen y aceleración.
- Restricciones de afinidad/anti-afinidad, datos locales, nodo preferido/prohibido y mantenimiento.
- Prioridad, política de espera y clave de idempotencia.
- Ubicación de datos y artefactos necesarios.

### Inventario del nodo
- Identidad autenticada, versión del agente y estado administrativo.
- CPU, arquitectura, carga y límites configurados.
- RAM total, usada, disponible y reservas.
- Espacio libre por volumen y métricas de I/O disponibles.
- GPU/aceleración y capacidades verificadas.
- Motores/imágenes instalados, versiones, ABI y checksums.
- Instancias, trabajos activos y límites de concurrencia medidos.
- Salud, heartbeat, marca temporal y estado active/draining/maintenance/offline/quarantined.
- Compatibilidad con la política de seguridad vigente.

Los datos deben incluir marca temporal. La telemetría vencida no puede autorizar una nueva asignación.

## 3. Filtros obligatorios
Descartar un nodo si:
1. No está autenticado, está revocado, en cuarentena, drenado, mantenimiento u offline.
2. El heartbeat o la telemetría superan la antigüedad permitida.
3. El agente o protocolo no son compatibles.
4. Faltan motor, imagen, versión Android o ABI requeridos.
5. Falta una capacidad obligatoria, como aceleración si la carga la necesita.
6. RAM libre tras reservas y compromisos no cubre la carga y el margen.
7. El disco quedaría bajo la reserva mínima.
8. Se supera el límite de concurrencia validado.
9. La afinidad, el mantenimiento o la política de datos impiden la colocación.
10. Ya existe asignación vigente o estado no reconciliado para la carga.
11. La salud, integridad del volumen o seguridad no cumplen la política.

Los filtros no son penalizaciones: un nodo incompatible nunca gana por puntuación.

## 4. Reservas y capacidad segura
Distinguir capacidad física, reserva del sistema, reserva de seguridad, consumo medido, compromisos y capacidad libre.

- RAM elegible = RAM total menos reservas y compromisos existentes.
- Disco elegible = espacio libre menos reserva mínima y compromisos previstos.
- CPU combina carga reciente, límites y perfiles medidos; no es simplemente el número de núcleos.
- La concurrencia máxima por motor/nodo se configura tras pruebas; sin evidencia, usar un límite conservador configurable.
- No sobreasignar RAM o disco por defecto.
- Si temperatura/GPU no se pueden medir fiablemente, marcar el dato como no disponible.

## 5. Puntuación de nodos elegibles
Solo después de los filtros obligatorios, normalizar factores entre 0 y 1:
- margen de memoria: 30 %;
- margen de CPU: 20 %;
- margen de almacenamiento: 15 %;
- salud/rendimiento de I/O: 10 %;
- localidad de datos: 10 %;
- balanceo de carga: 10 %;
- afinidad compatible: 5 %;
- penalización adicional de riesgo, cuando proceda.

Estos pesos son punto de partida, no resultados medidos. Guardarlos en configuración versionada. Comparar el algoritmo con una estrategia baseline simple usando idénticas cargas. Desempate determinista por menor riesgo, mejor localidad, menor número de compromisos y, finalmente, ID ordenado de nodo.

## 6. Proceso de asignación
1. Validar solicitud y clave de idempotencia.
2. Leer una instantánea consistente de inventario y asignaciones.
3. Filtrar nodos no elegibles y registrar cada razón.
4. Puntuar nodos elegibles y producir explicación.
5. Crear una reserva provisional atómica con ID de asignación, epoch monotónico y vencimiento de lease.
6. El agente receptor valida epoch, compatibilidad y capacidad local.
7. El agente confirma la reserva antes de ejecutar la operación autorizada.
8. Registrar transiciones, resultado y evidencia; liberar reservas al completar/cancelar de forma segura.
9. Si se pierde comunicación, marcar resultado incierto y reconciliar antes de reasignar.

La persistencia autoritativa y las garantías transaccionales requieren una decisión arquitectónica adicional. No asumir que SQLite independiente en la Master basta para coordinar escritores distribuidos durante particiones de red.

## 7. Leases, epochs y reconciliación
Cada asignación mantiene ID de carga, nodo propietario, epoch, vencimiento de lease, estado deseado y observado.

- Un agente rechaza órdenes con epoch anterior al último aceptado.
- El vencimiento del lease no demuestra que el proceso remoto se detuvo. Antes de reasignar, verificar fencing efectivo o detener/aislar de forma comprobable al propietario anterior.
- Al reconectar, el agente informa estado observado y operaciones pendientes; el controlador reconcilia estado deseado y real.
- Estados mínimos: pending, reserved, starting, running, stopping, stopped, failed, unknown y reconciling.
- Si no puede probarse que la instancia anterior dejó de ejecutarse, conservar unknown y bloquear una segunda ejecución.
- Los efectos externos de RPA no son transaccionales; no repetirlos automáticamente con resultado incierto.

## 8. Drenaje y fallos
- Draining: no admite nuevos trabajos; los existentes continúan salvo decisión explícita.
- Maintenance: requiere revisar cargas y plan de evacuación.
- Offline: no se envían órdenes y no se infiere que las cargas terminaron.
- Quarantined: bloquea asignaciones hasta revisión.
- La caída de la UI no ordena detener instancias.
- La caída del controlador no dispara acciones destructivas ni reasignaciones inseguras.
- Recuperación en otro nodo solo si backup, imagen, arquitectura y motor son compatibles y el propietario anterior está cercado.

## 9. Explicabilidad y auditoría
Registrar ID de solicitud, clave de idempotencia, versión de política/pesos, timestamp y antigüedad de telemetría, nodos considerados, razones de exclusión, puntuaciones, desempates, reserva, epoch, lease, aceptación/rechazo del agente, transiciones, errores y resultado.

No registrar contraseñas, tokens, cookies, datos personales innecesarios ni contenido privado. La UI debe mostrar por qué se eligió un nodo y por qué se descartaron otros.

## 10. Seguridad del protocolo
- Identidad única por nodo, autenticación mutua cuando sea viable y revocación.
- Canal cifrado en redes no confiables, firewall y red privada.
- Esquemas estrictos y límites de tamaño/tasa.
- Comandos tipados permitidos; nunca exponer shell arbitrario ni ADB a Internet.
- Protección contra repetición con epoch, ID de operación y expiración.
- Secretos fuera del repositorio y logs.
- Verificar procedencia/checksum de artefactos cuando proceda.
- Agente con privilegios mínimos y separación entre API y ejecutor local.

## 11. Pruebas de aceptación
1. Nodo sin ABI/motor compatible nunca recibe la carga.
2. RAM insuficiente descarta el nodo aunque tenga CPU libre.
3. Disco bajo reserva bloquea nuevas asignaciones.
4. Telemetría obsoleta impide asignación.
5. Nodo drenado no recibe nuevas cargas.
6. Solicitudes concurrentes para el mismo ID no crean dos propietarios.
7. Mensaje con epoch antiguo se rechaza.
8. Pérdida de heartbeat produce unknown, no stopped.
9. Tarea no idempotente incierta no se reintenta automáticamente.
10. Desempates deterministas y explicación reproducible desde logs.
11. Agente rechaza comandos no autorizados o fuera de esquema.
12. Reiniciar controlador/agente permite reconciliar sin duplicar instancias.
13. Comparar estrategia ponderada con baseline simple.
14. Repetir pruebas con nodos heterogéneos y reportar métricas reales.

## 12. Criterios de salida
Antes de implementar en producción: decidir persistencia/consistencia distribuida, probar esquemas, demostrar asignación sin duplicados bajo desconexión, hacer política configurable y explicable, registrar resultados y completar manual en español.

**Límite actual:** especificación documental; no existe planificador implementado ni se han ejecutado estas pruebas.
