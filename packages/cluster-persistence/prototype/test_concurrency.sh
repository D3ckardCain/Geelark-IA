#!/usr/bin/env bash
set -euo pipefail

# Prueba de concurrencia del índice parcial. Solo usar en la base desechable de CI.
# Demuestra exclusión mutua de reservas activas en PostgreSQL; no sustituye
# la transacción completa del servicio de asignación.
psql -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO cluster_control.nodes (node_id, display_name, admin_state, health_state)
VALUES
 ('11000000-0000-4000-8000-000000000001', 'concurrency-node-a', 'active', 'healthy'),
 ('11000000-0000-4000-8000-000000000002', 'concurrency-node-b', 'active', 'healthy');

INSERT INTO cluster_control.instances
 (instance_id, display_name, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('22000000-0000-4000-8000-000000000001', 'concurrency-instance', 'stopped', 'stopped', NULL, 0);
SQL

insert_reservation() {
  local reservation_id="$1"
  local node_id="$2"
  local epoch="$3"
  psql -v ON_ERROR_STOP=1 -c "
    INSERT INTO cluster_control.resource_reservations
      (reservation_id, instance_id, node_id, assignment_epoch,
       memory_bytes, storage_bytes, cpu_units, reservation_state)
    VALUES
      ('$reservation_id',
       '22000000-0000-4000-8000-000000000001',
       '$node_id', $epoch, 1048576, 1048576, 1, 'held');
  "
}

set +e
insert_reservation   '33000000-0000-4000-8000-000000000001'   '11000000-0000-4000-8000-000000000001' 1 > /tmp/cluster-reservation-a.log 2>&1 &
pid_a=$!
insert_reservation   '33000000-0000-4000-8000-000000000002'   '11000000-0000-4000-8000-000000000002' 2 > /tmp/cluster-reservation-b.log 2>&1 &
pid_b=$!
wait "$pid_a"
status_a=$?
wait "$pid_b"
status_b=$?
set -e

successes=0
failures=0
[[ "$status_a" -eq 0 ]] && successes=$((successes + 1)) || failures=$((failures + 1))
[[ "$status_b" -eq 0 ]] && successes=$((successes + 1)) || failures=$((failures + 1))

if [[ "$successes" -ne 1 || "$failures" -ne 1 ]]; then
  echo "FAIL: expected exactly one concurrent insert to succeed; A=$status_a B=$status_b"
  cat /tmp/cluster-reservation-a.log /tmp/cluster-reservation-b.log
  exit 1
fi

active_count="$(psql -At -v ON_ERROR_STOP=1 -c "
  SELECT count(*)
  FROM cluster_control.resource_reservations
  WHERE instance_id = '22000000-0000-4000-8000-000000000001'
    AND reservation_state IN ('held','uncertain');
")"

if [[ "$active_count" != "1" ]]; then
  echo "FAIL: expected exactly one active reservation, got $active_count"
  exit 1
fi

echo "PASS: two concurrent reservation attempts produced exactly one active reservation."
