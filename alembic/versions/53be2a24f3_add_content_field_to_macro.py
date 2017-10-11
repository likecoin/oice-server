"""Add content field to macro

Revision ID: 53be2a24f3
Revises: b229d970e6
Create Date: 2015-05-20 12:51:16.249345

"""

# revision identifiers, used by Alembic.
revision = '53be2a24f3'
down_revision = 'b229d970e6'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('macro',
        sa.Column('content', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column('macro', 'content')
