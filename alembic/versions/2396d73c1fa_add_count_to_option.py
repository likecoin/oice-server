"""add count to option

Revision ID: 2396d73c1fa
Revises: 19ee5d790ac
Create Date: 2015-10-02 16:17:54.575642

"""

# revision identifiers, used by Alembic.
revision = '2396d73c1fa'
down_revision = '19ee5d790ac'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'option',
        sa.Column('count', sa.Integer, server_default="0")
    )


def downgrade():
    op.drop_column('option', 'count')
