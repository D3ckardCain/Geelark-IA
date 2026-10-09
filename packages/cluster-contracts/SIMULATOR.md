# Simulador de runtime Android (solo pruebas)

Este módulo es un doble de prueba determinista en memoria para validar la interacción del plano de control con un adaptador de runtime antes de seleccionar o instalar un motor Android real.

## Qué valida
- Inicio y detención simulados con la máquina de estados del paquete.
- Rechazo de epochs que no coinciden con la asignación registrada.
- Idempotencia durante la vida del objeto: misma clave y mismo payload devuelve el mismo resultado; reutilizar la clave con otro payload se rechaza.
- Inspección sin modificar estado.

## Qué NO hace
- No ejecuta Android, ADB, QEMU, redroid, contenedores, procesos ni comandos de shell.
- No persiste estado: al cerrar el proceso se pierde todo.
- No autentica nodos, no sustituye las comprobaciones transaccionales de PostgreSQL ni el fencing persistente.
- No mide rendimiento ni demuestra compatibilidad con aplicaciones o paridad con GeeLark.

## Pruebas

Con el paquete de contratos y pytest instalados en el entorno:

```bash
python -m pytest packages/cluster-contracts/tests -q
```

El simulador usa solo la biblioteca estándar de Python además del paquete de contratos existente. No necesita Supabase, APIs, servicios cloud ni cambios en las PC físicas.
