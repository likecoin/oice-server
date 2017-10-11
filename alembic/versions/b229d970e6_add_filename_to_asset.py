"""Add filename to asset

Revision ID: b229d970e6
Revises: 1ee626830b2
Create Date: 2015-05-20 12:35:46.744883

"""

# revision identifiers, used by Alembic.
revision = 'b229d970e6'
down_revision = '1ee626830b2'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('asset',
        sa.Column('filename', sa.Unicode(1024), nullable=True)
    )

def downgrade():
    op.drop_column('asset', 'filename')
