import sqlalchemy as sa
from sqlalchemy.orm import relationship
from pyramid.security import Allow

from modmod.models.base import Base, BaseMixin
from . import DBSession


class UserLink(Base, BaseMixin):
    __tablename__ = 'user_link'

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    user_link_type_id = sa.Column(sa.Integer, sa.ForeignKey('user_link_type.id'), nullable=True)
    label = sa.Column(sa.Unicode(1024), nullable=False, server_default="")
    link = sa.Column(sa.Text, nullable=False)
    order = sa.Column(sa.Integer, nullable=False)

    type = relationship('UserLinkType')

    __table_args__ = (
        sa.Index('user_link_order_index', 'user_id', 'order'),
    )

    def __init__(self, user_id, label, link, order, user_link_type_id=None):
        self.user_id = user_id
        self.user_link_type_id = user_link_type_id
        self.label = label
        self.link = link
        self.order = order

    @property
    def __acl__(self):
        acl = super(UserLink, self).__acl__()
        acl = acl + [(Allow, self.user.email, 'get'),
                     (Allow, self.user.email, 'set')]
        return acl

    def serialize(self):
        return {
            'id': self.id,
            'typeAlias': self.type.alias if self.type else None,
            'label': self.label,
            'link': self.link,
        }


class UserLinkFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        one = UserLinkQuery(DBSession).fetch_by_id(key)
        return one


class UserLinkQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(UserLink)

    def fetch_by_id(self, id):
        return self.query \
                   .filter(UserLink.id == id) \
                   .one()
