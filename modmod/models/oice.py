import uuid
import os
import sqlalchemy as sa
from sqlalchemy.orm import relationship, validates, backref
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import true, false
from pyramid.security import Allow
from modmod.exc import ValidationError
from pyramid_safile import FileHandleStore
from ..config import (
    get_gcloud_bucket_id,
    get_o2_output_dir,
    get_oice_url,
    get_oice_view_url,
    get_upload_base_url,
)
from .oice_localization import OiceLocalization
from modmod.models.base import (
    Base,
    BaseMixin,
)

from . import DBSession
import logging

log = logging.getLogger(__name__)

class Oice(Base, BaseMixin):
    __tablename__ = 'oice'

    uuid = sa.Column(sa.Unicode(32), nullable=False, unique=True)
    story_id = sa.Column(
        sa.Integer, sa.ForeignKey('story.id'), nullable=False)
    order = sa.Column(sa.Integer, nullable=False)
    filename = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    is_deleted = sa.Column(sa.Boolean, nullable=False, server_default=false())
    is_show_ad = sa.Column(sa.Boolean, nullable=False, server_default=true())
    language = sa.Column(sa.Unicode(5), nullable=False, server_default="zh-HK")
    # Possible values of sharing_option
    # 0: Public
    # 1: Accessible by URL only
    # 999: Private
    sharing_option = sa.Column(sa.Integer, nullable=False, server_default="999")
    # Possible values of state
    # 0: Initial
    # 1: Previewed
    # 2: Published
    state = sa.Column(sa.Integer, nullable=False, server_default="0")
    fork_of = sa.Column(sa.Integer, nullable=True)
    view_count = sa.Column(sa.Integer, nullable=False, server_default="0")

    blocks = relationship(
        "Block",
        order_by="Block.position")

    localizations = relationship("OiceLocalization",
                              collection_class=attribute_mapped_collection('language'),
                              cascade="all,delete-orphan",
                              backref="oice",
                              lazy="joined")

    def __init__(self, *arg, **kw):
        super().__init__(*arg, **kw)
        if self.uuid is None:
            self.uuid = uuid.uuid4().hex

    @property
    def __acl__(self):
        acl = super(Oice, self).__acl__()
        for user in self.story.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    @property
    def image_url_obj(self):
        return self.get_image_url_obj()

    @property
    def og_image_url_obj(self):
        return self.get_og_image_url_obj()

    @property
    def description(self):
        return self.get_description()

    @property
    def og_title(self):
        return self.story.get_name() + ': ' + self.get_name()

    @property
    def og_description(self):
        return self.get_description()

    def get_image_url_obj(self, language=None):
        return self.story.get_cover_url_obj(language)

    def get_og_image_url_obj(self, language=None):
        return self.story.get_og_image_url_obj(language)

    def get_description(self, language=None):
        return self.story.get_description(language)

    def get_og_title(self, language=None):
        return self.story.get_name(language) + ': ' + self.get_name(language)

    def get_og_description(self, language=None):
        return self.story.get_description(language)

    def get_oice_url_with_language(self, url, language):
        if language:
            return '{}?lang={}'.format(url, language)
        return url

    @property
    def has_previewed(self):
        return self.state >= 1

    @property
    def has_published(self):
        return self.state >= 2

    def preview(self):
        if not self.has_previewed:
            self.state = 1

    def publish(self):
        if not self.has_published:
            self.state = 2

        # Don't set public to oice forked from sample story
        if not self.story.is_fork_from_sample_story:
            self.set_public()

    def reset_state(self):
        self.state = 0

    def set_public(self):
        self.sharing_option = 0

    def set_private(self):
        self.sharing_option = 999

    def is_public(self):
        return self.sharing_option == 0

    def get_share_url(self, language=None):
        share_url = get_oice_view_url(self.uuid)
        if language is not None and language in self.localizations and language != self.story.language:
            return self.get_oice_url_with_language(share_url, language)
        return share_url

    def get_oice_preview_url(self, language=None):
        view_url = get_oice_url(self.uuid)
        if language is not None and language in self.localizations:
            return self.get_oice_url_with_language(view_url, language)
        return view_url

    def get_view_url(self, language=None):
        view_url = get_gcloud_bucket_id() + get_o2_output_dir(self.uuid)
        if language is not None and language in self.localizations:
            return self.get_oice_url_with_language(view_url, language)
        return view_url

    def set_name(self, filename, language=None):
        if language == self.language:
            self.filename = filename
        elif language is not None and language in self.localizations:
            self.localizations[language].filename=filename
        else :
            localization = OiceLocalization(oice=self, language=language, filename=filename)
            DBSession.add(localization)
            self.localizations[language] = localization

    def get_name(self, language=None):
        if language is not None and language in self.localizations:
            return self.localizations[language].filename
        return self.filename

    def get_language(self, language=None):
        if language is not None and language in self.localizations:
            return language
        return self.language

    def get_next_episode(self, language=None):
        number_of_episodes = len(self.story.oice)
        next_oice = self.story.oice[(self.order + 1) % number_of_episodes] if number_of_episodes > 0 else None
        if not next_oice:
            return None
        return (next_oice if next_oice.is_public() and next_oice.has_published else self).serialize_min(language)

    def serialize(self, user=None, language=None):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'storyId': int(self.story_id),
            'storyName': self.story.get_name(language),
            'storyDescription': self.story.get_description(language),
            'storyCover': self.story.get_cover_storage_url(language),
            'name': self.get_name(language),
            'order': self.order,
            'description': self.get_description(language),
            'image': self.get_image_url_obj(language),
            'ogTitle': self.get_og_title(language),
            'ogDescription': self.get_og_description(language),
            'ogImage' : self.get_og_image_url_obj(language),
            'language' : self.get_language(language),
            'isShowAd': self.is_show_ad,
            'author' : self.story.users[0].serialize_credit(),  # assume user[0] is author
            'updatedAt': self.updated_at.isoformat(),
            'sharingOption': self.sharing_option,
            'hasPreviewed': self.has_previewed,
            'hasPublished': self.has_published,
            'url': self.get_view_url(language),
            'previewUrl': self.get_oice_preview_url(language),
            'shareUrl': self.get_share_url(language),
            'viewCount': self.view_count,
            'hasLiked': user in self.story.liked_users,
            'nextEpisode': self.get_next_episode(language),
        }

    def serialize_min(self, language=None):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'order': self.order,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'image': self.get_image_url_obj(language).get('cover'),
        }

    def serialize_profile(self, language=None):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'episode': self.order + 1,
            'name': self.get_name(language),
            'description': self.get_description(language),
            'cover': self.get_image_url_obj(language).get('cover'),
        }

    @validates('filename')
    def validate_tag(self, key, filename):
        if not filename:
            raise ValidationError("File name is needed.")

        if filename.startswith("_modmod"):
            raise ValidationError("This file name is reserved, "
                                  "please choose another name.")

        return filename


class OiceFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        oice = OiceQuery(DBSession).get_by_id(key)
        return oice


class OiceQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(Oice)\
            .filter(Oice.is_deleted == false())

    def fetch_oice_list_by_id(self, story_id):
        return self.query \
                   .filter(Oice.story_id == story_id) \
                   .order_by(Oice.order)

    def get_by_id(self, oice_id):
        return self.query \
                   .filter(Oice.id == oice_id) \
                   .one()

    def get_by_ids(self, oice_ids):
       return self.query \
                   .filter(Oice.id.in_(oice_ids)) \
                   .all()

    def get_by_uuid(self, uuid):
        return self.query \
                   .filter(Oice.uuid == uuid) \
                   .one_or_none()

    def get_sample_oice(self, language=None):
        oice_id = 10261

        if language:
            if language[:2] == 'zh':
                oice_id = 1055
            elif language[:2] == 'ja':
                oice_id = 10260

        return self.get_by_id(oice_id)
