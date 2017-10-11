"""add type to asset type

Revision ID: da227aeb4
Revises: 566d9896854
Create Date: 2015-08-13 14:14:16.313693

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'da227aeb4'
down_revision = '566d9896854'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'asset_type',
        sa.Column('type', sa.Unicode(1024), nullable=True)
    )


def downgrade():
    op.drop_column('asset_type', 'type')
