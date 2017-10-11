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


class CharacterLocalization(Base, BaseMixin):
    __tablename__ = 'character_localization'
    character_id = sa.Column('character_id', sa.Integer, sa.ForeignKey('character.id'), nullable=False)
    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    language = sa.Column(sa.Unicode(5), nullable=False, server_default="zh-HK")
    __table_args__ = (
        Index('characterlocalization_character_language_idx', 'character_id', 'language'),
    )
