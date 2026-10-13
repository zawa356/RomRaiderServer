"""Store immutable ECU/Logger capability snapshots and indexed parameters.

Revision ID: 0002_capabilities
Revises: 0001_initial
No existing telemetry, profile, PoC or credential row is rewritten.
"""
from alembic import op

revision = "0002_capabilities"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE v1_capability_snapshots (
          snapshot_id uuid PRIMARY KEY,
          device_id uuid NOT NULL REFERENCES v1_devices(device_id),
          vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
          logger_version text NOT NULL,
          definition_fingerprint text NOT NULL,
          observed_at timestamptz NOT NULL,
          content_hash char(64) NOT NULL,
          payload jsonb NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE v1_capability_parameters (
          snapshot_id uuid NOT NULL REFERENCES v1_capability_snapshots(snapshot_id),
          parameter_id text NOT NULL,
          name text NOT NULL,
          unit text NOT NULL,
          availability text NOT NULL CHECK (availability IN (
            'defined','possibly_supported','verified_readable','unsupported','unknown')),
          evidence text,
          PRIMARY KEY (snapshot_id,parameter_id)
        )
    """)
    op.execute("""
        CREATE INDEX ix_v1_capabilities_vehicle_recent
        ON v1_capability_snapshots(vehicle_id, observed_at DESC, snapshot_id)
    """)


def downgrade():
    raise RuntimeError("Automatic capability downgrade is disabled to protect histories")
