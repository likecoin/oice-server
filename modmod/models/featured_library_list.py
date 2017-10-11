import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import true, false
from sqlalchemy.orm.collections import attribute_mapped_collection
from modmod.models.base import (
    Base,
)
from . import DBSession


class FeaturedLibraryList(Base):
    __tablename__ = 'featured_library_list'

    id = sa.Column('id', sa.Integer, primary_key=True)
    alias = sa.Column('alias', sa.Unicode(length=256), nullable=False, index=True, unique=True)
    is_active = sa.Column(sa.Boolean, nullable=False, server_default=false())
    order = sa.Column(sa.Integer, nullable=False, index=True, server_default='0')
    libraries = relationship(
        'FeaturedLibrary',
        primaryjoin="FeaturedLibraryList.id==FeaturedLibrary.list_id",
        lazy='joined',
        cascade='',
        order_by='FeaturedLibrary.order',
    )
    localizations = relationship("FeaturedLibraryListLocalization",
                              collection_class=attribute_mapped_collection('language'),
                              cascade="all,delete-orphan",
                              backref="featured_library_list",
                              lazy="joined")

    def get_name(self, language):
        return self.localizations[language].name

    def serialize(self, language):
        return {
            "id": self.id,
            "name": self.get_name(language),
            "alias": self.alias,
        }


class FeaturedLibraryListQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(FeaturedLibraryList) \
                .filter(FeaturedLibraryList.is_active == true())

    def get_library_by_alias(self, alias):
        return self.query \
                .filter(FeaturedLibraryList.alias == alias) \
                .one_or_none()
