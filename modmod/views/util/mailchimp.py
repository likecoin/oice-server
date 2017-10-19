import requests
import logging

from modmod.exc import ValidationError

from ...models import (
    DBSession,
    UserQuery,
)


log = logging.getLogger(__name__)

MAILCHIMP_SUBSCRIBE_URL = None


def init_mailchimp(setting):
    global MAILCHIMP_SUBSCRIBE_URL
    MAILCHIMP_SUBSCRIBE_URL = setting.get('mailchimp.subscribe.url', None)


def construct_mailchimp_payload(user=None, **kwargs):
    fields = {}
    properties = {}

    email = kwargs.get('email')
    first_name = kwargs.get('first_name')
    last_name = kwargs.get('last_name')
    language = kwargs.get('language')
    stage = kwargs.get('stage')

    if user:
        if not email:
            email = user.email
        if not stage:
            stage = user.mailchimp_stage
        if not language:
            language = user.language

    if not email:
        raise ValidationError('ERR_MAILCHIMP_UPDATE_WITHOUT_EMAIL')

    if first_name:
        fields['FNAME'] = first_name

    if last_name:
        fields['LNAME'] = last_name

    if stage:
        fields['STAGE'] = stage

    if language:
        # Give language code only, for example 'zh-Hant' -> 'zh'
        # http://kb.mailchimp.com/lists/manage-contacts/view-and-edit-subscriber-languages#Language-Codes
        properties['language'] = language[:2]
        fields['LANGUAGE'] = language

    return {
        'email': email,
        'properties': properties,
        'fields': fields,
    }


def call_mailchimp_api(payload):
    global MAILCHIMP_SUBSCRIBE_URL
    requests.post(MAILCHIMP_SUBSCRIBE_URL, json=payload)


def subscribe_mailchimp(google_token, user, **kwargs):
    payload = {
        **construct_mailchimp_payload(user=user, **kwargs),
        'status': 'subscribed',
        'interests': {
            'general': True,
        },
    }

    # Get user info from Google
    url = 'https://www.googleapis.com/userinfo/v2/me'
    headers = {'Authorization': 'Bearer ' + google_token}
    response = requests.get(url, headers=headers)
    if response.status_code == requests.codes.ok:
        user_info = response.json()
        if 'given_name' in user_info:
            payload['fields']['FNAME'] = user_info['given_name']
        if 'family_name' in user_info:
            payload['fields']['LNAME'] = user_info['family_name']

    call_mailchimp_api(payload)


def update_mailchimp_field(user=None, **kwargs):
    payload = construct_mailchimp_payload(user=user, **kwargs)
    call_mailchimp_api(payload)


def update_user_mailchimp_stage(user=None, email=None, stage=1):
    if not user and email:
        user = UserQuery(DBSession).fetch_user_by_email(email).one_or_none()

    if not user:
        raise ValidationError('ERR_MAILCHIMP_UPDATE_WITHOUT_USER')

    if user.mailchimp_stage < stage:
        user.mailchimp_stage = stage
        update_mailchimp_field(email=email, stage=stage)
