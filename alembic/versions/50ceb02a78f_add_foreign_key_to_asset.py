"""add foreign key to asset

Revision ID: 50ceb02a78f
Revises: 1f660c9e45
Create Date: 2015-05-06 17:06:06.194648

"""

# revision identifiers, used by Alembic.
revision = '50ceb02a78f'
down_revision = '1f660c9e45'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_column('asset', 'asset_type')
    op.add_column(
        'asset',
        sa.Column(
            'asset_type_id',
            sa.Integer,
            sa.ForeignKey('asset_type.id'),
            nullable=False))

def downgrade():
    op.drop_constraint('asset_ibfk_1',
        table_name='asset',
        type_="foreignkey")
    op.drop_index('asset_type_id', table_name='asset')
    op.drop_column('asset', 'asset_type_id')

    op.add_column(
        'asset',
        sa.Column(
            'asset_type',
            sa.Unicode(1024),
            default=""))