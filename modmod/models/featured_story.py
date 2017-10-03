import sqlalchemy as sa
from sqlalchemy.orm import relationship
from modmod.models.base import Base


class FeaturedStory(Base):
    __tablename__ = 'featured_story'

    id = sa.Column('id', sa.Integer, primary_key=True)
    story_id = sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), nullable=False)
    order = sa.Column('order', sa.Integer, nullable=False)

    story = relationship("Story")
