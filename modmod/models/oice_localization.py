import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.sql.expression import false
import logging

from modmod.models.base import (
    Base,
    BaseMixin,
)
from . import DBSession
log = logging.getLogger(__name__)


class OiceLocalization(Base, BaseMixin):
    __tablename__ = 'oice_localization'
    oice_id = sa.Column('oice_id', sa.Integer, sa.ForeignKey('oice.id'), nullable=False)
    filename = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    language = sa.Column(sa.Unicode(5), nullable=False, server_default="zh-HK")
    __table_args__ = (
        Index('oicelocalization_oice_language_idx', 'oice_id', 'language'),
    )
