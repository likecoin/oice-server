import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.orm import relationship
from modmod.models.base import (
    Base,
)

class FeaturedLibraryListLocalization(Base):
    __tablename__ = 'featured_library_list_localization'
    __table_args__ = (
        Index('featuredlibrarylistlocalization_featuredlibrarylist_language_idx', 'list_id', 'language'),
    )

    id = sa.Column('id', sa.Integer, primary_key=True)
    list_id = sa.Column('list_id', sa.Integer, sa.ForeignKey('featured_library_list.id'), nullable=False)
    name = sa.Column(sa.Unicode(256), nullable=False)
    language = sa.Column(sa.Unicode(5), nullable=False, server_default="zh-HK")
