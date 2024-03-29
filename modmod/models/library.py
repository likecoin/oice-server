import json
import os
import itertools
import sqlalchemy as sa
from sqlalchemy import func, Index
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import true, false
from sqlalchemy.orm import lazyload
from pyramid.security import Allow
from pyramid_safile import FileHandleStore
from .user import User
from .user_library import user_library
from .user_purchased_library import user_purchased_library
from .user_selected_library import user_selected_library
from ..config import get_upload_base_url

from datetime import (
    datetime,
    timedelta,
)

from modmod.models.base import (
    Base,
    BaseMixin,
)

from .asset import Asset, AssetQuery
from . import DBSession

class Library(Base, BaseMixin):
    __tablename__ = 'library'

    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    asset = relationship(Asset,
                        primaryjoin='''and_(
                                            Library.id==Asset.library_id, \
                                            Asset.is_deleted==false(), \
                                            Asset.storage!=null() \
                                        )''',
                        cascade="all,delete",
                        backref=backref("library", lazy="joined"))
    is_deleted = sa.Column(sa.Boolean, nullable=False, server_default=false())
    description = sa.Column(sa.Unicode(4096), nullable=False, server_default="")
    license = sa.Column(sa.SmallInteger, nullable=False, server_default='0')
    cover_storage = sa.Column(FileHandleStore, nullable=True)
    is_public = sa.Column(sa.Boolean, nullable=False, server_default=false())
    is_default = sa.Column(sa.Boolean, nullable=False, index=True, server_default=false())
    priority = sa.Column(sa.Integer, nullable=False, server_default='0')
    price = sa.Column(sa.Float, nullable=False, index=True, server_default='-1')
    discount_price = sa.Column(sa.Float, nullable=False, server_default='0')
    # Possible values of settlement_currency
    # fiat / likecoin / None (which means free or private library)
    settlement_currency = sa.Column(sa.Unicode(128), index=True, nullable=True, server_default="")
    launched_at = sa.Column(sa.DateTime, nullable=True)
    users = relationship(
        "User",
        secondary=user_library,
        lazy='joined',
        cascade='',
        backref=backref("libraries", lazy="select")
    )
    purchased_users = relationship(
        "User",
        secondary=user_purchased_library,
        primaryjoin='''and_(
            user_purchased_library.c.library_id==Library.id,
            Library.is_deleted==false()
        )''',
        lazy='select',
        cascade='',
        backref=backref("libraries_purchased", lazy="select")
    )

    __table_args__ = (
        Index('ispublic_launchedat_idx', 'is_public', 'launched_at'),
    )

    @property
    def __acl__(self):
        acl = super(Library, self).__acl__()
        for user in self.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    @classmethod
    def create(cls, session, *args, **kwargs):
        # create normal project
        # add default lib and itself to the lib projects list
        self = cls(*args, **kwargs)
        return self

    @property
    def cover_storage_url(self):
        return get_upload_base_url() + self.cover_storage.url \
                if self.cover_storage else self.users[0].avatar_url()

    def import_handle(self, handle):
        self.cover_storage = handle

    def serialize_min(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cover': self.cover_storage_url,
            'coverStorage': self.cover_storage_url, # Deprecated
            'price': self.price,
            'discountPrice': self.discount_price,
            'settlementCurrency': self.settlement_currency,
            'license': self.license,
            'isPublic': self.is_public,
            'isNew': self.is_new,
            'isRecentUpdated': self.is_recent_updated,
            'assetCount': self.asset_count,
        }

    def serialize_og(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cover': self.cover_storage_url,
        }

    def serialize(self, user=None, isSelected=False):
        serialized_library = self.serialize_min()
        serialized_library['description'] = self.description
        serialized_library['isCollaborator'] = user in self.users
        serialized_library['author'] = self.users[0].serialize_min() if self.users else None  # Assume user[0] is the author
        serialized_library['updatedAt'] = self.updated_at.isoformat()
        serialized_library['launchedAt'] = self.launched_at.isoformat() if self.launched_at else None
        serialized_library['isSelected'] = isSelected
        return serialized_library

    def serialize_profile(self):
        return {
            'id': self.id,
            'name': self.name,
            'cover': self.cover_storage_url,
            'priority': self.priority,
        }

    def serialize_store(self, user=None):
        serialized_store = self.serialize_min()
        serialized_store['isCollaborator'] = user in self.users
        serialized_store['isPurchased'] = self.has_user_purchased(user)
        return serialized_store

    def serialize_store_detail(self, user=None):
        serialized_store = self.serialize_store(user)
        serialized_store['createdAt'] = self.created_at.isoformat()
        serialized_store['updatedAt'] = self.updated_at.isoformat()
        serialized_store['launchedAt'] = self.launched_at.isoformat() if self.launched_at else None
        serialized_store['author'] = self.users[0].serialize_min() if self.users else None  # Assume user[0] is the author
        serialized_store['credits'] = [u.serialize_credit() for u in self.get_assset_credits()]
        serialized_store['isSelected'] = self.has_user_selected(user)
        return serialized_store

    def get_assset_credits(self):
        asset_users = [a.users for a in self.asset if not a.is_deleted]
        merged = set(itertools.chain.from_iterable(asset_users))
        credits = sorted(merged, key=lambda user: user.display_name)
        return credits

    def has_user_purchased(self, user):
        if user is None:
            return False
        return LibraryQuery(DBSession) \
                   .query \
                   .join(Library.purchased_users) \
                   .filter(User.id == user.id) \
                   .filter(Library.id == self.id) \
                   .count() > 0

    def has_user_selected(self, user):
        if user is None:
            return False
        return LibraryQuery(DBSession) \
                   .query \
                   .join(Library.selected_users) \
                   .filter(User.id == user.id) \
                   .filter(Library.id == self.id) \
                   .count() > 0

    @property
    def is_new(self):
        return bool(self.created_at + timedelta(days=7) > datetime.utcnow() \
            or (self.launched_at and self.launched_at + timedelta(days=7) > datetime.utcnow()))

    @property
    def is_recent_updated(self):
        return bool(self.updated_at + timedelta(days=7) > datetime.utcnow())

    @property
    def is_launched(self):
        return bool(self.launched_at)

    @property
    def asset_count(self):
        return AssetQuery(DBSession).count_by_library(self)

class LibraryFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            return LibraryQuery(DBSession).get_library_by_id(key)
        except NoResultFound:
            raise NoResultFound('ERR_LIBRARY_NOT_EXIST')

class LibraryQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(Library)\
            .filter(Library.is_deleted == false())

    @property
    def count(self):
        return self.session.query(func.count(Library.id))\
            .filter(Library.is_deleted == false())

    def get_library_by_id(self, library_id):
        return self.query.filter(Library.id == library_id)\
            .one()

    def get_librarys_by_ids(self, library_ids):
        return self.query \
                   .filter(Library.id.in_(library_ids)) \
                   .all()

    def fetch_default_libs(self):
        return self.query\
            .filter(Library.is_default == true())

    def fetch_public_libs(self):
        return self.query\
            .filter(Library.is_public == true())

    def fetch_store_libs(self):
        q = self.session.query(Asset).filter(Asset.library_id == Library.id)
        return self.query\
            .options(lazyload(Library.users))\
            .filter(q.exists())\
            .filter(Library.is_public == true())\
            .filter(Library.launched_at.isnot(None))

    def count_store_libs(self):
        q = self.session.query(Asset).filter(Asset.library_id == Library.id)
        return self.count\
            .filter(q.exists())\
            .filter(Library.is_public == true())\
            .filter(Library.launched_at.isnot(None))

    def fetch_free_store_libs(self):
        return self.fetch_store_libs()\
            .filter(Library.price == 0)

    def count_free_store_libs(self):
        return self.count_store_libs()\
            .filter(Library.price == 0)

    def count_paid_store_libs(self):
        return self.count_store_libs() \
            .filter(Library.settlement_currency == 'fiat')

    def fetch_paid_store_libs(self):
        return self.fetch_store_libs() \
            .filter(Library.settlement_currency == 'fiat')

    def count_likecoin_store_libs(self):
        return self.count_store_libs() \
            .filter(Library.settlement_currency == 'likecoin')

    def fetch_likecoin_store_libs(self):
        return self.fetch_store_libs() \
            .filter(Library.settlement_currency == 'likecoin')
