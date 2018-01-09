import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import false
from modmod.models.base import Base
from . import DBSession


class StoryTag(Base):
    __tablename__ = 'story_tag'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(128), index=True, nullable=False, unique=True)
    order = sa.Column(sa.Integer, nullable=False)
    is_hidden = sa.Column(sa.Boolean, nullable=False, index=True, server_default=false())
    priority = sa.Column(sa.Integer, nullable=False, index=True, server_default='0')
    localizations = relationship('StoryTagLocalization',
                                 collection_class=attribute_mapped_collection('language'),
                                 cascade='all, delete-orphan',
                                 lazy='joined')

    def get_name(self, language=None):
        if language is not None and language in self.localizations:
            return self.localizations[language].name
        return self.name

    def serialize(self, language='en'):
        return {
            'id': self.id,
            'name': self.get_name(language),
        }


class StoryTagQuery:
    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(StoryTag)

    def fetch_all(self):
        return self.query.filter(StoryTag.is_hidden == false()).order_by(StoryTag.order).all()
