import datetime
import pyramid_safile

from .character import delete_character as operations_delete_character
from ..models import (
    Library
)

def delete_character(session, character):
    operations_delete_character(session, character)

def create_user_public_library(session, name):
    library_name = name + "的素材庫"
    library = Library.create(session,
                name=library_name,
                license=0,
                launched_at=datetime.datetime.utcnow(),
                price=0,
                is_public=True)

    session.add(library)
    session.flush()
    return library
