import sqlalchemy as sa
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.expression import true, false

from modmod.models.base import (
    Base,
    BaseMixin,
)


class AttributeDefinition(Base, BaseMixin):
    __tablename__ = 'attribute_definition'

    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    attribute_name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    asset_type = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    required = sa.Column(sa.Boolean, nullable=False, server_default=false())
    default_value = sa.Column(sa.Unicode(1024), nullable=True)
    localizable = sa.Column(sa.Boolean, nullable=False, server_default=false())

    asset_type_id = sa.Column(
        sa.Integer, sa.ForeignKey('asset_type.id'))
    asset_type_ref = relationship("AssetType")
    macro_id = sa.Column(
        sa.Integer, sa.ForeignKey('macro.id'), nullable=False)

    def serialize(self):
        return {
            'id': self.id,
            'macroId': self.macro_id,
            'label': self.name,
            'name': self.attribute_name,
            'type': self.asset_type,
            'assetType': self.asset_type_ref.serialize() if self.asset_type_ref else None,
            'defaultValue': self.default_value,
            'required': self.required
        }

    @property
    def is_asset(self):
        return self.asset_type == "reference"

    @validates('name')
    def validate_name(self, key, name):
        if not name:
            raise ValueError("Attribute name is required.")
        else:
            return name

    @validates('attribute_name')
    def validate_attribute_name(self, key, attribute_name):
        if not attribute_name:
            raise ValueError("Attribute name is required.")
        else:
            return attribute_name

    @validates('asset_type')
    def validate_asset_type(self, key, asset_type):
        if not asset_type:
            raise ValueError("Attribute type is required.")
        else:
            return asset_type
