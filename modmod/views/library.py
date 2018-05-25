from pyramid.response import FileResponse
import pyramid_safile
import logging
import transaction
import json
import datetime
import os.path
from cornice import Service
from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPForbidden
from modmod.exc import ValidationError
from operator import attrgetter

from ..models import (
    DBSession,
    Library,
    LibraryQuery,
    LibraryFactory,
    StoryQuery,
    User,
    UserQuery,
    PriceTier,
    PriceTierQuery,
)
from ..operations import library as operations

log = logging.getLogger(__name__)

library = Service(name='library',
                   path='library',
                   renderer='json')
library_id = Service(name='library_id',
                  path='library/{library_id}',
                  renderer='json',
                  factory=LibraryFactory,
                  traverse='/{library_id}')
library_id_og = Service(name='library_id_og',
                        path='library/{library_id}/og',
                        renderer='json',
                        factory=LibraryFactory,
                        traverse='/{library_id}')
library_id_selection = Service(name='library_id_selection',
                          path='library/{library_id}/selection',
                          renderer='json',
                          factory=LibraryFactory,
                          traverse='/{library_id}')


@library_id.get()
def show_library(request):
    email = request.authenticated_userid
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=email).one()
    except NoResultFound:
        raise HTTPForbidden

    library = request.context
    if not library.is_public:
        # check correct owner if library is not public
        if user not in library.users:
            raise HTTPForbidden

    return {
        "library": request.context.serialize(),
        "message": "ok",
        "code": 200
    }


@library_id_og.get()
def get_library_og(request):
    return {
        "library": request.context.serialize_og(),
        "message": "ok",
        "code": 200
    }


@library.get(permission='get')
def list_library(request):

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    query_types = request.GET.getall('type')
    if query_types:
        query_types = [type.lower() for type in query_types]

    # if type is not specified, return all types of library data
    all_types = ['public', 'private', 'forsale', 'selected', 'unselected']
    query_types = query_types or all_types

    response = {
        "message": "ok",
        "code": 200
    }

    public, private, waiting_for_sale, ready_for_sale = [], [], [], []

    user_library = [p for p in user.libraries if not p.is_deleted]
    user_library.sort(key=attrgetter("name"))

    for library in user_library:
        if library.price == -1:
            private.append(library)
        elif library.price == 0:
            public.append(library)
        elif library.price > 0:
            if library.is_public:
                ready_for_sale.append(library)
            else:
                waiting_for_sale.append(library)

    user_purchased_libraries_set = set(user.libraries_purchased)
    user_selected_libraries_set = set(user.libraries_selected)

    for t in query_types:
        if t == 'public':
            response['public'] = [library.serialize() for library in public]
        elif t == 'private':
            response['private'] = [library.serialize() for library in private]
        elif t == 'forsale':
            response['forSale'] = [library.serialize() for library in ready_for_sale + waiting_for_sale]
        elif t == 'selected':
            selected = user_purchased_libraries_set.intersection(user_selected_libraries_set)
            selected = sorted(selected, key=attrgetter("name"))
            response['selected'] = [library.serialize(user) for library in selected]
        elif t == 'unselected':
            unselected = user_purchased_libraries_set - user_selected_libraries_set
            unselected = sorted(unselected, key=attrgetter("name"))
            response['unselected'] = [library.serialize(user) for library in unselected]

    return response

@library.post(permission='get')
def add_library(request):

    try:
        meta = json.loads(request.POST['meta'])

        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

        library_name = 'New Library'
        if 'name' in meta:
            library_name = meta['name']

        library = Library.create(DBSession, name=library_name)

        if 'description' in meta:
            library.description = meta['description']
        if 'license' in meta:
            library.license = meta['license']

        if 'type' in meta:
            library_type = meta['type']
            if library_type == 'public':
                library.price = 0
                library.is_public = True
                library.launched_at = datetime.datetime.utcnow()
            elif library_type == 'private':
                if not user.is_paid:
                    raise HTTPForbidden
                library.price = -1
            if 'price' in meta:
                if library_type == 'forSale':
                    library.price = PriceTierQuery(DBSession).get_price_usd_by_tier(meta['price'])
                else:
                    raise ValidationError('ERR_LIBRARY_PRICE_TIER_SHOULD_NOT_BE_ATTACHED')
        else:
            # should provide type to determine library type at first
            raise ValidationError('ERR_ADD_LIBRARY_TYPE_INFORMATION_MISSING')

        if 'coverStorage' in request.POST:
            cover_storage = request.POST['coverStorage']
            factory = pyramid_safile.get_factory()
            extension = os.path.splitext(cover_storage.filename)[1]
            filename = 'cover_storage' + extension
            handle = factory.create_handle(filename, cover_storage.file)
            library.import_handle(handle)

        user.libraries.append(library)
        # preselect library created by user
        user.libraries_selected.append(library)

        DBSession.add(library)

        # flush because we need an ID
        DBSession.flush()

        return {
            "library": library.serialize(),
            "message": "ok",
            "code": 200,
        }
    except ValueError as e:
        raise ValidationError(str(e))


@library_id.post(permission='set')
def update_library(request):

    library_id = request.matchdict['library_id']

    try:

        library = LibraryQuery(DBSession)\
            .get_library_by_id(library_id)

        # Hardcode config for now, does not work
        # if 'config' in request.json_body:
        #     library.config_obj = request.json_body['config']

        if 'meta' in request.POST:
            meta = json.loads(request.POST['meta'])

            if 'name' in meta:
                library.name = meta['name']
            if 'description' in meta:
                library.description = meta['description']
            if 'license' in meta:
                library.license = meta['license']
            if 'price' in meta:
                if library.price <= 0:
                    raise ValidationError('ERR_LIBRARY_PRICE_TIER_SHOULD_NOT_BE_ATTACHED')
                else:
                    library.price = PriceTierQuery(DBSession).get_price_usd_by_tier(meta['price'])
            if 'launchedAt' in meta and 'isLaunched' in meta:
                if not meta['isLaunched'] and meta['launchedAt']:
                    library.launched_at = None
                    library.is_public = False
                elif meta['isLaunched'] and not meta['launchedAt']:
                    library.launched_at = datetime.datetime.utcnow()
                    library.is_public = True

        if 'coverStorage' in request.POST:
            cover_storage = request.POST['coverStorage']
            factory = pyramid_safile.get_factory()
            extension = os.path.splitext(cover_storage.filename)[1]
            filename = 'cover_storage' + extension
            handle = factory.create_handle(filename, cover_storage.file)
            library.import_handle(handle)

        DBSession.add(library)
        return {
            'code': 200,
            'message': 'ok',
            'library': library.serialize()
        }

    except ValueError as e:
        raise ValidationError(str(e))


@library_id.delete(permission='set')
def delete_library(request):

    library = request.context
    library.is_deleted = True

    for asset in library.asset:
        asset.is_deleted = True

    for character in library.character:
        operations.delete_character(DBSession, character)

    return {
        'code': 200,
        'message': 'ok'
    }

@library_id_selection.post()
def add_selected_library_to_user(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    library_to_be_added = request.context
    if user in library_to_be_added.purchased_users:
        user.libraries_selected.append(library_to_be_added)
    else:
        raise ValidationError('ERR_ADD_NOT_PURCHASED_LIBRARY_TO_LIBRARIES_SELECTED')

    return {
        'code': 200,
        'message': 'ok',
    }

@library_id_selection.delete()
def remove_selected_library_from_user(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    library_to_be_removed = request.context
    if user in library_to_be_removed.purchased_users:
        user.libraries_selected.remove(library_to_be_removed)
    else:
        raise ValidationError('ERR_REMOVE_NOT_PURCHASED_LIBRARY_FROM_LIBRARIES_SELECTED')

    return {
        'code': 200,
        'message': 'ok',
    }
