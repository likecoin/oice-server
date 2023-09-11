# pylama:ignore=W:select=W611,ignore=E501
from datetime import datetime
import json
import locale
import stripe
from zope.sqlalchemy import ZopeTransactionExtension
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)
from pyramid.security import forget
from pyramid.authentication import AuthTktCookieHelper
from pyramid.security import authenticated_userid
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.httpexceptions import HTTPForbidden
from modmod.exc import ValidationError

from .util import log_message
from ..config import get_upload_base_url
from ..models import (
    DBSession,
    UserQuery,
)

import logging
log = logging.getLogger(__name__)
KAFKA_TOPIC_BLOCK = 'oice-block'
KAFKA_TOPIC_ERROR = 'oice-error'

crisp_secret_key = None
stripe_api_key = None
stripe_client_id = None
stripe_plan_id = None
android_iap_validator_url = None
ios_iap_validator_url = None
ios_iap_validator_url_v2 = None
iap_sub_price = None
iap_sub_price_payout_ratio = None
voucher_api_url = None
voucher_api_key = None
cloud_function_api_base_url = None
is_production = False


def dict_get_value(_dict, keys_array, default_value=None):
    if not isinstance(_dict, dict):
        return None
    for i, key in enumerate(keys_array):
        if i < len(keys_array) - 1:
            _dict = _dict.get(key, {})
        else:
            _dict = _dict.get(key, default_value)
    return _dict


def includeme(config):
    global crisp_secret_key
    global stripe_api_key
    global stripe_client_id
    global stripe_plan_id
    global android_iap_validator_url
    global ios_iap_validator_url
    global ios_iap_validator_url_v2
    global voucher_api_url
    global voucher_api_key
    global cloud_function_api_base_url
    global es_log_whitelist
    global es_log_key
    global is_production

    crisp_secret_key = \
        config.get_settings().get('crisp.secret_key', None)
    stripe_api_key = \
        config.get_settings().get('stripe.api_key', None)
    stripe_client_id = \
        config.get_settings().get('stripe.client_id', None)
    stripe_plan_id = \
        config.get_settings().get('stripe.plan_id', None)
    android_iap_validator_url = \
        config.get_settings().get('iapvalidator.android_url', None)
    ios_iap_validator_url = \
        config.get_settings().get('iapvalidator.ios_url', None)
    ios_iap_validator_url_v2 = \
        config.get_settings().get('iapvalidator.ios_url_v2', None)
    voucher_api_url = \
        config.get_settings().get('voucher_api.url', None)
    voucher_api_key = \
        config.get_settings().get('voucher_api.key', None)
    cloud_function_api_base_url = \
        config.get_settings().get('oice.cloud_function_api_base_url', None)
    es_log_whitelist_str = \
        config.get_settings().get('eslog.whitelist', None)
    es_log_whitelist = [path for path in es_log_whitelist_str.split(',')]
    es_log_key = config.get_settings().get('eslog.key', '')
    is_production = config.get_settings().get('isProduction', '') == 'true'

def get_crisp_secret_key():
    global crisp_secret_key
    if crisp_secret_key is not None:
        return crisp_secret_key
    else:
        return None

def get_stripe_api_key():
    global stripe_api_key
    if stripe_api_key is not None:
        return stripe_api_key
    else:
        return None


def get_stripe_client_id():
    global stripe_client_id
    if stripe_client_id is not None:
        return stripe_client_id
    else:
        return None


def get_stripe_plan_id():
    global stripe_plan_id
    if stripe_plan_id is not None:
        return stripe_plan_id
    else:
        return None


def get_android_iap_validator_url():
    global android_iap_validator_url
    if android_iap_validator_url is not None:
        return android_iap_validator_url
    else:
        return None


def get_ios_iap_validator_url():
    global ios_iap_validator_url
    if ios_iap_validator_url is not None:
        return ios_iap_validator_url
    else:
        return None

def get_ios_iap_validator_url_v2():
    global ios_iap_validator_url_v2
    if ios_iap_validator_url_v2 is not None:
        return ios_iap_validator_url_v2
    else:
        return None


def get_iap_sub_price():
    global iap_sub_price
    if iap_sub_price is not None:
        return iap_sub_price
    else:
        return 9.99


def get_iap_sub_price_payout_ratio():
    global iap_sub_price_payout_ratio
    if iap_sub_price_payout_ratio is not None:
        return iap_sub_price_payout_ratio
    else:
        return 0.7

def get_voucher_api_url():
    global voucher_api_url
    if voucher_api_url is not None:
        return voucher_api_url
    else:
        return None


def get_voucher_api_key():
    global voucher_api_key
    if voucher_api_key is not None:
        return voucher_api_key
    else:
        return None


def get_cloud_function_api_base_url():
    global cloud_function_api_base_url
    if cloud_function_api_base_url is not None:
        return cloud_function_api_base_url
    else:
        return None


def get_es_log_whitelist():
    global es_log_whitelist
    if es_log_whitelist is not None:
        return es_log_whitelist
    else:
        return []

def get_es_log_key():
    global es_log_key
    return es_log_key

def get_is_production():
    global is_production
    return is_production

# function for setting general info in log
def set_basic_info_library_log(library, log_dict=None):
    if log_dict is None:
        log_dict = {}
    author = library.users[0] if library.users else None
    log_dict.update({
        'library': library.name,
        'description': library.description,
        'libraryId': library.id,
        'writer': author.display_name if author else None,
        'writerEmail': author.email if author else None,
        'writerId': author.id if author else None,
    })
    return log_dict


def set_basic_info_membership_log(user, log_dict=None):
    if log_dict is None:
        log_dict = {}
    if user:
        log_dict.update({
            'user': user.display_name,
            'email': user.email,
            'userId': user.id,
            'role': user.role,
            'expireDate': user.expire_date.isoformat() if user.expire_date else None,
            'isCancelled': user.is_cancelled,
            'isTrial': user.is_trial,
            'subscriptPlatform': user.platform,
            'createDate': user.created_at.isoformat(),
            'dayAfterCreate': (datetime.utcnow() - user.created_at).days,
        })
    return log_dict


def set_basic_info_oice_log(user, oice, log_dict=None):
    if log_dict is None:
        log_dict = {}
    log_dict.update({
        'user': user.display_name,
        'email': user.email,
        'userId': user.id,
        'createDate': user.created_at.isoformat(),
        'dayAfterCreate': (datetime.utcnow() - user.created_at).days,
        'oice': oice.filename,
        'oiceId': oice.id,
        'oiceUuid': oice.uuid,
        'story': oice.story.name,
        'storyId': oice.story_id,
    })
    return log_dict


def set_basic_info_oice_log_author(user=None, oice=None, log_dict=None):
    if log_dict is None:
        log_dict = {}
    if oice:
        if not user:
            user = oice.story.users[0]
        log_dict.update({
            'writer': user.display_name,
            'writerEmail': user.email,
            'writerId': user.id,
            'oice': oice.filename,
            'oiceId': oice.id,
            'oiceUuid': oice.uuid,
            'story': oice.story.name,
            'storyId': oice.story_id,
        })
    return log_dict


def set_basic_info_oice_source_log(user, oice, log_dict=None):
    if log_dict is None:
        log_dict = {}
    log_dict.update({
        'oiceSourceWriter': user.display_name,
        'oiceSourceWriterEmail': user.email,
        'oiceSourceWriterId': user.id,
        'oiceSource': oice.filename,
        'oiceSourceId': oice.id,
        'oiceSourceUuid': oice.uuid,
        'story': oice.story.name,
        'storyId': oice.story_id,
    })
    return log_dict


def set_register_log(data, action, log_dict=None):
    if log_dict is None:
        log_dict = {}
    if action:
        log_dict.update({
            'topic'                            : 'actionUser',
            'action'                           : action,
            'channel'                          : dict_get_value(data, ['branchData', '~channel'], 'direct'),
            'loginCTA_leadingReadEpisodeCount' : dict_get_value(data, ['remoteConfig', 'loginCTA', 'leadingReadEpisodeCount']),
            'loginCTA_periodicReadEpisodeCount': dict_get_value(data, ['remoteConfig', 'loginCTA', 'periodicReadEpisodeCount']),
        })
        log_dict = set_basic_info_referrer_log(
            dict_get_value(data, ['branchData', '+referrer'], 'none'),
            dict_get_value(data, ['branchData', 'referrer2'], 'none'),
            log_dict
        )
    return log_dict


def set_viewLock_log(data, action, log_dict=None):
    if log_dict is None:
        log_dict = {}
    if action:
        log_dict.update({
            'topic'                       : 'actionUser',
            'action'                      : action,
            'channel'                     : dict_get_value(data, ['branchData', '~channel'], 'direct'),
            'viewLock_maxReadEpisodeCount': dict_get_value(data, ['remoteConfig', 'viewLock', 'maxReadEpisodeCount']),
            'viewLock_warmUpDuration'     : dict_get_value(data, ['remoteConfig', 'viewLock', 'warmUpDuration']),
            'viewLock_coolDownDuration'   : dict_get_value(data, ['remoteConfig', 'viewLock', 'coolDownDuration']),
            'lockAt'                      : dict_get_value(data, ['viewLock', 'lockAt']),
            'unlockAt'                    : dict_get_value(data, ['viewLock', 'unlockAt']),
        })
        log_dict = set_basic_info_referrer_log(
            dict_get_value(data, ['branchData', '+referrer'], 'none'),
            dict_get_value(data, ['branchData', 'referrer2'], 'none'),
            log_dict
        )
    return log_dict


def set_basic_info_user_log(user, log_dict=None):
    if log_dict is None:
        log_dict = {}
    if user:
        log_dict.update({
            'user': user.display_name,
            'email': user.email,
            'userId': user.id,
            'createDate': user.created_at.isoformat(),
            'dayAfterCreate': (datetime.utcnow() - user.created_at).days,
        })
    return log_dict


# handle +referrer given by branch
def set_basic_info_referrer_log(referrer, referrer2, log_dict=None):
    if log_dict is None:
        log_dict = {}
    _referrer = referrer
    # if referrer is from oice web, try referrer2
    # fix for empty referrer
    if (get_upload_base_url() in referrer) and referrer2 != '' and referrer2 != 'none':
        _referrer = referrer2
    log_dict.update({ 'referrer': _referrer })
    return log_dict


# handle general data
def set_basic_info_log(request, log_dict=None):
    if log_dict is None:
        log_dict = {}

    client_ip = request.headers.get('X-Real-IP', '')
    forward_ip = request.headers.get('X-Forwarded-For', '').split(', ')[0]
    try:
        webhook_ip = dict_get_value(request.json_body, ['metadata', 'ip'])
    except Exception:
        webhook_ip = None

    log_dict.update({
        'remoteAddr'     : webhook_ip if webhook_ip else forward_ip or client_ip,
        'platform'       : request.headers.get('x-oice-platform', 'unknown'),
        'platformVersion': request.headers.get('x-oice-platform-version'),
        'browser'        : request.headers.get('x-oice-browser'),
        'browserVersion' : request.headers.get('x-oice-browser-version'),
        'appVersion'     : request.headers.get('x-oice-app-version'),
        'abtest'         : request.headers.get('x-oice-abtest'),
    })
    return log_dict


def log_block_message(log_dict, email, oice):
    user = UserQuery(DBSession).fetch_user_by_email(email=email).one()
    log_dict = set_basic_info_oice_log(user, oice, log_dict)
    log_message(KAFKA_TOPIC_BLOCK, log_dict)
    return


# function to log error
def log_error_message(code, message, request):
    log_dict = {
        'errorCode': code,
        'errorMessage': message,
        'method': request.method,
        'path': request.path,
        'email': request.authenticated_userid,
    }
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_ERROR, log_dict)
    return


def get_request_user(request):
    return UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()


def check_is_language_valid(language):
    if language is None:
        return None
    if language.lower().replace('-', '_') not in locale.locale_alias or len(language) > 5:
        raise ValidationError("ERR_INVALID_LANGUAGE")
    return language


@view_config(context=DBAPIError, renderer='json')
def db_error(exc, request):
    code = 500
    message = str(exc)
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message,
    }


@view_config(context=HTTPForbidden, renderer='json')
def permission_denied(exec, request):
    if not authenticated_userid(request):
        code = 401
        message = 'ERR_UNAUTHORIZED'
        request.response.status_code = code
        request.response.headerlist.append(('WWW-Authenticate', ''))
    else:
        code = 403
        message = 'ERR_FORBIDDEN'
        request.response.status_code = code

    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message,
    }


@view_config(context=NoResultFound, renderer='json')
def object_not_found(exc, request):
    code = 404
    message = str(exc) if len(str(exc)) > 0 else 'ERR_ITEM_NOT_FOUND'
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message,
    }


@view_config(context=ValidationError, renderer='json')
def validation_error(exc, request):
    code = 400
    message = str(exc)
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message if message else 'ERR_INVALID_RESQUEST_PARAMS',
    }


@view_config(context=stripe.error.CardError, renderer='json')
def stripe_card_error(exc, request):
    code = 400
    message = str(exc)
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message,
    }


@view_config(context=stripe.error.InvalidRequestError, renderer='json')
def stripe_invalid_request(exc, request):
    code = 400
    message = str(exc)
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message,
    }


@view_config(context=stripe.error.StripeError, renderer='json')
def stripe_generic_error(exc, request):
    code = 400
    message = str(exc)
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message,
    }


@view_config(context=Exception, renderer='json')
def general_error(exc, request):
    if not is_production:
        raise exc

    code = 500
    message = str(exc)
    request.response.status_code = code
    log_error_message(code, message, request)
    return {
        'code': code,
        'message': message if message else 'ERR_GENERAL_ERROR',
    }
