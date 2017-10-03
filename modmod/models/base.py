import logging
from datetime import datetime
import sqlalchemy as sa

from pyramid.security import ALL_PERMISSIONS
from pyramid.security import Allow
from sqlalchemy.ext.declarative import declarative_base

from . import DBSession

log = logging.getLogger(__name__)
Base = declarative_base()


class BaseMixin(object):

    __table_args__ = {'mysql_engine': 'InnoDB'}

    id = sa.Column('id', sa.Integer, primary_key=True)
    created_at = sa.Column('created_at', sa.DateTime, nullable=False)
    updated_at = sa.Column('updated_at', sa.DateTime, nullable=False)

    def __acl__(self):
        return [
            (Allow, 'r:admin', ALL_PERMISSIONS)
        ]

    @staticmethod
    def create_time(mapper, connection, instance):
        now = datetime.utcnow()
        instance.created_at = now
        instance.updated_at = now

    @staticmethod
    def update_time(mapper, connection, instance):
        if DBSession.is_modified(instance, include_collections=False):
            now = datetime.utcnow()
            instance.updated_at = now

    @classmethod
    def register(cls):
        sa.event.listen(
            BaseMixin, 'before_insert', cls.create_time, propagate=True)
        sa.event.listen(
            BaseMixin, 'before_update', cls.update_time, propagate=True)

    def accept(self, visitor, *args, **kwargs):
        klass = self.__class__.__name__.lower()
        return getattr(visitor, 'visit_' + klass)(self, *args, **kwargs)

BaseMixin.register()
