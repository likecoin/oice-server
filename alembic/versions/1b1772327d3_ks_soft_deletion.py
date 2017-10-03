"""ks soft deletion

Revision ID: 1b1772327d3
Revises: 1fa224796cc
Create Date: 2015-08-03 09:55:28.839213

"""

# revision identifiers, used by Alembic.
revision = '1b1772327d3'
down_revision = '515440ba894'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('ks',
        sa.Column('is_deleted', sa.Boolean, nullable=False, default=False)
    )

def downgrade():
    op.drop_column('ks', 'is_deleted')
