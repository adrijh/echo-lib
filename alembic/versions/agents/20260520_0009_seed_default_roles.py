"""seed default roles

Revision ID: 0009
Revises: 8bd664957e5e
Create Date: 2026-05-20
"""
from collections.abc import Sequence
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

revision: str = "0009"
down_revision: str | None = "8bd664957e5e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ADMIN_PERMISSIONS = [
    "agent:read", "agent:create", "agent:update", "agent:delete",
    "chat:send", "chat:read", "chat:delete",
    "document:read", "document:create", "document:delete",
    "skill:read", "skill:create", "skill:delete",
    "tenant:read",
    "metabase:read",
]

MEMBER_PERMISSIONS = [
    "agent:read", "agent:create", "agent:update", "agent:delete",
    "chat:send", "chat:read", "chat:delete",
    "document:read", "document:create", "document:delete",
    "skill:read", "skill:create", "skill:delete",
    "tenant:read",
    "metabase:read",
]

VIEWER_PERMISSIONS = [
    "agent:read",
    "chat:read",
    "document:read",
    "skill:read",
    "tenant:read",
    "metabase:read",
]

roles_table = sa.table(
    "roles",
    sa.column("id", sa.Uuid),
    sa.column("name", sa.String),
    sa.column("description", sa.String),
    sa.column("permissions", sa.ARRAY(sa.String)),
)


def upgrade() -> None:
    op.bulk_insert(roles_table, [
        {"id": uuid4(), "name": "admin", "description": "Full access to all resources", "permissions": ADMIN_PERMISSIONS},
        {"id": uuid4(), "name": "member", "description": "Standard user with read and write access", "permissions": MEMBER_PERMISSIONS},
        {"id": uuid4(), "name": "viewer", "description": "Read-only access", "permissions": VIEWER_PERMISSIONS},
    ])


def downgrade() -> None:
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'member', 'viewer')")
