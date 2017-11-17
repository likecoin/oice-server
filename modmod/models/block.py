import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from pyramid.security import Allow
from modmod.models.base import (
    Base,
    BaseMixin
)
from . import DBSession


class Block(Base, BaseMixin):
    __tablename__ = 'block'

    # Need the id specified here for BaseNestedSets declared_attr
    id = sa.Column('id', sa.Integer, primary_key=True)

    oice_id = sa.Column(
        sa.Integer, sa.ForeignKey('oice.id'), nullable=False)
    macro_id = sa.Column(
        sa.Integer, sa.ForeignKey('macro.id'), nullable=False)
    macro = relationship("Macro", lazy="joined")
    oice = relationship("Oice")
    position = sa.Column(sa.Integer, nullable=False)
    attributes = relationship("Attribute",
                              cascade="all,delete",
                              backref="block",
                              lazy="joined")

    __table_args__ = (
        Index('ks_position_idx', 'oice_id', 'position'),
    )

    @property
    def __acl__(self):
        acl = super(Block, self).__acl__()
        for user in self.oice.story.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    def serialize(self, language=None):
        return {
            'id': self.id,
            'oiceId': self.oice_id,
            'macroId': self.macro_id,
            'macroName': self.macro.tagname,
            'attributes': self.serialize_attributes(language)
        }

    def serialize_min(self):
        return {
            'id': self.id,
            'oiceId': self.oice_id,
            'macroId': self.macro_id,
            'macroName': self.macro.tagname,
            'order': self.position,
        }

    def serialize_attributes(self, language=None):
        if not language:
            language = self.oice.story.language
        attributes = {}
        for attribute in self.attributes:
            if (not attribute.attribute_definition.localizable) or \
                    (attribute.language == language) or \
                    ((attribute.attribute_definition.attribute_name not in attributes) and \
                    (attribute.language == self.oice.story.language)):
                attributes[attribute.attribute_definition.attribute_name] = attribute.serialize()
        return attributes

    def get_localizable_attributes(self, language=None):
        if not language:
            language = self.oice.story.language
        attributes = {}
        for attribute in self.attributes:
            if attribute.attribute_definition.localizable \
                and (attribute.language == language
                     or (
                        attribute.attribute_definition.attribute_name not in attributes
                        and attribute.language == self.oice.story.language
                    )):
                attributes[attribute.attribute_definition.attribute_name] = attribute.value
        return attributes

    def get_localized_attributes(self, language=None):
        if not language:
            language = self.oice.story.language
        attributes = {}
        for attribute in self.attributes:
            # if the attribute is not localize, use story main language as default
            if (not attribute.attribute_definition.localizable or \
                (attribute.language == language) or \
                ((attribute.attribute_definition.attribute_name not in attributes) and \
                (attribute.language == self.oice.story.language))):
                attributes[attribute.attribute_definition.attribute_name] = attribute.converted_value
        return attributes

    # TODO: Make a subclass for each block type
    def accept(self, visitor, *args, **kwargs):

        method_name = 'visit_' + self.macro.tagname + '_block'

        method = getattr(visitor, method_name, visitor.visit_default_block)
        return method(self, *args, **kwargs)


class BlockFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        block = DBSession.query(Block) \
                     .filter(Block.id == key) \
                     .one()
        return block
