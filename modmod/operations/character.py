from ..models import (
    DBSession,
    Character,
)
import transaction
import logging

log = logging.getLogger(__name__)
def insert_character(session, character_to_insert, parent_character):

    if parent_character:
        insert_index = parent_character.order+1
    else:
        insert_index = 1

    session.query(Character) \
           .filter(
                Character.library == character_to_insert.library,
                Character.order >= insert_index
            ) \
           .update(
                {Character.order: Character.order+1}
            )

    character_to_insert.order = insert_index
    session.add(character_to_insert)

def move_under(character, new_parent_character, session=DBSession):

    new_index = 1
    if new_parent_character:
        new_index = new_parent_character.order+1

        if character.library != new_parent_character.library:
            raise Exception('Source character and parent character are not in the same library')

    if character.order > new_index:
        move_up(character, new_index, session)
    elif character.order < new_index:

        move_down(character, new_index, session)

def move_up(character, new_index, session=DBSession):

    if character.order < new_index:
        raise 'Cannot move up, direction is not correct'
    elif character.order == new_index:
        return

    session.query(Character) \
           .filter(
                Character.library_id == character.library_id,
                Character.order >= new_index,
                Character.order < character.order
            ) \
           .update(
                {Character.order: Character.order+1}
            )

    character.order = new_index


def move_down(character, new_index, session=DBSession):

    if character.order > new_index:
        raise 'Cannot move down, direction is not correct'
    elif character.order == new_index:
        return

    session.query(Character) \
           .filter(
                Character.library_id == character.library_id,
                Character.order > character.order,
                Character.order <= new_index
            ) \
           .update(
                {Character.order: Character.order-1}
            )

    character.order = new_index


def delete_character(session, character):

    session.query(Character) \
           .filter(
                Character.library_id == character.library_id,
                Character.order > character.order
            ) \
           .update(
                {Character.order: Character.order-1}
            )

    character.is_deleted = True
