import os
import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import true, false
from pyramid.security import Allow
from pyramid_safile import FileHandleStore
from ..config import get_upload_base_url

from modmod.models.base import (
    Base,
    BaseMixin,
)

from .oice import Oice
from .library import LibraryQuery
from . import DBSession

from .story_library import story_library
from .story_localization import StoryLocalization


class Story(Base, BaseMixin):
    __tablename__ = 'story'

    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    oice = relationship(Oice,
                        primaryjoin="and_(Story.id == Oice.story_id, Oice.is_deleted == false())",
                        order_by=Oice.order,
                        cascade="all, delete",
                        backref=backref("story", lazy="joined"))
    published_oices = relationship(
        Oice,
        order_by=Oice.order,
        cascade="all, delete",
        primaryjoin='and_('
                    'Story.id == Oice.story_id,'
                    'Oice.is_deleted == false(),'
                    'Oice.sharing_option == 0,'
                    'Oice.state == 2)',
    )
    is_deleted = sa.Column(sa.Boolean, nullable=False, index=True, server_default=false())
    description = sa.Column(sa.Unicode(4096), nullable=False, server_default="")
    language = sa.Column(sa.Unicode(5), nullable=False, index=True, server_default="zh-HK")
    cover_storage = sa.Column(FileHandleStore, nullable=True)
    title_logo = sa.Column(FileHandleStore, nullable=True)
    hero_image = sa.Column(FileHandleStore, nullable=True)
    og_image = sa.Column(FileHandleStore, nullable=True)
    fork_of = sa.Column(sa.Integer, nullable=True)
    priority = sa.Column(sa.Integer, nullable=False, server_default='0')
    localizations = relationship("StoryLocalization",
                              collection_class=attribute_mapped_collection('language'),
                              cascade="all,delete-orphan",
                              backref="story",
                              lazy="joined")

    __table_args__ = (
        sa.Index('story_updated_at_idx', 'updated_at'),
    )

    @property
    def __acl__(self):
        acl = super(Story, self).__acl__()
        for user in self.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    @staticmethod
    def get_sample_story_id():
        return 492

    @property
    def is_fork_from_sample_story(self):
        return self.fork_of == Story.get_sample_story_id()

    def is_supported_language(self, language):
        return language is not None \
               and language in self.localizations

    @property
    def cover_storage_url(self):
        return get_upload_base_url() + self.cover_storage.url if self.cover_storage else None

    @property
    def title_logo_url(self):
        return get_upload_base_url() + self.title_logo.url if self.title_logo else None

    @property
    def hero_image_url(self):
        return get_upload_base_url() + self.hero_image.url if self.hero_image else None

    @property
    def cover_url_obj(self):
        image_obj = {}
        if self.cover_storage:
            image_obj['origin'] = self.cover_storage_url
            image_obj['button'] = self.cover_storage_url
            image_obj['cover'] = self.cover_storage_url
        return image_obj

    def import_handle(self, handle, language=None):
        if language == self.language or language is None:
            self.cover_storage = handle
        elif self.is_supported_language(language):
            self.localizations[language].import_handle(handle)

    def import_title_logo_handle(self, handle):
        self.title_logo = handle

    def import_hero_image_handle(self, handle):
        self.hero_image = handle

    @property
    def og_image_url_obj(self):
        og_image_obj = {}
        if self.og_image:
            og_image_obj['origin'] = get_upload_base_url() + self.og_image.url

            og_image_path = os.path.split(self.og_image.url)[0]

            og_image_button_url = og_image_path + '/og_image_button.jpg'
            og_image_obj['button'] = get_upload_base_url() + og_image_button_url

            og_image_120x63_url = og_image_path + '/og_image_120x63.jpg'
            og_image_obj['120*63'] = get_upload_base_url() + og_image_120x63_url

            og_image_600x315_url = og_image_path + '/og_image_600x315.jpg'
            og_image_obj['600*315'] = get_upload_base_url() + og_image_600x315_url

        return og_image_obj

        # return get_upload_base_url() + self.og_image.url if self.og_image else None

    def import_og_image_handle(self, handle, language=None):
        if language == self.language or language is None:
            self.og_image = handle
        elif self.is_supported_language(language):
            self.localizations[language].import_og_image_handle(handle)

    def set_name(self, name, language=None):
        if language == self.language or language is None:
            self.name = name
        elif self.is_supported_language(language):
            self.localizations[language].name=name
        else :
            localization = StoryLocalization(story=self, language=language, name=name)
            DBSession.add(localization)
            self.localizations[language] = localization

    def get_name(self, language=None):
        if self.is_supported_language(language):
            return self.localizations[language].name
        return self.name

    def set_description(self, description, language=None):
        if language == self.language or language is None:
            self.description = description
        elif self.is_supported_language(language):
            self.localizations[language].description=description

    def get_description(self, language=None):
        if self.is_supported_language(language):
            return self.localizations[language].description
        return self.description

    def get_language(self, language=None):
        if self.is_supported_language(language):
            return language
        return self.language

    def get_cover_storage_url(self, language=None):
        if self.is_supported_language(language):
            return self.localizations[language].cover_storage_url
        return self.cover_storage_url

    def get_cover_url_obj(self, language):
        if self.is_supported_language(language):
            return self.localizations[language].cover_url_obj
        return self.cover_url_obj

    def get_og_image_url_obj(self, language):
        if self.is_supported_language(language):
            return self.localizations[language].og_image_url_obj
        return self.og_image_url_obj

    def get_complementary_language(self, language):
        _language = None

        if language[:2] == 'zh':
            # try to find supported Chinese language
            _language = next((
                language for language in ['zh-HK', 'zh-TW', 'zh-CN']
                if self.is_supported_language(language)), None)

        if _language is None and self.is_supported_language('en'):  # attempt to fix issue #38
            _language = 'en'

        return _language

    @property
    def supported_languages(self):
        languages = [k for k in self.localizations.keys()]
        languages.append(self.language)
        return languages

    def serialize(self, language=None):
        return {
            'id': self.id,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'language': self.get_language(language),
            'author' : self.users[0].serialize() if self.users else None,  # assume user[0] is author
            'updatedAt': self.updated_at.isoformat(),
            'cover': self.get_cover_storage_url(language),
            'coverStorage': self.get_cover_storage_url(language), # deprecated
            'ogImage': self.get_og_image_url_obj(language),
        }

    def serialize_min(self, language=None):
        return {
            'id': self.id,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'cover': self.get_cover_storage_url(language),
            'authors': [u.serialize_min() for u in self.users],
        }

    def serialize_profile(self, language=None):
        return {
            'id': self.id,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'cover': self.get_cover_storage_url(language),
            'oiceUuid': self.oice[0].uuid if self.oice else '',
        }

    def serialize_app(self, user=None, language=None):
        return {
            'id': self.id,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'cover': self.get_cover_storage_url(language),
            'oiceUuid': self.oice[0].uuid if self.oice else '',
            'language': language,
            'oiceCount': len(self.published_oices),
            'likeCount': len(self.liked_users),
            'shareUrl': self.oice[0].get_share_url(language) if self.oice else '',
            'updatedAt': self.updated_at.isoformat(),
            'hasLiked': user in self.liked_users,
        }

    def serialize_featured(self, language=None):
        return {
            'id': self.id,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'cover': self.get_cover_storage_url(language),
            'titleLogo': self.title_logo_url,
            'heroImage': self.hero_image_url,
            'oice': self.oice[0].serialize() if self.oice else None,
        }


class StoryFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        one = StoryQuery(DBSession)\
            .get_story_by_id(key)
        return one


class StoryQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(Story)\
            .filter(Story.is_deleted == false())

    def get_story_by_id(self, story_id):
        return self.query.filter(Story.id == story_id)\
            .one()

    def get_story_by_id_list(self, story_ids):
        return self.query.filter(Story.id.in_(story_ids))\
            .all()

    def get_sample_story(self):
        return self.get_story_by_id(Story.get_sample_story_id())
