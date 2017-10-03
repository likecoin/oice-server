import sqlalchemy as sa
from sqlalchemy.orm import relationship
from pyramid.security import Allow
from modmod.models.base import (
    Base,
    BaseMixin,
)
import logging


log = logging.getLogger(__name__)


class Attribute(Base, BaseMixin):
    __tablename__ = 'attribute'

    attribute_definition = relationship("AttributeDefinition", lazy="joined")
    attribute_definition_id = sa.Column(
        sa.Integer, sa.ForeignKey('attribute_definition.id'), nullable=False)

    block_id = sa.Column(sa.Integer, sa.ForeignKey('block.id'), nullable=False)

    # The underlying MySQL Type used is "TEXT", which Mysql does not allow any native default value.
    # Any default value should be specified using `default` instead of `server_default`.
    value = sa.Column(sa.TEXT, default="")

    asset_id = sa.Column(sa.Integer, sa.ForeignKey('asset.id'))
    asset = relationship("Asset", lazy='joined')
    language = sa.Column(sa.Unicode(5))

    @property
    def __acl__(self):
        acl = super(Attribute, self).__acl__()
        for user in self.block.story.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]

        return acl

    def serialize(self):
        attr_def = self.attribute_definition
        return {
            'id': self.id,
            'value': self.serialized_value,
            'isAsset': attr_def.asset_type == 'reference' and attr_def.asset_type_id is not None,
            'asset': self.asset.serialize() if self.asset else {},
            'definition': attr_def.serialize()
        }

    @property
    def serialized_value(self):
        value = self.converted_value
        if self.attribute_definition.is_asset and value:
            return value.id
        elif not self.attribute_definition.is_asset:
            return value
        else:
            return ''

    @property
    def converted_value(self):
        # Convert value based on its attribute_definition type
        # FIXME: visitor for converting value?
        if self.attribute_definition.asset_type == 'boolean':
            return self.value in {'1', 'true', True}
        elif self.attribute_definition.is_asset:
            return self.asset
        else:
            return self.value
