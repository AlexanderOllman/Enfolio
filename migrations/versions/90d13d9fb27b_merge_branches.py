"""merge branches

Revision ID: 90d13d9fb27b
Revises: add_content_slug, add_project_fields
Create Date: 2025-04-02 21:13:34.581145

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90d13d9fb27b'
down_revision = ('add_content_slug', 'add_project_fields')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
