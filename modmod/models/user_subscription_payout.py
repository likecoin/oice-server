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


class UserSubscriptionPayout(Base, BaseMixin):
    __tablename__ = 'user_subscription_payout'

    subscription_user_id = sa.Column('subscription_user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    oice_id = sa.Column('oice_id', sa.Integer, sa.ForeignKey('oice.id'), nullable=False)
    author_id = sa.Column('author_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    # Possible values of platform:
    # - stripe
    # - android
    # - ios
    platform = sa.Column('platform', sa.Unicode(16), nullable=False)
    original_transaction_id = sa.Column(sa.Unicode(128), nullable=True, unique=True)
    payout_amount = sa.Column(sa.Float, nullable=False, server_default='0')
    is_paid = sa.Column(sa.Boolean, nullable=False, server_default=false())

    __table_args__ = (
        Index('usersubscriptionpayout_author_idx', 'author_id', 'is_paid'),
    )

class UserSubscriptionPayoutQuery:
    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(UserSubscriptionPayout)

    def fetch_by_transaction_id(self, transaction_id):
        return self.query \
                   .filter(UserSubscriptionPayout.original_transaction_id == transaction_id)\
                   .one_or_none()

    def fetch_unpaid_by_author_id(self, author_id):
        return self.query \
                   .filter(UserSubscriptionPayout.author_id == author_id)\
                   .filter(UserSubscriptionPayout.is_paid == false())\
                   .all()