"""add_missing_columns

Revision ID: add_missing_columns
Revises: 90d13d9fb27b
Create Date: 2025-04-02 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_missing_columns'
down_revision = '90d13d9fb27b'
branch_labels = None
depends_on = None


def upgrade():
    # Check if columns exist before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('content')]
    
    # Add missing columns from the model
    if 'employment_type' not in columns:
        op.add_column('content', sa.Column('employment_type', sa.String(50), nullable=True))
    
    if 'location' not in columns:
        op.add_column('content', sa.Column('location', sa.String(200), nullable=True))
    
    if 'is_remote' not in columns:
        op.add_column('content', sa.Column('is_remote', sa.Boolean(), nullable=True))
    
    if 'team_size' not in columns:
        op.add_column('content', sa.Column('team_size', sa.Integer(), nullable=True))
    
    if 'key_achievements' not in columns:
        op.add_column('content', sa.Column('key_achievements', sa.Text(), nullable=True))


def downgrade():
    # Drop columns added in this migration
    op.drop_column('content', 'employment_type')
    op.drop_column('content', 'location')
    op.drop_column('content', 'is_remote')
    op.drop_column('content', 'team_size')
    op.drop_column('content', 'key_achievements') 