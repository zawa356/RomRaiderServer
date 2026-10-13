"""Initial isolated v1 schema; PoC tables are not touched.

Revision ID: 0001_initial
Revises:
This baseline expects a fresh product-v1 namespace. If unmanaged v1 tables
already exist, fail closed: use a separately reviewed, data-preserving
adoption migration instead of silently stamping an unverified schema.
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    existing = conn.execute(text("""
        SELECT tablename FROM pg_catalog.pg_tables
        WHERE schemaname = current_schema()
          AND tablename LIKE 'v1\\_%' ESCAPE '\\'
          AND tablename <> 'v1_alembic_version'
        ORDER BY tablename
    """)).scalars().all()
    if existing:
        raise RuntimeError(
            "Unversioned product-v1 tables exist; refusing to stamp or overwrite: "
            + ", ".join(existing)
        )
    # schema.sql is an IMMUTABLE copy of the 0001 initial schema.
    # Future DDL must use a new Alembic revision, never edit schema.sql.
    baseline = Path(__file__).resolve().parents[2] / "schema.sql"
    for sql in baseline.read_text(encoding="utf-8").split(";"):
        if sql.strip():
            op.execute(sql)


def downgrade():
    raise RuntimeError(
        "No automatic downgrade: product-v1 raw telemetry must not be dropped. "
        "Create a separately reviewed reversible migration if required."
    )
