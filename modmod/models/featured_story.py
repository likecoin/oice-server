import sqlalchemy as sa
from sqlalchemy.orm import relationship
from modmod.models.base import Base
from . import DBSession


class FeaturedStory(Base):
    __tablename__ = 'featured_story'

    id = sa.Column('id', sa.Integer, primary_key=True)
    story_id = sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), nullable=False)
    # Normalized language code
    language = sa.Column(sa.Unicode(5), nullable=False, index=True, server_default='zh-HK')
    # Affect latest app
    tier = sa.Column('tier', sa.Integer, index=True, nullable=False)
    # Affect web and legacy app
    order = sa.Column('order', sa.Integer, index=True, nullable=False)

    story = relationship("Story")


class FeaturedStoryQuery:
    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(FeaturedStory)

    def has_language(self, language):
        return bool(self.session.execute('''
                                         SELECT 1
                                         FROM `featured_story`
                                         WHERE `language` LIKE "%s%%"''' % language
                                         ).scalar())

    def fetch_by_language(self, language):
        return self.query.filter(FeaturedStory.language.like(language + '%'))
