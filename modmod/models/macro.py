import sqlalchemy as sa
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql.expression import true, false
from modmod.models.base import (
    Base,
    BaseMixin,
)

from . import DBSession


class Macro(Base, BaseMixin):
    __tablename__ = 'macro'

    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    tagname = sa.Column(sa.Unicode(1024), nullable=False, server_default="")

    # The underlying MySQL Type used is "TEXT", which Mysql does not allow any native default values.
    # Any default value should be specified using `default` instead of `server_default`.
    content = sa.Column(sa.Text, nullable=True)

    attribute_definitions = relationship("AttributeDefinition",
                                         cascade="all,delete",
                                         backref="macro",
                                         lazy="select")
    macro_type = sa.Column(sa.Unicode(1024), server_default='system')
    is_hidden = sa.Column(sa.Boolean, nullable=False, server_default=false())

    def serialize(self):
        return {
            'id': self.id,
            'name': self.tagname,
            'isHidden': self.is_hidden,
        }

    @validates('name')
    def validate_name(self, key, name):
        if not name:
            raise ValueError("Macro name is required.")
        else:
            return name

    @validates('tagname')
    def validate_tag(self, key, tagname):
        if not tagname:
            raise ValueError("Macro tagname is required.")
        else:
            return tagname


class MacroQuery:

    def __init__(self, session=DBSession):
        self.session = session

    def query(self):
        return self.session.query(Macro)

    def get_by_id(self, macro_id):
        macro = self.session.query(Macro) \
                         .filter(Macro.id == macro_id) \
                         .one()
        return macro
