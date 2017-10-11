import sqlalchemy as sa
from sqlalchemy.orm import relationship
from modmod.models.base import (
    Base,
)

class TutorialOice(Base):
    __tablename__ = 'tutorial_oice'

    id = sa.Column('id', sa.Integer, primary_key=True)
    oice_id = sa.Column('oice_id', sa.Integer, sa.ForeignKey('oice.id'), nullable=False)
    order = sa.Column('order', sa.Integer, nullable=False)
    oice = relationship("Oice")
