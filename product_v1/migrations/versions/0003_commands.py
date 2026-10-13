"""Phase 1.1-D: durable command leases, reports and conservative reconciliation.

Revision ID: 0003_commands
Revises: 0002_capabilities
No PoC, raw observation or credentials are modified.
"""
from alembic import op

revision = "0003_commands"
down_revision = "0002_capabilities"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE v1_tasks (
          task_id uuid PRIMARY KEY,
          vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
          state text NOT NULL CHECK (state IN
            ('draft','active','paused','completed','cancelled')),
          created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_v1_task_active_vehicle
        ON v1_tasks(vehicle_id) WHERE state = 'active'
    """)
    op.execute("""
        CREATE TABLE v1_plan_revisions (
          plan_revision_id uuid PRIMARY KEY,
          task_id uuid NOT NULL REFERENCES v1_tasks(task_id),
          revision_number integer NOT NULL CHECK (revision_number > 0),
          plan_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
          created_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE(task_id, revision_number)
        )
    """)
    op.execute("""
        CREATE TABLE v1_approval_scopes (
          approval_scope_id uuid PRIMARY KEY,
          task_id uuid NOT NULL REFERENCES v1_tasks(task_id),
          vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
          approved_by text NOT NULL,
          allowed_actions text[] NOT NULL,
          starts_at timestamptz NOT NULL,
          expires_at timestamptz NOT NULL,
          revoked_at timestamptz,
          created_at timestamptz NOT NULL DEFAULT now(),
          CHECK (expires_at > starts_at)
        )
    """)
    op.execute("""
        CREATE TABLE v1_command_requests (
          command_id uuid PRIMARY KEY,
          vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
          device_id uuid NOT NULL REFERENCES v1_devices(device_id),
          task_id uuid NOT NULL REFERENCES v1_tasks(task_id),
          plan_revision_id uuid NOT NULL REFERENCES v1_plan_revisions(plan_revision_id),
          approval_scope_id uuid NOT NULL REFERENCES v1_approval_scopes(approval_scope_id),
          action text NOT NULL CHECK (action IN (
            'apply_measurement_plan','suspend_ai_changes',
            'restore_basic_logging','request_local_recovery')),
          expected_profile_revision_id uuid REFERENCES v1_profile_revisions(profile_revision_id),
          issued_at timestamptz NOT NULL DEFAULT now(),
          expires_at timestamptz NOT NULL,
          status text NOT NULL DEFAULT 'queued' CHECK (status IN (
            'queued','leased','received','rejected','applying',
            'applied_unverified','verified','failed','expired','cancelled','unknown')),
          lease_until timestamptz,
          updated_at timestamptz NOT NULL DEFAULT now(),
          CHECK (expires_at > issued_at)
        )
    """)
    op.execute("""
        CREATE INDEX ix_v1_command_delivery
        ON v1_command_requests(device_id, status, expires_at, issued_at)
    """)
    op.execute("""
        CREATE TABLE v1_command_reports (
          report_id uuid PRIMARY KEY,
          command_id uuid NOT NULL REFERENCES v1_command_requests(command_id),
          device_id uuid NOT NULL REFERENCES v1_devices(device_id),
          state text NOT NULL,
          reported_at timestamptz NOT NULL,
          received_at timestamptz NOT NULL DEFAULT now(),
          content_hash char(64) NOT NULL,
          payload jsonb NOT NULL
        )
    """)
    op.execute("""
        CREATE INDEX ix_v1_command_report_command
        ON v1_command_reports(command_id,received_at)
    """)
    op.execute("""
        CREATE TABLE v1_reconciliations (
          reconcile_id bigserial PRIMARY KEY,
          device_id uuid NOT NULL REFERENCES v1_devices(device_id),
          vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
          client_state_revision text NOT NULL,
          reported_at timestamptz NOT NULL,
          received_at timestamptz NOT NULL DEFAULT now(),
          content_hash char(64) NOT NULL,
          payload jsonb NOT NULL,
          UNIQUE(device_id,client_state_revision)
        )
    """)


def downgrade():
    raise RuntimeError("Command history downgrade requires explicit data-preserving migration")
