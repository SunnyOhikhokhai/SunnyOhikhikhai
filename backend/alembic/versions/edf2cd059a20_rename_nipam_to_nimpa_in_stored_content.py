"""rename NIPAM to NIMPA in stored content

Revision ID: edf2cd059a20
Revises: 1889870066a0
Create Date: 2026-10-06 01:06:16.174111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edf2cd059a20'
down_revision: Union[str, None] = '1889870066a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Organisation-written text that may mention the old name. Member-written
# content (discussions, comments) is left as the members wrote it.
COLUMNS = {
    "news": ["title", "excerpt", "body", "author_name", "source_note"],
    "news_categories": ["name"],
    "announcements": ["title", "body"],
    "events": ["title", "summary", "description", "organizer"],
    "area_councils": ["summary", "description"],
    "principal_profile": ["summary", "biography"],
    "projects": ["summary", "description"],
    "notifications": ["title", "body"],
}
RENAMES = [
    ("Non-Indigenes for Philip Aduda Movement", "Non-Indigenes Movement for Philip Aduda"),
    ("NIPAM", "NIMPA"),
]
ACCOUNTS = [("users", "full_name", "NIPAM Administrator", "NIMPA Administrator"), ("profiles", "display_name", "NIPAM Team", "NIMPA Team")]


def _rename(pairs) -> None:
    for table, cols in COLUMNS.items():
        for col in cols:
            for old, new in pairs:
                op.execute(sa.text(f"UPDATE {table} SET {col} = REPLACE({col}, :old, :new) WHERE {col} LIKE :pat").bindparams(old=old, new=new, pat=f"%{old}%"))


def upgrade() -> None:
    _rename(RENAMES)
    for table, col, old, new in ACCOUNTS:
        op.execute(sa.text(f"UPDATE {table} SET {col} = :new WHERE {col} = :old").bindparams(old=old, new=new))


def downgrade() -> None:
    _rename([(new, old) for old, new in reversed(RENAMES)])
    for table, col, old, new in ACCOUNTS:
        op.execute(sa.text(f"UPDATE {table} SET {col} = :old WHERE {col} = :new").bindparams(old=old, new=new))
