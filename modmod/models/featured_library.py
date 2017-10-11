import sqlalchemy as sa
from sqlalchemy.orm import relationship
from modmod.models.base import (
    Base,
)

class FeaturedLibrary(Base):
    __tablename__ = 'featured_library'

    id = sa.Column('id', sa.Integer, primary_key=True)
    list_id = sa.Column('list_id', sa.Integer, sa.ForeignKey('featured_library_list.id'), nullable=False)
    library_id = sa.Column('library_id', sa.Integer, sa.ForeignKey('library.id'), nullable=False)
    order = sa.Column(sa.Integer, nullable=False, server_default='0')
    library = relationship("Library")
