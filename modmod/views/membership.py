from cornice import Service
from datetime import datetime
import base64
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
    LibraryQuery,
)

from .util import (
    log_message,
)

from .store import (
    KAFKA_TOPIC_LIBRARY
)

from . import (
    get_site_external_host,
    get_stripe_api_key,
    get_stripe_price_id,
    set_basic_info_membership_log,
    set_basic_info_log,
    set_basic_info_oice_log_author,
    set_basic_info_library_log,
    get_voucher_api_url,
    get_voucher_api_key,
)
from ..operations import user as UserOperations

log = logging.getLogger(__name__)
KAFKA_TOPIC_USER = 'oice-user'

membership_checkout = Service(name='membership_checkout',
                          path='membership/checkout',
                          renderer='json')

membership_portal = Service(name='membership_portal',
                          path='membership/portal',
                          renderer='json')

membership_connect = Service(name='membership_connect',
                              path='membership/connect',
                              renderer='json')

membership = Service(name='membership',
                          path='membership',
                          renderer='json')

strip_hook = Service(name='strip_hook',
                        path='strip_hook',
                        renderer='json')

trial_hook = Service(name='trial_hook',
                        path='trial_hook',
                        renderer='json')

voucher_redeem_code = Service(
    name='version_voucher_redeem_code',
    path='v{version}/voucher/redeem/{code}',
    renderer='json',
)

@membership_checkout.post(permission='get')
def init_new_subscription(request):
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
        if not user:
            raise HTTPForbidden

        customer_id = None

        if user.customer_id:
            customer_id = user.customer_id

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': get_stripe_price_id(),
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url= 'https://' + get_site_external_host() + '/profile?action=backer_success',
            cancel_url= 'https://' + get_site_external_host() + '/profile?action=backer_cancel',
            automatic_tax={'enabled': True},
            customer=customer_id,
            customer_creation=None if customer_id else 'always',
            customer_email=None if customer_id else request.authenticated_userid,
            subscription_data={
                'metadata': {
                    'email': request.authenticated_userid,
                    'username': user.username,
                    'userId': user.id,
                }
            },
            metadata={
                'type': 'membership',
                'email': request.authenticated_userid,
                'username': user.username,
                'userId': user.id,
            },
        )

        url = checkout_session.url

        return {
            "url": url,
            "message": "ok",
            "code": 200
        }

    except:
        e = sys.exc_info()[:2]
        raise ValidationError(str(e))


@membership_portal.post(permission='get')
def go_to_membership_portal(request):
    try:
        user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

        if user.customer_id is None:
            raise ValidationError('subscription not found')

        portal_session = stripe.billing_portal.Session.create(
            customer=user.customer_id,
            return_url='https://' + get_site_external_host() + '/profile?action=backer_portal',
        )

        url = portal_session.url

        return {
            "url": url,
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

        subscription_list = stripe.Subscription.list(
                              customer=user.customer_id,
                              price=get_stripe_price_id(),
                              status='active'
                            )

        if subscription_list and subscription_list.data:
            current_subscription = subscription_list.data[0]
            current_subscription.cancel_at_period_end = True
            current_subscription.save()
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

    stripe_account_id = None

    if user.stripe_account_id:
        stripe_account_id = user.stripe_account_id
        current_account = stripe.Account.retrieve(user.stripe_account_id)
        if current_account.charges_enabled:
            raise ValidationError('ERR_STRIPE_ACCOUNT_ALREADY_CONNECTED')
    else:
        account = stripe.Account.create(
            type="express",
            email=request.authenticated_userid,
        )
        stripe_account_id = account.id
        user.stripe_account_id = account.id

    account_link = stripe.AccountLink.create(
        account=stripe_account_id,
        refresh_url='https://' + get_site_external_host() + '/profile?action=connect_refresh',
        return_url='https://' + get_site_external_host() + '/profile?action=connect_return',
        type="account_onboarding",
    )
    url = account_link.url

    return {
        "url": url,
        "message": "ok",
        "code": 200
    }

@membership_connect.get(permission='get')
def go_to_connect_dashboard(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one_or_none()
    if not user:
        raise HTTPForbidden

    if not user.stripe_account_id:
        raise ValidationError('ERR_STRIPE_ACCOUNT_ALREADY_CONNECTED')

    account_link = None

    stripe_account_id = user.stripe_account_id
    current_account = stripe.Account.retrieve(user.stripe_account_id)
    if current_account.charges_enabled:
        account_link = stripe.Account.create_login_link(
            user.stripe_account_id
        )
    else:
        account_link = stripe.AccountLink.create(
            account=stripe_account_id,
            refresh_url='https://' + get_site_external_host() + '/profile?action=connect_refresh',
            return_url='https://' + get_site_external_host() + '/profile?action=connect_return',
            type="account_onboarding",
        )
    url = account_link.url
    return {
        "url": url,
        "message": "ok",
        "code": 200
    }

@strip_hook.post()
def get_stripe_webhook(request):
    try:
        user = None
        event_json = request.json_body
        event = stripe.Event.retrieve(event_json["id"])

        if 'checkout.session.completed' == event.type:
            session = event.data.object
            if (session.metadata.type == 'library'):
                user_id = session.metadata.userId
                library_id = session.metadata.libraryId

                user = UserQuery(DBSession).get_user_by_id(user_id)
                if session.customer:
                    user.customer_id = session.customer

                library = LibraryQuery(DBSession).get_library_by_id(library_id)
                user.libraries_purchased.append(library)
                user.libraries_selected.append(library)

                log_dict = {
                    'action': 'buyLibrary',
                    'price': library.price,
                }
                log_dict = set_basic_info_library_log(library, log_dict)
                log_dict = set_basic_info_membership_log(user, log_dict)
                log_dict = set_basic_info_log(request, log_dict)
                log_message(KAFKA_TOPIC_LIBRARY, log_dict)

        elif 'invoice.paid' == event.type:
            invoice = event.data.object
            if invoice.subscription:
                current_subscription = stripe.Subscription.retrieve(invoice.subscription)
                user_id = current_subscription.metadata.userId
                user = UserQuery(DBSession).get_user_by_id(user_id)
                user.role = 'paid'
                user.is_trial = False
                user.is_cancelled = False
                user.customer_id = current_subscription.customer
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


@voucher_redeem_code.post(permission='get')
def redeem_voucher(request):
    user = UserQuery(DBSession).fetch_user_by_email(email=request.authenticated_userid).one()

    voucher_code = request.matchdict.get('code')
    url = get_voucher_api_url() + '/voucher/' + voucher_code + '/redeem'

    try:
        r = requests.post(
            url=url,
            headers={'Authentication': get_voucher_api_key()},
            data={'userId': user.id},
        )
        response = r.json()
    except Exception:
        pass
    else:
        code = response.get('code')

        if code == 'SUCCESS':
            new_expiry_date = datetime.strptime(response['redemption']['expireAt'], '%Y-%m-%dT%H:%M:%SZ')

            # Allow extend the expiry date
            if user.expire_date is not None and new_expiry_date - datetime.now() > new_expiry_date - user.expire_date:
                new_expiry_date = user.expire_date + (new_expiry_date - datetime.now())

            if user.expire_date is None or new_expiry_date > user.expire_date:
                user.role = 'paid'
                user.is_trial = False
                user.is_cancelled = False
                user.expire_date = new_expiry_date

            return {
                'code': 200,
                'message': 'ok',
                'user': user.serialize(),
                'newExpiryDate': new_expiry_date.isoformat(),
            }

        elif code == 'INVALID_CODE':
            raise ValidationError('ERR_VOUCHER_CODE_INVALID')

        elif code == 'NOT_YET':
            raise ValidationError('ERR_VOUCHER_NOT_YET_EFFECTIVE')

        elif code == 'EXPIRED':
            raise ValidationError('ERR_VOUCHER_EXPIRED')

        elif code == 'REDEEMED_ALREADY':
            raise ValidationError('ERR_VOUCHER_REDEEMED_ALREADY')

        elif code == 'REACH_LIMIT':
            raise ValidationError('ERR_VOUCHER_REDEMPTION_LIMIT_REACH')

    raise ValidationError('ERR_VOUCHER_SERVICE_FAILURE')
