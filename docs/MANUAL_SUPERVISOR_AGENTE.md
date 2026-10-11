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

La credencial debe estar en un archivo regular privado, sin permisos de grupo/otros, pertenecer al usuario del proceso y contener únicamente el valor hexadecimal esperado. Los directorios padre deben ser directorios reales, no enlaces simbólicos, pertenecer a root o al usuario del agente y no ser modificables por grupo/otros (se permite el bit sticky en ancestros del sistema como `/tmp`, pero no se recomienda guardar secretos allí). No guardarla en el TOML, el repositorio ni los logs.

### Rotación y revocación

El agente no rota credenciales automáticamente. La revocación se realiza desde el procedimiento administrativo del controlador; la nueva credencial debe entregarse por un canal confiable y escribirse en el archivo protegido. No registrar ni copiar el valor a tickets. Tras sustituirla, reiniciar el agente y comprobar que vuelve el heartbeat mediante los logs de códigos genéricos. El procedimiento completo de emisión/rotación desde el controlador sigue pendiente de documentar; no inventar ni habilitar endpoints de emisión en esta fase.

## Offline
SQLite conserva recibos locales durante interrupciones y reinicios. Heartbeat, capacidades, estado y entrega de recibos requieren conexión con el controlador. El supervisor no sondea la red continuamente: la detección automática de reconexión mediante el servicio del sistema sigue pendiente.

## Límites y seguridad
- No existe aún un servicio systemd validado ni un instalador de producción.
- La reconciliación de estado `unknown` debe seguir deshabilitada.
- No se ha probado en hardware físico.
- Mantener los PR en borrador hasta revisar seguridad, verificar CI del HEAD exacto y obtener autorización explícita antes de despliegue.
- El diseño no requiere APIs de pago ni servicios externos obligatorios; el hardware, electricidad y red local siguen teniendo costes propios.


## Comparación funcional con GeeLark como referencia

Esta fase cubre solo una base de gestión de nodos: estado/heartbeat, capacidades, conexión segura y entrega durable de recibos. No equivale a las funciones de GeeLark para crear/administrar teléfonos en la nube, perfiles, aplicaciones Android, automatizaciones ni operación visual. No afirmar paridad funcional en esta fase.

La siguiente evaluación debe comparar cada módulo futuro con la función equivalente de GeeLark, documentar diferencias y pruebas, y mantener deshabilitada toda ejecución Android hasta que exista un diseño de permisos, aislamiento, auditoría y aprobación independiente.

## Proveedores de credenciales

El modo predeterminado `credential_provider = "file"` usa `credential_file` y valida permisos privados, contenido hexadecimal, directorios padre y ausencia de symlinks. No poner el token en el TOML ni en argumentos de línea de comandos.

En Linux/systemd se puede seleccionar `credential_provider = "systemd"` y `systemd_credential_name = "geelark-agent-token"`. El adaptador lee desde `CREDENTIALS_DIRECTORY` (o desde `credentials_directory` si se configura explícitamente) y rechaza permisos inseguros, symlinks, archivos no regulares y contenido inválido. No hay unit file ni instalador aprobado; no activar este modo en producción hasta validar el procedimiento administrativo de emisión/rotación/revocación.

La fábrica `build_agent_components()` permite inyectar cualquier `CredentialProvider` compatible y devuelve cliente, runtime, sincronizador y supervisor sin iniciar hilos.


## Evidencia de CI en la pila canónica

La validación combinada del supervisor sobre la bandeja #52 y el sincronizador #57 pasó en GitHub Actions run 38124797722 en HEAD `4aa8363f06737ebaca85adfb8740dc846e7bfa6a`: 131 pruebas aprobadas, 1 advertencia deprecatoria Starlette/httpx y `pip check` correcto. Esta evidencia cubre el código del supervisor y su integración en la pila canónica; la CI no prueba instalación ni funcionamiento en equipos físicos.
