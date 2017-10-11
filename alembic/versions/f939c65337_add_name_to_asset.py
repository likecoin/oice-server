"""Add name to asset

Revision ID: f939c65337
Revises: 15579523343
Create Date: 2015-05-14 18:02:24.699105

"""

# revision identifiers, used by Alembic.
revision = 'f939c65337'
down_revision = '15579523343'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('asset',
        sa.Column('name', sa.Unicode(1024), nullable=False, default="")
    )

def downgrade():
    op.drop_column('asset', 'name')
