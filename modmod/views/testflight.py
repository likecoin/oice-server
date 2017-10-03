from cornice import Service
from modmod.exc import ValidationError

from ..operations.testflight import send_testflight_invitation


testflight_invitation = Service(name='testflight_invitation',
                                path='testflight/invitation',
                                renderer='json')

testflight_invitation_typeform = Service(name='testflight_invitation_typeform',
                                         path='testflight/invitation/typeform',
                                         renderer='json')


@testflight_invitation.post()
def add_tester(request):
    try:
        email = request.json_body['email']
        first_name = request.json_body.get('firstName')
        last_name = request.json_body.get('lastName')
    except Exception:
        raise ValidationError('ERR_ADD_TESTER_INVALID_PARAMS')

    send_testflight_invitation(email, first_name, last_name)

    return {
        'code': 200,
        'message': 'ok',
    }


@testflight_invitation_typeform.post()
def add_tester_from_typeform_webhook(request):
    try:
        # Ref: https://www.typeform.com/help/webhooks/#payload
        answers = request.json_body['form_response']['answers']
        email = next(a['email'] for a in answers if a['field']['type'] == 'email')
    except Exception:
        raise ValidationError('ERR_TESTFLIGHT_WEBHOOK_INVALID_PARAMS')

    send_testflight_invitation(email)

    return {
        'code': 200,
        'message': 'ok',
    }
