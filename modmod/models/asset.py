import mimetypes
import os
import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import true, false, null
from pyramid.security import Allow
from pyramid_safile import FileHandleStore

from modmod.models.base import (
    Base,
    BaseMixin,
)
from .asset_asset_type import association_table
from .asset_type import AssetType
from .asset_user import asset_user
from . import DBSession


class Asset(Base, BaseMixin):
    __tablename__ = 'asset'

    asset_types = relationship(
        "AssetType",
        secondary=association_table,
        lazy="joined",
        backref='assets',
        cascade='')

    name_tw = sa.Column(sa.Unicode(1024), nullable=False)
    name_en = sa.Column(sa.Unicode(1024), nullable=False)
    name_jp = sa.Column(sa.Unicode(1024), nullable=False)
    filename = sa.Column(sa.Unicode(1024), nullable=True)
    storage = sa.Column(FileHandleStore, nullable=True)
    credits_url = sa.Column(sa.Unicode(1024), nullable=False, server_default='')
    content_type = sa.Column(sa.Unicode(1024), nullable=True)
    order = sa.Column(sa.Integer, nullable=False, server_default='0')
    library_id = sa.Column(sa.Integer, sa.ForeignKey('library.id'), nullable=False)
    is_deleted = sa.Column(sa.Boolean, nullable=False, server_default=false())
    is_hidden = sa.Column(sa.Boolean, nullable=False, server_default=false())

    __table_args__ = (
        sa.Index('asset_library_idx', 'library_id', 'is_deleted'),
    )

    users = relationship(
        "User",
        secondary=asset_user,
        lazy='joined',
        cascade='',
        backref='assets'
    )

    def serialize(self):
        return {
            'id': self.id,
            'nameTw': self.name_tw,
            'nameEn': self.name_en,
            'nameJp': self.name_jp,
            'libraryId': self.library_id,
            'types': [type_.serialize() for type_ in self.asset_types],
            'contentType': self.content_type,
            'url': self.url(),
            'order': self.order,
            'users': [user.serialize_min() for user in self.users] if self.users else None,
            'creditsUrl': self.credits_url,
        }

    @property
    def __acl__(self):
        acl = super(Asset, self).__acl__()
        for user in self.library.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    def url(self):
        return self.storage.url if self.storage else None

    @property
    def extension(self):
        if self.filename is not None:
            return os.path.splitext(self.filename)[1]

        extension = mimetypes.guess_extension(self.content_type)

        if extension == ".mp3":
            # o2engine requires .mp4 instead of .mp3 for mobile compatibility
            return ".mp4"

        if extension == ".oga":
            # o2engine requires .ogg instead of .oga for mobile compatibility
            return ".ogg"

        return extension

    @classmethod
    def from_handle(cls, handle=None, asset_types=[], name_tw="", name_en="", name_jp="", library_id=None,
                    filename=None, users=[], credits_url='', order=0):
        self = cls(name_tw=name_tw,
                   name_en=name_en,
                   name_jp=name_jp,
                   filename=filename,
                   order=order)
        self.import_handle(handle)
        self.asset_types = asset_types
        self.library_id = library_id
        self.users = users
        self.credits_url = credits_url

        return self

    @property
    def export_filename(self):
        return "modmod_%d_%d" % (self.id, int(self.updated_at.timestamp()))

    @property
    def export_filename_with_ext(self):
        return self.export_filename + self.extension

    def import_handle(self, handle):
        if handle:
            self.storage = handle
            self.content_type = mimetypes.guess_type(handle.filename, strict=False)[0]
            if self.content_type is None:
                self.content_type = 'application/octet-stream'

class AssetFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        one = DBSession.query(Asset) \
                     .filter(Asset.id == key) \
                     .one()
        return one

class AssetQuery:
    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(Asset)\
            .filter(Asset.is_deleted == false())

    @property
    def count(self):
        return self.session.query(func.count(Asset.id))\
            .filter(Asset.is_deleted == false())

    def get_by_id(self, asset_id):
        return self.query \
                   .filter(Asset.id == asset_id) \
                   .one()

    def get_by_ids(self, asset_ids):
        return self.query \
                    .filter(Asset.id.in_(asset_ids)) \
                    .all()

    def count_by_library(self, library):
        library_id = library.id
        return self.count \
                   .filter(Asset.library_id == library_id)\
                   .scalar()

    @classmethod
    def fetch_by_library(cls, library, session=DBSession):
        library_id = library.id
        return session.query(Asset) \
            .filter(Asset.library_id == library_id) \
            .filter(Asset.is_deleted == false()) \
            .filter(Asset.storage != null()) \
            .order_by(Asset.order) \
            .all()

    def get_last_order_in_library(self, library_id):
        asset = self.query \
                    .filter(Asset.library_id == library_id) \
                    .order_by(Asset.order.desc()) \
                    .first()

        return asset.order + 1 if asset else 1
