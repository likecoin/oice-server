import sqlalchemy as sa
from sqlalchemy import Index
from sqlalchemy.sql.expression import false
import logging

from modmod.models.base import (
    Base,
    BaseMixin,
)

from . import DBSession

log = logging.getLogger(__name__)

class LikecoinTx(Base, BaseMixin):
    __tablename__ = 'likecoin_tx'

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)

    # Possible values of product_type: library
    product_type = sa.Column(sa.Unicode(128), index=True, nullable=False)
    product_id = sa.Column(sa.Integer, nullable=False)

    tx_hash =  sa.Column(sa.Unicode(128), nullable=True, unique=True)
    from_ = sa.Column(sa.Unicode(128), name='from', nullable=True)
    to = sa.Column(sa.Unicode(128), nullable=True)
    amount = sa.Column(sa.Float, nullable=False)
    max_reward = sa.Column(sa.Float, nullable=False, server_default='0')

    # Possible values of status: pending / success / failed
    status = sa.Column(sa.Unicode(128), index=True, nullable=False, server_default='pending')

    __table_args__ = (
        sa.UniqueConstraint('user_id', 'product_type', 'product_id', name='user_id_product_type_product_id'),
    )


class LikecoinTxFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        tx = LikecoinTxQuery(DBSession).get_by_id(key)
        return tx


class LikecoinTxQuery:
    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(LikecoinTx)

    def get_by_id(self, id):
        return self.query \
                   .filter(LikecoinTx.id == id) \
                   .one()

    def get_by_tx_hash(self, tx_hash):
        return self.query \
                   .filter(LikecoinTx.tx_hash == tx_hash) \
                   .one()
