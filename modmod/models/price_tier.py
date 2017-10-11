import sqlalchemy as sa

from modmod.models.base import (
    Base,
)

from . import DBSession

class PriceTier(Base):
    __tablename__ = 'price_tier'

    id = sa.Column('id', sa.Integer, primary_key=True)
    tier = sa.Column(sa.SmallInteger, nullable=False, server_default='0')
    price_usd = sa.Column(sa.Float, nullable=False, server_default='0')

    def serialize(self):
        return {
            "id": self.id,
            "tier": self.tier,
            "price": self.price_usd
        }

class PriceTierQuery:

    def __init__(self, session=DBSession):
        self.session = session

    def get_price_usd_by_tier(self, tier):
        return self.session.query(PriceTier.price_usd)\
            .filter(PriceTier.tier == tier)\
            .one()\
            .price_usd
