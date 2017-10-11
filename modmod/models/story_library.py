import sqlalchemy as sa

from modmod.models.base import (
    Base,
)

story_library = sa.Table(
    'story_library',
    Base.metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('story_id', sa.Integer, sa.ForeignKey('story.id'), nullable=False),
    sa.Column('library_id', sa.Integer, sa.ForeignKey('library.id'), nullable=False),
    sa.UniqueConstraint('story_id', 'library_id', name='story_id_library_id')
)
