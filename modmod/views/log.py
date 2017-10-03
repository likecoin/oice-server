import sys 
from cornice import Service 
import logging 
from pyramid.httpexceptions import HTTPForbidden 
from pyramid.security import authenticated_userid
from modmod.exc import ValidationError 
from .util import log_message 

 
from ..models import ( 
    DBSession, 
    OiceQuery, 
    UserQuery, 
) 
 
from . import (
    dict_get_value,
    set_basic_info_oice_source_log,
    set_basic_info_referrer_log,
    get_es_log_whitelist,
    get_es_log_key,
    set_basic_info_user_log,
    set_basic_info_membership_log,
    set_basic_info_oice_log_author,
    set_basic_info_log,
    set_register_log,
    set_viewLock_log,
)
 
KAFKA_TOPIC_OICE = 'oice-oice' 
KAFKA_TOPIC_USER = 'oice-user' 
KAFKA_TOPIC_ACQUISITION = 'oice-acquisition' 


log = logging.getLogger(__name__)  # log debug message
log_module = sys.modules[__name__]
_LOG_SUCCESS = {
    'code': 200,
    'message': 'ok',
}

log_service = Service(name='log_service',
                      path='log/{log_name}',
                      renderer='json')

log_whitelist_ips = [
    # branch.io
    # Ref: https://dev.branch.io/data-exchange/webhooks/advanced/#authenticating-webhook-events
    '52.9.159.121',
    '52.9.176.205',
    '52.9.188.221',
    '52.9.188.236',
]

@log_service.post()
def log_dispatch(request):
    client_ip = request.headers.get('X-Real-IP', '')
    forward_ip = request.headers.get('X-Forwarded-For', '').split(', ')[0]
    header_key = request.headers.get('Log-Key', '')
    body_key = dict_get_value(request.json_body, ['link_data', 'data', 'log_key'])
    log_name = request.matchdict['log_name']
    log_key = get_es_log_key()

    if (
        client_ip in log_whitelist_ips
        or forward_ip in log_whitelist_ips
        or header_key == log_key
        or (log_name in get_es_log_whitelist() and body_key == log_key)
       ):
        try:
            func = getattr(log_module, log_name)
            # beascuse of using set_basic_info_log later
            return func(request)
        except AttributeError:
            raise ValidationError('ERR_LOG_NAME_NOT_FOUND')
    else:
        raise HTTPForbidden

# expected platform: webhook
def logClickDeeplink(request):
    data = request.json_body
    # fix for branch.io bug
    if dict_get_value(data, ['link_data', 'data', '+click_timestamp']):
        log_dict = {
            'topic'    : 'actionAcquisition',
            'action'   : 'clickDeeplink',
            'channel'  : dict_get_value(data, ['link_data', 'data', '~channel'], 'direct'),
            'os'       : dict_get_value(data, ['os'], 'unknown'),
            'branchId' : dict_get_value(data, ['link_data', 'branch_id'], 'none'),
            'clickId'  : dict_get_value(data, ['click_id'], 'none'),
            'userAgent': dict_get_value(data, ['metadata', 'userAgent'], 'none'),
            'brand'    : dict_get_value(data, ['metadata', 'brand'], 'none'),
            'model'    : dict_get_value(data, ['metadata', 'model'], 'none'),
            'country'  : dict_get_value(data, ['metadata', 'country'], 'none'),
            'osVersion': dict_get_value(data, ['metadata', 'os_version'], 'none'),
            'ipString' : dict_get_value(data, ['metadata', 'ip'], 'none'),
        }
        log_dict = set_basic_info_referrer_log(
            dict_get_value(data, ['link_data', 'data', '+referrer'], 'none'),
            dict_get_value(data, ['link_data', 'data', 'referrer2'], 'none'),
            log_dict
        )
        if dict_get_value(data, ['link_data', 'data', 'uuid']):
            oice_source = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['link_data', 'data', 'uuid']))
            if oice_source:
                log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_dict.update({
            'abtest'   : dict_get_value(data, ['link_data', 'data', 'abtest']),
        })
        log_message(KAFKA_TOPIC_ACQUISITION,log_dict)
    return _LOG_SUCCESS


# expected platform: webhook
def logOpenDeeplink(request):
    data = request.json_body
    log_dict = {
        'topic'           : 'actionAcquisition',
        'action'          : 'openDeeplink',
        'channel'         : dict_get_value(data, ['session_referring_link_data', 'data', '~channel'], 'direct'),
        'os'              : dict_get_value(data, ['os'], 'unknown'),
        'branchId'        : dict_get_value(data, ['session_referring_link_data', 'branch_id'], 'none'),
        'clickId'         : dict_get_value(data, ['session_referring_click_id'], 'none'),
        'country'         : dict_get_value(data, ['metadata', 'country'], 'none'),
        'osVersion'       : dict_get_value(data, ['metadata', 'os_version'], 'none'),
        'ipString'        : dict_get_value(data, ['metadata', 'ip'], 'none'),
        'firstReferringAt': dict_get_value(data, ['metadata', 'first_referring_click_timestamp']),
    }
    log_dict = set_basic_info_referrer_log(
        dict_get_value(data, ['session_referring_link_data', 'data', '+referrer'], 'none'),
        dict_get_value(data, ['session_referring_link_data', 'data', 'referrer2'], 'none'),
        log_dict
    )
    if dict_get_value(data, ['session_referring_link_data', 'data', 'uuid']):
        oice_source = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['session_referring_link_data', 'data', 'uuid']))
        if oice_source:
            log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_dict.update({
            'abtest'   : dict_get_value(data, ['session_referring_link_data', 'data', 'abtest']),
    })
    log_message(KAFKA_TOPIC_ACQUISITION,log_dict)
    return _LOG_SUCCESS


# expected platform: webhook
def logInstallDeeplink(request):
    data = request.json_body
    log_dict = {
        'topic'           : 'actionAcquisition',
        'action'          : 'installDeeplink',
        'channel'         : dict_get_value(data, ['session_referring_link_data', 'data', '~channel'], 'direct'),
        'os'              : dict_get_value(data, ['os'], 'unknown'),
        'branchId'        : dict_get_value(data, ['session_referring_link_data', 'branch_id'], 'none'),
        'clickId'         : dict_get_value(data, ['session_referring_click_id'], 'none'),
        'country'         : dict_get_value(data, ['metadata', 'country'], 'none'),
        'osVersion'       : dict_get_value(data, ['metadata', 'os_version'], 'none'),
        'ipString'        : dict_get_value(data, ['metadata', 'ip'], 'none'),
        'firstReferringAt': dict_get_value(data, ['metadata', 'first_referring_click_timestamp']),
    }
    log_dict = set_basic_info_referrer_log(
        dict_get_value(data, ['session_referring_link_data', 'data', '+referrer'], 'none'),
        dict_get_value(data, ['session_referring_link_data', 'data', 'referrer2'], 'none'),
        log_dict
    )
    if dict_get_value(data, ['session_referring_link_data', 'data', 'uuid']):
        oice_source = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['session_referring_link_data', 'data', 'uuid']))
        if oice_source:
            log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_dict.update({
            'abtest'   : dict_get_value(data, ['session_referring_link_data', 'data', 'abtest']),
        })
    log_message(KAFKA_TOPIC_ACQUISITION, log_dict)
    return _LOG_SUCCESS

       
def logJoinCompetition(request):
    data = request.json_body
    log_dict = {
        'topic' : 'actionUser',
        'action': 'joinCompetition',
    }
    log_dict.update(data)
    user = UserQuery(DBSession).fetch_user_by_email(data.get('email')).one_or_none()
    if user:
        log_dict = set_basic_info_user_log(user, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: web
def logOiceWebAcquisition(request):
    data = request.json_body
    user = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = {
        'topic'   : 'actionAcquisition',
        'action'  : 'oiceWebAcquisition',
        'referrer': dict_get_value(data, ['referrer'], 'none') if dict_get_value(data, ['referrer'], 'none') != '' else 'none',
        'channel' : dict_get_value(data, ['channel'], 'direct'),
    }
    log_dict = set_basic_info_membership_log(user, log_dict)
    if dict_get_value(data, ['uuid']):
        oice_source = OiceQuery(DBSession).get_by_uuid(data.get('uuid',None))
        if oice_source:
            log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_ACQUISITION, log_dict)
    return _LOG_SUCCESS


# expected platform: web
def logClickWeb(request):
    data = request.json_body
    user = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = {
        'topic'        : 'actionAcquisition',
        'action'       : 'clickWeb',
        'actionTrigger': dict_get_value(data, ['actionTrigger']),
        'url'          : dict_get_value(data, ['url']),
        'referrer'     : dict_get_value(data, ['referrer'], 'none') if dict_get_value(data, ['referrer'], 'none') != '' else 'none',
        'channel'      : dict_get_value(data, ['channel'], 'direct'),
    }
    if user:
        log_dict = set_basic_info_membership_log(user, log_dict)
    if dict_get_value(data, ['uuid']):
        oice_source = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
        if oice_source:
            log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_ACQUISITION, log_dict)
    return _LOG_SUCCESS


# expected platform: web
def logReadOice(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = {
        'topic'   : 'actionOice',
        'action'  : 'readOice',
        'url'     : dict_get_value(data, ['url']),
        'referrer': dict_get_value(data, ['referrer'], 'none') if dict_get_value(data, ['referrer'], 'none') != '' else 'none',
        'channel' : dict_get_value(data, ['channel'], 'direct'),
    }
    log_dict = set_basic_info_membership_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return _LOG_SUCCESS


# expected platform: web
def logOiceWebBehaviour(request):
    data = request.json_body
    user = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = {
        'topic'   : 'actionAcquisition',
        'action'  : 'oiceWebBehaviour',
        'referrer': dict_get_value(data, ['referrer'], 'none') if dict_get_value(data, ['referrer'], 'none') != '' else 'none',
        'channel' : dict_get_value(data, ['channel'], 'direct'),
    }
    if user:
        log_dict = set_basic_info_membership_log(user, log_dict)
    if dict_get_value(data, ['uuid']):
        oice_source = OiceQuery(DBSession).get_by_uuid(data.get('uuid',None))
        if oice_source:
            log_dict = set_basic_info_oice_source_log(oice_source.story.users[0], oice_source, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logRequestRegister(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = set_register_log(data,'requestRegister', {})
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_OICE, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logSucceededRegister(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = set_register_log(data,'succeededRegister', {})
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logCancelRegister(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = set_register_log(data,'cancelRegister', {})
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logFailedRegister(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = set_register_log(data,'failedRegister', {})
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logStartViewLock(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = set_viewLock_log(data, 'startViewLock')
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logEndViewLock(request):
    data = request.json_body
    oice = OiceQuery(DBSession).get_by_uuid(dict_get_value(data, ['uuid']))
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = set_viewLock_log(data, 'endViewLock', {})
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_oice_log_author(oice.story.users[0], oice, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS


# expected platform: app
def logFirstTimeOpen(request):
    data = request.json_body
    viewer = UserQuery(DBSession).fetch_user_by_email(request.authenticated_userid).one_or_none()
    log_dict = {
        'topic'   : 'actionUser',
        'action'  : 'firstTimeOpen',
    }
    log_dict = set_basic_info_user_log(viewer, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)
    return _LOG_SUCCESS





# # Dispatch log/log_sample to this function
# def log_sample(data):
#    log.error(data['key'])
#    return _LOG_SUCCESS
