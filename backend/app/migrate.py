"""Bring the database schema up to date with Alembic.

Databases created by earlier versions of the Windows start script were built
with ``create_all`` and carry no Alembic version. They are stamped with the
revision their tables match before upgrading, so existing data is kept.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from .database import engine

BACKEND_DIR = Path(__file__).resolve().parent.parent


def alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def untracked_revision(tables: set[str], preference_columns: set[str] = frozenset()) -> str | None:
    """The revision an untracked database's tables correspond to."""
    if "alembic_version" in tables or "users" not in tables:
        return None
    if "whatsapp_events" in preference_columns:
        return "1889870066a0"
    if "sources" in tables:
        return "c244e77c88be"
    if "principal_profile" in tables:
        return "9a9061abd072"
    return "d144d266f88a"


def migrate() -> None:
    cfg = alembic_config()
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    columns = {c["name"] for c in insp.get_columns("notification_preferences")} if "notification_preferences" in tables else set()
    base = untracked_revision(tables, columns)
    if base:
        print(f"Database has no migration history; marking it as {base} before upgrading.")
        command.stamp(cfg, base)
    command.upgrade(cfg, "head")


if __name__ == "__main__":
    migrate()
