#!/usr/bin/env bash
set -euo pipefail

# Prueba de concurrencia de la TRANSACCIÓN de asignación, no solo del índice.
# Solo ejecutar contra la base temporal desechable de CI.
psql -v ON_ERROR_STOP=1 <<'SQL'
INSERT INTO cluster_control.nodes
 (node_id, display_name, admin_state, health_state, last_seen_at)
VALUES
 ('61000000-0000-4000-8000-000000000001', 'tx-node-a', 'active', 'healthy', clock_timestamp()),
 ('61000000-0000-4000-8000-000000000002', 'tx-node-b', 'active', 'healthy', clock_timestamp());

INSERT INTO cluster_control.node_capacity
 (node_id, memory_usable_bytes, storage_usable_bytes, cpu_usable_units, observed_at)
VALUES
 ('61000000-0000-4000-8000-000000000001', 100, 1000, 10, clock_timestamp()),
 ('61000000-0000-4000-8000-000000000002', 100, 1000, 10, clock_timestamp());

INSERT INTO cluster_control.instances
 (instance_id, display_name, desired_state, observed_state, owner_node_id, assignment_epoch)
VALUES
 ('62000000-0000-4000-8000-000000000001', 'concurrent-transaction-instance', 'running', 'stopped', NULL, 0);
SQL

assign_to_node() {
  local node_id="$1"
  local suffix="$2"
  psql -v ON_ERROR_STOP=1 -c "
    SELECT * FROM cluster_control.assign_instance(
      '62000000-0000-4000-8000-000000000001',
      '$node_id',
      '63000000-0000-4000-8000-$suffix',
      '64000000-0000-4000-8000-$suffix',
      '65000000-0000-4000-8000-$suffix',
      '66000000-0000-4000-8000-$suffix',
      '67000000-0000-4000-8000-$suffix',
      '68000000-0000-4000-8000-$suffix',
      'concurrent-test',
      'concurrent-key-$suffix',
      repeat('d',64),
      10, 10, 1
    );
  "
}

set +e
assign_to_node '61000000-0000-4000-8000-000000000001' '000000000001' > /tmp/cluster-assignment-a.log 2>&1 &
pid_a=$!
assign_to_node '61000000-0000-4000-8000-000000000002' '000000000002' > /tmp/cluster-assignment-b.log 2>&1 &
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
  echo "FAIL: expected one assignment transaction to succeed; A=$status_a B=$status_b"
  cat /tmp/cluster-assignment-a.log /tmp/cluster-assignment-b.log
  exit 1
fi

psql -v ON_ERROR_STOP=1 <<'SQL'
DO $$
DECLARE
  v_count bigint;
  v_epoch bigint;
  v_owner uuid;
BEGIN
  SELECT owner_node_id, assignment_epoch INTO v_owner, v_epoch
    FROM cluster_control.instances
   WHERE instance_id = '62000000-0000-4000-8000-000000000001';

  IF v_owner IS NULL OR v_epoch <> 1 THEN
    RAISE EXCEPTION 'FAIL: expected exactly one owner and epoch 1';
  END IF;

  SELECT count(*) INTO v_count FROM cluster_control.resource_reservations
   WHERE instance_id = '62000000-0000-4000-8000-000000000001'
     AND reservation_state IN ('held','uncertain');
  IF v_count <> 1 THEN RAISE EXCEPTION 'FAIL: expected one active reservation'; END IF;

  SELECT count(*) INTO v_count FROM cluster_control.operations
   WHERE instance_id = '62000000-0000-4000-8000-000000000001'
     AND operation_type = 'assign';
  IF v_count <> 1 THEN RAISE EXCEPTION 'FAIL: expected one assignment operation'; END IF;

  SELECT count(*) INTO v_count FROM cluster_control.outbox
   WHERE instance_id = '62000000-0000-4000-8000-000000000001'
     AND event_type = 'assignment.requested';
  IF v_count <> 1 THEN RAISE EXCEPTION 'FAIL: expected one outbox event'; END IF;
END $$;
SQL

echo "PASS: concurrent assignment transactions produced one owner, one epoch, one reservation, one operation and one outbox event."
