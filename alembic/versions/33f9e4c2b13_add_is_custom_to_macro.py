"""add_is_custom_to_macro

Revision ID: 33f9e4c2b13
Revises: 52d9f7773cc
Create Date: 2015-06-30 18:15:16.944727

"""

# revision identifiers, used by Alembic.
revision = '33f9e4c2b13'
down_revision = '52d9f7773cc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('macro',
        sa.Column('is_custom', sa.Boolean, server_default='0')
    )

def downgrade():
    op.drop_column('macro', 'is_custom')
