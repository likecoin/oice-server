import sqlalchemy as sa
from modmod.models.base import Base


class StoryTagLocalization(Base):
    __tablename__ = 'story_tag_localization'

    id = sa.Column(sa.Integer, primary_key=True)
    tag_id = sa.Column('tag_id', sa.Integer, sa.ForeignKey('story_tag.id'), nullable=False)
    language = sa.Column(sa.Unicode(5), nullable=False, server_default='zh-HK')
    name = sa.Column(sa.Unicode(128), nullable=False)

    __table_args__ = (
        sa.Index('story_tag_localization_story_tag_language_idx', 'tag_id', 'language', unique=True),
    )
