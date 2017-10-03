import json
from cornice import Service

from sqlalchemy import exc
from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPForbidden
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    Asset,
    Character,
    CharacterFactory,
    CharacterQuery,
    CharacterLocalization,
    LibraryFactory,
    LibraryQuery,
    UserQuery,
)
from ..operations.script_export_default import OVERRIDABLE_CHARACTER_CONFIG_ITEMS
from . import check_is_language_valid
from ..operations import character as operations

character_in_story = Service(name='character_in_story',
                         path='story/{story_id}/character',
                         renderer='json')
character_in_library = Service(name='character_in_library',
                         path='library/{library_id}/character',
                         renderer='json',
                         factory=LibraryFactory,
                         traverse='/{library_id}')
character = Service(name='character',
                    path='character/{character_id}',
                    renderer='json',
                    factory=CharacterFactory,
                    traverse='/{character_id}')
character_id_language = Service(name='character_language',
                                path='character/{character_id}/character/{language}',
                                renderer='json',
                                factory=CharacterFactory,
                                traverse='/{character_id}')


@character_in_story.get(permission='get')
def fetch_characters(request):
    query_language = check_is_language_valid(request.params.get('language'))
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    characters = CharacterQuery(DBSession).fetch_character_list_by_user_selected(user=user)
    serialized_characters = []
    for character in characters:
        serialized_character = character.serialize(query_language, user)
        if serialized_character['fgimages']:
            serialized_characters.append(serialized_character)

    return {
        'code': 200,
        'message': 'ok',
        'characters': serialized_characters,
    }


@character_in_library.get()
def fetch_characters_by_library(request):
    email = request.authenticated_userid
    query_language = check_is_language_valid(request.params.get('language'))
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=email).one()
    except NoResultFound:
        raise HTTPForbidden

    library_id = request.matchdict['library_id']
    library = LibraryQuery(DBSession).get_library_by_id(library_id)
    if not library.is_public:
        # check correct owner if library is not public
        if user not in library.users:
            raise HTTPForbidden

    characters = CharacterQuery(DBSession) \
        .fetch_character_by_library(library_id).all()

    return {
        'code': 200,
        'message': 'ok',
        'characters': [character.serialize(query_language, user) for character in characters]
    }


@character_in_library.post(permission='set')
def create_character(request):
    library_id = request.matchdict['library_id']

    try:
        name       = request.json_body.get('name', None)
        width      = request.json_body.get("width", 1080)
        height     = request.json_body.get("height", 1080)
        is_generic = request.json_body.get("isGeneric", False)
        order      = int(request.json_body.get("order", 0)) - 1
        config     = json.dumps(request.json_body.get("config", {}), sort_keys=True)

    except ValueError as e:
        raise ValidationError('Request object is invalid')
    try:
        # Try to insert a character
        character = Character(
            library_id=library_id,
            name=name,
            width=width,
            height=height,
            is_generic=is_generic,
            config=config,
        )

        DBSession.add(character)
        DBSession.flush()

        if order and order != -1:
            parent_character = DBSession.query(Character) \
                                    .filter(Character.order == order) \
                                    .filter(Character.library_id == library_id) \
                                    .first()
            operations.insert_character(DBSession, character, parent_character)
        else:
            order = CharacterQuery(DBSession) \
                .get_last_order_in_library(library_id=library_id)
            character.order = order

    except exc.DBAPIError as e:
        raise ValidationError(str(e.orig))
    else:
        return {
            'code': 200,
            'message': 'Success',
            'character': character.serialize()
        }


@character.get(permission='get')
def get_character(request):
    query_language = check_is_language_valid(request.params.get('language'))
    return {
        'code': 200,
        'message': 'success',
        'character': request.context.serialize(query_language)
    }


@character.post(permission='set')
def edit_character(request):
    query_language = check_is_language_valid(request.params.get('language'))
    try:
        # Get the corresponding character by id from DB
        character = request.context

        # Set mandatory attribute
        if 'isGeneric' in request.json_body:
            character.is_generic = request.json_body['isGeneric']

        if 'name' in request.json_body:
            character.set_name(request.json_body['name'], query_language)

        for key in ['width', 'order', 'height']:
            if key in request.json_body:
                setattr(character, key, request.json_body[key])

        # Set character config
        # Instead of using the existing config, we always create new config
        # as the config is an optional setting and also varify the config
        new_config = {}
        if 'config' in request.json_body:
            for key in OVERRIDABLE_CHARACTER_CONFIG_ITEMS:
                if key in request.json_body['config']:
                    new_config[key] = request.json_body['config'][key]

        serialized_config = json.dumps(new_config, sort_keys=True)
        setattr(character, 'config', serialized_config)

        DBSession.add(character)
        DBSession.flush()

    except ValueError as e:
        raise ValidationError('Request object is invalid')
    else:
        return {
            'code': 200,
            'message': 'Success',
            'character': character.serialize(query_language)
        }


@character.put(permission='set')
# move character
def move_character(request):
    query_language = check_is_language_valid(request.params.get('language'))
    order = int(request.json_body.get("order", 0)) - 1
    character = request.context
    parent_character = None
    if order:
        parent_character = DBSession.query(Character) \
                                .filter(Character.order == order) \
                                .filter(Character.library_id == character.library_id) \
                                .first()
    operations.move_under(character, parent_character, session=DBSession)
    serialized = character.serialize(query_language)

    return {
        "message": "ok",
        "character": serialized
    }


@character.delete(permission='set')
def delete_character(request):
    character_id = request.matchdict['character_id']

    character = DBSession.query(Character) \
                         .filter(Character.id == character_id) \
                         .one()

    operations.delete_character(DBSession, character)

    asset_ids = [a.id for a in character.fgimages]
    for id in asset_ids:
        asset = DBSession.query(Asset) \
                         .filter(Asset.id == id) \
                         .one()
        asset.is_deleted = True

    return {
        'code': 200,
        'message': 'ok',
    }


@character_id_language.get(permission='get')
def get_supported_language(request):
    character = request.context
    return {
        'code': 200,
        'message': 'ok',
        'languages': character.supported_languages,
    }


@character_id_language.post(permission='get')
def add_new_language(request):
    character = request.context
    language = check_is_language_valid(request.matchdict['language'])
    localization = CharacterLocalization(character=character, name=character.name, language=language)
    DBSession.add(localization)
    character.localizations[language] = localization
    return {
        'code': 200,
        'message': 'ok',
        'languages': character.supported_languages,
    }


@character_id_language.delete(permission='get')
def remove_language(request):
    character = request.context
    language = check_is_language_valid(request.matchdict['language'])
    if language in character.localizations:
        DBSession.delete(character.localizations[language])
    return {
        'code': 200,
        'message': 'ok',
        'languages': character.supported_languages,
    }
