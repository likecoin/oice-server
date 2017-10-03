"""add config to project

Revision ID: 1ec87c6930f
Revises: 52d9f7773cc
Create Date: 2015-06-30 16:39:04.940094

"""

# revision identifiers, used by Alembic.
revision = '1ec87c6930f'
down_revision = '33f9e4c2b13'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('project',
        sa.Column('config', sa.Text(), nullable=False)
    )

def downgrade():
    op.drop_column('project', 'config')
