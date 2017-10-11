"""add order to character

Revision ID: 15ee9d8d532
Revises: 29183d95596
Create Date: 2015-09-22 13:07:46.547170

"""

# revision identifiers, used by Alembic.
revision = '15ee9d8d532'
down_revision = '29183d95596'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('character',
        sa.Column('order', sa.Integer, nullable=False)
    )
    op.execute("UPDATE `character` SET `order`=999999")


def downgrade():
    op.drop_column('character', 'order')
