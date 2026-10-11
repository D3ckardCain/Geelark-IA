# Contrato HTTP — API de snapshots para el panel PC-MASTER v1

**Estado:** contrato de integración propuesto; el endpoint todavía no está implementado ni desplegado.

## Endpoint

GET /admin/v1/status/snapshots

- Solo lectura. No admite query parameters, payloads ni acciones mutables.
- Debe servirse en el mismo origen que el panel.
- Requiere una sesión de operador autenticada y autorizada por el backend. La interfaz no acepta tokens, no guarda credenciales y no concede permisos.
- Respuestas protegidas: Cache-Control: no-store, Content-Type: application/json.
- El backend debe usar una identidad PostgreSQL con permisos SELECT estrictamente necesarios. Nunca usar credenciales administrativas en el proceso web.
- Respuesta máxima: 500 snapshots. Timeout de consulta y límite de tamaño obligatorios.
- Si falta autenticación/autorización: 401/403. Si el servicio no está listo: 503. Nunca sustituir errores por datos ficticios.
- No habilita reconciliación, ejecución de tareas, ADB, shell ni mutaciones.

## Respuesta 200

    {
      "schema_version": "1.0",
      "generated_at": "2026-10-11T12:00:00Z",
      "snapshots": [
        {
          "schema_version": "1.0",
          "snapshot_id": "uuid",
          "generated_at": "2026-10-11T12:00:00Z",
          "source": "master-live",
          "node": {
            "node_id": "uuid",
            "display_name": "WORKER-01",
            "authorization_state": "active",
            "health_state": "healthy",
            "last_heartbeat_at": "2026-10-11T11:59:45Z",
            "agent_version": "1.0.0",
            "capabilities": ["heartbeat-v1"],
            "modules": [],
            "reported_health_state": "healthy"
          },
          "freshness": {
            "state": "fresh",
            "age_seconds": 15,
            "threshold_seconds": 90,
            "observed_at": "2026-10-11T11:59:45Z"
          }
        }
      ]
    }

El snapshot individual debe cumplir docs/contracts/master-worker-status-v1.schema.json. El ejemplo anterior es ilustrativo, no evidencia de un Worker real.

## Reglas de interpretación

- health_state lo deriva el Master; no copiar sin validar reported_health_state.
- unknown, missing o stale nunca se consideran saludables.
- authorization_state y health_state son independientes.
- Los módulos se limitan al registro cerrado del contrato v1. Un módulo ausente no se muestra como operativo.
- El panel escapa todos los valores remotos y no persiste snapshots en el navegador.
- La respuesta debe excluir credenciales, tokens, payloads de tareas, logs libres, rutas locales e información sensible.

## Puertas previas a despliegue

1. Implementar la capa HTTP en el servicio del Master; no añadir endpoint administrativo al transporte Worker.
2. Integrar autenticación/autorización de operador existente o una solución revisada; denegar por defecto.
3. Verificar con pruebas que el rol de base de datos no puede escribir y que no se filtra información sensible.
4. Probar 401/403/503, respuesta malformada, timeouts, datos obsoletos y límites de tamaño.
5. Ejecutar CI y revisión manual de seguridad.
6. Desplegar solo después de revisión humana explícita. No probar en PCs físicas sin autorización.

## Coste y offline

La interfaz sigue funcionando sin conexión para navegación, filtros y ejemplo ficticio explícito. Consultar nodos reales requiere conexión con el servicio autenticado. Este contrato no requiere servicios ni APIs de pago; el coste final de hosting depende de la infraestructura existente y debe seguir siendo $0 USD.
