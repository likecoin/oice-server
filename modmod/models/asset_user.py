import sqlalchemy as sa

from modmod.models.base import (
    Base,
)

asset_user = sa.Table(
    'asset_user',
    Base.metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('asset_id', sa.Integer, sa.ForeignKey('asset.id'), nullable=False),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
    sa.UniqueConstraint('asset_id', 'user_id', name='asset_id_user_id')
)
