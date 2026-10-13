"""Explicit product-v1 schema management. Never run migrations on GET/POST."""
import argparse
from pathlib import Path

from alembic import command
from alembic.config import Config


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
        command.check(cfg)


if __name__ == "__main__":
    main()
