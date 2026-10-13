"""Explicit product-v1 schema management. Never run migrations on GET/POST."""
import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from . import store


def config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(Path(__file__).with_name("migrations")))
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser(description="RomLogger product-v1 migrations")
    parser.add_argument("action", choices=("upgrade", "current", "history", "check"))
    args = parser.parse_args()
    cfg = config()
    if args.action == "upgrade":
        command.upgrade(cfg, "head")
    elif args.action == "current":
        command.current(cfg, verbose=True)
    elif args.action == "history":
        command.history(cfg, verbose=True)
    else:
        expected = ScriptDirectory.from_config(cfg).get_current_head()
        with store.connect() as db:
            row = db.execute("SELECT version_num FROM v1_alembic_version").fetchone()
        observed = row["version_num"] if row else None
        if observed != expected:
            raise SystemExit(
                f"Schema migration mismatch: database={observed!r}, expected={expected!r}"
            )
        print(f"Product-v1 schema is current: {observed}")


if __name__ == "__main__":
    main()
