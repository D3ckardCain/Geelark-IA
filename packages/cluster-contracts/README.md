# Contratos del clúster Geelark-IA

Paquete inicial de modelos de mensajes para el plano de control y los agentes de nodo. Solo valida estructura y coherencia local del payload; no implementa transporte, autenticación, persistencia, autorización, fencing, idempotencia durable ni consenso.

## Requisitos
- Python 3.11 o posterior.
- Pydantic 2.x.
- pytest para ejecutar las pruebas.

## Instalación y pruebas locales

Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "packages/cluster-contracts[test]"
python -m pytest packages/cluster-contracts/tests -q
```

En Windows PowerShell, activar el entorno con `.venv\Scripts\Activate.ps1`.

Las dependencias son software libre y no requieren API ni servicio cloud. La primera instalación puede necesitar acceso a un índice de paquetes para descargar dependencias; después, las pruebas de estos modelos se ejecutan localmente. Para entornos totalmente desconectados, preparar previamente un conjunto de paquetes compatible y verificado.

## Alcance actual
Modelos implementados: envelope común, telemetría CPU/RAM/volúmenes, heartbeat, requisitos Android, reserva de recursos, orden de asignación, códigos de error y resultado de operación.

No se debe usar este paquete como única barrera de seguridad. El servidor debe verificar autorización, epoch durable, idempotencia, elegibilidad, propietario de instancia y estado de fencing.


## Máquina de estados

El paquete incluye una máquina de estados pura para rechazar transiciones peligrosas. En particular, un estado `unknown` solo puede pasar a `reconciling`; no puede iniciar directamente en otro nodo. `running` no puede saltar directamente a `stopped` sin pasar por `stopping` y una confirmación del adaptador.

Estas funciones solo validan la transición local. La capa de persistencia deberá aplicar las reglas de forma transaccional y verificar propiedad, epoch y fencing; esta máquina no evita por sí sola carreras entre procesos o nodos.
