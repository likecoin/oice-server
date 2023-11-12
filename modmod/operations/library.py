import datetime
import logging
from sqlalchemy.sql.expression import true, false
from sqlalchemy import func

from .character import delete_character as operations_delete_character
from ..models import DBSession, Asset, Attribute, Block, Library, OiceQuery, Oice

log = logging.getLogger(__name__)


def get_oice_with_library(library, count=5):
    if library.asset_count == 0:
        return []
    oices = (
        DBSession.query(Oice)
        .select_from(Attribute)
        .join(Asset)
        .join(Block)
        .join(Oice)
        .filter(Asset.library_id == library.id)
        .filter(
            Oice.sharing_option == 0,
            Oice.state == 2,
            Oice.is_deleted == false(),
            Oice.fork_of.is_(None),
        )
        .group_by(Oice.id)
        .order_by(func.count(Block.id).desc())
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
