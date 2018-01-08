import sqlalchemy as sa
from modmod.models.base import Base


story_tagging = sa.Table(
    'story_tagging',
    Base.metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), nullable=False),
    sa.Column('tag_id', sa.Integer, sa.ForeignKey('story_tag.id'), nullable=False),
    sa.UniqueConstraint('story_id', 'tag_id', name='story_tagging_unique')
)