import sqlalchemy as sa

from modmod.models.base import (
    Base,
    BaseMixin,
)
from . import DBSession


class AssetType(Base, BaseMixin):
    __tablename__ = 'asset_type'

    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    folder_name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    type_ = sa.Column('type', sa.Unicode(1024), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "name": self.folder_name,
            "type": self.type_
        }

class AssetTypeQuery:
    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(AssetType)

    def fetch_all_asset_type(self):
        return self.query.all()
