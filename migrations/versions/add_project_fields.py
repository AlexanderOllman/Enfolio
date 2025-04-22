"""add_project_fields

Revision ID: add_project_fields
Revises: 65835df6c7f3
Create Date: 2023-07-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_project_fields'
down_revision = '65835df6c7f3'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns for project content type
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('content')]
    
    # Add columns only if they don't exist
    if 'project_status' not in columns:
        op.add_column('content', sa.Column('project_status', sa.String(50), nullable=True))
    
    if 'project_client' not in columns:
        op.add_column('content', sa.Column('project_client', sa.String(200), nullable=True))
    
    if 'media_urls' not in columns:
        op.add_column('content', sa.Column('media_urls', sa.JSON(), nullable=True))


def downgrade():
    # Drop columns added in this migration
    op.drop_column('content', 'project_status')
    op.drop_column('content', 'project_client')
    op.drop_column('content', 'media_urls') 