import sqlalchemy as sa
from sqlalchemy.orm import relationship
from pyramid_safile import FileHandleStore
from pyramid.security import Allow
from modmod.models.base import (
    Base,
    BaseMixin,
)
from . import DBSession


class ProjectExport(Base, BaseMixin):
    __tablename__ = 'project_export'

    story = relationship("Story")
    oice = relationship("Oice")
    project_id = sa.Column(
        sa.Integer, sa.ForeignKey('story.id'), nullable=False)
    ks_id = sa.Column(
        sa.Integer, sa.ForeignKey('oice.id'))
    exported_files = sa.Column(FileHandleStore, nullable=True)

    @property
    def __acl__(self):
        acl = super(ProjectExport, self).__acl__()
        for user in self.story.users:
            acl = acl + [(Allow, user.email, 'get'),
                         (Allow, user.email, 'set')]
        return acl

    def serialize(self):
        return {
            'id': self.id
        }


class ProjectExportFactory(object):

    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        project_export = DBSession.query(ProjectExport) \
            .filter(ProjectExport.id == key) \
            .one()
        return project_export
