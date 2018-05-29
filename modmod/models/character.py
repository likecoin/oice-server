import uuid
import sqlalchemy as sa
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import func, true, false
from pyramid.security import Allow

from modmod.models.base import (
    Base,
    BaseMixin,
)

import json
import logging
log = logging.getLogger(__name__)

from .character_fgimages import character_fgimages
from .character_localization import CharacterLocalization
from .library import Library
from .user import User
from . import DBSession
from ..operations.script_export_default import CHARACTER_CONFIG


class Character(Base, BaseMixin):
    __tablename__ = 'character'

    name = sa.Column(sa.Unicode(1024), nullable=False)
    description = sa.Column(sa.Unicode(1024), nullable=False, server_default='')
    library_id = sa.Column(sa.Integer, sa.ForeignKey('library.id'))
    uuid = sa.Column(sa.Unicode(128), nullable=False, unique=True)
    order = sa.Column(sa.Integer, nullable=False, server_default='0')
    width = sa.Column(sa.SmallInteger, nullable=False, server_default='540')
    height = sa.Column(sa.SmallInteger, nullable=False, server_default='540')

    # The underlying MySQL Type used is "TEXT", which Mysql does not allow any native default value.
    # Any default value should be specified using `default` instead of `server_default`.
    config = sa.Column(sa.Text, nullable=False, default=CHARACTER_CONFIG)
    is_deleted = sa.Column(sa.Boolean, nullable=False, server_default=false())
    is_generic = sa.Column(sa.Boolean, nullable=False, server_default=false())

    library = relationship("Library", backref="character")

    fgimages = relationship(
        "Asset",
        secondary=character_fgimages,
        secondaryjoin='and_( \
                        character_fgimages.c.asset_id==Asset.id, \
                        Asset.is_deleted==false() \
                        )',
        lazy='joined',
        cascade='',
        order_by='Asset.order',
    )

    localizations = relationship("CharacterLocalization",
                              collection_class=attribute_mapped_collection('language'),
                              cascade="all,delete-orphan",
                              backref="character",
                              lazy="joined")

    __table_args__ = (
        UniqueConstraint('library_id', 'uuid'), # Composite unique key [project_id, uuid]
        sa.Index('library_id_deleted_idx', 'library_id', 'is_deleted'),
    )

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        if self.uuid is None:
            self.uuid = uuid.uuid4().hex

    @property
    def __acl__(self):
        acl = super(Character, self).__acl__()
        for user in self.library.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    def getJSONConfig(self):
        converted_config = {}
        try:
            jsonObject = json.loads(self.config)
            for key, value in jsonObject.items():
                converted_config[key] = int(value)
        except:
            pass
        return converted_config

    @property
    def language(self): # default language to zh-HK
        return 'zh-HK'

    def set_name(self, name, language=None):
        if language == self.language:
            self.name = name
        elif language is not None and language in self.localizations:
            self.localizations[language].name=name
        else :
            localization = CharacterLocalization(character=self, language=language, name=name)
            DBSession.add(localization)
            self.localizations[language] = localization

    def get_name(self, language=None):
        if language is not None and language in self.localizations:
            return self.localizations[language].name
        return self.name

    @property
    def supported_languages(self):
        return [k for k in self.localizations.keys()].append(self.language)

    def is_author(self, user):
        return user in self.library.users if user else False

    def serialize_min(self, language=None):
        return {
            "id": self.id,
            "libraryId": self.library_id,
            "name": self.get_name(language),
            "width": self.width,
            "height": self.height,
            "config": self.getJSONConfig(),
            "isGeneric": self.is_generic,
        }

    def serialize_editor(self, language=None, user=None):
        is_library_author = self.is_author(user)
        return {
            **self.serialize_min(language=language),
            "fgimages": [fg.serialize_min()
                         for fg in self.fgimages
                         if not fg.is_hidden or is_library_author],
        }

    def serialize(self, language=None, user=None):
        is_library_author = self.is_author(user)
        return {
            **self.serialize_min(language=language),
            "description": self.description,
            "order": self.order,
            "fgimages": [fg.serialize()
                         for fg in self.fgimages
                         if not fg.is_hidden or is_library_author],
        }


class CharacterFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        one = DBSession.query(Character) \
                     .filter(Character.id == key) \
                     .one()
        return one


class CharacterQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(Character)

    def fetch_by_oice(self, oice):
        used_character_ids = set(attribute.value \
                                 for block in oice.blocks \
                                 if block.macro.tagname == 'characterdialog' \
                                 for attribute in block.attributes \
                                 if attribute.attribute_definition.asset_type == 'character')
        return self.fetch_by_ids(used_character_ids)

    def fetch_character_list_by_user_selected(self, user):
        return self.query \
                   .filter(Character.is_deleted == false()) \
                   .join(Character.library) \
                   .join(Library.selected_users) \
                   .filter(User.id == user.id) \
                   .order_by(Character.library_id) \
                   .order_by(Character.order)

    def fetch_character_by_id(self, character_id):
        return self.query \
                   .filter(Character.id == character_id)

    def fetch_by_ids(self, character_ids):
        return self.query \
                   .filter(Character.id.in_(character_ids)) \
                   .all()

    def fetch_character_by_library_id_and_uuid(self, library_id, uuid):
        return self.query \
            .filter(Character.library_id == library_id) \
            .filter(Character.uuid == uuid)

    def fetch_character_by_library(self, library_id):
        return self.query \
            .filter(Character.library_id == library_id) \
            .filter(Character.is_deleted == False) \
            .order_by(Character.order)

    def get_last_order_in_library(self, library_id):
        character = self.query \
                    .filter(Character.library_id == library_id) \
                    .filter(Character.is_deleted == False) \
                    .order_by(Character.order.desc()) \
                    .first()

        return character.order + 1

    def fetch_character_by_uuid(self, uuid):
        character = self.query \
                    .filter(Character.uuid == uuid) \
                    .first()

        return character
