# Especificación inicial del motor RPA

**Estado:** diseño v0.1, previo a implementación.  
**Objetivo:** automatización reproducible, visible, limitada y recuperable en Android virtualizado.

## 1. Diseño

RPA será un grafo dirigido de bloques tipados. Cada bloque tiene esquema de entrada, permisos requeridos, timeout, política de reintento, efectos esperados y condición de salida. No se ejecutarán expresiones arbitrarias, JavaScript, Python ni shell como mecanismo normal de automatización.

## 2. Tipos iniciales de bloques

- Control: inicio, fin, espera, condición, bucle limitado y llamada a subflujo.
- UI: tap por coordenadas, texto, swipe, tecla/atrás y captura de pantalla.
- Semántica: localizar elemento por texto/selector accesible cuando el motor lo permita; reportar no soportado si no hay árbol UI.
- Aplicaciones: abrir, cerrar, comprobar instalada e instalar APK aprobado.
- Estado: comprobar paquete/actividad, esperar elemento y validar texto/imagen.
- Datos: variables tipadas, plantilla de texto y fecha/hora local.
- Archivos: elegir artefacto de Library; importar/exportar solo por rutas permitidas.
- Instancias: ejecutar acción en una instancia o lista explícita.
- Control de ejecución: pausa, cancelación, checkpoint y resultado.
- Diagnóstico: evento redactado, captura opcional y motivo de fallo.

## 3. Seguridad y límites

- Ningún bloque ejecuta shell arbitrario por defecto.
- Límite de duración total y por bloque.
- Límite de iteraciones y profundidad de subflujos.
- Límite de acciones por minuto y concurrencia configurable.
- Botón de parada inmediata y cancelación cooperativa.
- Acciones destructivas requieren permiso explícito.
- Secretos referenciados por ID de almacén, nunca incrustados en el flujo.
- Logs con datos sensibles redactados; capturas desactivadas por defecto para apps sensibles.
- Cada ejecución registra versión del flujo, instancia, hora, bloque, resultado y error estable.
- Reintentar solo cuando la acción se declare idempotente o el usuario confirme.
- Flujos compartidos se validan como entrada no confiable.

## 4. Estados de ejecución

draft, validated, queued, running, pause_requested, paused, cancel_requested, cancelled, succeeded, failed y needs_review.

Las transiciones se persisten; tras reinicio, ejecuciones interrumpidas pasan a needs_review salvo que el bloque actual sea recuperable y seguro.

## 5. Modelo de sincronización

La sincronización entre instancias no duplica automáticamente todos los eventos. Define:
- instancia fuente;
- lista explícita de instancias destino;
- acciones permitidas;
- exclusiones por instancia;
- retraso opcional;
- política de error: continuar, detener todas o detener solo la fallida;
- registro por acción/instancia.

No sincronizar contraseñas, tokens o información privada sin selección explícita. Detectar y mostrar diferencias de resolución, idioma, estado de app y permisos.

## 6. Criterios de aceptación del primer MVP

- Crear y guardar un flujo simple de 3–5 bloques.
- Validarlo antes de ejecutar.
- Ejecutarlo en una instancia de prueba y mostrar estado por bloque.
- Pausarlo, reanudarlo y cancelarlo.
- Simular timeout y error del motor.
- Recuperar una ejecución interrumpida sin duplicar acciones no idempotentes.
- Comprobar límites de bucle y duración.
- Confirmar que los logs no contienen secretos.
- Exportar/importar un flujo validando esquema y versión.
- Documentar cada bloque y sus limitaciones en el manual en español.
