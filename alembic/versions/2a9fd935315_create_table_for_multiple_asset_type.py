"""Create table for multiple asset type

Revision ID: 2a9fd935315
Revises: 518080db1b4
Create Date: 2015-06-19 10:33:21.868755

"""

# revision identifiers, used by Alembic.
revision = '2a9fd935315'
down_revision = '518080db1b4'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'asset_asset_types',

        sa.Column('id', sa.Integer, primary_key=True, nullable=False),

        sa.Column('asset_id', sa.Integer,
        	sa.ForeignKey('asset.id'), nullable=False),
        sa.Column('asset_type_id', sa.Integer,
            sa.ForeignKey('asset_type.id'), nullable=False),

        mysql_engine='InnoDB'
    )

    conn = op.get_bind()
    conn.execute('INSERT INTO asset_asset_types (asset_id, asset_type_id) SELECT id, asset_type_id FROM asset;');

    # asset_type constraint
    op.drop_constraint('asset_ibfk_1',
        table_name='asset',
        type_="foreignkey")

    op.drop_index('asset_type_id', table_name='asset')
    op.drop_column('asset', 'asset_type_id')




def downgrade():
    op.add_column(
        'asset',
        sa.Column(
            'asset_type_id',
            sa.Integer,
            sa.ForeignKey('asset_type.id')))

    conn = op.get_bind()
    rows = conn.execute('SELECT * FROM asset_asset_types')
    for row in rows:
        conn.execute('UPDATE asset SET asset_type_id = '+str(row.asset_type_id)+' WHERE asset.id = '+str(row.asset_id))

    op.drop_table('asset_asset_types')
