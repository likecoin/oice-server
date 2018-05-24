import math
import stripe
from cornice import Service
from modmod.exc import ValidationError
from sqlalchemy import func
from sqlalchemy.orm import joinedload, contains_eager
from sqlalchemy.orm.exc import NoResultFound
from pyramid.httpexceptions import HTTPForbidden
from pyramid.response import Response

from ..models import (
    DBSession,
    AssetQuery,
    CharacterQuery,
    Library,
    LibraryFactory,
    LibraryQuery,
    User,
    UserQuery,
    PriceTier,
    FeaturedLibrary,
    FeaturedLibraryList,
    FeaturedLibraryListQuery,
)

from .util import log_message
from . import (
    set_basic_info_library_log,
    set_basic_info_log,
    set_basic_info_membership_log,
    check_is_language_valid,
)

KAFKA_TOPIC_LIBRARY = 'oice-library'

store_price = Service(name='store_price',
                      path='store/price',
                      renderer='json')

store_library = Service(name='store_library',
                        path='store/library',
                        renderer='json')

store_library_list_free = Service(name='store_library_list_free',
                                  path='store/library/list/free',
                                  renderer='json')

store_library_list_latest = Service(name='store_library_list_latest',
                                    path='store/library/list/latest',
                                    renderer='json')

store_library_list_featured = Service(name='store_library_list_featured',
                                    path='store/library/list/featured',
                                    renderer='json')

store_library_list_featured_type = Service(name='store_library_list_featured_type',
                                    path='store/library/list/featured/{type}',
                                    renderer='json')

store_library_id = Service(name='store_library_id',
                               path='store/library/{library_id}',
                               renderer='json',
                               factory=LibraryFactory,
                               traverse='/{library_id}')

store_library_id_asset = Service(name='store_library_id_asset',
                                     path='store/library/{library_id}/assets/{asset_type}',
                                     renderer='json',
                                     factory=LibraryFactory,
                                     traverse='/{library_id}')

store_library_id_character = Service(name='store_library_id_character',
                                     path='store/library/{library_id}/character',
                                     renderer='json',
                                     factory=LibraryFactory,
                                     traverse='/{library_id}')

store_library_id_purchase = Service(name='store_library_purchase',
                                 path='store/library/{library_id}/purchase',
                                 renderer='json',
                                 factory=LibraryFactory,
                                 traverse='/{library_id}')

@store_price.get()
def get_store_price(request):

    price_tier = DBSession.query(PriceTier) \
                                .order_by(PriceTier.tier) \
                                .all()

    return {
        'code': 200,
        'message': 'ok',
        'priceTiers': [o.serialize() for o in price_tier]
    }


def serialize_libraries_with_purchased(libraries, user):
    result_libraries = []

    if libraries:
        session = DBSession()
        result = session.execute('SELECT library_id FROM user_purchased_library WHERE user_id = %d' % user.id)
        purchased_library_ids = set([r[0] for r in result])

        for l in libraries:
            # Inject isPurchased flag
            is_purchased = l.id in purchased_library_ids
            if is_purchased:
                purchased_library_ids.remove(l.id)

            result_libraries.append({
                **l.serialize_min(),
                'isPurchased': is_purchased,
            })

    return result_libraries


@store_library.get()
def list_library(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    reply = {"message": "ok", "code": 200}

    if 'offset' in request.GET and 'limit' in request.GET:
        offset = request.GET['offset']
        limit = request.GET['limit']
        total_count = LibraryQuery(DBSession).count_store_libs().scalar()
        reply['totalPages'] = math.ceil(int(total_count)/int(limit))
        libraries = LibraryQuery(DBSession).fetch_store_libs()\
                  .options(joinedload(Library.purchased_users))\
                  .order_by(Library.updated_at.desc())\
                  .offset(offset).limit(limit)
        reply['pageNumber'] = int(int(offset)/int(limit) + 1)
    else:
        libraries = LibraryQuery(DBSession).fetch_store_libs()\
                .options(joinedload(Library.purchased_users))\
                .order_by(Library.updated_at.desc())

    reply['libraries'] = serialize_libraries_with_purchased(libraries, user)
    return reply


@store_library_list_free.get()
def list_free_library(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    reply = {"message": "ok", "code": 200}
    if 'offset' in request.GET and 'limit' in request.GET:
      offset = request.GET['offset']
      limit = request.GET['limit']
      totalCount = LibraryQuery(DBSession).count_free_store_libs()\
                            .outerjoin(Library.purchased_users)\
                            .order_by(func.count(User.id).desc())\
                            .group_by(Library.id)\
                            .count() # count the row return by group_by
      reply['totalPages'] = math.ceil(int(totalCount)/int(limit))
      libraries = LibraryQuery(DBSession).fetch_free_store_libs()\
                  .outerjoin(Library.purchased_users)\
                  .options(contains_eager(Library.purchased_users))\
                  .order_by(func.count(User.id).desc())\
                  .group_by(Library.id)\
                  .offset(offset).limit(limit)
      reply['pageNumber'] = int(int(offset)/int(limit) + 1)
    else:
      libraries = LibraryQuery(DBSession).fetch_free_store_libs()\
                  .outerjoin(Library.purchased_users)\
                  .options(contains_eager(Library.purchased_users))\
                  .order_by(func.count(User.id).desc())\
                  .group_by(Library.id)

    reply['libraries'] = serialize_libraries_with_purchased(libraries, user)
    return reply


@store_library_list_latest.get()
def list_latest_library(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()

    reply = {"message": "ok", "code": 200}
    if 'offset' in request.GET and 'limit' in request.GET:
        offset = request.GET['offset']
        limit = request.GET['limit']
        total_count = LibraryQuery(DBSession).count_store_libs().scalar()
        reply['totalPages'] = math.ceil(int(total_count)/int(limit))
        libraries = LibraryQuery(DBSession).fetch_store_libs()\
                .options(joinedload(Library.purchased_users))\
                .order_by(Library.launched_at.desc())\
                .offset(offset).limit(limit)
        reply['pageNumber'] = int(int(offset)/int(limit) + 1)
    else:
        libraries = LibraryQuery(DBSession).fetch_store_libs()\
                .options(joinedload(Library.purchased_users))\
                .order_by(Library.launched_at.desc())

    reply['libraries'] = serialize_libraries_with_purchased(libraries, user)
    return reply


@store_library_list_featured.get()
def get_featured_library_list(request):
    query_language = request.params.get('language')
    query_language = check_is_language_valid(query_language) if query_language else 'en'

    featured_library_list = FeaturedLibraryListQuery(DBSession) \
                                    .query \
                                    .order_by(FeaturedLibraryList.order) \
                                    .all()

    return {
        'code': 200,
        'message': 'ok',
        'list': [lst.serialize(query_language) for lst in featured_library_list],
    }


@store_library_list_featured_type.get()
def list_featured_library_type(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()

    request_list_type = request.matchdict['type']
    featured_library_list = FeaturedLibraryListQuery(DBSession).get_library_by_alias(request_list_type)

    libraries = []
    if featured_library_list:
        libraries = serialize_libraries_with_purchased([fl.library for fl in featured_library_list.libraries], user)

    return {
        'code': 200,
        'message': 'ok',
        'libraries': libraries,
    }


@store_library_id.get()
def fetch_library(request):

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    library = request.context

    log_dict = {
        'action': 'viewLibrary',
        'price': library.price,
    }
    log_dict = set_basic_info_library_log(library, log_dict)
    log_dict = set_basic_info_membership_log(user, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_LIBRARY, log_dict)
    
    return {
        'library': library.serialize_store_detail(user),
        'message': "ok",
        'code': 200
    }


@store_library_id_asset.get()
def list_asset(request):

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()

    library = request.context
    if not library.is_launched:
        # check correct owner if library is not public
        if user not in library.users:
            raise HTTPForbidden

    asset_type = request.matchdict['asset_type']

    assets = AssetQuery.fetch_by_library(
        library=library,
        session=DBSession)

    is_library_author = user in library.users if user else False

    return {
        'code': 200,
        'message': 'ok',
        'assets': [a.serialize() for a in assets \
                    if any(at.folder_name == asset_type for at in a.asset_types) and \
                    (not a.is_hidden or is_library_author)]
    }


@store_library_id_character.get()
def fetch_library_characters(request):

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()

    library = request.context

    if not library.is_launched:
        # check correct owner if library is not public
        if user not in library.users:
            raise HTTPForbidden

    characters = CharacterQuery(DBSession).fetch_character_by_library(library.id).all()
    serialized_characters = []
    for character in characters:
        serialized_character = character.serialize(user=user)
        if serialized_character['fgimages']:
            serialized_characters.append(serialized_character)

    return {
        'code': 200,
        'message': 'ok',
        'characters': serialized_characters,
    }


@store_library_id_purchase.post()
def purchase_library(request):

    library = request.context;
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()
    except NoResultFound:
        raise HTTPForbidden
    if library in user.libraries_purchased: raise ValidationError('ERR_LIBRARY_ALREADY_OWNED')
    if library in user.libraries_selected: raise ValidationError('ERR_LIBRARY_ALREADY_SELECTED')

    if not library.is_launched or 0 > library.price:
       raise ValidationError('ERR_LIBRARY_NOT_FOR_SALE')

    log_dict = {
        'action': 'buyLibrary',
        'price': library.price,
    }

    if 0 == library.price:
        user.libraries_purchased.append(library)
        user.libraries_selected.append(library)

        log_dict = set_basic_info_library_log(library, log_dict)
        log_dict = set_basic_info_membership_log(user, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_LIBRARY, log_dict)

        return {
            'library': library.serialize_store_detail(user),
            'message': "ok",
            'code': 200
        }
    else:
        if not library.users or not library.users[0].stripe_account_id:
            raise ValidationError('ERR_LIBRARY_NOT_CONNECTED')

        charge_amount = library.price * 100

        if not user.customer_id:
            token = request.json_body

            # Create a Customer
            customer = stripe.Customer.create(
              source=token['id'],
              email=request.authenticated_userid
            )
            user.customer_id = customer.id

        else:
            customer = stripe.Customer.retrieve(user.customer_id)
            if request.body and 'id' in request.json_body:
              customer.source = request.json_body['id']
              customer.save()

        try:
            charge = stripe.Charge.create(
                amount=int(charge_amount),
                currency="usd",
                customer=customer,
                description='oice asset store - ' + library.name,
                destination={
                  "amount": int(math.ceil(charge_amount * 0.7)),
                  "account": library.users[0].stripe_account_id,
                }
            )
        except Exception as e:
            return Response(status=400, json={
                'code': 400,
                'message': 'ERR_LIBRARY_PURCHASE_FAILURE',
                'stripeCode': str(e),
            })

        user.libraries_purchased.append(library)
        user.libraries_selected.append(library)

        log_dict = set_basic_info_library_log(library, log_dict)
        log_dict = set_basic_info_membership_log(user, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_LIBRARY, log_dict)

        return {
            'library': library.serialize_store_detail(user),
            'message': "ok",
            'code': 200
        }
