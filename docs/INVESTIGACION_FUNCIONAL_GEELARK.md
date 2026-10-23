# Investigación funcional de GeeLark — registro inicial

**Fecha de consulta:** 2026-10-09  
**Estado:** investigación documental inicial; no equivale a auditoría completa ni a pruebas directas dentro del cliente.  
**Idioma de registro:** español.  
**Alcance del proyecto:** replicar funciones de GeeLark aplicables a Android mediante entornos Android virtualizados/emulados en hardware anfitrión local, sin teléfonos físicos como requisito y sin servicios cloud obligatorios. iOS queda excluido.

## 1. Conclusión ejecutiva

GeeLark no es solamente un emulador Android. La documentación y las páginas públicas describen una plataforma que combina:

- perfiles de cloud phone Android;
- configuración y asignación de proxies;
- huella/configuración de dispositivo por perfil;
- aplicaciones y gestión de archivos;
- biblioteca de contenido;
- automatización RPA visual y plantillas;
- sincronización de acciones entre varios dispositivos;
- API, ADB y webhooks;
- analítica, logs, grupos, miembros y permisos;
- funciones de IA y generación de contenido;
- recursos/marketplace, facturación y gestión del servicio.

La infraestructura original es cloud: los teléfonos Android se ejecutan en infraestructura remota de GeeLark. Nuestro diseño sustituirá ese plano de ejecución por Android virtualizado/emulado localmente. Esta sustitución cambia las restricciones de rendimiento, compatibilidad, aislamiento, red, identidad del dispositivo y escalabilidad; por ello, no se debe asumir equivalencia automática.

## 2. Alcance y método de evidencia

Cada afirmación se clasifica así:

- **Documentado públicamente:** se describe en una página oficial o en el centro de ayuda.
- **Inferencia de diseño:** conclusión técnica que debe validarse antes de convertirse en requisito.
- **Pendiente de verificar:** requiere inspección más profunda de documentación, cliente, opciones y flujos.
- **No equivalente por defecto:** requiere una alternativa local o podría tener diferencias estructurales.

No se ha probado todavía la aplicación de escritorio de GeeLark ni se han verificado todas las opciones de cada pantalla. Este documento no debe leerse como una auditoría exhaustiva.

## 3. Inventario funcional documentado inicialmente

### 3.1 Perfiles / teléfonos Android en la nube
**Evidencia:** https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8  
La ayuda describe creación individual, rápida y por lotes; grupos; selección de sistema operativo; proxy; selección de modelo/versión Android; configuración del perfil y límites según plan. La creación rápida y por lotes se indica como función de plan Pro.

**Adaptación local por investigar:** crear instancias Android virtualizadas locales, nombrarlas, agruparlas, definir recursos, guardar snapshots/configuración y administrar su ciclo de vida. Confirmar qué virtualizadores permiten una experiencia Android completa y qué límites de aceleración gráfica, ARM/x86, sensores, Play Services y compatibilidad de apps aplican.

### 3.2 Huella e identidad del dispositivo
**Evidencia:** la página de cloud phone afirma que cada dispositivo tiene una huella única: https://www.geelark.com/es/producto/cloud-phone/  
La página de precios incluye una capacidad llamada “Custom device fingerprint”: https://www.geelark.com/es/pricing/

**Límite importante:** las páginas públicas no revelan por sí solas todos los campos, mecanismos ni garantías de esa huella. No asumir que consiste solo en cambiar un identificador, ni que un emulador puede reproducir una identidad física completa. Investigar campos configurables, persistencia entre reinicios, independencia entre perfiles y diferencias detectables de virtualización. Documentar honestamente las limitaciones.

### 3.3 Proxies y conectividad
**Evidencia:** la creación de perfiles describe proxies guardados o personalizados y verificación de conexión/localización: https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8  
**Adaptación local:** catálogo de proxies, credenciales protegidas, validación, asignación por instancia y diagnóstico. El sistema puede gestionar endpoints aportados por el usuario; no se promete proveer proxies gratuitos fiables. Un proxy no cambia automáticamente GPS, SIM, IP móvil ni todos los indicadores del dispositivo.

### 3.4 Automatización: plantillas, RPA y Synchronizer
**Evidencia:** https://www.geelark.com/features/automation/ y https://www.geelark.com/features/rpa/  
La web describe plantillas listas, flujos RPA visuales, acciones como toques, deslizamientos, escritura, espera, carga de archivos, lógica condicional, bucles, variables y manejo de errores. Synchronizer replica acciones compatibles desde una ventana principal a otros dispositivos, incluida entrada de texto y entrada masiva de texto diferente.

**Adaptación local:** editor visual de flujos, motor de ejecución, plantillas versionadas, cola persistente, sincronización de eventos, selección explícita de instancias, pausas, cancelación, reintentos y registros. Verificar las acciones reales y sus parámetros con documentación detallada y pruebas.

### 3.5 API, ADB y webhooks
**Evidencia:** https://www.geelark.com/features/api/ y https://help.geelark.com/ADB-1600be7d9e418006b80cf649bcdc80ad  
La página API menciona operaciones de ciclo de vida de cloud phones, automatización, apps, archivos, Library, ADB y webhooks. La guía ADB describe habilitar ADB en un perfil, iniciar el teléfono cloud y conectarse mediante dirección IP/puerto y un código de acceso.

**Adaptación local:** API/CLI local para instancias, apps, archivos, tareas y eventos. Usar ADB solo en las interfaces que exponga el entorno virtualizado. No depender de API de GeeLark ni de sus endpoints privados.

### 3.6 Aplicaciones y operaciones masivas
**Evidencia:** el centro de ayuda lista Applications y notas de versión documentan acciones de apertura, cierre, reinicio, desinstalación y actualización de aplicaciones por grupos de perfiles: https://help.geelark.com/ y https://help.geelark.com/v3-8-0-3080be7d9e41816a8b2bc0bbc2964ed1?pvs=21  
**Adaptación local:** inventario de paquetes por instancia, instalación de APK, abrir/cerrar, versión, actualización, asignación por grupos y resultados por dispositivo. La viabilidad depende de permisos Android, arquitectura APK, Play Services y restricciones del sistema.

### 3.7 Library / archivos multimedia
**Evidencia:** https://help.geelark.com/Library-1c20be7d9e41800a8535ea943b930bd4  
Library centraliza fotos y videos, permite subir archivos, importar desde servicios compatibles y usarlos en automatización. La página consultada menciona hasta 100 GB y borrado a los 30 días para el servicio GeeLark.

**Adaptación local:** biblioteca persistente local con etiquetas, búsqueda, metadatos, deduplicación, vista previa, asignación a flujos y política de retención configurable. No copiar límites de almacenamiento temporales del producto cloud como requisitos del sistema local.

### 3.8 IA / AIGC
**Evidencia:** el centro de ayuda lista AIGC, AI Generation Function y manuales de funciones de IA: https://help.geelark.com/  
**Adaptación local:** inventariar por separado cada función (texto, imagen, video, edición, subtítulos, asistente). Evaluar modelos locales según hardware y licencia. Si una función requiere un servicio comercial, debe tener alternativa local o marcarse como no equivalente. No asumir paridad de calidad ni velocidad sin pruebas.

### 3.9 Analítica, registros y auditoría
**Evidencia:** el centro de ayuda y la página de precios incluyen Analytics y Operation Logs; Analytics se lista como función Pro en la página consultada: https://www.geelark.com/es/pricing/  
**Adaptación local:** métricas de ejecución, errores, duración, uso de CPU/RAM/GPU/almacenamiento, resultados por instancia y exportación. Las métricas se basarán solo en datos locales que realmente se puedan observar.

### 3.10 Grupos, miembros, roles y permisos
**Evidencia:** el centro de ayuda lista Groups y Members; la página de precios incluye gestión de roles/permisos y transferencia de perfiles en planes indicados: https://help.geelark.com/ y https://www.geelark.com/es/pricing/  
**Adaptación local:** grupos de instancias, roles, permisos mínimos, auditoría y posible modo multiusuario LAN. Mantener el uso local de un operador como primera versión solo si no impide la paridad requerida; la decisión final queda pendiente de análisis completo.

### 3.11 Recursos, marketplace y plantillas
**Evidencia:** el centro de ayuda lista Resources y la web de automatización habla de plantillas listas y marketplace: https://help.geelark.com/ y https://www.geelark.com/features/automation/  
**Adaptación local:** repositorio de plantillas/recursos importables, validación, versionado, firma/hash opcional y exportación. No asumir acceso al catálogo propietario ni copiar recursos sin licencia.

### 3.12 Facturación, límites y funciones comerciales
**Evidencia:** https://www.geelark.com/es/pricing/ y https://help.geelark.com/billing-basics?invite_code=Jn5qUj  
La página consultada indica 2 perfiles y 30 minutos de uso de cloud phone en el plan gratuito, cobro por minuto tras el periodo gratuito, además de alquiler mensual, paralelos y paquetes de tiempo de pago. Algunas capacidades aparecen restringidas por plan.

**Implicación:** el coste de ejecución cloud de GeeLark no cumple el objetivo permanente de $0. No usar su servicio cloud como dependencia del proyecto. La facturación comercial de GeeLark no se replica como cobro real; se sustituye por gestión local de recursos, límites configurables y medición de uso. Se debe revisar periódicamente la página oficial, ya que precios y planes pueden cambiar.

### 3.13 Cámara, sensores, SIM y hardware virtual
**Evidencia parcial:** la página española del producto indica que los cloud phones no incluyen tarjeta SIM ni eSIM y no permiten llamadas ni SMS: https://www.geelark.com/es/producto/cloud-phone/  
La ayuda también lista una guía para usar la cámara del cloud phone: https://help.geelark.com/

**Pendiente:** documentar cámara, GPS, sensores, portapapeles, notificaciones, almacenamiento, llamadas/SMS, biometría, audio, rotación, resolución y cualquier puente con dispositivos locales. No asumir que todos los sensores o servicios están emulados igual en todas las versiones.

## 4. Matriz inicial de estado

| Área | Evidencia pública inicial | Adaptación local prevista | Estado |
|---|---|---|---|
| Perfiles Android | Creación individual/rápida/masiva | Gestión de instancias virtuales | Investigación inicial |
| Identidad/huella | Huella única y opción de huella personalizada | Perfilado por instancia; límites por investigar | Pendiente de profundizar |
| Grupos | Documentación de grupos | Agrupar y etiquetar instancias | Investigación inicial |
| Proxies | Gestión y verificación | Configuración por instancia | Investigación inicial |
| Aplicaciones | Centro de ayuda y operaciones masivas | Paquetes y operaciones por instancia | Investigación inicial |
| Archivos/Library | Biblioteca multimedia central | Biblioteca local persistente | Investigación inicial |
| RPA | Editor visual y lógica de flujo | Motor y editor local | Investigación inicial |
| Plantillas | Marketplace y flujos predefinidos | Catálogo local importable | Investigación inicial |
| Synchronizer | Acciones en tiempo real y texto masivo | Replicación local multiinstancia | Investigación inicial |
| API/CLI/ADB | API y guía ADB | API/CLI local y puente ADB | Investigación inicial |
| Webhooks/eventos | Callbacks documentados en la página API | Eventos locales | Investigación inicial |
| Analytics/logs | Funciones de análisis y registros | Observabilidad local | Investigación inicial |
| Miembros/permisos | Roles y permisos por plan | Roles locales/LAN | Investigación inicial |
| IA/AIGC | Área de IA y generación | Modelos locales según hardware | Pendiente de profundizar |
| Recursos | Área Resources | Recursos locales | Investigación inicial |
| Facturación/planes | Límites comerciales y cobro cloud | No replicar cobros; medir recursos localmente | Diferencia estructural |
| Instalación/actualización | Centro de ayuda y notas de versión | Instalador/actualizador local | Pendiente de profundizar |
| Offline | No es el foco del servicio cloud | Diseño local con limitaciones explícitas | Requisito propio |

## 5. Riesgos y preguntas técnicas que deben resolverse

1. ¿Qué plataforma de virtualización permite instancias Android completas, estables y con aceleración en el hardware anfitrión disponible?
2. ¿Qué arquitectura de CPU del anfitrión y de las imágenes Android será compatible con las aplicaciones objetivo?
3. ¿Qué componentes de Google/Play Services son necesarios y cómo se obtienen legalmente?
4. ¿Qué campos de identidad de GeeLark son configurables, cuáles persisten y cuáles no se pueden reproducir honestamente en virtualización?
5. ¿Qué límites de CPU, RAM, GPU, almacenamiento y ancho de banda aparecen al ejecutar varias instancias?
6. ¿Qué funciones de GeeLark dependen de servicios propietarios, modelos comerciales o infraestructura cloud?
7. ¿Qué capacidades de cámara, GPS, sensores, red y notificaciones se pueden simular y cuáles requieren hardware externo?
8. ¿Qué funciones deben estar disponibles sin Internet y cuáles necesitan conectividad externa para cumplir su propósito?

## 6. Próximos pasos de investigación

1. Recorrer todos los artículos del Centro de ayuda, no solo las páginas comerciales.
2. Desglosar cada menú en funciones, campos, acciones, estados y errores.
3. Extraer los detalles del manual RPA y del API para crear un catálogo de acciones/endpoints.
4. Analizar notas de versión para detectar funciones añadidas o cambiadas.
5. Completar matriz de paridad con evidencia por fila.
6. Comparar opciones de virtualización Android local sin elegir stack hasta documentar compatibilidad, licencias y límites.
7. Registrar resultados de pruebas prácticas en issues y actualizar este documento.

## 7. Fuentes oficiales consultadas

- Centro de ayuda: https://help.geelark.com/
- Perfiles: https://help.geelark.com/Profile-e60c92ba743748a697c07551f59812b8
- Producto cloud phone en español: https://www.geelark.com/es/producto/cloud-phone/
- Precios en español: https://www.geelark.com/es/pricing/
- Facturación: https://help.geelark.com/billing-basics?invite_code=Jn5qUj
- Library: https://help.geelark.com/Library-1c20be7d9e41800a8535ea943b930bd4
- ADB: https://help.geelark.com/ADB-1600be7d9e418006b80cf649bcdc80ad
- Automatización: https://www.geelark.com/features/automation/
- RPA: https://www.geelark.com/features/rpa/
- API: https://www.geelark.com/features/api/
- Synchronizer: https://www.geelark.com/features/synchronizer/
- Nota de versión sobre aplicaciones: https://help.geelark.com/v3-8-0-3080be7d9e41816a8b2bc0bbc2964ed1?pvs=21

## 8. Registro de cambios

- 2026-10-09: primera investigación documental consolidada; se aclara que GeeLark es una plataforma integrada de cloud phones, gestión, automatización, sincronización, API y recursos, no solo un emulador.
- 2026-10-09: se fija el alcance de nuestro proyecto en Android virtualizado/emulado localmente en hardware anfitrión; no se presupone el uso de teléfonos físicos.


## 9. Investigación preliminar de motores Android local

Esta sección es una comparación de candidatos, no una selección definitiva. El motor final debe probarse con aplicaciones Android objetivo, identidad por instancia, ADB, automatización, persistencia, aislamiento, gráficos y consumo de recursos.

### Candidato A — redroid

Fuente: https://github.com/remote-android/redroid-doc y https://github.com/Nredroid

La documentación pública describe Android en contenedores para hosts Linux, aceleración GPU, arquitectura amd64/arm64 y posibilidad de ejecutar múltiples instancias. La lista pública consultada incluye imágenes Android 9 a 17, según etiqueta/variante.

**Ventajas potenciales:** orientado a múltiples instancias, automatización y operación tipo servicio; puede ajustarse al requisito de instancias locales.  
**Riesgos/preguntas:** requisitos de kernel y GPU, configuración de contenedores privilegiados, compatibilidad de apps y Play Services, manejo de identidad, estabilidad y seguridad del host. Verificar licencia de cada repositorio e imagen antes de distribuir o usar comercialmente. No asumir que la imagen Android base equivale a un teléfono real.

### Candidato B — Android Emulator oficial

Fuentes: https://developer.android.com/studio/run/emulator-acceleration y https://developer.android.google.cn/studio/run/emulator?hl=es-419

La documentación oficial explica aceleración de virtualización mediante el hipervisor del sistema operativo y publica requisitos mínimos orientativos de 16 GB de RAM para una experiencia adecuada. La ruta de aceleración depende del sistema operativo y de las extensiones de virtualización del procesador.

**Ventajas potenciales:** herramientas oficiales Android, compatibilidad de desarrollo, imágenes de distintas versiones y herramientas de prueba conocidas.  
**Riesgos/preguntas:** está orientado principalmente a desarrollo y pruebas; la densidad de instancias, control centralizado, rendimiento prolongado y personalización de identidad deben medirse. En Windows, la documentación indica que Android Emulator Hypervisor Driver (AEHD) dejará de mantenerse el 31 de diciembre de 2026 y recomienda migrar a Windows Hypervisor Platform.

### Candidato C — Waydroid

Fuentes: https://github.com/waydroid/waydroid y https://github.com/waydroid/docs

Waydroid usa contenedores Linux para ejecutar un sistema Android basado en LineageOS; la documentación consultada menciona Android 13 para su imagen actual. Requiere GNU/Linux compatible y acceso a componentes del host.

**Ventajas potenciales:** software libre, integración con Linux y ejecución local.  
**Riesgos/preguntas:** su modelo de contenedor e integración de escritorio puede no ofrecer aislamiento de dispositivo completo ni una granja de perfiles independientes de forma directa. Debe comprobarse si puede sostener la semántica de perfiles y aislamiento que requiere GeeLark.

### Candidato D — Android-x86 en máquina virtual

Fuentes: https://www.android-x86.org/source.html y https://www.android-x86.org/

Android-x86 permite ejecutar compilaciones Android para x86 en hardware compatible y máquinas virtuales como QEMU o VirtualBox. El proyecto declara Apache License 2.0 para el proyecto base y GPL para algunos componentes.

**Ventajas potenciales:** aislamiento por máquina virtual y compatibilidad con hipervisores comunes.  
**Riesgos/preguntas:** versiones y mantenimiento disponibles, sensores simulados, arquitectura x86 frente a aplicaciones que requieren ARM, Play Services, gráficos y costes de recursos por instancia.

### Criterios de selección obligatorios

1. Licencia de motor, imagen, componentes Android, herramientas y complementos.
2. Posibilidad de crear, clonar, arrancar, detener, reiniciar y eliminar instancias mediante comandos/API.
3. ADB estable y captura/control de pantalla.
4. Persistencia y aislamiento de datos entre instancias.
5. Posibilidad de configurar cada instancia de forma independiente, sin afirmar que se puede falsificar cualquier identidad.
6. Compatibilidad de APK arm64-v8a, armeabi-v7a y x86_64 según necesidad.
7. Cámara, GPS, sensores, audio, notificaciones, portapapeles y aceleración gráfica.
8. Consumo de CPU, RAM, VRAM, almacenamiento y tiempo de arranque por instancia.
9. Seguridad: permisos de contenedores/VM, exposición de puertos y separación de redes.
10. Funcionamiento sin servicios cloud ni pagos obligatorios.
11. Soporte de varias instancias en el sistema operativo anfitrión seleccionado.
12. Reproducibilidad de instalación, backup, actualización y rollback.

### Conclusión provisional

No se selecciona todavía un motor. redroid parece especialmente relevante para investigar escenarios de múltiples instancias Linux; Android Emulator es el candidato de referencia para herramientas oficiales; Waydroid y Android-x86 cubren alternativas de contenedor y máquina virtual. La elección requiere una prueba comparativa en el hardware real del usuario y un inventario más preciso de las funciones de GeeLark.

## 10. Registro de cambios

- 2026-10-09: primera investigación documental consolidada; se aclara que GeeLark es una plataforma integrada de cloud phones, gestión, automatización, sincronización, API y recursos, no solo un emulador.
- 2026-10-09: se fija el alcance de nuestro proyecto en Android virtualizado/emulado localmente en hardware anfitrión; no se presupone el uso de teléfonos físicos.
- 2026-10-09: se añade comparación preliminar de redroid, Android Emulator, Waydroid y Android-x86, sin seleccionar stack definitivo.


## Nota de vigencia estratégica — 2026-10-22

Este documento se conserva como evidencia funcional histórica/preliminar; la fecha de las fuentes funcionales originales no se actualiza por esta nota. La estrategia técnica se revisó el 2026-10-22: la ruta manual QEMU + Android-x86 + VNC está retirada; AOSP Cuttlefish es solo candidato de laboratorio y no está aprobado; redroid permanece bloqueado por la Issue #27; Android Emulator es referencia de compatibilidad y Waydroid sigue como alternativa secundaria. No se ha completado una prueba en WORKER físico ni se ha medido densidad de instancias. Antes de implementar paridad, reconciliar con la investigación ampliada de la PR #86 y distinguir evidencia documentada, inferencia, código en PR, CI por SHA y prueba real.
