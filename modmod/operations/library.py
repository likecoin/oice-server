import datetime
import logging
from sqlalchemy.sql.expression import false

from .character import delete_character as operations_delete_character
from ..models import DBSession, Asset, Attribute, Block, Library, OiceQuery, Oice

log = logging.getLogger(__name__)

def get_oice_with_library(library, count=5):
    if library.asset_count == 0:
        return []
    block_ids = (
        DBSession.query(Attribute.block_id)
        .join(Asset)
        .filter(Asset.library_id == library.id)
        .distinct()
    )
    block_ids = [a.block_id for a in block_ids]
    if len(block_ids) == 0:
        return []
    oice_ids = DBSession.query(Block.oice_id).filter(Block.id.in_(block_ids)).all()
    oice_ids = [b.oice_id for b in oice_ids]
    if len(oice_ids) == 0:
        return []
    oices = (
        DBSession.query(Oice)
        .filter(Oice.is_deleted == false())
        .filter(Oice.id.in_(oice_ids))
        .order_by(Oice.view_count.desc())
        .limit(count)
        .all()
    )
    return oices


def delete_character(session, character):
    operations_delete_character(session, character)


def create_user_public_library(session, name):
    library_name = name + "的素材庫"
    library = Library.create(
        session,
        name=library_name,
        license=0,
        launched_at=datetime.datetime.utcnow(),
        price=0,
        is_public=True,
    )

    session.add(library)
    session.flush()
    return library
