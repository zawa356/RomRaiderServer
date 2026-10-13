"""Alembic online environment for the isolated RomLogger v1 schema."""
import os

from alembic import context
from sqlalchemy import create_engine, pool

config = context.config


def run_migrations_online() -> None:
    raw_url = os.environ["DATABASE_URL"]
    if raw_url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + raw_url[len("postgresql://"):]
    elif raw_url.startswith("postgres://"):
        url = "postgresql+psycopg://" + raw_url[len("postgres://"):]
    else:
        url = raw_url
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=None,
            version_table="v1_alembic_version",
            transactional_ddl=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    raise RuntimeError("Product v1 migrations require a real PostgreSQL connection")
run_migrations_online()
