import sqlalchemy as sa
from sqlalchemy.sql.expression import false
from sqlalchemy.orm import relationship
from modmod.models.base import Base, BaseMixin
from . import DBSession


class UserReadOiceProgress(Base, BaseMixin):
    __tablename__ = 'user_read_oice_progress'

    user_id = sa.Column(sa.Integer, sa.ForeignKey('user.id'), nullable=False)
    oice_id = sa.Column(sa.Integer, sa.ForeignKey('oice.id'), nullable=False)
    is_finished = sa.Column(sa.Boolean, nullable=False, server_default=false())

    oice = relationship("Oice")

    __table_args__ = (
        sa.UniqueConstraint('user_id', 'oice_id', name='user_read_oice_unique'),
    )


class UserReadOiceProgressQuery:

    def __init__(self, session=DBSession):
        self.session = session

    @property
    def query(self):
        return self.session.query(UserReadOiceProgress)

    def fetch_by_user_id_and_oice_ids(self, user_id, oice_ids):
        return self.query \
                   .filter(UserReadOiceProgress.oice_id.in_(oice_ids)) \
                   .filter(UserReadOiceProgress.user_id == user_id)

    def fetch_by_user_id_and_oice_id(self, user_id, oice_id):
        return self.fetch_by_user_id_and_oice_ids(user_id, set([oice_id])).one_or_none()

    def fetch_by_user_id_and_story(self, user_id, story):
        oice_ids = set([o.id for o in story.oice])
        return self.fetch_by_user_id_and_oice_ids(user_id, oice_ids)

