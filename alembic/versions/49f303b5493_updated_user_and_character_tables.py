"""Updated 'user' and 'character' tables

Revision ID: 49f303b5493
Revises: 2396d73c1fa
Create Date: 2016-07-26 11:22:35.758896

"""

# revision identifiers, used by Alembic.
revision = '49f303b5493'
down_revision = '2396d73c1fa'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('user',
        sa.Column('token', sa.Unicode(1024), nullable=True)
    )
    op.add_column('character',
        sa.Column('width', sa.SmallInteger, nullable=False, server_default="540")
    )
    op.add_column('character',
        sa.Column('height', sa.SmallInteger, nullable=False, server_default="540")
    )
    op.add_column('character',
        sa.Column('config', sa.Text, nullable=True)
    )

def downgrade():
    op.drop_column('user', 'token')
    op.drop_column('character', 'width')
    op.drop_column('character', 'height')
    op.drop_column('character', 'config')
