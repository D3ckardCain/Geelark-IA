# Arquitectura tecnológica vigente — GeeLark-IA

**Actualizado:** 2026-10-22. **Estado:** arquitectura objetivo; no implica que todos los módulos estén integrados ni aceptados.  
**Alcance:** panel web PC-MASTER Windows + redroid en PC-WORKERS físicos Debian 13 + componentes necesarios de control distribuido.  
**Coste obligatorio objetivo:** 0 USD.

## 1. Decisión de alcance

- PC-MASTER es el panel web central y su servicio de control en Windows. El lanzador/configurador de escritorio es un componente separado, no el panel.
- El adaptador del motor Android permanece agnóstico. redroid es el primer candidato a evaluar, pero está bloqueado para ejecución física por #27 hasta validar la mitigación sobre la imagen/digest exactos. Cuttlefish queda como alternativa de contingencia no aprobada; Android Emulator es referencia de compatibilidad.
- Debian 13 es el sistema base previsto para los workers.
- Las rutas técnicas retiradas quedan fuera del alcance de producto.
- No instalar ningún motor Android en hardware físico hasta aprobar licencias, seguridad y plan de pruebas. La issue #27 bloquea específicamente redroid por el riesgo de `/proc/sys/kernel/modprobe`.
- GeeLark es referencia funcional pública; la implementación será independiente y local-first.

## 2. Componentes y responsabilidades

| Componente | Responsabilidad |
|---|---|
| Panel PC-MASTER Windows | UI web de administración, inventario, estado, perfiles, tareas, alertas y auditoría |
| Servicio de control Master | API privada, autenticación, autorización, configuración deseada, asignaciones y coordinación |
| Persistencia local | Estado autoritativo, operaciones, idempotencia, auditoría, reservas y outbox durable |
| Agente de Worker | Identidad del nodo, heartbeat, capacidades, recepción de órdenes tipadas, ejecución permitida y reporte |
| Motor Android (pendiente de selección) | redroid es la primera opción a evaluar; bloqueado por #27 hasta resolver seguridad; Cuttlefish queda como contingencia |
| Adaptador Android | Contrato de ciclo de vida, estado, captura/entrada, instalación de APK, archivos, persistencia y errores |
| Automatización | Flujos tipados con timeout, cancelación, límites de bucle, recuperación y resultados por paso |
| Observabilidad | Salud reportada por Worker y salud derivada por Master, logs redactados y métricas |

## 3. Plataforma prevista

- **PC-MASTER:** Windows 10/11 de 64 bits; conservar el panel web central y el lanzador separado.
- **PC-WORKERS:** Debian 13 en hardware físico; el inventario inicial de laboratorio es i5-11400, 32 GB RAM, NVMe de 500 GB y sin GPU dedicada.
- **Red:** LAN Gigabit; el servicio de agente debe usar transporte autenticado y cifrado. No publicar ADB ni el socket Docker a la LAN.
- **Runtime:** pendiente de aprobación. Evaluar redroid primero y fijar versión/digest solo tras revisar requisitos, licencias y seguridad; Cuttlefish es contingencia, no prioridad.
- **Dependencias:** paquetes libres/locales cuando sea viable; documentar licencia, versión, origen, coste, límites y procedimiento de actualización.

La densidad no se infiere del hardware: se mide primero con una instancia y después con dos. Solo se escala si las métricas y pruebas de aislamiento lo permiten.

## 4. Seguridad y autorización

- Un nodo pendiente puede informar heartbeat/capacidades y consultar un estado limitado; no recibe ni ejecuta tareas.
- La activación requiere autorización desde PC-MASTER y credenciales individuales revocables.
- La API usa HTTPS privado con CA local, autorización por operación, límites de tamaño/frecuencia, timeouts, idempotencia y protección contra repetición.
- No ofrecer shell arbitrario, comandos Docker ni ADB indiscriminado como API administrativa.
- ADB queda en loopback o en un canal explícitamente protegido.
- No arrancar redroid en hardware físico hasta resolver la issue #27 con evidencia de la imagen exacta.
- Los logs y artefactos no contienen tokens, contraseñas, cookies ni claves privadas.

## 5. Persistencia, despacho y recuperación

- Registrar operación, auditoría, idempotencia y outbox en una transacción antes de enviar una orden.
- Las órdenes llevan identificador, nodo propietario y epoch de fencing.
- Un estado incierto se reconcilia; no se libera ni reasigna automáticamente una instancia si puede seguir ejecutándose en el nodo anterior.
- Los fallos de red y reinicios no deben duplicar efectos ni borrar datos persistentes.
- La persistencia Android se separa por instancia y tiene límites y permisos explícitos.

## 6. Preparación y aceptación

1. Evaluar redroid como primera opción, resolver #27 con evidencia para imagen/digest exactos y medir una instancia aislada; Cuttlefish queda como contingencia si redroid no supera seguridad/viabilidad.
2. Mantener la issue #27 abierta hasta demostrar mitigación de redroid o descartar formalmente su uso.
3. Aprobar el aprovisionamiento de Debian 13 y ejecutar diagnóstico de solo lectura en WORKER-01.
4. Probar una instancia: inicio/parada/reinicio, ADB restringido, APK autorizada, captura/entrada, archivos, persistencia y métricas.
5. Probar dos instancias simultáneas con separación de datos, puertos y control.
6. Integrar el agente con PC-MASTER y validar enrolamiento, heartbeat, autorización, despacho, idempotencia y reconciliación.
7. Publicar manual del módulo, pruebas reproducibles, incidencias y soluciones en español.

## 7. Coste y registro

El objetivo obligatorio es 0 USD en software y servicios esenciales. Antes de adoptar una dependencia, registrar licencia, precio, requisito de tarjeta, cuotas, almacenamiento, ancho de banda, límites y riesgos. No declarar paridad con GeeLark ni capacidad de producción sin evidencia práctica.

## Fuentes y seguimiento

- [Alcance vigente](ALCANCE_PC_MASTER_REDROID.md)
- [Estado del proyecto](ESTADO_PROYECTO.md)
- [Evaluación de redroid](COMPARATIVA_MOTORES_ANDROID.md)
- [Modelo de amenazas](MODELO_AMENAZAS_SEGURIDAD.md)
- [Bloqueo de seguridad #27](https://github.com/D3ckardCain/Geelark-IA/issues/27)
- [Preparación del worker](PREPARACION_WORKER_REDROID.md)
- [Diagnóstico previo del worker](GUIA_DIAGNOSTICO_PREVIO_REDROID.md)
