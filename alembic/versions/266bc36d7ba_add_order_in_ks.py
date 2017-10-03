"""add order in ks

Revision ID: 266bc36d7ba
Revises: 4d5807cb5f7
Create Date: 2016-10-20 10:13:41.171214

"""

# revision identifiers, used by Alembic.
revision = '266bc36d7ba'
down_revision = '4d5807cb5f7'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('ks', sa.Column('order', sa.Integer(), nullable=False))

def downgrade():
    op.drop_column('ks', 'order')