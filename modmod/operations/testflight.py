import re
import requests

from modmod.exc import ValidationError
from ..config import (
    get_testflight_account,
    get_testflight_pass,
    get_testflight_provider_id,
    get_testflight_app_id,
    get_testflight_testers_group_id,
)


# Ref: https://github.com/Donohue/testflight_invite

ITUNESCONNECT_API_BASE_URL = 'https://itunesconnect.apple.com'
TESTFLIGHT_TESTERS_API_ENDPOINT = None

def get_itunesconnect_service_key():
    # Look for the service key in the login controller js file
    # Possibly will break in the future
    url = ITUNESCONNECT_API_BASE_URL + '/itc/static-resources/controllers/login_cntrl.js'
    response = requests.get(url)
    matches = re.search(r"itcServiceKey = '(.*)'", response.text)
    if not matches:
        raise ValidationError('ERR_ITUNECONNECT_SERVICE_KEY_NOT_FOUND')
    return matches.group(1)


def send_testflight_invitation(email, first_name=None, last_name=None):
    if not re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email):
        raise ValidationError('ERR_TESTFLIGHT_INVALID_TESTER_EMAIL')

    session = requests.Session()

    # Login to iTunes Connect
    url = 'https://idmsa.apple.com/appleauth/auth/signin'
    headers = {
        'X-Apple-Widget-Key': get_itunesconnect_service_key(),
    }
    payload = {
        'accountName': get_testflight_account(),
        'password': get_testflight_pass(),
    }
    response = session.post(url, headers=headers, json=payload)
    if response.status_code != requests.codes.ok:
        raise ValidationError('ERR_ITUNECONNECT_LOGIN_FAILURE')

    # Check whether the email has already joined TestFlight
    payload = {
        'search': email,
        'sort': 'status',
        'order': 'dsc',
        'limit': 1,
    }

    if TESTFLIGHT_TESTERS_API_ENDPOINT is None:
        TESTFLIGHT_TESTERS_API_ENDPOINT = ITUNESCONNECT_API_BASE_URL + (
                                              '/testflight/v2' +
                                              '/providers/%(provider_id)s' +
                                              '/apps/%(app_id)s' +
                                              '/groups/%(group_id)s' +
                                              '/testers'
                                          ) % {
                                              'provider_id': get_testflight_provider_id(),
                                              'app_id': get_testflight_app_id(),
                                              'group_id': get_testflight_testers_group_id(),
                                          }

    response = session.get(TESTFLIGHT_TESTERS_API_ENDPOINT, params=payload)
    search_results = response.json()['data']

    if not search_results:
        # Send invitation email and add the email to testers group
        payload = [{
            'email': email,
            'firstName': first_name,
            'lastName': last_name,
        }]
        response = session.post(TESTFLIGHT_TESTERS_API_ENDPOINT, json=payload)
        if response.status_code != requests.codes.ok:
            raise ValidationError('ERR_TESTFLIGHT_ADD_TESTER_FAILURE')
    else:
        tester = search_results[0]
        if tester['email'] == email:
            status = tester['status']

            if status == 'installed':
                raise ValidationError('ERR_TESTFLIGHT_TESTER_EXIST')

            elif status == 'invited':
                # Resend invitation
                url = ITUNESCONNECT_API_BASE_URL + '/testflight/v1/invites/%s/resend' % APP_ID
                response = session.post(url, params={'testerId': tester['id']})
                if response.status_code != requests.codes.ok:
                    raise ValidationError('ERR_TESTFLIGHT_RESEND_INVITATION_FAILURE')
