"""add_responsibilities_column

Revision ID: add_responsibilities_column
Revises: add_skills_column
Create Date: 2025-04-03 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_responsibilities_column'
down_revision = 'add_skills_column'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('content')]
    
    # Add responsibilities column if it doesn't exist
    if 'responsibilities' not in columns:
        op.add_column('content', sa.Column('responsibilities', sa.Text(), nullable=True))


def downgrade():
    # Drop column added in this migration
    op.drop_column('content', 'responsibilities') 