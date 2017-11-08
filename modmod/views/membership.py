from cornice import Service
from datetime import datetime
import logging
import math
import stripe
import requests
import sys
import json
from pyramid.httpexceptions import HTTPForbidden
from modmod.exc import ValidationError

from ..models import (
    DBSession,
    User,
    UserQuery,
    OiceQuery,
)

from .util import (
    update_user_mailchimp_stage,
    log_message,
)

from . import (
    get_stripe_api_key,
    get_stripe_client_id,
    get_stripe_plan_id,
    set_basic_info_membership_log,
    set_basic_info_log,
    set_basic_info_oice_log_author,
    get_android_iap_validator_url,
    get_ios_iap_validator_url,
    get_iap_sub_price,
    get_iap_sub_price_payout_ratio,
)
from ..operations import user as UserOperations

log = logging.getLogger(__name__)
KAFKA_TOPIC_USER = 'oice-user'
membership = Service(name='membership',
                          path='membership',
                          renderer='json')

membership_connect = Service(name='membership_connect',
                              path='membership/connect',
                              renderer='json')

membership_android= Service(name='membership_android',
                              path='membership/android',
                              renderer='json')

membership_ios = Service(name='membership_ios',
                              path='membership/ios',
                              renderer='json')

strip_hook = Service(name='strip_hook',
                        path='strip_hook',
                        renderer='json')

strip_connect_hook = Service(name='strip_connect_hook',
                                path='strip_connect_hook',
                                renderer='json')

trial_hook = Service(name='trial_hook',
                        path='trial_hook',
                        renderer='json')


@membership.post(permission='get')
def post_new_subscription(request):
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
        if not user:
            raise HTTPForbidden

        # Get the credit card details submitted by the form
        token = request.json_body

        customer = None

        if user.is_new_subscribe:
            log_action = 'startSubscribe'
        else:
            log_action = 'reSubscribe'

        if not user.customer_id:
            # Create a Customer
            customer = stripe.Customer.create(
              source=token['id'],
              plan=get_stripe_plan_id(),
              email=request.authenticated_userid
            )

            user.customer_id = customer.id

        else:
            # update customer's token
            customer = stripe.Customer.retrieve(user.customer_id)
            customer.source = token['id']
            customer.save()

        subscription_list = stripe.Subscription.all(
                              customer=user.customer_id,
                              plan=get_stripe_plan_id(),
                              status='active'
                            )

        current_subscription = None

        if subscription_list and subscription_list.data:
            current_subscription = subscription_list.data[0]
            current_subscription.plan = get_stripe_plan_id()
            current_subscription.save()
            new_expire_date = datetime.fromtimestamp(current_subscription.current_period_end)
            if user.expire_date is None or new_expire_date > user.expire_date:
                user.expire_date = new_expire_date
                user.platform = 'stripe'
        else:
            if user.expire_date and user.expire_date > datetime.utcnow():
                # Has an deleted sub not expired
                expire_time_s = (user.expire_date - datetime.utcfromtimestamp(0)).total_seconds()
                current_subscription = stripe.Subscription.create(
                  customer=customer,
                  plan=get_stripe_plan_id(),
                  trial_end=expire_time_s
                )
            else:
                current_subscription = stripe.Subscription.create(
                  customer=customer,
                  plan=get_stripe_plan_id()
                )
                user.expire_date = datetime.fromtimestamp(current_subscription.current_period_end)

        user.role = 'paid'
        user.is_trial = False
        user.is_cancelled = False

        log_dict = {
            'action': log_action,
            'token': token,
        }
        log_dict = set_basic_info_membership_log(user, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_USER, log_dict)

        return {
            "user": user.serialize(),
            "message": "ok",
            "code": 200
        }

    except:
        e = sys.exc_info()[:2]
        raise ValidationError(str(e))


@membership.delete(permission='get')
def cancel_subscription(request):
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

        subscription_list = stripe.Subscription.all(
                              customer=user.customer_id,
                              plan=get_stripe_plan_id(),
                              status='active'
                            )

        if subscription_list and subscription_list.data:
            current_subscription = subscription_list.data[0]
            current_subscription.delete(at_period_end=True)
            user.is_cancelled = True

            log_dict = {
                'action': 'cancelSubscribe',
            }
            log_dict = set_basic_info_membership_log(user, log_dict)
            log_dict = set_basic_info_log(request, log_dict)
            log_message(KAFKA_TOPIC_USER, log_dict)

            return {
                "user": user.serialize(),
                "message": "ok",
                "code": 200
            }
        else:
            raise ValidationError('subscription not found')

    except:
        e = sys.exc_info()[:2]
        raise ValidationError(str(e))

@membership_connect.post(permission='get')
def register_connect_oauth(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    payload = request.json_body
    data = {
        "grant_type": "authorization_code",
        "client_id": get_stripe_client_id(),
        "client_secret": get_stripe_api_key(),
        "code": payload['code'],
    }

    url = 'https://connect.stripe.com/oauth/token'
    resp = requests.post(url, params=data)
    # Do not store access_token for now since we do not need it
    # user.stripe_access_token = resp.json().get('access_token')
    # user.stripe_refresh_token = resp.json().get('refresh_token')
    user.stripe_account_id = resp.json().get('stripe_user_id')
    return {
        "user": user.serialize(),
        "message": "ok",
        "code": 200
    }

@membership_connect.delete(permission='get')
def revoke_stripe_access(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    requests.post(
        'https://connect.stripe.com/oauth/deauthorize',
        params={
            'client_id': get_stripe_client_id(),
            'stripe_user_id': user.stripe_account_id,
        },
        headers={ 'Authorization': 'Bearer ' + get_stripe_api_key() }
    )

    user.stripe_account_id = None

    # Remove all user's on sale libraries from asset store
    user_on_sale_libraries = [l for l in user.libraries if not l.is_deleted and l.price > 0]
    for library in user_on_sale_libraries:
        library.launched_at = None

    return {
        "user": user.serialize(),
        "message": "ok",
        "code": 200
    }

@membership_android.post(permission='get')
def post_android_subscription(request):
    payload = request.json_body

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    if user.is_new_subscribe:
        log_action = 'startSubscribe'
    else:
        log_action = 'reSubscribe'
    
    payload = {'receipt': payload['receipt']}
    url = get_android_iap_validator_url()
    r = requests.post(url, data=payload)
    result = None
    if r.status_code == requests.codes.ok:
        response_content = r.text
        response_dict = json.loads(response_content)
        code = response_dict['code']
        if code != 0:
            raise ValidationError('ERR_IAP_VALIDATOR_NON_ZERO')
        original_transaction_id = response_dict['original_transaction_id']
        expire_date = response_dict['expires_date']
        developer_payload = response_dict['developer_payload']
        payout_amount = int(math.ceil(get_iap_sub_price() * get_iap_sub_price_payout_ratio() * 100))/100.0
        result = UserOperations.handle_membership_update(user, original_transaction_id, \
                                                expire_date, developer_payload, "android", \
                                                payout_amount)
    else:
        raise ValidationError('ERR_IAP_VALIDATOR_CONN')

    log_dict = {
        'action': log_action,
        'token': payload,
    }
    if developer_payload.split(':')[0] == 'subs':
        developer_payload = developer_payload.split(':')[2:]
        developer_payload = ':'.join(developer_payload)
    payload_dict = json.loads(developer_payload)
    if 'oiceId' in payload_dict:
        oice_id = payload_dict['oiceId']
        oice = OiceQuery(DBSession).get_by_id(oice_id=oice_id)
        log_dict = set_basic_info_oice_log_author(oice=oice, log_dict=log_dict)
    log_dict = set_basic_info_membership_log(user, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)

    return {
        "user": user.serialize(),
        "message": result,
        "code": 200
    }

@membership_ios.post(permission='get')
def post_ios_subscription(request):

    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    if user.is_new_subscribe:
        log_action = 'startSubscribe'
    else:
        log_action = 'reSubscribe'

    payload = request.json_body
    receipt = {'receipt': payload['receipt']}
    url = get_ios_iap_validator_url()
    r = requests.post(url, data=receipt)
    result = None
    if r.status_code == requests.codes.ok:
        response_content = r.text
        response_dict = json.loads(response_content)
        code = response_dict['code']
        if code != 0:
            raise ValidationError('ERR_IAP_VALIDATOR_NON_ZERO')

        original_transaction_id = response_dict['original_transaction_id']
        expire_date = response_dict['expires_date']
        developer_payload = payload['developerPayload']
        payout_amount = int(math.ceil(get_iap_sub_price() * get_iap_sub_price_payout_ratio() * 100))/100.0
        result = UserOperations.handle_membership_update(user, original_transaction_id, \
                                            expire_date, developer_payload, "ios", \
                                            payout_amount)
    else:
        raise ValidationError('ERR_IAP_VALIDATOR_CONN')

    length = math.ceil(len(payload["receipt"])/2)
    log_dict = {
        'action': log_action,
        'receiptPartA': payload["receipt"][0:length],
        'receiptPartB': payload["receipt"][length:],
    }
    payload_dict = json.loads(developer_payload)
    if 'oiceId' in payload_dict:
        oice_id = payload_dict['oiceId']
        oice = OiceQuery(DBSession).get_by_id(oice_id=oice_id)
        log_dict = set_basic_info_oice_log_author(oice=oice, log_dict=log_dict)
    log_dict = set_basic_info_membership_log(user, log_dict)
    log_dict = set_basic_info_log(request, log_dict)
    log_message(KAFKA_TOPIC_USER, log_dict)

    return {
        "user": user.serialize(),
        "message": result,
        "code": 200
    }

@strip_hook.post()
def get_stripe_webhook(request):
    try:
        user = None
        event_json = request.json_body
        event = stripe.Event.retrieve(event_json["id"])
        if 'invoice.payment_succeeded' == event.type:
            invoice = event.data.object
            current_subscription = stripe.Subscription.retrieve(invoice.subscription)
            user = UserQuery(DBSession).fetch_user_by_customer_id(customer_id = invoice.customer)
            user.role = 'paid'
            user.is_trial = False
            new_expire_date = datetime.fromtimestamp(current_subscription.current_period_end)
            if user.expire_date is None or new_expire_date > user.expire_date:
                user.expire_date = new_expire_date
                user.platform = 'stripe'
            log_dict = {
                'action': 'subscriptionExtended',
            }
            log_dict = set_basic_info_membership_log(user, log_dict)
            log_dict = set_basic_info_log(request, log_dict)
            log_message(KAFKA_TOPIC_USER, log_dict)

        elif 'customer.subscription.deleted' == event.type:
            subscription = event.data.object
            customer = stripe.Customer.retrieve(subscription.customer)
            user = UserQuery(DBSession).fetch_user_by_customer_id(customer_id = subscription.customer)
            # Do not hard reset expire date due to possibly still have other platform's subscription
            # user.role = 'user'
            # user.expire_date = datetime.utcnow()
            # log_dict = {
            #     'action': 'subscriptionExpired',
            # }
            # log_dict = set_basic_info_membership_log(user, log_dict)
            # log_message(KAFKA_TOPIC_USER, log_dict)

        return {
            "message": "ok",
            "code": 200
        }

    except:
        e = sys.exc_info()[:2]
        raise ValidationError(str(e))

@strip_connect_hook.post()
def get_stripe_connect_webhook(request):
    try:
        user = None
        event_json = request.json_body
        event = stripe.Event.retrieve(event_json["id"])
        if 'account.application.deauthorized' == event.type:
            account = event.data.object
            user = UserQuery(DBSession).fetch_user_by_stripe_account_id(stripe_account_id = account.id)
            user.stripe_account_id = None
        return {
            "message": "ok",
            "code": 200
        }

    except:
        e = sys.exc_info()[:2]
        raise ValidationError(str(e))

@trial_hook.post()
def check_user_trial_expire(request):
    current_time = datetime.utcnow()
    expire_users = DBSession.query(User) \
                   .filter(User.role == "paid") \
                   .filter(User.expire_date < current_time) \
                   .all()
    for user in expire_users:
        user.role = 'user'
        if user.is_trial:
            update_user_mailchimp_stage(user=user, stage=5)
            log_dict = {
                'action': 'trialExpired',
            }
        else:
            log_dict = {
                'action': 'subscriptionExpired',
            }
        log_dict = set_basic_info_membership_log(user, log_dict)
        log_dict = set_basic_info_log(request, log_dict)
        log_message(KAFKA_TOPIC_USER, log_dict)
    return {
        "message": "ok",
        "code": 200
    }
