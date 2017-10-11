from sqlalchemy.orm.session import make_transient
from zope.sqlalchemy import mark_changed
import uuid
import pyramid_safile
import logging

log = logging.getLogger(__name__)

# currently not used
def fork_attributes(DBSession, block, attributes):
    for attribute in attributes:
        #DBSession.expunge(attribute)
        attribute.id = None
        make_transient(attribute)
    session = DBSession()
    session.bulk_save_objects(attributes)
    mark_changed(session)
    return attributes