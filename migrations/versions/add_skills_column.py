"""add_skills_column

Revision ID: add_skills_column
Revises: add_missing_columns
Create Date: 2025-04-03 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_skills_column'
down_revision = 'add_missing_columns'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('content')]
    
    # Add skills column if it doesn't exist
    if 'skills' not in columns:
        op.add_column('content', sa.Column('skills', sa.String(500), nullable=True))


def downgrade():
    # Drop column added in this migration
    op.drop_column('content', 'skills') 