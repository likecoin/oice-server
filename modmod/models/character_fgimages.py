import sqlalchemy as sa

from modmod.models.base import (
    Base,
)

character_fgimages = sa.Table(
    'character_fgimages',
    Base.metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('character_id', sa.Integer, sa.ForeignKey('character.id'), nullable=False),
    sa.Column('asset_id', sa.Integer, sa.ForeignKey('asset.id'), nullable=False),
    sa.UniqueConstraint('character_id', 'asset_id', name='character_id_asset_id'),
    sa.Index("characterid_assetid_idx", 'character_id', 'asset_id'),
)
