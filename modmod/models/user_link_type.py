import sqlalchemy as sa
from modmod.models.base import Base

from . import DBSession


class UserLinkType(Base):
    __tablename__ = 'user_link_type'

    id = sa.Column('id', sa.Integer, primary_key=True)
    alias = sa.Column(sa.Unicode(32), nullable=False)
    name = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    link_regex = sa.Column(sa.Unicode(1024), nullable=False, server_default="")

    __table_args__ = (
        sa.UniqueConstraint('alias', name='user_link_type_alias_unique'),
    )

    def serialize(self):
        return {
            'alias': self.alias,
            'name': self.name,
            'linkRegex': self.link_regex,
        }


class UserLinkTypeQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(UserLinkType)

    def fetch_all(self):
        return self.query.all()

    def fetch_by_alias(self, alias):
        return self.query \
            .filter(UserLinkType.alias == alias) \
            .one_or_none()
