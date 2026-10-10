# Manual del supervisor de agente

## Estado
La rama `feat/agent-supervisor-heartbeat` añade un supervisor saliente de telemetría. Aún está en revisión y no está desplegado.

## Funciones
- Enviar heartbeat periódico.
- Publicar capacidades declarativas.
- Consultar el estado del propio nodo.
- Sincronizar recibos ya guardados en SQLite.
- Mantener la telemetría separada del sincronizador de recibos.

El supervisor no reclama tareas, no acepta tareas, no ejecuta Android/ADB/shell y no abre puertos de escucha. Los nodos pendientes conservan la política del controlador: heartbeat, capacidades y consulta de su propio estado solamente.

## Requisitos
- Python 3.11 o superior.
- Paquetes locales `cluster-agent-guard` y `cluster-agent-transport`.
- Controlador HTTPS con certificado válido para una CA local y una IP privada/loopback.
- Archivo de configuración TOML y credencial protegida por permisos del sistema operativo.

## Instalación de desarrollo
En un entorno virtual desde la raíz del repositorio:

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e packages/cluster-agent-guard
python -m pip install -e "packages/cluster-agent-transport[test]"
python -m pytest packages/cluster-agent-transport/tests -q
```

Son instrucciones para una futura prueba autorizada; no se han ejecutado en PCs físicas.

## Configuración
El TOML debe declarar `node_id`, `controller_url`, `ca_cert`, `journal_path`, `credential_file`, `agent_version` y una lista `capabilities`. Los intervalos de heartbeat, capacidades y consulta de estado son configurables. La dirección del controlador debe ser una IP privada/loopback literal y usar HTTPS; no se permite desactivar la validación de certificados.

La credencial debe estar en un archivo regular privado, sin permisos de grupo/otros, pertenecer al usuario del proceso y contener únicamente el valor hexadecimal esperado. No guardarla en el TOML, el repositorio ni los logs. La rotación y revocación deben gestionarse desde el controlador y el sistema operativo.

## Offline
SQLite conserva recibos locales durante interrupciones y reinicios. Heartbeat, capacidades, estado y entrega de recibos requieren conexión con el controlador. El supervisor no sondea la red continuamente: la detección automática de reconexión mediante el servicio del sistema sigue pendiente.

## Límites y seguridad
- No existe aún un servicio systemd validado ni un instalador de producción.
- La reconciliación de estado `unknown` debe seguir deshabilitada.
- No se ha probado en hardware físico.
- Mantener los PR en borrador hasta revisar seguridad, verificar CI del HEAD exacto y obtener autorización explícita antes de despliegue.
- El diseño no requiere APIs de pago ni servicios externos obligatorios; el hardware, electricidad y red local siguen teniendo costes propios.
