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


## 7. Requisitos derivados de la referencia funcional GeeLark (2026-10-12)

La documentación pública de GeeLark describe estas familias de funciones RPA: acciones de interfaz, lógica/condiciones, bucles, variables, manejo de excepciones, ejecución/programación y revisión de estado/logs. Las guías de principiantes aportan opciones concretas para selectores y variables. Se documentan como referencia funcional, no como promesa de paridad exacta.

### 7.1 Acciones y localización

- Acciones iniciales a catalogar: abrir app, tocar/clicar elemento, pulsación prolongada, deslizar/desplazar, ingresar texto, esperar y cargar archivo aprobado.
- Modos de selector observados: texto visible, atributos (`fullId`, `desc`, `className`) y coordenadas.
- Condición del selector: coincidencia exacta o parcial.
- Orden del elemento: índice fijo o selección aleatoria dentro de un intervalo.
- Espera máxima configurable en milisegundos y opción explícita para localizar elementos no visibles.
- Cada acción debe devolver resultado tipado, al menos éxito/fallo, y una causa estable. La configuración debe admitir notas descriptivas.

### 7.2 Variables y flujo

- Tipos observados: string, number, boolean y object (referencia a elemento UI).
- Lectura de texto de un elemento, almacenamiento en variable y reutilización en acciones posteriores.
- Bucles limitados por cantidad, conjunto de elementos o datos; condiciones con ramas; manejo de excepción configurable (omitir paso o detener flujo).
- El diseño local debe detectar variables inexistentes, incompatibilidad de tipos, límites de iteración, timeout y cancelación. Todo bucle debe tener límite máximo y checkpoint cuando la recuperación sea segura.

### 7.3 Seguridad, robustez y paridad

- Preferir selectores semánticos sobre coordenadas; registrar la resolución, idioma y versión Android para diagnosticar diferencias.
- No ejecutar Python, JavaScript ni shell arbitrario como mecanismo normal de automatización.
- Aleatoriedad, si se ofrece para selección de elementos, debe ser explícita, acotada y reproducible/auditable; no debe presentarse como mecanismo para evadir controles de plataformas.
- La ejecución se asigna a una lista explícita de instancias; cada instancia necesita estado, progreso, resultado y error independiente.
- Los logs y capturas deben redactar secretos y tener política de retención configurable.

### 7.4 Fuentes de referencia

- RPA de GeeLark: https://www.geelark.com/features/rpa/
- Guía de selectores: https://www.geelark.com/es/blog-es/geelark-guia-de-rpa-para-principiantes-4/
- Variables: https://www.geelark.com/blog/geelark-rpa-guide-5/
- Visión general de automatización: https://www.geelark.com/es/blog-es/automatizacion-de-apps-android-y-navegador-geelark-rpa/

Esta sección no constituye una lista exhaustiva de los más de 40 módulos que la página comercial anuncia. Cada bloque pendiente debe registrarse con parámetros, entradas/salidas, errores, permisos, límites y prueba de aceptación antes de implementarse.
