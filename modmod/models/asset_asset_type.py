import sqlalchemy as sa

from modmod.models.base import (
    Base,
)

association_table = sa.Table(
    'asset_asset_types',
    Base.metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('asset_id', sa.Integer, sa.ForeignKey('asset.id'), nullable=False),
    sa.Column('asset_type_id', sa.Integer, sa.ForeignKey('asset_type.id'), nullable=False),
    sa.UniqueConstraint('asset_id', 'asset_type_id', name='asset_id_asset_type_id')
)
