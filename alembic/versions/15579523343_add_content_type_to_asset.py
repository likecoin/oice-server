"""add content type to asset

Revision ID: 15579523343
Revises: 50ceb02a78f
Create Date: 2015-05-06 17:48:04.268263

"""

# revision identifiers, used by Alembic.
revision = '15579523343'
down_revision = '50ceb02a78f'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('asset',
        sa.Column('content_type', sa.Unicode(1024), nullable=False, default="")
    )

def downgrade():
    op.drop_column('asset', 'content_type')
