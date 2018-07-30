import logging
import os.path
import json
import requests
import datetime
import hmac
import hashlib
import re
from collections import defaultdict
from operator import attrgetter
from cornice import Service
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import false
from sqlalchemy import func
from pyramid.security import authenticated_userid
from pyramid.security import forget
from pyramid.security import remember
from pyramid.response import Response
import pyramid_safile
from io import BytesIO
from modmod.exc import ValidationError
from firebase_admin import auth
from oauth2client.crypt import AppIdentityError
from . import dict_get_value

from ..models import (
    DBSession,
    User,
    UserQuery,
    UserFactory,
    StoryQuery,
    OiceQuery,
    Attribute,
    Block,
    Oice,
    LibraryQuery
)
from ..operations.story import fork_story
from ..operations.oice import fork_oice
from ..operations.library import create_user_public_library
from ..operations.credit import get_user_story_credit
from ..operations.user import handle_anonymous_user_app_story_progress
from .util import (
    subscribe_mailchimp,
    update_mailchimp_field,
    update_user_mailchimp_stage,
    do_elastic_search_user,
    update_elastic_search_user,
    log_message,
    normalize_language,
    normalize_ui_language,
)
from . import (
    get_likecoin_api_url,
    get_cloud_function_api_base_url,
    get_intercom_secret_key,
    get_is_production,
    set_basic_info_user_log,
    set_basic_info_oice_source_log,
    set_basic_info_referrer_log,
    set_basic_info_log,
)

log = logging.getLogger(__name__)
KAFKA_TOPIC_USER = 'oice-user'

login = Service(name='login',
                path='login',
                renderer='json')
logout = Service(name='logout',
                 path='logout',
                 renderer='json')
profile = Service(name='profile',
                  path='profile',
                  renderer='json')
profile_username_check = Service(name='profile_username_check',
                  path='profile/username/check',
                  renderer='json')
likecoin_connect = Service(
    name='likecoin_connect',
    path='likecoin/connect',
    renderer='json',
)
credits = Service(name='credits',
                  path='credits/user/{user_id}',
                  renderer='json',
                  factory=UserFactory,
                  traverse='/{user_id}')
search = Service(name='search',
                      path='user/search/{prefix}',
                      renderer='json')
user_id_profile = Service(name='user_id_profile',
                    path='user/{user_id}/profile',
                    renderer='json',
                    factory=UserFactory,
                    traverse='/{user_id}')
user_id_profile_details = Service(name='user_id_profile_details',
                            path='user/{user_id}/profile/details',
                            renderer='json',
                            factory=UserFactory,
                            traverse='/{user_id}')
user_status = Service(name='user_status',
                    path='user/status',
                    renderer='json')
user_likecoin_id = Service(name='user_likecoin_id',
                           path='user/likecoin/{likecoin_id}',
                           renderer='json')

@login.post()
def login_user(request):

    try:
        email = request.json_body.get('email')
        firebase_token = request.json_body.get('firebaseToken')
        is_anonymous = request.json_body.get('isAnonymous')
        firebase_user_id = request.json_body.get('firebaseUserId')
        google_token = request.json_body.get('googleToken')
        branch_data = request.json_body.get('branchData')
        prev_firebase_user_id = request.json_body.get('prevFirebaseUserId')
    except ValueError:
        raise ValidationError('ERR_INVALID_AUTH_PARAM')

    if get_is_production() or email != 'oice-dev':
        try:
            auth.verify_id_token(firebase_token)
        except ValueError:
            raise ValidationError('ERR_FIREBASE_AUTH_ERROR')
        except AppIdentityError:
            raise ValidationError('ERR_INVALID_FIREBASE_TOKEN')

    old_auth_id = authenticated_userid(request)

    fetch_username = email
    if is_anonymous and firebase_user_id:
        fetch_username = firebase_user_id

    # Init these bool here to avoid scope issue
    is_first_login = False
    is_trial_ended = False

    log_dict = {
        'topic'      : 'actionUser',
        'isAnonymous': 'true' if is_anonymous else 'false',
        'isDeeplink' : 'false',
    }
    if branch_data:
        log_dict.update({
            'channel'   : dict_get_value(branch_data, ['~channel'], 'direct'),
            'isDeeplink': 'true',
        })
        log_dict = set_basic_info_referrer_log(
            dict_get_value(branch_data, ['+referrer'], 'none'),
            dict_get_value(branch_data, ['referrer2'], 'none'),
            log_dict
        )
        oice_source = OiceQuery(DBSession).get_by_uuid(dict_get_value(branch_data, ['uuid']))
        if oice_source:
            log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)

    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=fetch_username).one()
    except NoResultFound:

        user = User(email=fetch_username,is_anonymous=is_anonymous)
        if firebase_user_id:
            user.display_name = firebase_user_id
        DBSession.add(user)
        DBSession.flush()

        is_first_login = True
        is_trial_ended = False

        # log
        log_dict.update({'action': 'createUser'})
        log_dict = set_basic_info_user_log(user, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_USER, log_dict)

    else:
        user.last_login_at = datetime.datetime.utcnow()

        if not user.is_anonymous:
            sample_story = StoryQuery(DBSession).get_sample_story(user.language);
            story = next((user_story for user_story in user.stories if sample_story.id == user_story.fork_of), None)
            if not story:
                story = fork_story(DBSession, sample_story)
                sample_oice = OiceQuery(DBSession).get_sample_oice(language=user.language);
                oice = fork_oice(DBSession, story, sample_oice)
                user.stories.append(story)

        if user.is_trial:
            if user.is_paid() and user.expire_date < datetime.datetime.utcnow():
                user.role = 'user'
                update_user_mailchimp_stage(user=user, stage=5)
            if user.is_free():
                user.is_trial = False
                is_trial_ended = True
        else:
            # if user.is_free() and not user.expire_date:
                # Disabled trial due to busines request
                # UserOperations.start_trial(user)
            is_trial_ended = False

        is_first_login = False

        if not old_auth_id or request.headers.get('x-oice-app-version'):
            # log
            is_redeem_account = prev_firebase_user_id and firebase_user_id != prev_firebase_user_id

            log_dict.update({
                'action': 'redeemAccount' if is_redeem_account else 'login',
            })
            log_dict = set_basic_info_user_log(user, log_dict)
            log_dict = set_basic_info_log(request, log_dict)
            log_message(KAFKA_TOPIC_USER, log_dict)

            if is_redeem_account:
                handle_anonymous_user_app_story_progress(is_existing_user=True, \
                                                         prev_user_email=prev_firebase_user_id, \
                                                         new_user=user)

    photo_url = request.json_body.get('photoURL', None)
    if photo_url and user.avatar_storage is None:
        r = requests.get(photo_url)
        avatar = BytesIO(r.content)
        factory = pyramid_safile.get_factory()
        handle = factory.create_handle('avatar.png', avatar)
        user.import_handle(handle)

    language = request.json_body.get('language', None)
    normalized_language = None

    if language and user.language is None:
        normalized_language = normalize_language(language)
    if normalized_language:
        user.language = normalized_language
        # derive ui_language when creating user
        user.ui_language = normalize_ui_language(normalized_language)

    if (is_first_login or user.is_anonymous) and google_token:

        display_name = request.json_body.get('displayName', None)

        if email:
            user.email = email
            if not display_name:
                display_name = email.split('@')[0]

        if display_name:
            user.display_name = display_name

        sample_story = StoryQuery(DBSession).get_sample_story(normalized_language);
        story = fork_story(DBSession, sample_story)
        sample_oice = OiceQuery(DBSession).get_sample_oice(language=normalized_language);
        oice = fork_oice(DBSession, story, sample_oice)

        # open a public library for new user
        library = create_user_public_library(DBSession, user.display_name)

        user.stories.append(story)
        user.libraries.append(library)
        user.libraries_selected.append(library)

        # pre-select default libraries for new user
        default_libs = LibraryQuery(DBSession).fetch_default_libs()
        user.libraries_purchased.extend(default_libs)
        user.libraries_selected.extend(default_libs)

        # Disabled trial due to busines request
        # UserOperations.start_trial(user)

        user.last_login_at = datetime.datetime.utcnow()
        subscribe_mailchimp(google_token, user, language=language)

        # update elastic search when create user
        update_elastic_search_user(user.display_name, email)

        if is_first_login and request.headers.get('x-oice-app-version'):
            # log
            log_dict.update({'action': 'bindAccount'})
            log_dict = set_basic_info_user_log(user, log_dict)
            log_dict = set_basic_info_log(request, log_dict)
            log_message(KAFKA_TOPIC_USER, log_dict)

            handle_anonymous_user_app_story_progress(is_existing_user=False, \
                                                     prev_user_email=prev_firebase_user_id, \
                                                     new_user=user)

        user.is_anonymous = False

    serialize_user = user.serialize()
    serialize_user['isFirstLogin'] = is_first_login
    serialize_user['isTrialEnded'] = is_trial_ended

    serialize_user['intercomUserHash'] = hmac.new(
        bytes(get_intercom_secret_key().encode('utf-8')),
        bytes(str(user.id).encode('utf-8')),
        digestmod=hashlib.sha256
    ).hexdigest()

    response = Response()
    response.status_code = 200
    response.headers = remember(request, user.email)
    response.content_type = 'application/json'
    response.charset = 'UTF-8'
    response.text = json.dumps({'code': 200, 'user': serialize_user})

    return response


@logout.delete()
def logout_user(request):
    headers = forget(request)
    return Response(status_code=200, headers=headers)


@profile.get(permission='get')
def get_profile(request):

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    return {
        'code': 200,
        'user': user.serialize()
    }


@profile.post(permission='get')
def update_profile(request):

    try:
        email = request.authenticated_userid
        user = UserQuery(DBSession).fetch_user_by_email(email=email).one()

        log_dict = {
            'change': [],
            'action': 'changeSetting',
        }

        if 'meta' in request.POST:
            meta = json.loads(request.POST['meta'])

            if 'displayName' in meta:
                log_dict['change'].append({
                        'whichFieldChange': 'user',
                        'beforeChange': user.display_name,
                        'afterChange': meta['displayName'],
                    })
                user.display_name = meta['displayName']

                # update elastic search when update profile
                update_elastic_search_user(user.display_name, email)

            if 'username' in meta:
                log_dict['change'].append({
                        'whichFieldChange': 'username',
                        'beforeChange': user.username,
                        'afterChange': meta['username'],
                    })
                user.username = meta['username']

            if 'description' in meta:
                log_dict['change'].append({
                        'whichFieldChange': 'description',
                        'beforeChange': user.description,
                        'afterChange': meta['description'],
                    })
                user.description = meta['description']

            if 'seekingSubscriptionMessage' in meta:
                new_value = meta['seekingSubscriptionMessage']
                log_dict['change'].append({
                        'whichFieldChange': 'seekingSubscriptionMessage',
                        'beforeChange': user.seeking_subscription_message,
                        'afterChange': new_value,
                    })
                user.seeking_subscription_message = new_value

            if 'language' in meta:
                language = normalize_language(meta['language'])
                log_dict['change'].append({
                    'whichFieldChange': 'language',
                    'beforeChange': user.language,
                    'afterChange': language,
                })
                user.language = language

            if 'uiLanguage' in meta:
                log_dict['change'].append({
                    'whichFieldChange': 'ui_language',
                    'beforeChange': user.ui_language,
                    'afterChange': meta['uiLanguage'],
                })
                user.ui_language = meta['uiLanguage']

            if 'tutorialState' in meta:
                newValue = int("".join(str(int(item)) for item in meta['tutorialState']), 2)
                log_dict['change'].append({
                    'whichFieldChange': 'tutorialState',
                    'beforeChange': user.tutorial_state,
                    'afterChange': newValue,
                })
                user.tutorial_state = newValue

        if 'avatar' in request.POST:
            avatar_file = request.POST['avatar']
            factory = pyramid_safile.get_factory()
            extension = os.path.splitext(avatar_file.filename)[1]
            filename = 'avatar' + extension
            handle = factory.create_handle(filename, avatar_file.file)

            log_dict['change'].append({
                    'whichFieldChange': 'avatar',
                    'beforeChange': json.dumps(user.avatar_storage.descriptor) if user.avatar_storage else None,
                    'afterChange': json.dumps(handle.descriptor) if handle else None,
                })
            user.import_handle(handle)

        update_mailchimp_field(user=user)

        log_dict = set_basic_info_user_log(user, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_USER, log_dict)

        return {
            "user": user.serialize(),
            "message": "ok",
            "code": 200
        }

    except ValueError as e:
        raise ValidationError(str(e))

@profile_username_check.post(permission='get')
def check_username_valid(request):
    username = request.json_body.get('username', None)

    if username:
        # check format of username
        if len(username) < 6:
            raise ValidationError('ERR_USERNAME_LENGTH_TOO_SHORT')
        elif not username[0].isalpha():
            raise ValidationError('ERR_USERNAME_CAN_ONLY_START_WITH_LETTER')
        elif username.isdigit():
            raise ValidationError('ERR_USERNAME_IS_A_NUMBER')

        invalid_char_regex = re.compile(r"[^a-zA-Z0-9\.\_]")
        if invalid_char_regex.search(username):
            raise ValidationError('ERR_USERNAME_CONTAINS_INVALID_CHARACTER')

        # check uniqueness of username
        user = UserQuery(DBSession) \
                .fetch_user_by_username(username) \
                .one_or_none()

        if user:
            raise ValidationError('ERR_USERNAME_NOT_UNIQUE')

    return {
        "code": 200,
        "message": "ok",
    }


@likecoin_connect.post(permission='get')
def connect_like_coin(request):
    session = DBSession()
    user = UserQuery(session).fetch_user_by_email(email=request.authenticated_userid).one()

    if 'likeCoinId' in request.json_body:
        like_coin_id = str(request.json_body.get('likeCoinId', ''))

        r = requests.get(get_likecoin_api_url() + '/users/id/' + like_coin_id + '/min')
        if r.status_code != requests.codes.ok:
            raise ValidationError('ERR_LIKECOIN_CONNECT_INVALID_ID')

        wallet_address = request.json_body.get('address', '')
        if wallet_address and wallet_address != r.json().get('wallet'):
            raise ValidationError('ERR_LIKECOIN_CONNECT_ID_WALLET_MISMATCH')

    else:
        raise ValidationError('ERR_LIKECOIN_CONNECT_MISSING_PARAMS')

    if not user.like_coin_id:
        try:
            user.username = like_coin_id
            session.flush()
        except IntegrityError:
            raise ValidationError('ERR_LIKECOIN_CONNECT_USER_ID_DUPLICATED')
        try:
            user.like_coin_id = like_coin_id
            session.flush()
        except IntegrityError:
            raise ValidationError('ERR_LIKECOIN_CONNECT_DUPLICATED')

    elif user.like_coin_id != like_coin_id:
        raise ValidationError('ERR_LIKECOIN_CONNECT_ALREADY')

    return {
        'code': 200,
        'message': 'ok',
        'user': user.serialize(),
    }


@credits.get()
def get_user_credit(request):
    user = request.context
    credits = get_user_story_credit(user.id)
    return {
        "code": 200,
        "message": "ok",
        "user": user.serialize_credit(),
        "stories": credits["stories"],
        "libraries": credits["libraries"],
    }

@search.get(permission='get')
def search_user(request):
    prefix = request.matchdict['prefix']
    emails,email_score = do_elastic_search_user(prefix)

    users = UserQuery(DBSession).fetch_user_by_emails(emails=emails) if emails else []
    users.sort(key=lambda user: email_score[user.email], reverse=True)

    return {
        "code": 200,
        "message": "ok",
        "users": [u.serialize_min() for u in users],
    }

@user_id_profile.get()
def get_user_id_profile(request):
    user = request.context
    return {
      "code": 200,
      "message": "ok",
      "user": user.serialize_credit(),
    }

@user_id_profile_details.get()
def get_user_id_profile_details(request):
    user = request.context

    # stats
    # number of public oice from the user
    number_of_oices = 0
    # number of assets from user's public library
    number_of_assets = 0
    # number of oices using any of assets from the user
    number_of_credits = 0

    # user stories (not deleted, and has at least some oices published)
    stories = []
    stories_view_count = {}
    for story in user.stories:
        public_oice = [oice for oice in story.oice if oice.is_public()]
        number_of_public_oice = len(public_oice)

        if number_of_public_oice > 0:
            number_of_oices += number_of_public_oice
            story_view_count = sum(oice.view_count for oice in public_oice)
            stories_view_count[story.id] = story_view_count
            stories.append(story)

    # sort story according to priority (if set), otherwise by view_count of sum of oices)
    if stories:
        stories.sort(key=lambda story: stories_view_count[story.id], reverse=True)
        is_sorted_by_priority = any(story.priority > 0 for story in stories)
        if is_sorted_by_priority:
            stories.sort(key=attrgetter("priority"))

    stories = [story.serialize_profile() for story in stories]

    # get list of libraries the user owned AND list libraries credited the user
    credited_libraries = set()
    user_libraries = set()
    libraries_asset_ids = defaultdict(list)

    user_libraries_ids = set()
    # handle creators of library (which may not be credited in any assets in the library at all)
    for library in user.libraries:
        if library.is_public and not library.is_deleted:
            user_libraries.add(library)
            libraries_asset_ids[library.id] = [asset.id for asset in library.asset]
            user_libraries_ids.add(library.id)

    # handle asset credits (BUT NOT the owner of library)
    for asset in user.assets:
        if not asset.is_deleted:
            library = asset.library
            # if library is not in user's libraries
            if not library.id in user_libraries_ids and library.is_public and not library.is_deleted:
                libraries_asset_ids[library.id].append(asset.id)
                credited_libraries.add(library)

    # unique oice ids that use library assets from this user
    oice_ids_use_library = set()

    # stores {'oice_id1': 12, 'oice_id2': 34, ...}, which counts number of assets from user's libaries the oice uses
    oice_count_dictionary = defaultdict(int)
    # stores {'library_id1': 56, 'library_id2': 78, ...}, which counts number of oices that use a particular library
    libraries_use_count = defaultdict(int)

    for library_id, asset_ids in libraries_asset_ids.items():
        number_of_assets += len(asset_ids)
        block_ids = DBSession.query(Attribute.block_id) \
                     .filter(Attribute.asset_id.in_(asset_ids)) \
                     .distinct()
        block_ids = [b.block_id for b in block_ids]

        # Find oice_ids that used assets from this library
        if block_ids:
            oice_ids = DBSession.query(Block.oice_id, func.count(Block.oice_id).label('used_asset_block_count')) \
                        .filter(Block.id.in_(block_ids)) \
                        .filter(Block.oice_id == Oice.id) \
                        .filter(Oice.sharing_option == 0) \
                        .filter(Oice.is_deleted == false()) \
                        .group_by(Block.oice_id)
            for o in oice_ids:
                oice_count_dictionary[o.oice_id] += o.used_asset_block_count

            oice_ids = [o.oice_id for o in oice_ids]
            oice_ids_use_library.update(oice_ids)
            libraries_use_count[library_id] = len(oice_ids)

    # sort library for each group of library, then combine
    # 1. sort user's libraries by priority if is set, then by number of public oices used
    if user_libraries:
        user_libraries = sorted(user_libraries, key=lambda library: libraries_use_count[library.id], reverse=True)
        is_sorted_by_priority = any(library.priority > 0 for library in user_libraries)
        if is_sorted_by_priority:
            user_libraries = sorted(user_libraries, key=attrgetter("priority"))
    # 2. sort libraries that credited the user's asset (NOT his/her library),
    #    and sort by number of assets that belongs to the user
    if credited_libraries:
        credited_libraries = sorted(credited_libraries, key=lambda library: len(libraries_asset_ids[library.id]), reverse=True)
    libraries = [library.serialize_profile() for library in user_libraries] + [library.serialize_profile() for library in credited_libraries]

    number_of_credits = len(oice_ids_use_library)

    # find out top stories using the users' asset
    oices = OiceQuery(DBSession) \
        .get_by_ids(oice_ids_use_library)

    story_count_dictionary = defaultdict(int)
    story_ids = set()
    for oice in oices:
        story_count_dictionary[oice.story_id] += oice_count_dictionary[oice.id]
        story_ids.add(oice.story_id)

    credit_stories = StoryQuery(DBSession) \
                .get_story_by_id_list(story_ids)

    # exclude story written by the user
    credit_stories = [story for story in credit_stories if story.users[0].id != user.id]
    credit_stories.sort(key=lambda story: story_count_dictionary[story.id], reverse=True)
    credits = [story.serialize_profile() for story in credit_stories]

    return {
      "code": 200,
      "message": "ok",
      "profile": {
        "stats": {
          "oices": number_of_oices,
          "assets": number_of_assets,
          "credits": number_of_credits,
        },
        "stories": stories,
        "libraries": libraries,
        "credits": credits,
      },
    }

@user_status.get(permission='get')
def check_user_status(request):
    return {
      "code": 200,
      "message": "ok",
    }


@user_likecoin_id.get()
def check_likecoin_connect_status(request):
    likecoin_id = request.matchdict['likecoin_id']
    user = UserQuery(DBSession).query.filter(User.like_coin_id == likecoin_id).one_or_none()

    response = Response()
    response.charset = 'UTF-8'
    response.status_code = 200 if user else 404
    response.text = 'OK' if user else 'NOT FOUND'
    return response
