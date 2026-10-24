# Plan de prueba de concepto del aprovisionamiento de PC WORKER — GeeLark-IA

**Fecha:** 2026-10-09. **Estado:** pendiente de ejecución.  
**Coste objetivo:** 0 USD en software/servicios obligatorios.

## Objetivo
Validar con al menos dos PC físicas el flujo objetivo: descubrimiento de equipos, aprobación de adopción desde PC-MASTER Windows, instalación desatendida de Debian 13 por red cuando sea compatible, enrolamiento del agente, despliegue de herramientas de virtualización Android y puesta en servicio. Verificar compatibilidad, licencias y seguridad antes de instalar artefactos.

## Registro previo
Crear un registro GitHub por ejecución con fecha, protocolo, IDs lógicos de nodos, CPU/arquitectura, RAM, GPU/aceleración, disco, red, virtualización, OS/kernel, motor/imagen Android, ABI, versiones, licencias, comandos, logs redactados, resultados y desviaciones. No subir secretos, claves privadas, tokens, datos personales ni imágenes sin autorización. Usar datos sintéticos y una APK de prueba autorizada.

## Fase A — licencias y preparación
1. Verificar requisitos de arranque por red, Debian 13, virtualización por hardware y motor Android.
2. Revisar licencias del motor, imagen, SDK, APK y herramientas, incluido uso comercial y redistribución si corresponde.
3. Separar descargas puntuales de componentes que exigen conectividad permanente.
4. Rechazar componentes con licencia incompatible o procedencia dudosa.
Salida: inventario aprobado; no iniciar si queda un bloqueo crítico.

## Fase B — línea base por nodo
En cada PC por separado: instalar con documentación oficial, registrar versiones, iniciar Android, comprobar ADB solo localmente mediante el adaptador de prueba, instalar/abrir APK autorizada, capturar pantalla, enviar entrada, transferir archivo, reiniciar para comprobar persistencia y detener midiendo liberación de recursos. Repetir tres veces y registrar todos los fallos.

## Fase C — rendimiento
Medir por nodo:
- tiempo hasta Android listo y parada limpia;
- CPU media/picos y RAM del host/proceso/VM/contenedor;
- almacenamiento consumido y crecimiento;
- latencia de captura/entrada;
- estabilidad, errores, bloqueos, reinicios y desconexiones.

Escenarios: una instancia en reposo; una instancia ejecutando la misma secuencia de prueba; concurrencia escalonada de 1, 2, 3… hasta el umbral de seguridad o primeros errores; presión de memoria controlada en un entorno desechable. No extrapolar capacidad máxima sin medición.

## Fase D — dos nodos
1. Registrar ambos agentes autenticados y comprobar inventario/heartbeat.
2. Enviar una carga compatible con ambos y guardar la explicación de colocación.
3. Enviar una carga que solo uno pueda ejecutar y confirmar el rechazo del otro.
4. Ejecutar cargas en paralelo y comprobar aislamiento.
5. Drenar un nodo y verificar que no recibe asignaciones nuevas.
6. Desconectar y reconectar un nodo; reconciliar sin duplicar instancias.
7. Reiniciar el controlador y comprobar que no ordena paradas destructivas ni pierde asignaciones persistidas.

## Fase E — fallos
Probar por separado: caída del agente, pérdida de red, caída del controlador, telemetría obsoleta, volumen de prueba cerca del umbral, orden con epoch antiguo, petición repetida con clave de idempotencia, interrupción de inicio/parada y restauración de backup en nodo compatible.

Si no se demuestra que la instancia anterior dejó de ejecutarse, no iniciar otra copia. Si una acción externa RPA tiene resultado incierto, no repetirla automáticamente.

## Fase F — comparación
Ejecutar el aprovisionamiento completo en dos nodos compatibles y registrar evidencia por etapa: arranque por red, instalación Debian, identidad y autenticación del agente, instalación del runtime Android, verificación de artefactos, inicio de una instancia, persistencia, reinicio y recuperación de fallos. Registrar compatibilidad, seguridad, rendimiento, coste y problemas reproducibles.

## Criterios de aprobación
- Carga Android reproducible en dos nodos heterogéneos.
- Colocación respeta ABI, motor, RAM, disco y límites.
- Órdenes no autorizadas y epochs antiguos se rechazan.
- Desconexión produce estado incierto/offline y no duplicación.
- Controlador reiniciable y estado reconciliable.
- Backup/restauración comprobados con checksums y prueba funcional.
- Métricas, errores y límites por nodo documentados.
- Sin servicio ni licencia obligatoria de pago.
- Manual completo en español de instalación, operación, recuperación y diagnóstico.

## Criterios de rechazo o repetición
Repetir si se desconoce una licencia, las mediciones no son comparables, cambian parámetros sin registro, no pueden reconstruirse incidencias, aparece más de un propietario, ADB/consolas se exponen a redes no confiables, estimaciones se presentan como mediciones o la solución depende de cloud/trial/pago obligatorio.

## Entregables
- Entorno, versiones y licencias; SBOM preliminar.
- Logs redactados y comandos reproducibles.
- Métricas por nodo/escenario.
- Registro de fallos, causa probable, solución y repetición.
- Comparativa basada en evidencia y actualización de ADR-003.
- Manual del módulo clúster y actualización de matriz de paridad.
- Separar funciones propias del clúster de equivalencias reales con GeeLark.

## Plantilla de resultados

| Campo | Resultado |
|---|---|
| ID de ejecución / fecha / protocolo | Pendiente |
| Nodos / firmware / Debian / runtime Android | Pendiente |
| Motor / imagen / ABI | Pendiente |
| Licencias verificadas | Pendiente |
| Inicio Android (mediana/p95) | Pendiente |
| CPU/RAM por escenario | Pendiente |
| Instancias estables por nodo | Pendiente |
| Errores/bloqueos | Pendiente |
| Desconexión/reconciliación | Pendiente |
| Backup/restauración | Pendiente |
| Incidencias y soluciones | Pendiente |
| Recomendación y evidencia | Pendiente |

**Estado real:** plan documental pendiente de ejecución. El aprovisionamiento integral todavía no está validado en hardware físico.
