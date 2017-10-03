import os
import sqlalchemy as sa
from sqlalchemy import Index
from pyramid_safile import FileHandleStore
import logging

from modmod.models.base import (
    Base,
    BaseMixin,
)
from ..config import get_upload_base_url


log = logging.getLogger(__name__)


class StoryLocalization(Base, BaseMixin):
    __tablename__ = 'story_localization'
    story_id = sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), nullable=False)
    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    description = sa.Column(sa.Unicode(4096), nullable=False, server_default="")
    language = sa.Column(sa.Unicode(5), nullable=False, server_default="zh-HK")
    cover_storage = sa.Column(FileHandleStore, nullable=True)
    og_image = sa.Column(FileHandleStore, nullable=True)
    __table_args__ = (
        Index('storylocalization_oice_language_idx', 'story_id', 'language'),
    )

    @property
    def cover_storage_url(self):
        return get_upload_base_url() + self.cover_storage.url if self.cover_storage else None

    @property
    def cover_url_obj(self):
        image_obj = {}
        if self.cover_storage:
            image_obj['origin'] = self.cover_storage_url
            image_obj['button'] = self.cover_storage_url
            image_obj['cover'] = self.cover_storage_url
        return image_obj

    def import_handle(self, handle):
        self.cover_storage = handle

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

    def import_og_image_handle(self, handle):
        self.og_image = handle
