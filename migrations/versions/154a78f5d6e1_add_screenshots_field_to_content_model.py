"""Add screenshots field to Content model

Revision ID: 154a78f5d6e1
Revises: add_responsibilities_column
Create Date: 2025-04-17 19:21:49.856146

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '154a78f5d6e1'
down_revision = 'add_responsibilities_column'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('content', schema=None) as batch_op:
        batch_op.add_column(sa.Column('screenshots', sa.JSON(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('content', schema=None) as batch_op:
        batch_op.drop_column('screenshots')

    # ### end Alembic commands ###
